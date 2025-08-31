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
        const filename = window.location.pathname.split('/').pop();
        fields.filename = filename;
    }
    
    // Create and append input fields
    Object.keys(fields).forEach(key => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = fields[key] || '';
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Close editor function
function closeEditor() {
    if (window.history.length > 1) {
        window.history.back();
    } else {
        window.location.href = '/admin';
    }
}

// Auto-save functionality
let autoSaveTimeout;
function scheduleAutoSave() {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        console.log('Auto-save could be triggered here');
    }, 30000); // 30 seconds
}

// Initialize auto-save listeners
function initializeAutoSave() {
    const contentField = document.getElementById('content');
    const titleField = document.getElementById('title');
    
    if (contentField) {
        contentField.addEventListener('input', scheduleAutoSave);
    }
    if (titleField) {
        titleField.addEventListener('input', scheduleAutoSave);
    }
}

// Initialize date field with current date if empty
function initializeDateField() {
    const dateField = document.getElementById('date');
    if (dateField && !dateField.value) {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        dateField.value = formattedDate;
    }
}

// Initialize all preview functionality
function initializePreview() {
    initializeDateField();
    initializeAutoSave();
}