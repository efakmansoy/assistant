// RAG Assistant - Main JavaScript

class RAGAssistant {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupFormValidation();
    }
    
    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            // Smooth scrolling for anchor links
            this.setupSmoothScrolling();
            
            // Auto-hide alerts
            this.setupAutoHideAlerts();
            
            // Loading states for buttons
            this.setupLoadingStates();
            
            // File upload handling
            this.setupFileUploads();
        });
    }
    
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    
    setupAutoHideAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert && alert.parentNode) {
                    alert.style.transition = 'opacity 0.3s ease';
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        if (alert.parentNode) {
                            alert.remove();
                        }
                    }, 300);
                }
            }, 5000);
        });
    }
    
    setupLoadingStates() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>İşleniyor...';
                    
                    // Re-enable after 10 seconds as fallback
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }, 10000);
                }
            });
        });
    }
    
    setupFileUploads() {
        const fileUploads = document.querySelectorAll('.file-upload-area');
        fileUploads.forEach(uploadArea => {
            const input = uploadArea.querySelector('input[type="file"]');
            
            if (input) {
                // Click to upload
                uploadArea.addEventListener('click', () => {
                    input.click();
                });
                
                // Drag and drop
                uploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadArea.classList.add('dragover');
                });
                
                uploadArea.addEventListener('dragleave', () => {
                    uploadArea.classList.remove('dragover');
                });
                
                uploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    uploadArea.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        input.files = files;
                        this.handleFileSelection(input);
                    }
                });
                
                // File selection
                input.addEventListener('change', () => {
                    this.handleFileSelection(input);
                });
            }
        });
    }
    
    handleFileSelection(input) {
        const files = input.files;
        const uploadArea = input.closest('.file-upload-area');
        const fileList = uploadArea.querySelector('.file-list') || this.createFileList(uploadArea);
        
        fileList.innerHTML = '';
        
        Array.from(files).forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item d-flex align-items-center justify-content-between p-2 border rounded mb-2';
            
            const fileInfo = document.createElement('div');
            fileInfo.innerHTML = `
                <i class="fas fa-file-pdf text-danger me-2"></i>
                <strong>${file.name}</strong>
                <small class="text-muted ms-2">(${this.formatFileSize(file.size)})</small>
            `;
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-sm btn-outline-danger';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';
            removeBtn.addEventListener('click', () => {
                fileItem.remove();
                // Clear input if no files left
                if (fileList.children.length === 0) {
                    input.value = '';
                }
            });
            
            fileItem.appendChild(fileInfo);
            fileItem.appendChild(removeBtn);
            fileList.appendChild(fileItem);
        });
    }
    
    createFileList(uploadArea) {
        const fileList = document.createElement('div');
        fileList.className = 'file-list mt-3';
        uploadArea.appendChild(fileList);
        return fileList;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    setupFormValidation() {
        // Bootstrap form validation
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
        
        // Custom validation for password confirmation
        const passwordFields = document.querySelectorAll('input[type="password"]');
        passwordFields.forEach(field => {
            const confirmField = document.querySelector(`input[name="${field.name}_confirm"]`) ||
                               document.querySelector('input[name="confirm_password"]');
            
            if (confirmField && field.name === 'password') {
                const validatePasswords = () => {
                    if (field.value !== confirmField.value) {
                        confirmField.setCustomValidity('Şifreler eşleşmiyor');
                    } else {
                        confirmField.setCustomValidity('');
                    }
                };
                
                field.addEventListener('input', validatePasswords);
                confirmField.addEventListener('input', validatePasswords);
            }
        });
    }
    
    initializeComponents() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
        
        // Initialize progress bars animation
        this.animateProgressBars();
        
        // Initialize counters
        this.animateCounters();
    }
    
    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const target = bar.getAttribute('aria-valuenow');
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.width = target + '%';
            }, 500);
        });
    }
    
    animateCounters() {
        const counters = document.querySelectorAll('.stat-number');
        counters.forEach(counter => {
            const target = parseInt(counter.textContent);
            const duration = 2000;
            const step = target / (duration / 16);
            let current = 0;
            
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current);
            }, 16);
        });
    }
    
    // Utility functions
    showLoader() {
        const loader = document.createElement('div');
        loader.className = 'spinner-overlay';
        loader.innerHTML = `
            <div class="spinner-border spinner-border-lg text-primary" role="status">
                <span class="sr-only">Yükleniyor...</span>
            </div>
        `;
        document.body.appendChild(loader);
        return loader;
    }
    
    hideLoader(loader) {
        if (loader && loader.parentNode) {
            loader.remove();
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // API Helper functions
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            this.showNotification('Bir hata oluştu. Lütfen tekrar deneyin.', 'danger');
            throw error;
        }
    }
    
    // Project management functions
    async createProject(projectData) {
        const loader = this.showLoader();
        try {
            const result = await this.makeRequest('/api/projects', {
                method: 'POST',
                body: JSON.stringify(projectData)
            });
            
            this.showNotification('Proje başarıyla oluşturuldu!', 'success');
            return result;
        } catch (error) {
            this.showNotification('Proje oluşturulurken hata oluştu.', 'danger');
            throw error;
        } finally {
            this.hideLoader(loader);
        }
    }
    
    async loadProjects() {
        try {
            return await this.makeRequest('/api/projects');
        } catch (error) {
            this.showNotification('Projeler yüklenirken hata oluştu.', 'danger');
            return [];
        }
    }
}

// Global instance
window.ragAssistant = new RAGAssistant();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RAGAssistant;
}