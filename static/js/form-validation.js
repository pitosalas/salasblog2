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

function showError(statusMessage, text) {
    statusMessage.className = 'alert alert-danger';
    statusMessage.textContent = text;
    statusMessage.style.display = 'block';
}

function showSuccess(statusMessage, text) {
    statusMessage.className = 'alert alert-success';
    statusMessage.textContent = text;
    statusMessage.style.display = 'block';
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 3000);
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

// Save post function
async function savePost(endpoint, statusMessageId = 'statusMessage') {
    const form = document.getElementById('editForm');
    const statusMessage = document.getElementById(statusMessageId);
    
    // Validate form
    if (!validatePostForm('editForm', statusMessageId)) {
        return;
    }
    
    const formData = new FormData(form);
    
    // Show loading state
    const saveBtn = event.target;
    const originalText = showLoading(saveBtn, 'Saving...');
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(statusMessage, result.message || 'Saved successfully!');
        } else {
            throw new Error(result.detail || 'Save failed');
        }
    } catch (error) {
        showError(statusMessage, 'Error: ' + error.message);
    } finally {
        hideLoading(saveBtn, originalText);
    }
}