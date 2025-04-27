import os
from langchain import hub
import random
from datetime import datetime
from langchain.tools import BaseTool
from datetime import timedelta
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from dotenv import load_dotenv


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = hub.pull("hwchase17/react")

print(prompt.template)


def get_fortune(date_string):
    try:
        date = datetime.strptime(date_string, "%m月%d日")
    except ValueError:
        return "無効な日付形式です。'X月X日'の形式で入力してください。"

    # 運勢のリスト
    fortunes = ["大吉", "中吉", "小吉", "吉", "末吉", "凶", "大凶"]

    # 運勢の重み付け（大吉と大凶の確率を低くする）
    weights = [1, 3, 3, 4, 3, 2, 1]

    # 日付に基づいてシードを設定（同じ日付なら同じ運勢を返す）
    random.seed(date.month * 100 + date.day)

    # 運勢をランダムに選択
    fortune = random.choices(fortunes, weights=weights)[0]

    return f"{date_string}の運勢は【{fortune}】です。"


class Get_fortune(BaseTool):
    name: str = "Get_fortune"
    description: str = (
        "特定の日付の運勢を占う。インプットは  'date_string'です。'date_string' は、占いを行う日付で、mm月dd日 という形式です。「1月1日」のように入力し、「'1月1日'」のように余計な文字列を付けてはいけません。"
    )

    def _run(self, date_string) -> str:
        return get_fortune(date_string)

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
tools = [Get_date(), Get_fortune()]

# エージェントの作成
agent = create_react_agent(model, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# 入力メッセージの作成と実行
response = agent_executor.invoke({"input": "今日の運勢を教えてください。"})

print("\n結果:")
print(response["output"])
