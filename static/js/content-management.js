/**
 * Content Management Functions
 * Handles creation, deletion, preview, and validation of blog content
 */

// Delete functions
function deletePost(filename) {
    if (confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
        // Implementation would be added here
        console.log('Delete post:', filename);
    }
}

function deletePage(filename) {
    if (confirm('Are you sure you want to delete this page? This action cannot be undone.')) {
        // Implementation would be added here
        console.log('Delete page:', filename);
    }
}

function deleteRaindrop(filename) {
    if (confirm('Are you sure you want to delete this raindrop? This action cannot be undone.')) {
        // Implementation would be added here
        console.log('Delete raindrop:', filename);
    }
}

// Form validation utilities
function validatePostForm(formId = 'editForm', statusMessageId = 'statusMessage') {
    const form = document.getElementById(formId);
    const statusMessage = document.getElementById(statusMessageId);
    
    const title = document.getElementById('title').value.trim();
    const date = document.getElementById('date').value;
    const content = document.getElementById('content').value.trim();
    
    if (!title) {
        showError(statusMessage, 'Please enter a post title');
        return false;
    }
    
    if (!date) {
        showError(statusMessage, 'Please select a date');
        return false;
    }
    
    if (!content) {
        showError(statusMessage, 'Please enter some content');
        return false;
    }
    
    return true;
}

// Status message utilities
function showError(statusMessage, text) {
    statusMessage.className = 'alert alert-danger';
    statusMessage.textContent = text;
    statusMessage.style.display = 'block';
}

function showSuccess(statusMessage, text) {
    statusMessage.className = 'alert alert-success';
    statusMessage.textContent = text;
    statusMessage.style.display = 'block';
}

function showLoading(button, loadingText) {
    const originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
    return originalText;
}

function hideLoading(button, originalText) {
    button.textContent = originalText;
    button.disabled = false;
}

// Create new post/page functionality
async function createPost(endpoint, statusMessageId = 'statusMessage') {
    const form = document.getElementById('newPostForm');
    const statusMessage = document.getElementById(statusMessageId);
    
    // Validate form
    if (!validatePostForm('newPostForm', statusMessageId)) {
        return;
    }
    
    const formData = new FormData(form);
    
    // Show loading state
    const createBtn = event.target;
    const originalText = showLoading(createBtn, 'Creating...');
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(statusMessage, `Created successfully! Filename: ${result.filename}`);
            
            // Optional: redirect after creation
            setTimeout(() => {
                window.location.href = result.edit_url || '/admin';
            }, 2000);
        } else {
            throw new Error(result.detail || 'Creation failed');
        }
    } catch (error) {
        showError(statusMessage, 'Error: ' + error.message);
    } finally {
        hideLoading(createBtn, originalText);
    }
}

// Save post functionality
async function savePost(endpoint, statusMessageId = 'statusMessage') {
    const form = document.getElementById('editForm');
    const statusMessage = document.getElementById(statusMessageId);
    
    // Validate form
    if (!validatePostForm('editForm', statusMessageId)) {
        return;
    }
    
    const formData = new FormData(form);
    
    // Show loading state
    const saveBtn = document.getElementById('saveBtn');
    const originalText = showLoading(saveBtn, 'Saving...');
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(statusMessage, 'Post saved successfully!');
        } else {
            throw new Error(result.detail || 'Save failed');
        }
    } catch (error) {
        showError(statusMessage, 'Error: ' + error.message);
    } finally {
        hideLoading(saveBtn, originalText);
    }
}

// Preview functionality
function previewPost(isNew = false) {
    const content = document.getElementById('content').value;
    const title = document.getElementById('title').value;
    const date = document.getElementById('date').value;
    const category = document.getElementById('category').value;
    const type = document.getElementById('type').value;
    
    if (!content.trim()) {
        alert('Please enter some content to preview');
        return;
    }
    
    // Create a form and submit to preview endpoint
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = isNew ? '/admin/preview-new-post' : '/admin/preview-post';
    form.target = '_blank';
    
    // Add form fields
    const fields = {
        title: title,
        content: content,
        date: date,
        category: category,
        type: type
    };
    
    // Add filename for existing posts
    if (!isNew) {
        const filenameInput = document.getElementById('filename');
        if (filenameInput) {
            fields.filename = filenameInput.value;
        }
    }
    
    // Create hidden input fields
    Object.entries(fields).forEach(([key, value]) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value || '';
        form.appendChild(input);
    });
    
    // Submit form
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Auto-save functionality
let autoSaveTimeout;
function initializeAutoSave(endpoint) {
    const contentTextarea = document.getElementById('content');
    const titleInput = document.getElementById('title');
    
    if (contentTextarea || titleInput) {
        [contentTextarea, titleInput].forEach(input => {
            if (input) {
                input.addEventListener('input', () => {
                    clearTimeout(autoSaveTimeout);
                    autoSaveTimeout = setTimeout(() => {
                        autoSave(endpoint);
                    }, 10000); // Auto-save after 10 seconds of inactivity
                });
            }
        });
    }
}

async function autoSave(endpoint) {
    const statusMessage = document.getElementById('autoSaveStatus') || 
                         document.getElementById('statusMessage');
    
    if (!statusMessage) return;
    
    try {
        const form = document.getElementById('editForm');
        if (!form) return;
        
        const formData = new FormData(form);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            statusMessage.className = 'alert alert-info';
            statusMessage.textContent = 'Auto-saved';
            statusMessage.style.display = 'block';
            
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 2000);
        }
    } catch (error) {
        console.warn('Auto-save failed:', error);
    }
}

// Initialize preview functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Set up preview button if it exists
    const previewBtn = document.getElementById('previewBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', () => previewPost());
    }
    
    // Set up auto-save if we're on an edit page
    const editForm = document.getElementById('editForm');
    if (editForm) {
        const endpoint = editForm.action || window.location.pathname;
        initializeAutoSave(endpoint);
    }
});