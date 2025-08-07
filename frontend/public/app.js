// グローバル状態
let currentUser = null;
let assignments = [];
let events = [];
let streams = [];
let selectedStream = null;
let currentStreamAnnouncements = [];
let authToken = null;

// 設定
const API_BASE_URL = 'http://localhost:8000'; // バックエンドAPI URL
const USE_MOCK_DATA = true; // フロントエンドのみの場合は true に設定

// デバッグ情報
console.log('⚙️ 設定情報:');
console.log('  API_BASE_URL:', API_BASE_URL);
console.log('  USE_MOCK_DATA:', USE_MOCK_DATA);

// ユーティリティ関数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 新規ユーザー向けサンプルデータ生成
function generateSampleDataForUser(user) {
    const userName = user.name || 'ユーザー';
    const today = new Date();
    
    // サンプル課題データ
    const sampleAssignments = [
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
            title: '数学の課題例',
            subject: '数学',
            description: '二次関数の問題を解いてみましょう。',
            due_at: new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000).toISOString(),
            created_at: new Date().toISOString()
        },
        {
            id: 'sample-2',
            title: '英語のレポート例',
            subject: '英語',
            description: '好きな本について英語で感想を書いてください。',
            due_at: new Date(today.getTime() + 5 * 24 * 60 * 60 * 1000).toISOString(),
            created_at: new Date().toISOString()
        }
    ];
    
    // サンプルイベントデータ
    const sampleEvents = [
        {
            id: 'welcome-event-1',
            title: `${userName}さんのCampusFlow開始記念！`,
            description: 'あなたの学習管理の旅が始まりました。頑張ってください！',
            category: 'academic',
            location: 'オンライン',
            start_at: new Date().toISOString(),
            end_at: new Date(today.getTime() + 2 * 60 * 60 * 1000).toISOString(),
            created_at: new Date().toISOString()
        },
        {
            id: 'sample-event-1',
            title: '体育祭準備',
            description: '年に一度の体育祭の準備を行います',
            category: 'sports',
            location: '体育館',
            start_at: new Date(today.getTime() + 10 * 24 * 60 * 60 * 1000).toISOString(),
            end_at: new Date(today.getTime() + 10 * 24 * 60 * 60 * 1000 + 4 * 60 * 60 * 1000).toISOString(),
            created_at: new Date().toISOString()
        },
        {
            id: 'sample-event-2',
            title: '文化祭企画会議',
            description: '文化祭の出し物について話し合います',
            category: 'cultural',
            location: '会議室A',
            start_at: new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000).toISOString(),
            end_at: new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000 + 2 * 60 * 60 * 1000).toISOString(),
            created_at: new Date().toISOString()
        }
    ];
    
    return { sampleAssignments, sampleEvents };
}

// ユーティリティ関数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getAssignmentStatus(dueDate) {
    const due = new Date(dueDate);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const dueDay = new Date(due.getFullYear(), due.getMonth(), due.getDate());
    
    if (dueDay < today) return 'overdue';
    if (dueDay.getTime() === today.getTime()) return 'due-today';
    if (dueDay.getTime() === today.getTime() + 24 * 60 * 60 * 1000) return 'due-tomorrow';
    return 'upcoming';
}

function getStatusColor(status) {
    switch (status) {
        case 'overdue':
            return 'text-red-600 bg-red-50';
        case 'due-today':
            return 'text-orange-600 bg-orange-50';
        case 'due-tomorrow':
            return 'text-yellow-600 bg-yellow-50';
        default:
            return 'text-blue-600 bg-blue-50';
    }
}

function getStatusText(status) {
    switch (status) {
        case 'overdue':
            return '期限超過';
        case 'due-today':
            return '今日締切';
        case 'due-tomorrow':
            return '明日締切';
        default:
            return '予定';
    }
}

function getCategoryText(category) {
    switch (category) {
        case 'academic':
            return '学習';
        case 'cultural':
            return '文化';
        case 'sports':
            return 'スポーツ';
        case 'administrative':
            return '管理';
        default:
            return 'その他';
    }
}

function getRoleText(role) {
    switch (role) {
        case 'student':
            return '学生';
        case 'teacher':
            return '教師';
        case 'admin':
            return '管理者';
        default:
            return role;
    }
}

// 認証機能
function checkAuth() {
    const token = localStorage.getItem('authToken');
    if (token) {
        authToken = token;
        return true;
    }
    return false;
}

function showLoginPage() {
    console.log('🔐 ログインページ表示開始');
    
    const loginPage = document.getElementById('login-page');
    const mainContent = document.getElementById('main-content');
    const mainNav = document.getElementById('main-nav');
    
    if (loginPage) {
        loginPage.classList.remove('hidden');
        console.log('✅ ログインページを表示');
    } else {
        console.error('❌ ログインページ要素が見つかりません');
    }
    
    if (mainContent) {
        mainContent.classList.add('hidden');
        console.log('✅ メインコンテンツを非表示');
    } else {
        console.error('❌ メインコンテンツ要素が見つかりません');
    }
    
    if (mainNav) {
        mainNav.classList.add('hidden');
        console.log('✅ ナビゲーションを非表示');
    } else {
        console.error('❌ ナビゲーション要素が見つかりません');
    }
}

function showMainContent() {
    console.log('🏠 メインコンテンツ表示開始');
    
    const loginPage = document.getElementById('login-page');
    const mainContent = document.getElementById('main-content');
    const mainNav = document.getElementById('main-nav');
    
    if (loginPage) {
        loginPage.classList.add('hidden');
        console.log('✅ ログインページを非表示');
    } else {
        console.error('❌ ログインページ要素が見つかりません');
    }
    
    if (mainContent) {
        mainContent.classList.remove('hidden');
        console.log('✅ メインコンテンツを表示');
    } else {
        console.error('❌ メインコンテンツ要素が見つかりません');
    }
    
    if (mainNav) {
        mainNav.classList.remove('hidden');
        console.log('✅ ナビゲーションを表示');
    } else {
        console.error('❌ ナビゲーション要素が見つかりません');
    }
}

async function loginWithGoogle() {
    try {
        console.log('🔐 Google ログイン開始');
        document.getElementById('login-loading').classList.remove('hidden');
        document.getElementById('login-error').classList.add('hidden');
        
        if (USE_MOCK_DATA) {
            console.log('🧪 モックログインモード');
            // モックログイン
            const mockToken = 'mock_jwt_token_' + Date.now();
            const mockUser = {
                id: '1',
                name: '田中太郎',
                email: 'tanaka@example.com',
                role: 'student',
                picture_url: null
            };
            
            console.log('💾 認証情報保存:', mockUser);
            localStorage.setItem('authToken', mockToken);
            localStorage.setItem('currentUser', JSON.stringify(mockUser));
            authToken = mockToken;
            currentUser = mockUser;
            
            setTimeout(() => {
                console.log('✅ モックログイン完了');
                document.getElementById('login-loading').classList.add('hidden');
                showMainContent();
                initializeApp();
            }, 1000);
            return;
        }
        
        // 実際のGoogle OAuth
        const response = await fetch(`${API_BASE_URL}/api/auth/google/login`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.url) {
            window.location.href = data.url;
        } else {
            throw new Error('認証URLの取得に失敗しました');
        }
        
    } catch (error) {
        console.error('ログインエラー:', error);
        document.getElementById('login-loading').classList.add('hidden');
        document.getElementById('login-error').classList.remove('hidden');
        document.getElementById('login-error-message').textContent = error.message;
    }
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    authToken = null;
    currentUser = null;
    assignments = [];
    events = [];
    
    showLoginPage();
}

// API呼び出し
async function fetchUser() {
    try {
        if (USE_MOCK_DATA) {
            const savedUser = localStorage.getItem('currentUser');
            if (savedUser) {
                currentUser = JSON.parse(savedUser);
                updateUserInfo();
                return;
            }
        }
        
        const headers = {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        };
        
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, { headers });
        if (response.ok) {
            currentUser = await response.json();
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateUserInfo();
        } else {
            throw new Error('ユーザー情報の取得に失敗しました');
        }
    } catch (error) {
        console.error('ユーザー情報の取得に失敗しました:', error);
        logout();
    }
}

async function fetchAssignments() {
    try {
        if (USE_MOCK_DATA) {
            const response = await fetch('/api/assignments');
            const mockData = await response.json();
            
            // 全てのユーザーに基本データを保証
            let baseAssignments = mockData || [];
            
            // 新規ユーザーか既存ユーザーかをチェック
            const isFirstTime = !localStorage.getItem('hasUsedApp');
            
            if (isFirstTime && currentUser) {
                // 新規ユーザーには個人化されたサンプルデータを追加
                const { sampleAssignments } = generateSampleDataForUser(currentUser);
                assignments = [...sampleAssignments, ...baseAssignments];
                localStorage.setItem('hasUsedApp', 'true');
                
                // ウェルカムメッセージを表示
                setTimeout(() => {
                    showWelcomeMessage(currentUser.name);
                }, 2000);
            } else {
                // 既存ユーザーにも最低限のデータを保証
                if (baseAssignments.length === 0 && currentUser) {
                    const { sampleAssignments } = generateSampleDataForUser(currentUser);
                    assignments = sampleAssignments.slice(1); // ウェルカム課題以外
                } else {
                    assignments = baseAssignments;
                }
            }
        } else {
            const headers = {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            };
            const response = await fetch(`${API_BASE_URL}/api/assignments`, { headers });
            if (response.ok) {
                const apiAssignments = await response.json();
                
                // API から取得したデータが空の場合、デフォルトデータを追加
                if (apiAssignments.length === 0 && currentUser) {
                    const { sampleAssignments } = generateSampleDataForUser(currentUser);
                    assignments = sampleAssignments.slice(1); // ウェルカム課題以外
                } else {
                    assignments = apiAssignments;
                }
            } else {
                throw new Error('課題の取得に失敗しました');
            }
        }
        
        updateDashboardAssignments();
        if (document.getElementById('assignments').classList.contains('hidden') === false) {
            renderAssignments();
        }
    } catch (error) {
        console.error('課題の取得に失敗しました:', error);
        // エラー時もデフォルトデータを表示
        if (currentUser) {
            const { sampleAssignments } = generateSampleDataForUser(currentUser);
            assignments = sampleAssignments;
            updateDashboardAssignments();
        }
    }
}

async function fetchEvents() {
    try {
        if (USE_MOCK_DATA) {
            const response = await fetch('/api/events');
            const mockData = await response.json();
            
            // 全てのユーザーに基本データを保証
            let baseEvents = mockData || [];
            
            // 新規ユーザーか既存ユーザーかをチェック
            const isFirstTime = !localStorage.getItem('hasUsedApp');
            
            if (isFirstTime && currentUser) {
                // 新規ユーザーには個人化されたサンプルデータを追加
                const { sampleEvents } = generateSampleDataForUser(currentUser);
                events = [...sampleEvents, ...baseEvents];
            } else {
                // 既存ユーザーにも最低限のデータを保証
                if (baseEvents.length === 0 && currentUser) {
                    const { sampleEvents } = generateSampleDataForUser(currentUser);
                    events = sampleEvents.slice(1); // ウェルカムイベント以外
                } else {
                    events = baseEvents;
                }
            }
        } else {
            const headers = {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            };
            const response = await fetch(`${API_BASE_URL}/api/events`, { headers });
            if (response.ok) {
                const apiEvents = await response.json();
                
                // API から取得したデータが空の場合、デフォルトデータを追加
                if (apiEvents.length === 0 && currentUser) {
                    const { sampleEvents } = generateSampleDataForUser(currentUser);
                    events = sampleEvents.slice(1); // ウェルカムイベント以外
                } else {
                    events = apiEvents;
                }
            } else {
                throw new Error('イベントの取得に失敗しました');
            }
        }
        
        updateDashboardEvents();
        if (document.getElementById('events').classList.contains('hidden') === false) {
            renderEvents();
        }
    } catch (error) {
        console.error('イベントの取得に失敗しました:', error);
        // エラー時もデフォルトデータを表示
        if (currentUser) {
            const { sampleEvents } = generateSampleDataForUser(currentUser);
            events = sampleEvents;
            updateDashboardEvents();
        }
    }
}

async function fetchStreams() {
    console.log('📡 fetchStreams開始');
    try {
        console.log('🔍 条件確認: USE_MOCK_DATA =', USE_MOCK_DATA, ', authToken =', authToken ? 'あり' : 'なし');
        if (USE_MOCK_DATA || !authToken) {
            console.log('📋 モックデータを使用します');
            // モックデータ
            streams = [
                {
                    id: 1,
                    name: '1年A組',
                    description: '1年A組のクラスストリーム',
                    type: 'class',
                    class_name: '1年A組',
                    grade: 1,
                    memberCount: 32,
                    announcementCount: 3,
                    membership: { can_post: false, can_moderate: false, is_admin: false }
                },
                {
                    id: 2,
                    name: '数学科',
                    description: '数学の授業・課題に関する情報',
                    type: 'subject',
                    subject_name: '数学',
                    memberCount: 128,
                    announcementCount: 5,
                    membership: { can_post: false, can_moderate: false, is_admin: false }
                },
                {
                    id: 3,
                    name: '全校',
                    description: '全校生徒への重要なお知らせ',
                    type: 'school',
                    memberCount: 450,
                    announcementCount: 2,
                    membership: { can_post: false, can_moderate: false, is_admin: false }
                },
                {
                    id: 4,
                    name: '英語科',
                    description: '英語の授業・課題に関する情報',
                    type: 'subject',
                    subject_name: '英語',
                    memberCount: 95,
                    announcementCount: 7,
                    membership: { can_post: false, can_moderate: false, is_admin: false }
                },
                {
                    id: 5,
                    name: '生徒会',
                    description: '生徒会からのお知らせ',
                    type: 'school',
                    memberCount: 450,
                    announcementCount: 1,
                    membership: { can_post: false, can_moderate: false, is_admin: false }
                }
            ];
            console.log('✅ モックストリームデータを設定:', streams.length, '件');
        } else {
            const headers = {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            };
            const response = await fetch(`${API_BASE_URL}/api/streams`, { headers });
            if (response.ok) {
                streams = await response.json();
            } else {
                throw new Error('ストリームの取得に失敗しました');
            }
        }
        
        console.log('📋 ストリーム取得完了:', streams.length, '件のストリーム');
        
        // ストリームページが表示中の場合は再描画
        if (document.getElementById('streams') && !document.getElementById('streams').classList.contains('hidden')) {
            renderStreams();
        }
    } catch (error) {
        console.error('ストリームの取得に失敗しました:', error);
        streams = [];
        
        // エラーの場合も再描画（空の状態を表示）
        if (document.getElementById('streams') && !document.getElementById('streams').classList.contains('hidden')) {
            renderStreams();
        }
    }
}

// UI更新関数
function updateUserInfo() {
    if (currentUser) {
        document.getElementById('user-name').textContent = currentUser.name;
        document.getElementById('user-role').textContent = getRoleText(currentUser.role);
        document.getElementById('welcome-name').textContent = currentUser.name + 'さん';
        document.getElementById('user-role-display').textContent = getRoleText(currentUser.role);
        
        document.getElementById('total-assignments').textContent = assignments.length;
        document.getElementById('total-events').textContent = events.length;
    }
}

function updateDashboardAssignments() {
    const container = document.getElementById('dashboard-assignments');
    
    if (assignments.length === 0) {
        container.innerHTML = '<div class="text-center py-8"><p class="text-gray-500">課題がありません</p></div>';
        return;
    }
    
    const html = assignments.slice(0, 5).map(assignment => {
        const status = getAssignmentStatus(assignment.due_at);
        return `
            <div class="border-l-4 border-blue-400 pl-4 py-2">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="text-sm font-medium text-gray-900">${assignment.title}</h3>
                        <p class="text-sm text-gray-500">${assignment.subject}</p>
                    </div>
                    <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}">
                        ${getStatusText(status)}
                    </span>
                </div>
                <p class="mt-1 text-xs text-gray-500">
                    締切: ${formatDate(assignment.due_at)}
                </p>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

function updateDashboardEvents() {
    const container = document.getElementById('dashboard-events');
    
    if (events.length === 0) {
        container.innerHTML = '<div class="text-center py-8"><p class="text-gray-500">イベントがありません</p></div>';
        return;
    }
    
    const html = events.slice(0, 5).map(event => `
        <div class="border-l-4 border-green-400 pl-4 py-2">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-sm font-medium text-gray-900">${event.title}</h3>
                    <p class="text-sm text-gray-500 capitalize">${getCategoryText(event.category)}</p>
                    ${event.location ? `<p class="text-xs text-gray-400">📍 ${event.location}</p>` : ''}
                </div>
            </div>
            <p class="mt-1 text-xs text-gray-500">
                ${formatDate(event.start_at)} - ${formatDate(event.end_at)}
            </p>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function renderAssignments() {
    const container = document.getElementById('assignments-content');
    
    if (assignments.length === 0) {
        container.innerHTML = `
            <div class="bg-white shadow overflow-hidden sm:rounded-md">
                <div class="px-4 py-12 text-center">
                    <p class="text-gray-500">課題がありません</p>
                </div>
            </div>
        `;
        return;
    }
    
    // 統計計算
    const statusCounts = {
        overdue: assignments.filter(a => getAssignmentStatus(a.due_at) === 'overdue').length,
        today: assignments.filter(a => getAssignmentStatus(a.due_at) === 'due-today').length,
        tomorrow: assignments.filter(a => getAssignmentStatus(a.due_at) === 'due-tomorrow').length
    };
    
    const sortedAssignments = [...assignments].sort((a, b) => 
        new Date(a.due_at) - new Date(b.due_at)
    );
    
    const html = `
        <!-- 統計カード -->
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">📝</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">合計課題</dt>
                            <dd class="text-lg font-medium text-gray-900">${assignments.length}</dd>
                        </div>
                    </div>
                </div>
            </div>
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white text-sm">⚠️</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">期限超過</dt>
                            <dd class="text-lg font-medium text-gray-900">${statusCounts.overdue}</dd>
                        </div>
                    </div>
                </div>
            </div>
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-sm">🔥</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">今日締切</dt>
                            <dd class="text-lg font-medium text-gray-900">${statusCounts.today}</dd>
                        </div>
                    </div>
                </div>
            </div>
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-white text-sm">⏰</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">明日締切</dt>
                            <dd class="text-lg font-medium text-gray-900">${statusCounts.tomorrow}</dd>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 課題一覧 -->
        <div class="bg-white shadow overflow-hidden sm:rounded-md">
            <div class="px-4 py-5 sm:px-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900">課題一覧</h3>
                <p class="mt-1 max-w-2xl text-sm text-gray-500">期限順に表示されています</p>
            </div>
            
            <ul class="divide-y divide-gray-200">
                ${sortedAssignments.map(assignment => {
                    const status = getAssignmentStatus(assignment.due_at);
                    return `
                        <li>
                            <div class="px-4 py-4 sm:px-6 hover:bg-gray-50">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <div class="flex-shrink-0">
                                            <div class="inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(status)}">
                                                ${getStatusText(status)}
                                            </div>
                                        </div>
                                        <div class="ml-4">
                                            <div class="flex items-center">
                                                <p class="text-sm font-medium text-gray-900">${assignment.title}</p>
                                            </div>
                                            <div class="mt-2 flex items-center text-sm text-gray-500">
                                                <p class="mr-4">📚 ${assignment.subject}</p>
                                                <p>📅 締切: ${formatDate(assignment.due_at)}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-2">
                                        <button class="inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                                            詳細
                                        </button>
                                    </div>
                                </div>
                                ${assignment.description ? `
                                    <div class="mt-2 text-sm text-gray-600 ml-20">
                                        ${assignment.description}
                                    </div>
                                ` : ''}
                            </div>
                        </li>
                    `;
                }).join('')}
            </ul>
        </div>
    `;
    
    container.innerHTML = html;
}

function renderEvents() {
    const container = document.getElementById('events-content');
    
    if (events.length === 0) {
        container.innerHTML = `
            <div class="bg-white shadow overflow-hidden sm:rounded-md">
                <div class="px-4 py-12 text-center">
                    <p class="text-gray-500">イベントがありません</p>
                </div>
            </div>
        `;
        return;
    }
    
    // 統計計算
    const statusCounts = {
        today: events.filter(e => {
            const today = new Date();
            const eventDate = new Date(e.start_at);
            return today.toDateString() === eventDate.toDateString();
        }).length,
        tomorrow: events.filter(e => {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const eventDate = new Date(e.start_at);
            return tomorrow.toDateString() === eventDate.toDateString();
        }).length,
        upcoming: events.filter(e => {
            const eventDate = new Date(e.start_at);
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            return eventDate > tomorrow;
        }).length
    };
    
    const sortedEvents = [...events].sort((a, b) => 
        new Date(a.start_at) - new Date(b.start_at)
    );
    
    const html = `
        <!-- 統計カード -->
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">📅</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">合計イベント</dt>
                            <dd class="text-lg font-medium text-gray-900">${events.length}</dd>
                        </div>
                    </div>
                </div>
            </div>
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm">✨</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">今日</dt>
                            <dd class="text-lg font-medium text-gray-900">${statusCounts.today}</dd>
                        </div>
                    </div>
                </div>
            </div>
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">🔜</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">明日</dt>
                            <dd class="text-lg font-medium text-gray-900">${statusCounts.tomorrow}</dd>
                        </div>
                    </div>
                </div>
            </div>
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm">📆</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dt class="text-sm font-medium text-gray-500 truncate">今後予定</dt>
                            <dd class="text-lg font-medium text-gray-900">${statusCounts.upcoming}</dd>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- イベント一覧 -->
        <div class="bg-white shadow overflow-hidden sm:rounded-md">
            <div class="px-4 py-5 sm:px-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900">イベント一覧</h3>
                <p class="mt-1 max-w-2xl text-sm text-gray-500">日付順に表示されています</p>
            </div>
            
            <div class="divide-y divide-gray-200">
                ${sortedEvents.map(event => `
                    <div class="px-4 py-4 sm:px-6">
                        <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-3">
                                    <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                                        ${getCategoryText(event.category)}
                                    </span>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <button class="inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                                        詳細
                                    </button>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <h5 class="text-sm font-medium text-gray-900">${event.title}</h5>
                                <div class="mt-1 flex items-center text-sm text-gray-500 space-x-4">
                                    <span>⏰ ${formatDate(event.start_at)} - ${formatDate(event.end_at)}</span>
                                    ${event.location ? `<span>📍 ${event.location}</span>` : ''}
                                </div>
                                ${event.description ? `
                                    <p class="mt-2 text-sm text-gray-600">${event.description}</p>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// ナビゲーション
function showDashboard() {
    console.log('🏠 ダッシュボード表示処理開始');
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    const dashboardEl = document.getElementById('dashboard');
    if (dashboardEl) {
        dashboardEl.classList.remove('hidden');
        console.log('✅ ダッシュボード要素表示完了');
    } else {
        console.error('❌ ダッシュボード要素が見つかりません');
    }
    
    updateNavigation('dashboard');
    updateDashboardAssignments();
    updateDashboardEvents();
}

function showAssignments() {
    console.log('📝 課題ページ表示処理開始');
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    const assignmentsEl = document.getElementById('assignments');
    if (assignmentsEl) {
        assignmentsEl.classList.remove('hidden');
        console.log('✅ 課題ページ要素表示完了');
    } else {
        console.error('❌ 課題ページ要素が見つかりません');
    }
    
    updateNavigation('assignments');
    renderAssignments();
}

function showEvents() {
    console.log('📅 イベントページ表示処理開始');
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    const eventsEl = document.getElementById('events');
    if (eventsEl) {
        eventsEl.classList.remove('hidden');
        console.log('✅ イベントページ要素表示完了');
    } else {
        console.error('❌ イベントページ要素が見つかりません');
    }
    
    updateNavigation('events');
    renderEvents();
}

function showStreams() {
    console.log('💬 ストリームページ表示処理開始');
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    const streamsEl = document.getElementById('streams');
    if (streamsEl) {
        streamsEl.classList.remove('hidden');
        console.log('✅ ストリームページ要素表示完了');
    } else {
        console.error('❌ ストリームページ要素が見つかりません');
    }
    
    updateNavigation('streams');
    
    // ストリームが読み込まれていない場合は取得してから表示
    console.log('🔍 ストリームデータ確認:', streams ? streams.length : 'null', '件');
    if (!streams || streams.length === 0) {
        console.log('📋 ストリームデータが未取得、取得中...');
        fetchStreams().then(() => {
            console.log('📋 fetchStreams完了、renderStreams呼び出し');
            renderStreams();
        });
    } else {
        console.log('📋 既存ストリームデータを使用、renderStreams呼び出し');
        renderStreams();
    }
}

// ストリーム一覧を表示
function renderStreams() {
    console.log('🎨 renderStreams開始、streams:', streams ? streams.length : 'null', '件');
    const streamsContainer = document.getElementById('streams-list');
    if (!streamsContainer) {
        console.error('❌ streams-list要素が見つかりません');
        return;
    }

    console.log('✅ streams-list要素見つかりました');

    if (!streams || streams.length === 0) {
        console.log('📋 ストリームデータが空です');
        streamsContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <p>まだ参加しているストリームがありません</p>
            </div>
        `;
        return;
    }

    const streamHTML = streams.map(stream => `
        <div class="p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
             onclick="selectStream(${stream.id})">
            <div class="flex items-center justify-between mb-2">
                <h4 class="font-medium text-gray-900">${escapeHtml(stream.name)}</h4>
                <span class="px-2 py-1 text-xs rounded-full ${getStreamTypeColor(stream.type)}">
                    ${getStreamTypeLabel(stream.type)}
                </span>
            </div>
            <p class="text-gray-600 text-sm mb-2">${escapeHtml(stream.description || '')}</p>
            <div class="flex items-center text-xs text-gray-500">
                <span class="mr-3">👥 ${stream.memberCount || 0}</span>
                <span>📝 ${stream.announcementCount || 0}</span>
            </div>
        </div>
    `).join('');

    streamsContainer.innerHTML = streamHTML;
    console.log('✅ ストリーム一覧表示完了:', streams.length, '件');
}

// ストリームタイプの色を取得
function getStreamTypeColor(type) {
    switch (type) {
        case 'class': return 'bg-blue-100 text-blue-800';
        case 'subject': return 'bg-green-100 text-green-800';
        case 'school': return 'bg-purple-100 text-purple-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// ストリームタイプのラベルを取得
function getStreamTypeLabel(type) {
    switch (type) {
        case 'class': return 'クラス';
        case 'subject': return '教科';
        case 'school': return '学校';
        default: return 'その他';
    }
}

// ストリームを選択
function selectStream(streamId) {
    console.log('📋 ストリーム選択:', streamId);
    selectedStream = streams.find(s => s.id === streamId);
    if (selectedStream) {
        console.log('✅ 選択されたストリーム:', selectedStream.name);
        fetchStreamAnnouncements(streamId);
        
        // 選択状態を更新
        updateStreamSelection(streamId);
    } else {
        console.error('❌ ストリームが見つかりません:', streamId);
    }
}

// ストリーム選択状態を更新
function updateStreamSelection(streamId) {
    const streamCards = document.querySelectorAll('#streams-list > div');
    streamCards.forEach(card => {
        card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
        card.classList.add('hover:bg-gray-50');
    });
    
    const selectedIndex = streams.findIndex(s => s.id === streamId);
    if (selectedIndex !== -1) {
        const selectedCard = document.querySelector(`#streams-list > div:nth-child(${selectedIndex + 1})`);
        if (selectedCard) {
            selectedCard.classList.remove('hover:bg-gray-50');
            selectedCard.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50');
        }
    }
}

// ストリームのお知らせを取得
async function fetchStreamAnnouncements(streamId) {
    try {
        console.log('📡 ストリームお知らせ取得開始:', streamId);
        
        // ストリーム別のモックデータを生成
        const mockAnnouncementsByStream = {
            1: [ // 1年A組
                {
                    id: 1,
                    title: '明日の時間割変更について',
                    content: '明日（1月16日）の3時間目と4時間目が入れ替わります。3時間目：国語、4時間目：数学となります。',
                    author: '担任：佐藤先生',
                    created_at: '2024-01-15T16:30:00Z',
                    priority: 'high'
                },
                {
                    id: 2,
                    title: 'クラス懇談会のお知らせ',
                    content: '1月20日（土）14:00よりクラス懇談会を開催いたします。保護者の皆様のご参加をお待ちしております。',
                    author: '担任：佐藤先生',
                    created_at: '2024-01-12T09:00:00Z',
                    priority: 'normal'
                },
                {
                    id: 3,
                    title: '提出物について',
                    content: '冬休みの宿題の提出期限は明日までです。まだ提出していない人は忘れずに提出してください。',
                    author: '担任：佐藤先生',
                    created_at: '2024-01-14T08:15:00Z',
                    priority: 'normal'
                }
            ],
            2: [ // 数学科
                {
                    id: 4,
                    title: '数学小テストの実施について',
                    content: '来週月曜日（1月22日）の1時間目に因数分解の小テストを実施します。教科書p.45-60の範囲から出題予定です。',
                    author: '数学科：田中先生',
                    created_at: '2024-01-15T14:20:00Z',
                    priority: 'high'
                },
                {
                    id: 5,
                    title: '補習授業のお知らせ',
                    content: '数学が苦手な生徒向けの補習授業を毎週水曜日の放課後に実施しています。参加希望者は担当教員まで。',
                    author: '数学科：田中先生',
                    created_at: '2024-01-10T12:00:00Z',
                    priority: 'normal'
                },
                {
                    id: 6,
                    title: '数学検定のご案内',
                    content: '3月に実施される数学検定の申し込みを開始しました。希望者は2月15日までに申込書を提出してください。',
                    author: '数学科：田中先生',
                    created_at: '2024-01-08T10:30:00Z',
                    priority: 'normal'
                }
            ],
            3: [ // 全校
                {
                    id: 7,
                    title: '【重要】インフルエンザ予防について',
                    content: 'インフルエンザが流行しています。手洗い・うがい・マスク着用を徹底し、体調不良の際は無理せず休養してください。',
                    author: '保健室',
                    created_at: '2024-01-15T11:00:00Z',
                    priority: 'high'
                },
                {
                    id: 8,
                    title: '学校説明会の開催について',
                    content: '2月3日（土）に来年度入学予定者向けの学校説明会を開催します。在校生の皆さんもお手伝いをお願いします。',
                    author: '教務部',
                    created_at: '2024-01-13T15:45:00Z',
                    priority: 'normal'
                }
            ],
            4: [ // 英語科
                {
                    id: 9,
                    title: 'English Speaking Contest参加者募集',
                    content: '年次英語スピーキングコンテストの参加者を募集しています。申込締切は1月31日です。',
                    author: '英語科：Johnson先生',
                    created_at: '2024-01-14T13:15:00Z',
                    priority: 'normal'
                },
                {
                    id: 10,
                    title: '英語検定の結果発表',
                    content: '12月に実施された英語検定の結果を発表しました。合格者は英語科掲示板を確認してください。',
                    author: '英語科：山田先生',
                    created_at: '2024-01-11T16:00:00Z',
                    priority: 'normal'
                }
            ],
            5: [ // 生徒会
                {
                    id: 11,
                    title: '文化祭実行委員募集',
                    content: '今年度の文化祭実行委員を募集しています。やる気のある生徒の応募をお待ちしています！',
                    author: '生徒会',
                    created_at: '2024-01-12T17:30:00Z',
                    priority: 'normal'
                }
            ]
        };
        
        currentStreamAnnouncements = mockAnnouncementsByStream[streamId] || [];
        renderStreamAnnouncements();
        
    } catch (error) {
        console.error('❌ ストリームお知らせ取得エラー:', error);
        showNotification('お知らせの取得に失敗しました', 'error');
    }
}

// ストリームお知らせを表示
function renderStreamAnnouncements() {
    const announcementsContainer = document.getElementById('stream-announcements');
    if (!announcementsContainer) {
        console.error('❌ stream-announcements要素が見つかりません');
        return;
    }

    if (!currentStreamAnnouncements || currentStreamAnnouncements.length === 0) {
        announcementsContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <p>お知らせがありません</p>
            </div>
        `;
        return;
    }

    const announcementsHTML = currentStreamAnnouncements.map(announcement => `
        <div class="bg-white rounded-lg shadow p-6 mb-4">
            <div class="flex items-start justify-between mb-3">
                <h3 class="text-lg font-semibold text-gray-900">${escapeHtml(announcement.title)}</h3>
                ${announcement.priority === 'high' ? '<span class="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">重要</span>' : ''}
            </div>
            <p class="text-gray-700 mb-4">${escapeHtml(announcement.content)}</p>
            <div class="flex items-center text-sm text-gray-500">
                <span class="mr-4">👤 ${escapeHtml(announcement.author)}</span>
                <span>📅 ${formatDate(announcement.created_at)}</span>
            </div>
        </div>
    `).join('');

    announcementsContainer.innerHTML = announcementsHTML;
    console.log('✅ ストリームお知らせ表示完了:', currentStreamAnnouncements.length, '件');
}

// お知らせ検索
function searchAnnouncements() {
    const searchInput = document.getElementById('stream-search');
    if (!searchInput) {
        console.error('❌ stream-search要素が見つかりません');
        return;
    }

    const query = searchInput.value.trim();
    console.log('🔍 お知らせ検索:', query);

    if (!query) {
        renderStreamAnnouncements();
        return;
    }

    if (!currentStreamAnnouncements) {
        console.log('📝 検索対象のお知らせがありません');
        return;
    }

    const filteredAnnouncements = currentStreamAnnouncements.filter(announcement => 
        announcement.title.toLowerCase().includes(query.toLowerCase()) ||
        announcement.content.toLowerCase().includes(query.toLowerCase()) ||
        announcement.author.toLowerCase().includes(query.toLowerCase())
    );

    console.log('🔍 検索結果:', filteredAnnouncements.length, '件');

    const announcementsContainer = document.getElementById('stream-announcements');
    if (filteredAnnouncements.length === 0) {
        announcementsContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <p>「${escapeHtml(query)}」に一致するお知らせが見つかりません</p>
            </div>
        `;
    } else {
        const announcementsHTML = filteredAnnouncements.map(announcement => `
            <div class="bg-white rounded-lg shadow p-6 mb-4">
                <div class="flex items-start justify-between mb-3">
                    <h3 class="text-lg font-semibold text-gray-900">${escapeHtml(announcement.title)}</h3>
                    ${announcement.priority === 'high' ? '<span class="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">重要</span>' : ''}
                </div>
                <p class="text-gray-700 mb-4">${escapeHtml(announcement.content)}</p>
                <div class="flex items-center text-sm text-gray-500">
                    <span class="mr-4">👤 ${escapeHtml(announcement.author)}</span>
                    <span>📅 ${formatDate(announcement.created_at)}</span>
                </div>
            </div>
        `).join('');
        announcementsContainer.innerHTML = announcementsHTML;
    }
}

function updateNavigation(active) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('border-blue-500', 'text-gray-900');
        link.classList.add('border-transparent', 'text-gray-500');
    });
    
    const activeLink = document.querySelector(`a[data-tab="${active}"]`);
    if (activeLink) {
        activeLink.classList.remove('border-transparent', 'text-gray-500');
        activeLink.classList.add('border-blue-500', 'text-gray-900');
    }
}

// デバッグ用関数
function debugStreams() {
    console.log('=== ストリームデバッグ情報 ===');
    console.log('USE_MOCK_DATA:', USE_MOCK_DATA);
    console.log('authToken:', authToken);
    console.log('streams配列:', streams);
    console.log('streams長さ:', streams ? streams.length : 'null');
    console.log('streams-list要素:', document.getElementById('streams-list'));
    console.log('stream-announcements要素:', document.getElementById('stream-announcements'));
}

function forceShowStreams() {
    console.log('🔧 強制ストリーム表示開始');
    streams = []; // 一度クリア
    fetchStreams().then(() => {
        console.log('🔧 強制取得完了、表示開始');
        showStreams();
    });
}

// ウィンドウにデバッグ関数を公開
window.debugStreams = debugStreams;
window.forceShowStreams = forceShowStreams;

// ウェルカムメッセージ表示
function showWelcomeMessage(userName) {
    // 既存のウェルカムメッセージがあれば削除
    const existingWelcome = document.getElementById('welcome-notification');
    if (existingWelcome) {
        existingWelcome.remove();
    }

    // ウェルカムメッセージを作成
    const welcomeDiv = document.createElement('div');
    welcomeDiv.id = 'welcome-notification';
    welcomeDiv.className = 'fixed top-4 right-4 z-50 bg-blue-500 text-white p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-500 translate-x-full';
    welcomeDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <div class="text-2xl">🎉</div>
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium">
                    ${userName}さん、CampusFlowへようこそ！
                </p>
                <p class="mt-1 text-xs text-blue-100">
                    まずはサンプル課題とイベントをチェックしてみてください。
                </p>
            </div>
            <div class="ml-auto pl-3">
                <button onclick="closeWelcomeMessage()" class="text-blue-200 hover:text-white">
                    <span class="sr-only">閉じる</span>
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(welcomeDiv);

    // アニメーションでスライドイン
    setTimeout(() => {
        welcomeDiv.classList.remove('translate-x-full');
    }, 100);

    // 5秒後に自動的に消す
    setTimeout(() => {
        closeWelcomeMessage();
    }, 5000);
}

function closeWelcomeMessage() {
    const welcomeDiv = document.getElementById('welcome-notification');
    if (welcomeDiv) {
        welcomeDiv.classList.add('translate-x-full');
        setTimeout(() => {
            welcomeDiv.remove();
        }, 500);
    }
}

// アプリ初期化
async function initializeApp() {
    console.log('🔄 アプリ初期化開始');
    
    try {
        console.log('👤 ユーザー情報取得中...');
        await fetchUser();
        console.log('✅ ユーザー情報取得完了:', currentUser);
        
        console.log('📝 課題取得中...');
        await fetchAssignments();
        console.log('✅ 課題取得完了:', assignments.length, '件');
        
        console.log('📅 イベント取得中...');
        await fetchEvents();
        console.log('✅ イベント取得完了:', events.length, '件');
        
        console.log('📋 ストリーム取得中...');
        await fetchStreams();
        console.log('✅ ストリーム取得完了:', streams.length, '件');
        console.log('📋 取得したストリーム:', streams.map(s => s.name));
        
        console.log('🏠 ダッシュボード表示開始');
        showDashboard();
        
        console.log('🔧 ユーザー情報UI更新');
        updateUserInfo();
        
        console.log('✅ アプリ初期化完了');
    } catch (error) {
        console.error('❌ アプリ初期化エラー:', error);
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 アプリケーション開始');
    
    // ナビゲーションのイベントリスナーを設定
    const navLinks = document.querySelectorAll('.nav-link');
    console.log('📋 ナビゲーションリンク数:', navLinks.length);
    
    navLinks.forEach((link) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.getAttribute('data-tab');
            console.log('🔗 ナビゲーションクリック:', tab);
            if (tab === 'dashboard') showDashboard();
            else if (tab === 'assignments') showAssignments();
            else if (tab === 'events') showEvents();
            else if (tab === 'streams') showStreams();
        });
    });

    // 認証チェック
    console.log('🔐 認証チェック開始');
    if (checkAuth()) {
        console.log('✅ 認証済み - メインコンテンツ表示');
        showMainContent();
        await initializeApp();
    } else {
        console.log('❌ 未認証 - ログインページ表示');
        showLoginPage();
    }
    
    // URL パラメータでGoogle OAuth コールバックを処理
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code && !USE_MOCK_DATA) {
        try {
            console.log('OAuth callback started with code:', code);
            document.getElementById('login-loading').classList.remove('hidden');
            
            const response = await fetch(`${API_BASE_URL}/api/auth/google/callback?code=${code}`);
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.access_token) {
                localStorage.setItem('authToken', data.access_token);
                localStorage.setItem('currentUser', JSON.stringify(data.user));
                authToken = data.access_token;
                currentUser = data.user;
                
                // URLをクリーンアップ
                window.history.replaceState({}, document.title, window.location.pathname);
                
                console.log('About to call showMainContent');
                showMainContent();
                console.log('About to call initializeApp');
                await initializeApp();
                
                document.getElementById('login-loading').classList.add('hidden');
            } else {
                throw new Error('認証に失敗しました');
            }
        } catch (error) {
            console.error('OAuth callback error:', error);
            document.getElementById('login-loading').classList.add('hidden');
            document.getElementById('login-error').classList.remove('hidden');
            document.getElementById('login-error-message').textContent = 'ログインに失敗しました';
            showLoginPage();
        }
    }
});

// グローバル関数を明示的に登録
window.showDashboard = showDashboard;
window.showAssignments = showAssignments;
window.showEvents = showEvents;
window.showStreams = showStreams;
window.loginWithGoogle = loginWithGoogle;
window.logout = logout;
window.closeWelcomeMessage = closeWelcomeMessage;
window.selectStream = selectStream;
window.searchAnnouncements = searchAnnouncements;