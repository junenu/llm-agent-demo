"""
LLM‑driven Cisco IOS network assistant (concise edition)

Capabilities
------------
* **Version**: retrieve software version number only
* **RouteTable**: show IPv4 or IPv6 routing table
* **RouteProto**: inspect BGP/OSPF neighbor / summary state
* **Ping**: ping from router to target IP (5 packets, default)
* **IfaceConfig**: shut / no‑shut interface with pre‑check (idempotent)

Design Notes
* Each tool is small, single‑responsibility, Pydantic‑v2 compliant
* Netmiko connections managed via `with` context
* No file writes – stdout only for simplicity
"""

from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar, Literal, Optional
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from netmiko import ConnectHandler

# -----------------------------------------------------------------------------
# Configuration helpers
# -----------------------------------------------------------------------------

TZ_TOKYO = ZoneInfo("Asia/Tokyo")
BASE_DIR = Path(__file__).resolve().parent

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY is not set in environment or .env file")


# inventory loader

def load_device_from_env() -> dict:
    return {
        "device_type": os.getenv("DEVICE_TYPE", "cisco_ios"),
        "host": os.getenv("DEVICE_HOST"),
        "username": os.getenv("DEVICE_USERNAME"),
        "password": os.getenv("DEVICE_PASSWORD"),
    }


def load_device_from_yaml(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        devices = yaml.safe_load(f)
    return devices[0] if isinstance(devices, list) and devices else None


def get_device() -> dict:
    device = load_device_from_yaml(BASE_DIR / "devices.yaml") or load_device_from_env()
    required = {"host", "username", "password", "device_type"}
    missing = [k for k in required if not device.get(k)]
    if missing:
        raise ValueError(f"Missing device parameters: {', '.join(missing)}")
    return device


DEVICE = get_device()

# -----------------------------------------------------------------------------
# Utility funcs
# -----------------------------------------------------------------------------

VERSION_REGEX = re.compile(r"Version\s+([A-Za-z0-9.()]+)")


def extract_version(show_ver_output: str) -> str:
    for line in show_ver_output.splitlines():
        if "Version" in line:
            m = VERSION_REGEX.search(line)
            return m.group(1) if m else line.strip()
    return "[Version line not found]"


# -----------------------------------------------------------------------------
# Tool implementations
# -----------------------------------------------------------------------------

class GetVersionTool(BaseTool):
    name: ClassVar[str] = "GetVersion"
    description: ClassVar[str] = "Cisco IOS から 'show version' を実行し、ソフトウェアのバージョン番号のみを返す。引数不要。"

    def _run(self) -> str:  # type: ignore[override]
        try:
            with ConnectHandler(**DEVICE) as conn:
                output = conn.send_command("show version")
            return extract_version(output)
        except Exception as e:
            return f"[ERROR] {e}"

    async def _arun(self):  # type: ignore[override]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run)


class GetRouteTableTool(BaseTool):
    name: ClassVar[str] = "GetRouteTable"
    description: ClassVar[str] = (
        "IPv4/IPv6 ルーティングテーブルを取得するツール。input は 'ipv4' または 'ipv6'。省略時は ipv4。"
    )

    def _run(self, protocol: Literal["ipv4", "ipv6"] | str = "ipv4") -> str:  # type: ignore[override]
        cmd = "show ip route" if str(protocol).lower() != "ipv6" else "show ipv6 route"
        try:
            with ConnectHandler(**DEVICE) as conn:
                return conn.send_command(cmd)
        except Exception as e:
            return f"[ERROR] {e}"

    async def _arun(self, protocol: str = "ipv4") -> str:  # type: ignore[override]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, protocol)


class GetRouteProtoStateTool(BaseTool):
    name: ClassVar[str] = "GetRouteProtoState"
    description: ClassVar[str] = (
        "動的ルーティングプロトコル (BGP/OSPF) の状態を確認。input は 'bgp' or 'ospf'。"
    )

    _cmd_map = {
        "bgp": "show ip bgp summary",
        "ospf": "show ip ospf neighbor",
    }

    def _run(self, proto: Literal["bgp", "ospf"] | str = "bgp") -> str:  # type: ignore[override]
        cmd = self._cmd_map.get(str(proto).lower())
        if cmd is None:
            return "[ERROR] proto must be 'bgp' or 'ospf'"
        try:
            with ConnectHandler(**DEVICE) as conn:
                return conn.send_command(cmd)
        except Exception as e:
            return f"[ERROR] {e}"

    async def _arun(self, proto: str = "bgp") -> str:  # type: ignore[override]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, proto)


class PingTool(BaseTool):
    name: ClassVar[str] = "Ping"
    description: ClassVar[str] = (
        "ルーターから指定 IP へ ping を実行 (5 回)。input は target IP アドレス。"
    )

    def _run(self, target: str) -> str:  # type: ignore[override]
        try:
            with ConnectHandler(**DEVICE) as conn:
                return conn.send_command(f"ping {target}")
        except Exception as e:
            return f"[ERROR] {e}"

    async def _arun(self, target: str) -> str:  # type: ignore[override]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, target)


class IfaceConfigTool(BaseTool):
    name: ClassVar[str] = "IfaceConfig"
    description: ClassVar[str] = (
        "インターフェースを shut / no shut する。input は 'GigabitEthernet0/1 shutdown' / 'GigabitEthernet0/1 noshutdown' の形式。"
    )

    def _run(self, command: str) -> str:  # type: ignore[override]
        try:
            iface, action = command.split(maxsplit=1)
            desired = "shutdown" if action.lower().startswith("shut") else "no shutdown"
            with ConnectHandler(**DEVICE) as conn:
                current_cfg = conn.send_command(f"show run interface {iface}")
                already = ("shutdown" in current_cfg) == (desired == "shutdown")
                if already:
                    return f"[SKIP] {iface} は既に {desired} 状態です。"
                conn.enable()
                conn.config_mode()
                conn.send_command(f"interface {iface}")
                conn.send_command(desired)
                conn.exit_config_mode()
                return f"[OK] {iface} を {desired} しました。"
        except ValueError:
            return "[ERROR] input format: '<iface> shutdown|noshutdown'"
        except Exception as e:
            return f"[ERROR] {e}"

    async def _arun(self, command: str) -> str:  # type: ignore[override]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, command)


# -----------------------------------------------------------------------------
# Agent setup
# -----------------------------------------------------------------------------

prompt = hub.pull("hwchase17/react")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

tools = [
    GetVersionTool(),
    GetRouteTableTool(),
    GetRouteProtoStateTool(),
    PingTool(),
    IfaceConfigTool(),
]

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cisco IOS network assistant via LLM agent")
    parser.add_argument("query", nargs="*", help="User query (default: 'バージョン情報を教えて')")
    args = parser.parse_args()

    user_input = " ".join(args.query) or "バージョン情報を教えて"
    res = agent_executor.invoke({"input": user_input})
    print(res["output"])
