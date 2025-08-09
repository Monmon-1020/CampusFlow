// Simple HTTP server without external dependencies
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3001;

// MIME types
const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json'
};

// サンプルデータ生成関数
function generateSampleData(userName = 'ユーザー') {
  const today = new Date();
  
  return {
    assignments: [
      {
        id: 'welcome-1',
        title: `${userName}さんへ：CampusFlowへようこそ！`,
        subject: 'システム案内',
        description: 'CampusFlowの使い方を確認して、学習管理を始めましょう。',
        due_at: new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      },
      {
        id: 'sample-1',
        title: '数学の基本問題',
        subject: '数学',
        description: '二次関数のグラフを描いて、頂点と軸の方程式を求めてください。',
        due_at: new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      },
      {
        id: 'sample-2',
        title: '英語読解レポート',
        subject: '英語',
        description: '指定された英文を読んで、内容について感想を英語で書いてください。',
        due_at: new Date(today.getTime() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      },
      {
        id: 'sample-3',
        title: '理科実験レポート',
        subject: '理科',
        description: '化学反応の実験結果をまとめ、考察を含めたレポートを作成してください。',
        due_at: new Date(today.getTime() + 10 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      }
    ],
    events: [
      {
        id: 'welcome-event-1',
        title: `${userName}さんのCampusFlow開始記念`,
        description: '学習管理システムの利用開始を記念して！',
        category: 'academic',
        location: 'オンライン',
        start_at: new Date().toISOString(),
        end_at: new Date(today.getTime() + 2 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      },
      {
        id: 'sample-event-1',
        title: '中間テスト期間',
        description: '各科目の中間テストが実施されます。',
        category: 'academic',
        location: '各教室',
        start_at: new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString(),
        end_at: new Date(today.getTime() + 18 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      },
      {
        id: 'sample-event-2',
        title: '体育祭',
        description: '年に一度の体育祭です。',
        category: 'sports',
        location: '校庭・体育館',
        start_at: new Date(today.getTime() + 21 * 24 * 60 * 60 * 1000).toISOString(),
        end_at: new Date(today.getTime() + 21 * 24 * 60 * 60 * 1000 + 6 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      },
      {
        id: 'sample-event-3',
        title: '文化祭準備',
        description: '文化祭の出し物準備を行います。',
        category: 'cultural',
        location: '各教室',
        start_at: new Date(today.getTime() + 28 * 24 * 60 * 60 * 1000).toISOString(),
        end_at: new Date(today.getTime() + 28 * 24 * 60 * 60 * 1000 + 3 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString()
      }
    ]
  };
}

// Mock API data（デフォルトデータ）
const mockData = {
  user: {
    id: '1',
    name: '田中太郎',
    email: 'tanaka@example.com',
    role: 'student'
  },
  ...generateSampleData('田中太郎')
};

// Development mode detection
const isDev = process.env.NODE_ENV !== 'production';

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  // API routes
  if (url.pathname === '/api/me') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(mockData.user));
    return;
  }
  
  if (url.pathname === '/api/assignments') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(mockData.assignments));
    return;
  }
  
  if (url.pathname === '/api/events') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(mockData.events));
    return;
  }
  
  // Handle OAuth callback by redirecting to root with query params
  if (url.pathname === '/auth/google/callback') {
    const callbackUrl = `/?callback=google&${url.search.substring(1)}`;
    res.writeHead(302, { 'Location': callbackUrl });
    res.end();
    return;
  }
  
  // Static files
  let filePath = path.join(__dirname, 'public', url.pathname === '/' ? 'index.html' : url.pathname);
  
  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // File not found - serve index.html for SPA routing
        fs.readFile(path.join(__dirname, 'public', 'index.html'), (err, content) => {
          if (err) {
            res.writeHead(500);
            res.end('Server Error');
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(content);
          }
        });
      } else {
        res.writeHead(500);
        res.end('Server Error');
      }
    } else {
      const ext = path.extname(filePath);
      const contentType = mimeTypes[ext] || 'text/plain';
      
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

server.listen(PORT, () => {
  console.log(`🎓 CampusFlow frontend running at http://localhost:${PORT}`);
  console.log(`📁 Serving static files from: ${path.join(__dirname, 'public')}`);
  console.log(`🔌 API endpoints: /api/me, /api/assignments, /api/events`);
  if (isDev) {
    console.log(`🔧 Development mode - Mock data enabled`);
  }
  console.log(`\n   Press Ctrl+C to stop the server\n`);
});