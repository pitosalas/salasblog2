/**
 * Shared delete handlers for admin-controls buttons across post/page/raindrop
 * templates (blog_post.html, page.html, pages_list.html, raindrop_post.html).
 * Loaded globally via base.html so every content-type template gets a working
 * delete button from one place instead of four separate copies.
 */
async function deleteContentItem(endpoint, filename, btn, onSuccess) {
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = 'Deleting...';
    try {
        const resp = await fetch(`${endpoint}/${filename}`, { method: 'POST' });
        const result = await resp.json().catch(() => ({}));
        if (resp.ok) {
            onSuccess();
        } else {
            btn.disabled = false;
            btn.textContent = originalText;
            alert('Error: ' + (result.detail || 'Delete failed'));
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = originalText;
        alert('Error: ' + e.message);
    }
}

function deletePost(filename, btn, onSuccess) {
    if (!confirm('Delete this post permanently? This cannot be undone.')) return;
    deleteContentItem('/admin/delete-post', filename, btn, onSuccess || (() => {
        window.location.href = '/blog/';
    }));
}

function deletePage(filename, btn, onSuccess) {
    if (!confirm('Delete this page permanently? This cannot be undone.')) return;
    deleteContentItem('/admin/delete-page', filename, btn, onSuccess || (() => {
        const card = btn.closest('.col');
        if (card) {
            card.remove();
        } else {
            window.location.href = '/pages/';
        }
    }));
}

function deleteRaindrop(filename, btn, onSuccess) {
    if (!confirm('Delete this raindrop permanently? This cannot be undone.')) return;
    deleteContentItem('/admin/delete-raindrop', filename, btn, onSuccess || (() => {
        window.location.href = '/raindrops/';
    }));
}
