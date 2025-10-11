// Main JavaScript file for AGENSTOCK

// Global variables
let currentUser = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check authentication status
    checkAuthStatus();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize components
    initializeComponents();
}


function checkAuthStatus() {
    // Try to fetch user profile to check authentication.
    // Do not redirect from known public pages (about, enhanced-research, index, login, signup).
    const publicPaths = ['/', '/about', '/enhanced-research', '/login', '/signup', '/research'];
    const currentPath = window.location.pathname;
    const isPublic = publicPaths.some(p => currentPath === p || currentPath.startsWith(p + '/'));

    fetch('/api/users/profile', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        if (response.status === 401 && !isPublic) {
            // Not authenticated and not on a public page, redirect to login
            window.location.href = '/login';
        }
        // If 200, user is authenticated; optionally load profile data elsewhere.
    })
    .catch(() => {
        if (!isPublic) {
            window.location.href = '/login';
        }
    });
}

    function checkAuthStatus() {
        // Try to fetch user profile to check authentication
        fetch('/api/users/profile', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => {
            if (response.status === 401) {
                // Not authenticated, redirect to login
                const currentPath = window.location.pathname;
                if (currentPath !== '/' && !currentPath.includes('/login') && !currentPath.includes('/signup')) {
                    window.location.href = '/login';
                }
            }
            // If 200, user is authenticated, do nothing
        })
        .catch(() => {
            // On error, redirect to login
            const currentPath = window.location.pathname;
            if (currentPath !== '/' && !currentPath.includes('/login') && !currentPath.includes('/signup')) {
                window.location.href = '/login';
            }
        });
    }

// Removed verifyToken and localStorage logic. Only cookie-based authentication remains.
    // Removed verifyToken, now handled by checkAuthStatus using cookies

function updateUIForAuthenticatedUser() {
    // Update navigation
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu && currentUser) {
        const welcomeElement = document.createElement('span');
        welcomeElement.className = 'user-welcome';
        welcomeElement.textContent = `Welcome, ${currentUser.username}`;
        
        // Clear existing menu and add authenticated items
        navMenu.innerHTML = '';
        navMenu.appendChild(welcomeElement);
        
        if (currentUser.role === 'admin') {
            const adminLink = document.createElement('a');
            adminLink.href = '/admin/dashboard';
            adminLink.className = 'nav-link';
            adminLink.textContent = 'Admin';
            navMenu.appendChild(adminLink);
        }
        
        const dashboardLink = document.createElement('a');
        dashboardLink.href = '/dashboard';
        dashboardLink.className = 'nav-link';
        dashboardLink.textContent = 'Dashboard';
        navMenu.appendChild(dashboardLink);
        
        const logoutLink = document.createElement('a');
        logoutLink.href = '#';
        logoutLink.className = 'nav-link';
        logoutLink.textContent = 'Logout';
        logoutLink.onclick = handleLogout;
        navMenu.appendChild(logoutLink);
    }
}

async function handleLogout(event) {
    event.preventDefault();
    
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Clear local storage and redirect
        localStorage.removeItem('access_token');
        authToken = null;
        currentUser = null;
        window.location.href = '/';
    }
}

function setupEventListeners() {
    // Global error handler
    window.addEventListener('error', function(e) {
        console.error('Global error:', e.error);
    });
    
    // Handle API errors globally
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
    });
}

function initializeComponents() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize modals
    initializeModals();
    
    // Initialize forms
    initializeForms();
}

function initializeTooltips() {
    // Simple tooltip implementation
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltipText = e.target.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function initializeModals() {
    // Close modal when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.style.display = 'none';
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal-overlay[style*="display: flex"]');
            if (openModal) {
                openModal.style.display = 'none';
            }
        }
    });
}

function initializeForms() {
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                submitButton.disabled = true;
                
                // Revert button after form submission (handled by individual forms)
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 3000);
            }
        });
    });
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(endpoint, mergedOptions);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('API call failed:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

// Stock-related utilities
function validateStockSymbol(symbol) {
    return /^[A-Z]{1,5}$/.test(symbol);
}

function getStockColor(change) {
    return change >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
}

// Export for use in other modules
window.AGENSTOCK = {
    apiCall,
    formatCurrency,
    formatPercent,
    formatNumber,
    showNotification,
    validateStockSymbol,
    getStockColor
};

// Add notification styles
const notificationStyles = `
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 1rem;
    z-index: 10000;
    max-width: 400px;
    animation: slideIn 0.3s ease;
}

.notification-success {
    border-left: 4px solid var(--success-color);
}

.notification-error {
    border-left: 4px solid var(--danger-color);
}

.notification-warning {
    border-left: 4px solid var(--warning-color);
}

.notification-info {
    border-left: 4px solid var(--primary-color);
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
}

.notification-close {
    background: none;
    border: none;
    color: var(--gray-color);
    cursor: pointer;
    padding: 0.25rem;
}

.tooltip {
    position: fixed;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.8rem;
    z-index: 1000;
    pointer-events: none;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', notificationStyles);