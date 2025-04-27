# LLM Agent Demo

このリポジトリは、LangChainを使用したLLM（大規模言語モデル）エージェントのデモプロジェクトです。特にCiscoネットワークデバイスの情報を取得するためのツールを実装しています。

## 📚 概要

このプロジェクトでは、以下の機能を提供しています：

- LangChain ReActフレームワークを使用したエージェント実装
- OpenAI APIを利用したChatモデルの活用
- netmikoを使用したCiscoデバイスへの接続と情報取得
- 日付取得ツールと連携したバージョン情報取得

## 🛠️ ディレクトリ構成

```
.
├── README.md          # このファイル
├── jupetta/           # メインアプリケーションディレクトリ
│   ├── .env           # 環境変数設定ファイル
│   └── main.py        # メインプログラム
└── test/              # テスト用ディレクトリ
    └── tools.py       # テストツール
```

## 🚀 セットアップと実行方法

### 前提条件

- Python 3.9以上
- pip
- OpenAI APIキー

### インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/junenu/llm-agent-demo.git
cd llm-agent-demo
```

2. 必要なパッケージのインストール:
```bash
pip install <適宜必要なパッケージを指定してください>
```

3. 環境変数の設定:
jupetta/.envファイルを作成し、以下のように設定してください:
```
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

### 実行方法

メインプログラムを実行:
```bash
cd jupetta
python main.py
```

## 🔧 機能詳細

### 実装済みツール

1. **Get_date**
   - 今日、明日、明後日の日付を取得
   - 日本のタイムゾーン(Asia/Tokyo)に対応

2. **Get_version**
   - Cisco IOSデバイスのバージョン情報を取得
   - netmikoライブラリを使用してSSH接続

## 📝 使用例

エージェントに「バージョン情報を教えてください」と質問すると、以下のような流れで処理が行われます:

1. エージェントが日付情報が必要と判断し、Get_dateツールを使用
2. 取得した日付を元に、Get_versionツールでCiscoデバイスの情報を取得
3. 整形された結果を返却

## 🔒 セキュリティ注意事項

- .envファイルはgitignoreに追加し、APIキーをGitにコミットしないよう注意
- 本番環境ではパスワードをハードコーディングせず、適切な認証情報管理を行う

## 📦 依存ライブラリ

- langchain
- openai
- netmiko
- python-dotenv
- zoneinfo
