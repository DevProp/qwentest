// SMC Trader - Main JavaScript

/**
 * Format number with commas and decimals
 */
function formatNumber(num, decimals = 2) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format currency value
 */
function formatCurrency(value, symbol = '$') {
    return symbol + formatNumber(value, 4);
}

/**
 * Format percentage
 */
function formatPercentage(value, decimals = 2) {
    return (value * 100).toFixed(decimals) + '%';
}

/**
 * Get signal strength color class
 */
function getSignalStrengthClass(strength) {
    const classes = {
        'Very Strong': 'text-success',
        'Strong': 'text-success',
        'Moderate': 'text-warning',
        'Weak': 'text-danger'
    };
    return classes[strength] || 'text-muted';
}

/**
 * Get signal strength badge class
 */
function getSignalStrengthBadge(strength) {
    const classes = {
        'Very Strong': 'bg-success',
        'Strong': 'bg-success',
        'Moderate': 'bg-warning',
        'Weak': 'bg-danger'
    };
    return classes[strength] || 'bg-secondary';
}

/**
 * Debounce function for search inputs
 */
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

/**
 * Auto-refresh functionality for analysis pages
 */
let autoRefreshInterval;

function startAutoRefresh(intervalMs = 60000) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        console.log('Auto-refreshing data...');
        // Could implement partial refresh here instead of full page reload
    }, intervalMs);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'danger');
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '11';
    document.body.appendChild(container);
    return container;
}

/**
 * Calculate risk-reward ratio
 */
function calculateRiskReward(entry, stopLoss, takeProfit) {
    const risk = Math.abs(entry - stopLoss);
    const reward = Math.abs(takeProfit - entry);
    return reward / risk;
}

/**
 * Calculate position size based on risk percentage
 */
function calculatePositionSize(accountBalance, riskPercentage, entry, stopLoss) {
    const riskAmount = accountBalance * (riskPercentage / 100);
    const riskPerUnit = Math.abs(entry - stopLoss);
    return riskAmount / riskPerUnit;
}

/**
 * Format time ago from timestamp
 */
function timeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }
    
    return 'just now';
}

/**
 * Export analysis data as CSV
 */
function exportToCSV(data, filename = 'smc_analysis.csv') {
    const headers = Object.keys(data[0]);
    const csv = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Initialize tooltips
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add loading state to forms on submit
    const forms = document.querySelectorAll('form[data-loading]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';
            }
        });
    });
});

// Symbol search with autocomplete
const symbolSearchHandler = debounce(async function(query) {
    if (query.length < 2) return;
    
    try {
        const response = await fetch(`/api/search?q=${query}`);
        const data = await response.json();
        
        // Could display autocomplete suggestions here
        console.log('Symbol suggestions:', data.symbols);
    } catch (error) {
        console.error('Search error:', error);
    }
}, 300);

// Handle symbol search input
document.addEventListener('input', function(e) {
    if (e.target.id === 'symbolSearch') {
        symbolSearchHandler(e.target.value);
    }
});

console.log('SMC Trader initialized');
