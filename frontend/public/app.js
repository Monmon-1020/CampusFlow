// グローバル状態
let currentUser = null;
let assignments = [];
let events = [];

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

// API呼び出し
async function fetchUser() {
    try {
        const response = await fetch('/api/me');
        currentUser = await response.json();
        updateUserInfo();
    } catch (error) {
        console.error('ユーザー情報の取得に失敗しました:', error);
    }
}

async function fetchAssignments() {
    try {
        const response = await fetch('/api/assignments');
        assignments = await response.json();
        updateDashboardAssignments();
        if (document.getElementById('assignments').style.display !== 'none') {
            renderAssignments();
        }
    } catch (error) {
        console.error('課題の取得に失敗しました:', error);
    }
}

async function fetchEvents() {
    try {
        const response = await fetch('/api/events');
        events = await response.json();
        updateDashboardEvents();
        if (document.getElementById('events').style.display !== 'none') {
            renderEvents();
        }
    } catch (error) {
        console.error('イベントの取得に失敗しました:', error);
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
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    document.getElementById('dashboard').classList.remove('hidden');
    
    updateNavigation('dashboard');
    updateDashboardAssignments();
    updateDashboardEvents();
}

function showAssignments() {
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    document.getElementById('assignments').classList.remove('hidden');
    
    updateNavigation('assignments');
    renderAssignments();
}

function showEvents() {
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    document.getElementById('events').classList.remove('hidden');
    
    updateNavigation('events');
    renderEvents();
}

function updateNavigation(active) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('border-blue-500', 'text-gray-900');
        link.classList.add('border-transparent', 'text-gray-500');
    });
    
    const activeLink = document.querySelector(`a[onclick="show${active.charAt(0).toUpperCase() + active.slice(1)}()"]`);
    if (activeLink) {
        activeLink.classList.remove('border-transparent', 'text-gray-500');
        activeLink.classList.add('border-blue-500', 'text-gray-900');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    await fetchUser();
    await fetchAssignments();
    await fetchEvents();
    
    showDashboard();
    
    // 統計情報を更新
    updateUserInfo();
});