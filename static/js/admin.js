// Admin-specific functionality
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