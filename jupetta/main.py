from dotenv import load_dotenv
import os
from langchain import hub
import random
from datetime import datetime
from langchain.tools import BaseTool
from datetime import timedelta
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from netmiko import ConnectHandler

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からAPIキーを取得
openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = hub.pull("hwchase17/react")

print(prompt.template)

device = {
    "device_type": "cisco_ios",
    'host': '192.168.64.23',
    'username': 'admin',
    'password': 'admin'
}
# ConnectHandlerクラスのインスタンスを作成します
# ConnectionHandlerはインスタンス化時に接続するので、グローバル変数として保持せず、
# 必要なときに接続するようにします
# connection = ConnectHandler(**device)


def get_version_info(date_string: str) -> str:
    """
    Cisco IOSデバイスのバージョン情報を取得する

    Args:
        date_string: バージョン情報を取得する日付文字列

    Returns:
        str: バージョン情報
    """
    try:
        # 関数内で接続を確立して使用
        connection = ConnectHandler(**device)
        result = f"{date_string} で指定された日付のバージョン情報を取得します。"
        result += connection.send_command("show version")
        result += f"\n取得日: {date_string}"
        connection.disconnect()  # 接続を明示的に閉じる
        return result
    except Exception as e:
        return f"Error getting version info: {str(e)}"


class Get_version(BaseTool):
    name: str = "Get_version"
    description: str = (
        "特定の日付のバージョン情報を取得する。インプットは  'date_string'です。'date_string' は、バージョン情報を取得する日付で、mm月dd日 という形式です。「1月1日」のように入力し、「'1月1日'」のように余計な文字列を付けてはいけません。"
    )

    def _run(self, date_string) -> str:
        return get_version_info(date_string)

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("does not support async")

def get_date(date):
    date_now = datetime.now(ZoneInfo("Asia/Tokyo"))
    if "今日" in date:
        date_delta = 0
    elif "明日" in date:
        date_delta = 1
    elif "明後日" in date:
        date_delta = 2
    else:
        return "サポートしていません"
    return (date_now + timedelta(days=date_delta)).strftime("%m月%d日")


class Get_date(BaseTool):
    name: str = "Get_date"
    description: str = (
        "今日の日付を取得する。インプットは 'date'です。'date' は、日付を取得する対象の日で、'今日', '明日', '明後日' という3種類の文字列から指定します。「今日」のように入力し、「'今日'」のように余計な文字列を付けてはいけません。"
    )

    def _run(self, date) -> str:
        return get_date(date)

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("does not support async")

# モデルの設定
model = ChatOpenAI(model="gpt-4o-mini")

# ツールのリスト
tools = [Get_version(), Get_date()]

# エージェントの作成
agent = create_react_agent(model, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# 入力メッセージの作成と実行
response = agent_executor.invoke({"input": "バージョン情報を教えてください。"})

print("\n結果:")
print(response["output"])
