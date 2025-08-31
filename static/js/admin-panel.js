/**
 * Admin Panel Manager
 * Handles all admin operations with unified interface
 */
class AdminPanel {
    constructor() {
        this.operations = {
            'sync-btn': {
                endpoint: '/api/sync-raindrops',
                operation: 'Sync Raindrops',
                statusEndpoint: '/api/sync-status',
                polling: true
            },
            'regen-btn': {
                endpoint: '/api/regenerate',
                operation: 'Regenerate Site',
                polling: false
            },
            'sync-to-volume-btn': {
                endpoint: '/api/sync-to-volume',
                operation: 'Sync Working → Persistent',
                polling: true
            },
            'sync-from-volume-btn': {
                endpoint: '/api/sync-from-volume', 
                operation: 'Sync Persistent → Working',
                polling: true
            },
            'bidirectional-sync-btn': {
                endpoint: '/api/bidirectional-sync',
                operation: 'Bidirectional Sync',
                polling: true
            },
            'git-sync-now-btn': {
                endpoint: '/api/scheduler/git-sync-now',
                operation: 'Sync to GitHub',
                polling: true
            },
            'raindrop-sync-now-btn': {
                endpoint: '/api/scheduler/sync-raindrops-now',
                operation: 'Sync Raindrops',
                polling: true
            },
            'scheduler-start-btn': {
                endpoint: '/api/scheduler/start',
                operation: 'Start Scheduler',
                polling: false
            },
            'scheduler-stop-btn': {
                endpoint: '/api/scheduler/stop',
                operation: 'Stop Scheduler', 
                polling: false
            },
            'sync-pages-btn': {
                endpoint: '/api/sync-pages',
                operation: 'Sync Pages from GitHub',
                polling: true
            },
            'emergency-restore-btn': {
                endpoint: '/api/emergency-restore',
                operation: 'Emergency Restore',
                polling: true,
                confirmMessage: 'Are you sure? This will overwrite /data/content with GitHub repository content!'
            }
        };
    }

    init() {
        // Set up button handlers
        Object.keys(this.operations).forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.dataset.originalText = button.textContent;
                button.onclick = () => this.runOperation(buttonId);
            }
        });
        
        // Load initial status
        this.loadSchedulerStatus();
    }

    async runOperation(buttonId) {
        const config = this.operations[buttonId];
        const button = document.getElementById(buttonId);
        const statusDiv = document.getElementById(buttonId.replace('-btn', '-status'));
        
        // Confirmation check
        if (config.confirmMessage && !confirm(config.confirmMessage)) {
            return;
        }
        
        // Set loading state
        this.setButtonState(button, 'loading', `${config.operation}...`);
        this.showStatus(statusDiv, 'loading', `Starting ${config.operation.toLowerCase()}...`);
        
        try {
            const response = await fetch(config.endpoint, { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                if (config.polling && (result.status === 'started' || result.status === 'running')) {
                    this.pollStatus(config.statusEndpoint || '/api/operation-status', 
                                  button, statusDiv, config);
                } else {
                    this.showStatus(statusDiv, 'success', `✓ ${config.operation} completed`);
                    this.setButtonState(button, 'normal', button.dataset.originalText);
                }
            } else {
                throw new Error(result.detail || result.message || 'Operation failed');
            }
        } catch (error) {
            this.showStatus(statusDiv, 'error', `✗ ${config.operation} failed: ${error.message}`);
            this.setButtonState(button, 'normal', button.dataset.originalText);
        }
    }

    async pollStatus(statusEndpoint, button, statusDiv, config) {
        const startTime = Date.now();
        const poll = async () => {
            try {
                const response = await fetch(statusEndpoint);
                const status = await response.json();
                
                if (status.running) {
                    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                    this.showStatus(statusDiv, 'loading', 
                        `${status.message || config.operation + ' in progress...'} (${elapsed}s)`);
                    setTimeout(poll, 2000);
                } else {
                    if (status.success) {
                        this.showStatus(statusDiv, 'success', 
                            `✓ ${status.message || config.operation + ' completed'}`);
                    } else {
                        this.showStatus(statusDiv, 'error', 
                            `✗ ${status.message || config.operation + ' failed'}`);
                    }
                    this.setButtonState(button, 'normal', button.dataset.originalText);
                    this.loadSchedulerStatus(); // Refresh scheduler status
                }
            } catch (error) {
                this.showStatus(statusDiv, 'error', `✗ Status check failed: ${error.message}`);
                this.setButtonState(button, 'normal', button.dataset.originalText);
            }
        };
        setTimeout(poll, 1000);
    }

    setButtonState(button, state, text) {
        button.disabled = state === 'loading';
        button.textContent = text;
        
        if (state === 'loading') {
            button.classList.add('btn-secondary');
            button.classList.remove('btn-primary', 'btn-success', 'btn-warning', 'btn-danger');
        } else {
            button.classList.remove('btn-secondary');
        }
    }

    showStatus(statusDiv, type, message) {
        const statusClass = type === 'success' ? 'alert alert-success' : 
                          type === 'error' ? 'alert alert-danger' :
                          'alert alert-info';
        statusDiv.innerHTML = `<div class="${statusClass} mt-2">${message}</div>`;
    }

    async loadSchedulerStatus() {
        try {
            const response = await fetch('/api/scheduler/status');
            const status = await response.json();
            
            const statusDiv = document.getElementById('scheduler-status');
            if (statusDiv) {
                const isRunning = status.running;
                const statusClass = isRunning ? 'alert alert-success' : 'alert alert-secondary';
                const statusText = isRunning ? '✅ Scheduler is running' : '⏸️ Scheduler is stopped';
                
                let html = `<div class="${statusClass}">
                    ${statusText}<br>
                    <small>
                        📡 <strong>Last Git Sync:</strong> ${status.last_git_sync || 'Never'}<br>
                        📚 <strong>Last Raindrop Sync:</strong> ${status.last_raindrop_sync || 'Never'}
                    </small>
                </div>`;
                statusDiv.innerHTML = html;
            }
        } catch (error) {
            console.error('Failed to load scheduler status:', error);
        }
    }
}

// Global admin panel instance
window.adminPanel = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
    window.adminPanel.init();
});