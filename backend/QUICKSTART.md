# CampusFlow Backend - クイックスタート

## 前提条件

- Python 3.12+
- Poetry (Python パッケージマネージャー)
- PostgreSQL または SQLite

## ローカル起動手順

### 1. Poetry のインストール（未インストールの場合）

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. 依存関係のインストール

```bash
cd backend
poetry install
```

### 3. 環境変数の設定

`.env` ファイルを作成:

```bash
# SQLite を使用する場合（開発用）
DATABASE_URL=sqlite:///./campusflow.db

# PostgreSQL を使用する場合（本番用）
# DATABASE_URL=postgresql://user:password@localhost:5432/campusflow

# JWT Secret Key (ランダムな文字列を生成)
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Google OAuth (オプション)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Redis (オプション - Celeryタスク用)
REDIS_URL=redis://localhost:6379/0

# SMTP (オプション - メール送信用)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@campusflow.local
```

### 4. データベース初期化

```bash
poetry run alembic upgrade head
```

### 5. サーバー起動

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

または簡易スクリプトを使用:

```bash
./start-local.sh
```

## アクセス

- **API サーバー**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 開発用コマンド

```bash
# コード整形
poetry run black .
poetry run isort .

# リンター
poetry run flake8 .

# テスト実行
poetry run pytest

# 新しいマイグレーション作成
poetry run alembic revision --autogenerate -m "Add new feature"

# Celery ワーカー起動 (Redis が必要)
poetry run celery -A src.celery_app worker --loglevel=info

# Celery Beat 起動 (定期タスク用)
poetry run celery -A src.celery_app beat --loglevel=info
```

## トラブルシューティング

### Poetry が見つからない

```bash
# ~/.local/bin を PATH に追加
export PATH="/home/$USER/.local/bin:$PATH"

# または直接実行
/home/$USER/.local/bin/poetry --version
```

### データベース接続エラー

SQLite を使用する場合は自動で DB ファイルが作成されます。
PostgreSQL の場合は事前にデータベースとユーザーを作成してください：

```sql
CREATE DATABASE campusflow;
CREATE USER campusflow_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE campusflow TO campusflow_user;
```

### ポート 8000 が使用中

別のポートを使用：

```bash
poetry run uvicorn src.main:app --reload --port 8001
```