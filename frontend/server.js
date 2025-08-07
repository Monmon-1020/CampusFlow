const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// 静的ファイルを提供
app.use(express.static(path.join(__dirname, 'public')));

// API エンドポイント（モック）
app.get('/api/me', (req, res) => {
  res.json({
    id: '1',
    name: '田中太郎',
    email: 'tanaka@example.com',
    role: 'student'
  });
});

app.get('/api/assignments', (req, res) => {
  res.json([
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
  ]);
});

app.get('/api/events', (req, res) => {
  res.json([
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
  ]);
});

// すべてのルートでindex.htmlを返す（SPA対応）
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🎓 CampusFlow frontend running at http://localhost:${PORT}`);
});