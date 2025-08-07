# CampusFlow Frontend

シンプルなNode.jsベースのフロントエンドアプリケーションです。

## 特徴

- **依存関係なし**: Express などの外部ライブラリを使わない純粋なNode.js HTTPサーバー
- **軽量**: HTMLファイル1個とJavaScriptファイル1個のシンプル構成
- **モックAPI**: バックエンド無しでも動作する内蔵モックデータ
- **日本語対応**: 完全日本語UI
- **レスポンシブ**: Tailwind CSS使用

## 実行方法

### 1. Node.jsが必要
Node.js 16以上がインストールされている必要があります。

### 2. サーバー起動
```bash
cd frontend
node simple-server.js
```

または

```bash
cd frontend  
npm start
```

### 3. ブラウザでアクセス
http://localhost:3001 にアクセス

## API エンドポイント

以下のモックAPIが利用可能です：

- `GET /api/me` - ユーザー情報
- `GET /api/assignments` - 課題一覧  
- `GET /api/events` - イベント一覧

## ファイル構成

```
frontend/
├── simple-server.js    # Node.js HTTPサーバー
├── package.json        # NPM設定
├── README.md          # このファイル
└── public/
    ├── index.html     # メインHTMLファイル
    └── app.js         # フロントエンドJavaScript
```

## 機能

### ダッシュボード
- 課題とイベントの概要表示
- 統計情報の表示
- ユーザー情報の表示

### 課題管理
- 課題一覧表示
- 期限による自動ステータス分類
- 期限超過、今日締切、明日締切の色分け

### イベント管理  
- イベント一覧表示
- カテゴリー別分類（学習、文化、スポーツ、管理）
- 日時情報の表示

## カスタマイズ

`simple-server.js` の `mockData` オブジェクトを編集することで、表示データを変更できます。

## 本格運用時

バックエンドAPIサーバーと連携する場合は、`public/app.js` の fetch URL を実際のAPIエンドポイントに変更してください。