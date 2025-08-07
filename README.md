# CampusFlow

CampusFlowは、課題締切・行事カレンダー・リマインド機能を統合した学校管理システムです。Phase 1では、Google OAuth認証、課題管理、イベント管理、およびメール通知機能をサポートしています。

## 🚀 機能

### Phase 1 (MVP)
- **Google OAuth認証** - Google Workspaceアカウントでのシングルサインオン
- **課題管理** - 課題の作成、閲覧、進捗管理
- **イベント管理** - 学校行事の作成・管理
- **リマインド機能** - 課題の締切前日に自動メール通知
- **役割管理** - 学生・教師・管理者の権限設定
- **レスポンシブUI** - Tailwind CSSによる美しいデザイン

### Phase 2 (予定)
- 目安箱機能
- 忘れ物・備品管理

## 🏗️ 技術スタック

| レイヤー | 技術 |
|----------|------|
| **Frontend** | Node.js + Pure HTML/JavaScript + Tailwind CSS |
| **State Management** | Vanilla JavaScript (No Framework) |
| **Backend** | Python 3.12 + FastAPI + SQLModel |
| **Database** | PostgreSQL 15 |
| **Authentication** | Google OAuth2 + JWT |
| **Task Queue** | Celery + Redis |
| **Container** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

## 📋 前提条件

- Docker & Docker Compose (フル環境用)
- Node.js 16+ (フロントエンドのみ動かす場合)
- Python 3.12+ & Poetry (バックエンド開発用)
- Google Cloud Console アカウント (OAuth設定用)

## 🚀 セットアップ

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd CampusFlow
```

### 2. Google OAuth設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択
3. APIs & ServicesでGoogle+ APIを有効化
4. 認証情報でOAuth 2.0クライアントIDを作成
   - アプリケーションタイプ: Webアプリケーション
   - 承認済みのリダイレクトURI: `http://localhost:8000/api/auth/google/callback`
5. クライアントIDとクライアントシークレットをメモ

### 3. 環境変数設定

`.env`ファイルを作成:

```bash
cp .env.example .env
```

`.env`を編集して以下を設定:

```env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### 4. アプリケーションの起動

**Docker Composeを使用 (推奨)**

```bash
# 全サービスの起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d --build
```

**ローカル開発環境**

バックエンド:
```bash
cd apps/backend
export PATH="/home/codespace/.local/bin:$PATH"  # Poetry用
poetry install
poetry run alembic upgrade head  # データベースマイグレーション
poetry run uvicorn src.main:app --reload --port 8000
```

フロントエンド:
```bash
cd frontend
node simple-server.js
```

Celery (バックグラウンドタスク):
```bash
cd apps/backend
poetry run celery -A src.celery_app worker --loglevel=info
poetry run celery -A src.celery_app beat --loglevel=info
```

### 5. アプリケーションにアクセス

- **フロントエンド**: http://localhost:3001
- **バックエンドAPI**: http://localhost:8000  
- **API ドキュメント**: http://localhost:8000/docs

### 6. フロントエンドのみ動かす場合

バックエンドが不要な場合、フロントエンドは内蔵のモックデータで動作します:

```bash
cd frontend
node simple-server.js
```

http://localhost:3001 にアクセスして動作確認してください。

## 🔧 開発コマンド

### バックエンド

```bash
cd apps/backend

# 依存関係のインストール
poetry install

# コード整形
poetry run black .
poetry run isort .

# Linting
poetry run flake8 .

# テスト実行
poetry run pytest

# データベースマイグレーション
poetry run alembic revision --autogenerate -m "migration message"
poetry run alembic upgrade head

# サーバー起動
poetry run uvicorn src.main:app --reload
```

### フロントエンド

```bash
cd frontend

# サーバー起動
node simple-server.js

# または npm経由で起動
npm start
```

### Docker

```bash
# 全サービス起動
docker-compose up

# 特定サービスのみ起動
docker-compose up backend frontend

# ログ確認
docker-compose logs -f backend

# サービス停止
docker-compose down

# データも削除
docker-compose down -v
```

## 📊 データベース

### マイグレーション

```bash
cd apps/backend

# 新しいマイグレーションを生成
poetry run alembic revision --autogenerate -m "Add new table"

# マイグレーション実行
poetry run alembic upgrade head

# マイグレーション履歴
poetry run alembic history

# 特定バージョンにロールバック
poetry run alembic downgrade <revision>
```

## 🧪 テスト

```bash
# バックエンドテスト
cd apps/backend
poetry run pytest -v --cov=src

# フロントエンドテスト (実装予定)
cd apps/frontend
npm test
```

## 📧 メール設定

本番環境でメール通知を有効にするには、以下の環境変数を設定してください:

```env
SMTP_SERVER=your_smtp_server
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=noreply@yourdomain.com
```

開発環境では、メールはコンソールに出力されます。

## 🚀 デプロイ

### 本番環境での注意点

1. **JWT Secret Key**: 強力なランダムキーを生成
2. **Database URL**: 本番データベースのURLを設定
3. **Google OAuth**: 本番ドメインをリダイレクトURIに追加
4. **環境変数**: 全ての必要な環境変数を設定
5. **HTTPS**: 本番では必ずHTTPSを使用

### Docker Production Build

```bash
# 本番用イメージをビルド
docker-compose -f docker-compose.prod.yml build

# 本番環境で起動
docker-compose -f docker-compose.prod.yml up -d
```

## 🗂️ プロジェクト構造

```
CampusFlow/
├── apps/
│   └── backend/          # FastAPI アプリケーション
│       ├── src/
│       │   ├── models.py      # データベースモデル
│       │   ├── schemas.py     # Pydantic スキーマ
│       │   ├── database.py    # DB設定
│       │   ├── auth.py        # 認証ロジック
│       │   ├── main.py        # FastAPIアプリ
│       │   ├── celery_app.py  # Celery設定
│       │   ├── tasks.py       # バックグラウンドタスク
│       │   └── routers/       # APIルーター
│       ├── alembic/           # データベースマイグレーション
│       └── tests/             # テストファイル
├── frontend/             # Node.js シンプルフロントエンド
│   ├── simple-server.js      # Node.js HTTPサーバー
│   ├── package.json          # NPM設定
│   ├── README.md             # フロントエンド説明
│   └── public/
│       ├── index.html        # メインHTMLファイル
│       └── app.js            # フロントエンドJS
├── .github/workflows/    # GitHub Actions
├── docker-compose.yml    # Docker Compose設定
└── README.md
```

## 🤝 貢献

1. Issueを作成して機能要求やバグ報告を行う
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. Pull Requestを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 📞 サポート

問題がある場合は、GitHubのIssuesページで報告してください。

---

**CampusFlow Team**