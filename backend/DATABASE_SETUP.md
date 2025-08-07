# CampusFlow データベースセットアップ

## データベース設定

### 1. SQLite（開発用・簡単設定）

```bash
cd backend

# .env ファイルに設定
echo "DATABASE_URL=sqlite:///./campusflow.db" > .env

# マイグレーション実行
poetry run alembic upgrade head
```

### 2. PostgreSQL（本番用・推奨）

#### PostgreSQL インストール

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
PostgreSQL 公式サイトからダウンロード: https://www.postgresql.org/download/

#### データベースとユーザー作成

```bash
# PostgreSQL にログイン
sudo -u postgres psql

# データベース作成
CREATE DATABASE campusflow;

# ユーザー作成
CREATE USER campusflow_user WITH PASSWORD 'your_secure_password';

# 権限付与
GRANT ALL PRIVILEGES ON DATABASE campusflow TO campusflow_user;

# 終了
\q
```

#### 環境変数設定

```bash
cd backend

# .env ファイルに設定
cat > .env << EOF
DATABASE_URL=postgresql://campusflow_user:your_secure_password@localhost:5432/campusflow
JWT_SECRET_KEY=$(openssl rand -hex 32)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/callback
EOF
```

### 3. Google OAuth 設定

#### Google Cloud Console での設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または選択
3. 「APIとサービス」→「ライブラリ」で「Google+ API」を有効化
4. 「APIとサービス」→「認証情報」でOAuth 2.0クライアントIDを作成

**設定値:**
- アプリケーション タイプ: ウェブ アプリケーション
- 承認済みの JavaScript 生成元: `http://localhost:3001`
- 承認済みのリダイレクト URI: `http://localhost:3001/auth/callback`

## データベース操作コマンド

### マイグレーション

```bash
cd backend

# 現在のマイグレーション状態確認
poetry run alembic current

# 新しいマイグレーション作成
poetry run alembic revision --autogenerate -m "Add new feature"

# マイグレーション実行
poetry run alembic upgrade head

# マイグレーション履歴
poetry run alembic history

# 特定バージョンにロールバック
poetry run alembic downgrade <revision_id>

# 最初の状態に戻す
poetry run alembic downgrade base
```

### データベースリセット（開発時）

```bash
cd backend

# SQLite の場合
rm -f campusflow.db
poetry run alembic upgrade head

# PostgreSQL の場合
psql -U campusflow_user -d campusflow -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
poetry run alembic upgrade head
```

### 初期データ投入

管理者ユーザーを手動で作成する場合:

```bash
cd backend

# Python シェル起動
poetry run python3 -c "
import asyncio
from src.database import engine
from src.models import User
from sqlmodel import Session

async def create_admin():
    with Session(engine) as session:
        admin = User(
            email='admin@example.com',
            name='管理者',
            role='admin'
        )
        session.add(admin)
        session.commit()
        print('管理者ユーザーを作成しました')

asyncio.run(create_admin())
"
```

## バックアップとリストア

### PostgreSQL バックアップ

```bash
# データベース全体バックアップ
pg_dump -U campusflow_user -d campusflow > backup_$(date +%Y%m%d_%H%M%S).sql

# 特定テーブルのみバックアップ
pg_dump -U campusflow_user -d campusflow -t users -t assignments > users_backup.sql
```

### PostgreSQL リストア

```bash
# データベースリストア
psql -U campusflow_user -d campusflow < backup_20231201_120000.sql
```

### SQLite バックアップ

```bash
# データベースファイルをコピー
cp campusflow.db campusflow_backup_$(date +%Y%m%d_%H%M%S).db
```

## トラブルシューティング

### よくあるエラー

**1. `relation "users" does not exist`**
```bash
# マイグレーションを実行
poetry run alembic upgrade head
```

**2. `FATAL: password authentication failed`**
```bash
# .env ファイルの DATABASE_URL を確認
# PostgreSQL のユーザー名・パスワードを確認
```

**3. `ModuleNotFoundError: No module named 'psycopg2'`**
```bash
# PostgreSQL 用のドライバをインストール
poetry add psycopg2-binary
```

### データベース接続確認

```bash
cd backend

# 接続テスト
poetry run python3 -c "
from src.database import engine
print('データベース接続成功!')
print(f'Database URL: {engine.url}')
"
```

## セキュリティ考慮事項

1. **本番環境では強力なパスワードを使用**
2. **JWT_SECRET_KEY は十分にランダムな値を生成**
3. **データベースユーザーには必要最小限の権限のみ付与**
4. **定期的なバックアップの実行**
5. **SSL/TLS 接続の有効化（本番環境）**