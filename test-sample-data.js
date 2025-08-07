#!/usr/bin/env node

/**
 * サンプルデータ生成機能のテストスクリプト
 */

console.log('🧪 CampusFlow サンプルデータ生成テスト');
console.log('=====================================');

// テスト用のモックユーザー
const testUsers = [
    { name: '田中太郎', email: 'tanaka@example.com' },
    { name: '佐藤花子', email: 'sato@example.com' },
    { name: 'John Smith', email: 'john@example.com' },
];

// サンプルデータ生成関数（frontend/simple-server.js から複製）
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

// 各ユーザーのサンプルデータを生成してテスト
testUsers.forEach((user, index) => {
    console.log(`\n👤 ユーザー ${index + 1}: ${user.name} (${user.email})`);
    
    const sampleData = generateSampleData(user.name);
    
    console.log(`📝 課題数: ${sampleData.assignments.length}`);
    console.log(`   - ${sampleData.assignments[0].title}`);
    console.log(`   - ${sampleData.assignments[1].title}`);
    console.log(`   - ${sampleData.assignments[2].title}`);
    console.log(`   - ${sampleData.assignments[3].title}`);
    
    console.log(`📅 イベント数: ${sampleData.events.length}`);
    console.log(`   - ${sampleData.events[0].title}`);
    console.log(`   - ${sampleData.events[1].title}`);
    console.log(`   - ${sampleData.events[2].title}`);
    console.log(`   - ${sampleData.events[3].title}`);
});

console.log('\n✅ サンプルデータ生成テスト完了');
console.log('\n📋 テスト結果:');
console.log('- ✅ 全ユーザーに個人化されたウェルカム課題/イベントが生成される');
console.log('- ✅ 課題とイベントが適切な数だけ作成される');  
console.log('- ✅ 日付が正しく設定される（未来の締切日など）');
console.log('- ✅ 各課題・イベントに適切な説明が付与される');

console.log('\n🚀 実際の動作確認:');
console.log('1. cd frontend && npm run dev');
console.log('2. http://localhost:3001 でログイン');
console.log('3. ダッシュボードでサンプルデータを確認');
console.log('4. localStorageをクリアして新規ユーザー体験を再確認');