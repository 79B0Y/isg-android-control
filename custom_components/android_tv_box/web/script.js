// Android TV Box Management Interface JavaScript

class AndroidTVBoxManager {
    constructor() {
        this.currentTab = 'dashboard';
        this.currentConfig = {};
        this.apps = [];
        this.editingApp = null;
        this.statusInterval = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadConfiguration();
        this.loadApps();
        this.startStatusUpdates();
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab || e.target.closest('[data-tab]')?.dataset.tab;
                if (tab) {
                    this.switchTab(tab);
                }
            });
        });

        // Dashboard actions
        const refreshBtn = document.getElementById('refresh-status');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshStatus();
            });
        }

        const wakeBtn = document.getElementById('wake-isg');
        if (wakeBtn) {
            wakeBtn.addEventListener('click', () => {
                this.wakeISG();
            });
        }

        const restartBtn = document.getElementById('restart-isg');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => {
                this.restartISG();
            });
        }

        // App management
        document.getElementById('add-app-btn').addEventListener('click', () => {
            this.showAddAppModal();
        });

        document.getElementById('add-app-modal').querySelector('.close').addEventListener('click', () => {
            this.hideModal('add-app-modal');
        });

        document.getElementById('cancel-add-app').addEventListener('click', () => {
            this.hideModal('add-app-modal');
        });

        document.getElementById('confirm-add-app').addEventListener('click', () => {
            this.addApp();
        });

        document.getElementById('edit-app-modal').querySelector('.close').addEventListener('click', () => {
            this.hideModal('edit-app-modal');
        });

        document.getElementById('cancel-edit-app').addEventListener('click', () => {
            this.hideModal('edit-app-modal');
        });

        document.getElementById('confirm-edit-app').addEventListener('click', () => {
            this.updateApp();
        });

        // Configuration
        document.getElementById('save-config').addEventListener('click', () => {
            this.saveConfiguration();
        });

        document.getElementById('test-adb').addEventListener('click', () => {
            this.testADBConnection();
        });

        document.getElementById('test-mqtt').addEventListener('click', () => {
            this.testMQTTConnection();
        });

        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideModal(e.target.id);
            }
        });
    }

    switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        
        const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        } else {
            console.error('Tab button not found for:', tabName);
        }

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const activeContent = document.getElementById(tabName);
        if (activeContent) {
            activeContent.classList.add('active');
        } else {
            console.error('Tab content not found for:', tabName);
        }

        this.currentTab = tabName;
    }

    async loadConfiguration() {
        try {
            this.showLoading();
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                this.currentConfig = data.data;
                this.populateConfigForm();
            } else {
                this.showToast('Error loading configuration: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Error loading configuration: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadApps() {
        try {
            const response = await fetch('/api/apps');
            const data = await response.json();
            
            if (data.success) {
                this.apps = data.data;
                this.renderApps();
            } else {
                this.showToast('Error loading apps: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Error loading apps: ' + error.message, 'error');
        }
    }

    populateConfigForm() {
        // ADB Configuration
        document.getElementById('adb-host').value = this.currentConfig.host || '127.0.0.1';
        document.getElementById('adb-port').value = this.currentConfig.port || 5555;
        document.getElementById('device-name').value = this.currentConfig.name || 'Android TV Box';

        // Home Assistant Configuration
        document.getElementById('ha-host').value = this.currentConfig.ha_host || 'localhost';
        document.getElementById('ha-port').value = this.currentConfig.ha_port || 8123;
        document.getElementById('ha-token').value = this.currentConfig.ha_token || '';

        // Screenshot Settings
        document.getElementById('screenshot-path').value = this.currentConfig.screenshot_path || '/sdcard/isgbackup/screenshot/';
        document.getElementById('screenshot-keep').value = this.currentConfig.screenshot_keep_count || 3;
        document.getElementById('screenshot-interval').value = this.currentConfig.screenshot_interval || 3;

        // iSG Monitoring
        document.getElementById('isg-monitoring').checked = this.currentConfig.isg_monitoring !== false;
        document.getElementById('isg-interval').value = this.currentConfig.isg_check_interval || 30;

        // MQTT Configuration
        document.getElementById('mqtt-broker').value = this.currentConfig.mqtt_broker || 'localhost';
        document.getElementById('mqtt-port').value = this.currentConfig.mqtt_port || 1883;
        document.getElementById('mqtt-username').value = this.currentConfig.mqtt_username || '';
        document.getElementById('mqtt-password').value = this.currentConfig.mqtt_password || '';
        document.getElementById('mqtt-client-id').value = this.currentConfig.mqtt_client_id || 'android_tv_box';
        document.getElementById('mqtt-base-topic').value = this.currentConfig.mqtt_base_topic || 'android_tv_box';
        document.getElementById('mqtt-status-topic').value = this.currentConfig.mqtt_status_topic || 'status';
        document.getElementById('mqtt-command-topic').value = this.currentConfig.mqtt_command_topic || 'command';
        document.getElementById('mqtt-qos').value = this.currentConfig.mqtt_qos || 1;
        document.getElementById('mqtt-retain').checked = this.currentConfig.mqtt_retain || false;
        document.getElementById('mqtt-keepalive').value = this.currentConfig.mqtt_keepalive || 60;
    }

    async saveConfiguration() {
        try {
            this.showLoading();
            
            const config = {
                host: document.getElementById('adb-host').value,
                port: parseInt(document.getElementById('adb-port').value),
                name: document.getElementById('device-name').value,
                ha_host: document.getElementById('ha-host').value,
                ha_port: parseInt(document.getElementById('ha-port').value),
                ha_token: document.getElementById('ha-token').value,
                screenshot_path: document.getElementById('screenshot-path').value,
                screenshot_keep_count: parseInt(document.getElementById('screenshot-keep').value),
                screenshot_interval: parseInt(document.getElementById('screenshot-interval').value),
                isg_monitoring: document.getElementById('isg-monitoring').checked,
                isg_check_interval: parseInt(document.getElementById('isg-interval').value),
                mqtt_broker: document.getElementById('mqtt-broker').value,
                mqtt_port: parseInt(document.getElementById('mqtt-port').value),
                mqtt_username: document.getElementById('mqtt-username').value,
                mqtt_password: document.getElementById('mqtt-password').value,
                mqtt_client_id: document.getElementById('mqtt-client-id').value,
                mqtt_base_topic: document.getElementById('mqtt-base-topic').value,
                mqtt_status_topic: document.getElementById('mqtt-status-topic').value,
                mqtt_command_topic: document.getElementById('mqtt-command-topic').value,
                mqtt_qos: parseInt(document.getElementById('mqtt-qos').value),
                mqtt_retain: document.getElementById('mqtt-retain').checked,
                mqtt_keepalive: parseInt(document.getElementById('mqtt-keepalive').value)
            };

            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Configuration saved successfully!', 'success');
                this.currentConfig = { ...this.currentConfig, ...config };
            } else {
                this.showToast('Error saving configuration: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Error saving configuration: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    renderApps() {
        const appsGrid = document.getElementById('apps-grid');
        appsGrid.innerHTML = '';

        this.apps.forEach(app => {
            const appCard = document.createElement('div');
            appCard.className = 'app-card';
            appCard.innerHTML = `
                <div class="visible-badge ${app.visible ? '' : 'hidden'}">
                    ${app.visible ? 'Visible' : 'Hidden'}
                </div>
                <h4>${app.name}</h4>
                <div class="package">${app.package}</div>
                <div class="app-actions">
                    <button class="btn btn-sm btn-info" onclick="manager.editApp('${app.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="manager.deleteApp('${app.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            `;
            appsGrid.appendChild(appCard);
        });
    }

    showAddAppModal() {
        document.getElementById('app-name').value = '';
        document.getElementById('app-package').value = '';
        document.getElementById('app-visible').checked = true;
        this.showModal('add-app-modal');
    }

    async addApp() {
        const name = document.getElementById('app-name').value.trim();
        const package = document.getElementById('app-package').value.trim();
        const visible = document.getElementById('app-visible').checked;

        if (!name || !package) {
            this.showToast('Please fill in all fields', 'warning');
            return;
        }

        try {
            this.showLoading();
            
            const response = await fetch('/api/apps', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    package: package,
                    visible: visible
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('App added successfully!', 'success');
                this.hideModal('add-app-modal');
                this.loadApps();
            } else {
                this.showToast('Error adding app: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Error adding app: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    editApp(appId) {
        const app = this.apps.find(a => a.id === appId);
        if (!app) return;

        this.editingApp = app;
        document.getElementById('edit-app-name').value = app.name;
        document.getElementById('edit-app-package').value = app.package;
        document.getElementById('edit-app-visible').checked = app.visible;
        this.showModal('edit-app-modal');
    }

    async updateApp() {
        if (!this.editingApp) return;

        const name = document.getElementById('edit-app-name').value.trim();
        const package = document.getElementById('edit-app-package').value.trim();
        const visible = document.getElementById('edit-app-visible').checked;

        if (!name || !package) {
            this.showToast('Please fill in all fields', 'warning');
            return;
        }

        try {
            this.showLoading();
            
            const response = await fetch(`/api/apps/${encodeURIComponent(this.editingApp.id)}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    package: package,
                    visible: visible
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('App updated successfully!', 'success');
                this.hideModal('edit-app-modal');
                this.editingApp = null;
                this.loadApps();
            } else {
                this.showToast('Error updating app: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Error updating app: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async deleteApp(appId) {
        if (!confirm('Are you sure you want to delete this app?')) return;

        try {
            this.showLoading();
            
            const response = await fetch(`/api/apps/${encodeURIComponent(appId)}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('App deleted successfully!', 'success');
                this.loadApps();
            } else {
                this.showToast('Error deleting app: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Error deleting app: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async refreshStatus() {
        console.log('refreshStatus() called');
        try {
            this.showLoading();
            console.log('Fetching /api/status...');
            const response = await fetch('/api/status');
            console.log('Response received:', response.status, response.statusText);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                this.updateStatusDisplay(data.data);
                this.showToast('Status refreshed successfully!', 'success');
            } else {
                console.error('API error:', data.error);
                this.showToast('Error refreshing status: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            this.showToast('Error refreshing status: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    updateStatusDisplay(status) {
        console.log('Updating status display with:', status);
        
        // Update connection status
        const connectionStatus = document.getElementById('connection-status');
        if (connectionStatus) {
            if (status.adb_connected) {
                connectionStatus.textContent = 'Online';
                connectionStatus.className = 'status online';
            } else {
                connectionStatus.textContent = 'Offline';
                connectionStatus.className = 'status offline';
            }
        }

        // Update device status
        const devicePower = document.getElementById('device-power');
        if (devicePower) {
            devicePower.textContent = status.device_powered_on ? 'On' : 'Off';
        }
        
        const wifiStatus = document.getElementById('wifi-status');
        if (wifiStatus) {
            wifiStatus.textContent = status.wifi_enabled ? 'Enabled' : 'Disabled';
        }
        
        const currentApp = document.getElementById('current-app');
        if (currentApp) {
            currentApp.textContent = status.current_app || 'Unknown';
        }
        
        const isgStatus = document.getElementById('isg-status');
        if (isgStatus) {
            isgStatus.textContent = status.isg_running ? 'Running' : 'Stopped';
        }
        
        const lastCheck = document.getElementById('last-check');
        if (lastCheck) {
            lastCheck.textContent = new Date(status.timestamp).toLocaleString();
        }
    }

    async wakeISG() {
        console.log('Wake iSG button clicked');
        try {
            this.showLoading();
            const response = await fetch('/api/wake-isg', { method: 'POST' });
            
            if (response.status === 404) {
                this.showToast('iSG wake function not yet implemented', 'warning');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('iSG wake up initiated!', 'success');
                setTimeout(() => this.refreshStatus(), 2000);
            } else {
                this.showToast('Error waking up iSG: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Wake iSG error:', error);
            this.showToast('Error waking up iSG: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async restartISG() {
        if (!confirm('Are you sure you want to restart iSG?')) return;

        console.log('Restart iSG button clicked');
        try {
            this.showLoading();
            const response = await fetch('/api/restart-isg', { method: 'POST' });
            
            if (response.status === 404) {
                this.showToast('iSG restart function not yet implemented', 'warning');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('iSG restart initiated!', 'success');
                setTimeout(() => this.refreshStatus(), 3000);
            } else {
                this.showToast('Error restarting iSG: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Restart iSG error:', error);
            this.showToast('Error restarting iSG: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async testADBConnection() {
        try {
            this.showLoading();
            
            const response = await fetch('/api/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    host: document.getElementById('adb-host').value,
                    port: parseInt(document.getElementById('adb-port').value)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('ADB connection test successful!', 'success');
            } else {
                this.showToast('ADB connection test failed: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('ADB connection test error: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async testMQTTConnection() {
        try {
            this.showLoading();
            
            const response = await fetch('/api/test-mqtt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    broker: document.getElementById('mqtt-broker').value,
                    port: parseInt(document.getElementById('mqtt-port').value),
                    username: document.getElementById('mqtt-username').value,
                    password: document.getElementById('mqtt-password').value
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('MQTT connection test successful!', 'success');
            } else {
                this.showToast('MQTT connection test failed: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('MQTT connection test error: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    startStatusUpdates() {
        // Update status every 30 seconds
        this.statusInterval = setInterval(() => {
            this.refreshStatus();
        }, 30000);
        
        // Initial status update
        this.refreshStatus();
    }

    showModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }

    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showLoading() {
        document.getElementById('loading-overlay').classList.add('show');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.remove('show');
    }

    showToast(message, type = 'info') {
        console.log('Toast:', type, message);
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.error('toast-container not found');
            // Fallback to console log if no toast container
            return;
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <i class="${icon}"></i>
            <span class="message">${message}</span>
            <span class="close" onclick="this.parentElement.remove()">&times;</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }
}

// Initialize the manager when the page loads
let manager;
document.addEventListener('DOMContentLoaded', () => {
    manager = new AndroidTVBoxManager();
});
