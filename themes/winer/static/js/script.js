// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
        
        // Close menu when clicking on a link
        const navLinks = document.querySelectorAll('.nav-menu a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });
    }
});

// Search functionality
let searchData = [];
let searchResults = null;
let searchInput = null;

// Load search data
async function loadSearchData() {
    try {
        const response = await fetch('/search.json');
        if (response.ok) {
            searchData = await response.json();
        }
    } catch (error) {
        console.warn('Search data not available:', error);
    }
}

// Simple search function
function performSearch(query) {
    if (!query || query.length < 2) {
        return [];
    }
    
    const queryLower = query.toLowerCase();
    return searchData.filter(item => {
        return item.title.toLowerCase().includes(queryLower) ||
               item.content.toLowerCase().includes(queryLower) ||
               item.category.toLowerCase().includes(queryLower);
    }).slice(0, 10); // Limit to 10 results
}

// Display search results
function displaySearchResults(results) {
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-result">No results found</div>';
        searchResults.classList.add('active');
        return;
    }
    
    const html = results.map(result => `
        <div class="search-result" onclick="window.location.href='${result.url}'">
            <h4>${highlightText(result.title, searchInput.value)}</h4>
            <p>${highlightText(truncateText(result.content, 100), searchInput.value)}</p>
        </div>
    `).join('');
    
    searchResults.innerHTML = html;
    searchResults.classList.add('active');
}

// Highlight search terms in text
function highlightText(text, query) {
    if (!query || query.length < 2) return text;
    
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<strong>$1</strong>');
}

// Truncate text to specified length
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength).trim() + '...';
}

// Escape special characters for regex
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Hide search results
function hideSearchResults() {
    if (searchResults) {
        searchResults.classList.remove('active');
    }
}

// Initialize search
document.addEventListener('DOMContentLoaded', function() {
    searchInput = document.getElementById('search-input');
    searchResults = document.getElementById('search-results');
    
    if (searchInput && searchResults) {
        // Load search data
        loadSearchData();
        
        // Search input handler
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                hideSearchResults();
                return;
            }
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                const results = performSearch(query);
                displaySearchResults(results);
            }, 300);
        });
        
        // Hide results when input loses focus (with delay for clicks)
        searchInput.addEventListener('blur', function() {
            setTimeout(hideSearchResults, 200);
        });
        
        // Show results when input gains focus (if there's a query)
        searchInput.addEventListener('focus', function() {
            if (this.value.trim().length >= 2) {
                const results = performSearch(this.value.trim());
                displaySearchResults(results);
            }
        });
        
        // Handle keyboard navigation
        searchInput.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                hideSearchResults();
                this.blur();
            }
        });
    }
});

// Close search results when clicking outside
document.addEventListener('click', function(event) {
    if (searchInput && searchResults && 
        !searchInput.contains(event.target) && 
        !searchResults.contains(event.target)) {
        hideSearchResults();
    }
});