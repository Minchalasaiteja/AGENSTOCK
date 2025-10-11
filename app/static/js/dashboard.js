// Dashboard specific JavaScript

class Dashboard {
    constructor() {
        this.portfolioData = null;
        this.chatSessions = [];
        this.watchlist = [];
    }

    async init() {
        await this.loadDashboardData();
        this.setupEventListeners();
        this.updateRealTimeData();
        this.setupWebsocket();
    }

    async loadDashboardData() {
        try {
            const data = await AGENSTOCK.apiCall('/api/users/dashboard-data');
            this.updateDashboard(data);
            window.dashboardRecentChats = data.recent_chats;
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    updateDashboard(data) {
        this.updatePortfolioSummary(data.portfolio_summary);
        this.updateRecentActivity(data.recent_chats);
        this.updateWatchlist(data.watchlist);
    }

    updatePortfolioSummary(summary) {
        if (!summary) return;

        const totalValueElement = document.getElementById('portfolioValue');
        const totalPnLElement = document.getElementById('totalPnL');
        const portfolioChangeElement = document.getElementById('portfolioChange');
        const pnlChangeElement = document.getElementById('pnlChange');

        if (totalValueElement) {
            totalValueElement.textContent = AGENSTOCK.formatCurrency(summary.total_value);
        }

        if (totalPnLElement) {
            totalPnLElement.textContent = AGENSTOCK.formatCurrency(summary.total_pnl);
        }

        if (portfolioChangeElement) {
            const changeClass = summary.daily_change >= 0 ? 'positive' : 'negative';
            const changeSymbol = summary.daily_change >= 0 ? '+' : '';
            portfolioChangeElement.textContent = `${changeSymbol}${summary.daily_change}%`;
            portfolioChangeElement.className = `stat-change ${changeClass}`;
        }

        if (pnlChangeElement) {
            const pnlPercent = summary.total_invested > 0 ? 
                (summary.total_pnl / summary.total_invested) * 100 : 0;
            const changeClass = pnlPercent >= 0 ? 'positive' : 'negative';
            const changeSymbol = pnlPercent >= 0 ? '+' : '';
            pnlChangeElement.textContent = `${changeSymbol}${pnlPercent.toFixed(2)}%`;
            pnlChangeElement.className = `stat-change ${changeClass}`;
        }
    }

    updateRecentActivity(chats) {
        this.chatSessions = chats || [];
        const activityList = document.getElementById('recentActivity');
        
        if (!activityList) return;

        if (this.chatSessions.length === 0) {
            activityList.innerHTML = '<div class="no-activity">No recent activity</div>';
            return;
        }

        activityList.innerHTML = this.chatSessions.map(chat => `
            <div class="activity-item" onclick="openChatSession('${chat._id}')">
                <div class="activity-icon">
                    <i class="fas fa-comment"></i>
                </div>
                <div class="activity-content">
                    <h4>${this.escapeHtml(chat.title)}</h4>
                    <p>${this.formatDate(chat.updated_at)}</p>
                </div>
                <div class="activity-message-count">
                    ${chat.message_count || 0} messages
                </div>
            </div>
        `).join('');
    }

    updateWatchlist(watchlist) {
        this.watchlist = watchlist || [];
        const watchlistCountElement = document.getElementById('watchlistCount');
        
        if (watchlistCountElement) {
            watchlistCountElement.textContent = this.watchlist.length;
        }
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Quick action cards
        this.setupQuickActions();
    }

    setupQuickActions() {
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.addEventListener('click', (e) => {
                e.preventDefault();
                const action = card.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });
    }

    handleQuickAction(action) {
        switch (action) {
            case 'research':
                window.location.href = '/research';
                break;
            case 'enhanced-research':
                window.location.href = '/enhanced-research';
                break;
            case 'portfolio':
                window.location.href = '/portfolio';
                break;
            case 'chat':
                window.location.href = '/chat';
                break;
            case 'compare':
                window.location.href = '/compare';
                break;
            default:
                console.log('Unknown action:', action);
        }
    }

    async refreshData() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            const originalHtml = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            refreshBtn.disabled = true;
            
            await this.loadDashboardData();
            
            setTimeout(() => {
                refreshBtn.innerHTML = originalHtml;
                refreshBtn.disabled = false;
                AGENSTOCK.showNotification('Dashboard updated successfully', 'success');
            }, 1000);
        }
    }

    updateRealTimeData() {
        // Poll for chat sessions every 10 seconds to provide near real-time updates
        this.pollInterval = setInterval(() => {
            this.refreshRecentChats();
            this.simulateMarketUpdates();
        }, 10000); // Update every 10 seconds
    }

    setupWebsocket() {
        try {
            const userId = window.currentUserId || '';
            if (!userId) return;

            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            const host = window.location.host;
            const ws = new WebSocket(`${protocol}://${host}/api/chat/ws/${userId}`);

            ws.onopen = () => console.log('Dashboard websocket connected');
            ws.onmessage = (evt) => {
                try {
                    const payload = JSON.parse(evt.data);
                    if (payload.type === 'session_update') {
                        // Update or insert session in chatSessions
                        const session = payload.session;
                        const idx = this.chatSessions.findIndex(s => s._id === session._id);
                        if (idx === -1) this.chatSessions.unshift(session);
                        else this.chatSessions[idx] = session;
                        this.updateRecentActivity(this.chatSessions);
                    } else if (payload.type === 'portfolio_update') {
                        const portfolio = payload.portfolio;
                        if (portfolio && portfolio.total_value !== undefined) {
                            document.getElementById('portfolioValue').textContent = `$${Number(portfolio.total_value).toLocaleString()}`;
                        }
                    }
                } catch (e) {
                    console.error('Invalid websocket payload', e);
                }
            };
            ws.onclose = () => console.log('Dashboard websocket closed');
            ws.onerror = (e) => console.error('Dashboard websocket error', e);
        } catch (err) {
            console.error('Failed to setup websocket', err);
        }
    }

    async refreshRecentChats() {
        try {
            const data = await AGENSTOCK.apiCall('/api/users/dashboard-data');
            if (data && data.recent_chats) {
                // Only update if there are changes
                const ids = (this.chatSessions || []).map(c => c._id).join(',');
                const newIds = data.recent_chats.map(c => c._id).join(',');
                if (ids !== newIds) {
                    this.updateRecentActivity(data.recent_chats);
                    window.dashboardRecentChats = data.recent_chats;
                } else {
                    // Update counts/message_count if changed
                    this.chatSessions = data.recent_chats;
                    this.updateRecentActivity(this.chatSessions);
                }
            }
        } catch (err) {
            console.error('Failed to refresh recent chats', err);
        }
    }

    simulateMarketUpdates() {
        const tickers = document.querySelectorAll('.ticker-item');
        tickers.forEach(ticker => {
            const changeElement = ticker.querySelector('.ticker-change');
            if (changeElement) {
                const randomChange = (Math.random() - 0.5) * 2; // -1% to +1%
                const changeClass = randomChange >= 0 ? 'positive' : 'negative';
                const changeSymbol = randomChange >= 0 ? '+' : '';
                
                changeElement.textContent = `${changeSymbol}${randomChange.toFixed(2)}%`;
                changeElement.className = `ticker-change ${changeClass}`;
            }
        });
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) {
            return 'Just now';
        } else if (diffMins < 60) {
            return `${diffMins} min ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Global functions
function openChatSession(sessionId) {
    // Navigate to the dedicated chats/history page for the session
    if (!sessionId) return window.location.href = '/chats';
    window.location.href = `/chats/${sessionId}`;
}

function loadDashboardData() {
    const dashboard = new Dashboard();
    dashboard.init();
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});