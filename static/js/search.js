/**
 * Site Search Functionality
 * Handles search input, results display, and user interactions
 */

class SiteSearch {
    constructor() {
        this.searchData = [];
        this.searchResults = null;
        this.searchInput = null;
        this.searchTimeout = null;
        this.init();
    }

    async init() {
        this.searchInput = document.getElementById('search-input');
        this.searchResults = document.getElementById('search-results');
        
        if (this.searchInput && this.searchResults) {
            await this.loadSearchData();
            this.setupEventListeners();
        }
    }

    // Load search data from JSON file
    async loadSearchData() {
        try {
            const response = await fetch('/search.json');
            if (response.ok) {
                this.searchData = await response.json();
            }
        } catch (error) {
            console.warn('Search data not available:', error);
        }
    }

    // Set up all search-related event listeners
    setupEventListeners() {
        // Search input handler with debouncing
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                this.hideResults();
                return;
            }
            
            // Debounce search
            this.searchTimeout = setTimeout(() => {
                const results = this.performSearch(query);
                this.displayResults(results);
            }, 300);
        });
        
        // Hide results when input loses focus (with delay for clicks)
        this.searchInput.addEventListener('blur', () => {
            setTimeout(() => this.hideResults(), 200);
        });
        
        // Show results when input gains focus (if there's a query)
        this.searchInput.addEventListener('focus', () => {
            if (this.searchInput.value.trim().length >= 2) {
                const results = this.performSearch(this.searchInput.value.trim());
                this.displayResults(results);
            }
        });
        
        // Handle keyboard navigation
        this.searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.hideResults();
                this.searchInput.blur();
            }
        });

        // Close search results when clicking outside
        document.addEventListener('click', (event) => {
            if (!this.searchInput.contains(event.target) && 
                !this.searchResults.contains(event.target)) {
                this.hideResults();
            }
        });
    }

    // Simple search function with filtering and limiting
    performSearch(query) {
        if (!query || query.length < 2) {
            return [];
        }
        
        const queryLower = query.toLowerCase();
        return this.searchData.filter(item => {
            return item.title.toLowerCase().includes(queryLower) ||
                   item.content.toLowerCase().includes(queryLower) ||
                   item.category.toLowerCase().includes(queryLower);
        }).slice(0, 10); // Limit to 10 results
    }

    // Display search results with highlighting
    displayResults(results) {
        if (!this.searchResults) return;
        
        if (results.length === 0) {
            this.searchResults.innerHTML = '<div class="search-result">No results found</div>';
            this.searchResults.classList.add('active');
            return;
        }
        
        const html = results.map(result => `
            <div class="search-result" onclick="window.location.href='${result.url}'">
                <h4>${this.highlightText(result.title, this.searchInput.value)}</h4>
                <p>${this.highlightText(this.truncateText(result.content, 100), this.searchInput.value)}</p>
            </div>
        `).join('');
        
        this.searchResults.innerHTML = html;
        this.searchResults.classList.add('active');
    }

    // Highlight search terms in text
    highlightText(text, query) {
        if (!query || query.length < 2) return text;
        
        const regex = new RegExp(`(${this.escapeRegExp(query)})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    // Truncate text to specified length
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength).trim() + '...';
    }

    // Escape special characters for regex
    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Hide search results
    hideResults() {
        if (this.searchResults) {
            this.searchResults.classList.remove('active');
        }
    }
}

// Initialize search when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SiteSearch();
});