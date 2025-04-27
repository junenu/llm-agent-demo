# jupetta - LLM駆動型Cisco IOSネットワークアシスタント

## 🌟 概要

jupettaは、LangChainとOpenAI APIを活用したLLM駆動のCisco IOSネットワークアシスタントです。日常的なネットワーク管理タスクを自然言語で簡単に実行できます。

## 💻 機能

jupettaは以下の機能を備えています：

- **バージョン確認** (`GetVersion`): ネットワーク機器のソフトウェアバージョンを取得
- **ルーティングテーブル表示** (`GetRouteTable`): IPv4/IPv6ルーティングテーブルの確認
- **ルーティングプロトコル状態** (`GetRouteProtoState`): BGP/OSPFネイバーやサマリー状態の確認
- **Ping実行** (`Ping`): ルーターから指定IPアドレスへのping実行
- **インターフェース設定** (`IfaceConfig`): インターフェースのshut/no shut操作（冪等性あり）

## 🛠️ 設計方針

- 各ツールは単一責任の原則に基づき、Pydantic v2に準拠
- Netmikoコネクションは`with`コンテキストで安全に管理
- 出力はファイル書き込みなしで標準出力のみを使用（シンプルさ重視）
- LangChain ReActフレームワークによるエージェント実装
- GPT-4o-miniモデルを活用した自然言語理解

## 📁 ディレクトリ構成

```
.
├── README.md          # このファイル
├── jupetta/           # メインアプリケーションディレクトリ
│   ├── .env           # 環境変数設定ファイル（要作成）
│   ├── devices.yaml   # デバイス情報設定ファイル（オプション）
│   └── main.py        # メインプログラム
└── test/              # テスト用ディレクトリ
    └── tools.py       # テストツール
```

## 🚀 セットアップと実行方法

### 前提条件

- Python 3.9以上
- pip
- OpenAI APIキー
- Ciscoデバイスへのアクセス権限

### インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/junenu/llm-agent-demo.git
cd llm-agent-demo
```

2. 必要なパッケージのインストール:
```bash
pip install langchain langchain_openai netmiko python-dotenv pyyaml
```

3. 環境変数の設定:
jupetta/.envファイルを作成し、以下のように設定してください:
```
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
DEVICE_TYPE=cisco_ios
DEVICE_HOST=192.168.1.1
DEVICE_USERNAME=admin
DEVICE_PASSWORD=password
```

または、devices.yamlファイルを使用することもできます:
```yaml
- device_type: cisco_ios
  host: 192.168.1.1
  username: admin
  password: password
```

### 実行方法

メインプログラムを実行:
```bash
cd jupetta
python main.py "ルーターのバージョンを教えて"
```

引数なしで実行すると、デフォルトで「バージョン情報を教えて」というクエリが使用されます。

## 💬 使用例

```
$ python main.py "ルーティングテーブルを表示して"
> ルーティングテーブルを表示します。IPv4とIPv6のどちらを確認しますか？

$ python main.py "インターフェースGigabitEthernet0/1をシャットダウンして"
> インターフェースの状態を確認し、シャットダウン操作を実行します。
> [OK] GigabitEthernet0/1 を shutdown しました。

$ python main.py "192.168.1.100にpingを実行して"
> 192.168.1.100へのping結果を表示します。
```

## 🔒 セキュリティに関する注意事項

- 環境変数ファイル(.env)やdevices.yamlはgitignoreに追加し、認証情報をGitにコミットしないよう注意してください
- 本番環境では適切な認証情報管理を行い、パスワードの漏洩に注意してください

## 📦 依存ライブラリ

- langchain / langchain_openai: LLMエージェントフレームワーク
- netmiko: ネットワークデバイスへのSSH接続
- python-dotenv: 環境変数管理
- pyyaml: YAMLファイルの読み込み
- zoneinfo: タイムゾーン管理

## 🤖 技術的詳細

jupettaはGPT-4o-miniモデルを使用し、温度パラメータ0.0でより一貫性のある応答を生成します。すべてのツールは同期・非同期の両方の実装を備え、効率的なI/O処理を可能にしています。
