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

// Mock API data
const mockData = {
  user: {
    id: '1',
    name: '田中太郎',
    email: 'tanaka@example.com',
    role: 'student'
  },
  assignments: [
    {
      id: '1',
      title: '数学の宿題',
      subject: '数学',
      description: '教科書の問題1-10を解く',
      due_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      created_at: new Date().toISOString()
    },
    {
      id: '2',
      title: 'レポート提出',
      subject: '国語',
      description: '夏目漱石について1000字程度で書く',
      due_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      created_at: new Date().toISOString()
    },
    {
      id: '3',
      title: '英語の課題',
      subject: '英語',
      description: 'Unit 5の単語を覚える',
      due_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      created_at: new Date().toISOString()
    }
  ],
  events: [
    {
      id: '1',
      title: '体育祭',
      description: '年に一度の体育祭です',
      category: 'sports',
      location: '校庭',
      start_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      end_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000 + 4 * 60 * 60 * 1000).toISOString(),
      created_at: new Date().toISOString()
    },
    {
      id: '2',
      title: '文化祭準備',
      description: '文化祭の準備作業',
      category: 'cultural',
      location: '各教室',
      start_at: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      end_at: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000 + 2 * 60 * 60 * 1000).toISOString(),
      created_at: new Date().toISOString()
    }
  ]
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