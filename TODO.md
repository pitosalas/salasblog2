# TODO: Refactoring Opportunities

## raindrop.py → utils.py Refactoring

### 1. Replace Duplicate Date Parsing
**Current**: Multiple instances of `datetime.fromisoformat(date_str.replace("Z", "+00:00"))` in raindrop.py
**Locations**: Lines 83, 291, 303, 309
**Action**: Use existing `utils._parse_iso_date()` function instead
**Benefit**: Eliminate code duplication, consistent date handling

### 2. Extract Generic JSON Cache Operations
**Current**: JSON cache loading/saving logic in raindrop.py (lines 45-71)
**Move to utils.py**:
```python
def load_json_cache(cache_file: Path, env_var: str = None) -> dict:
    """Load JSON cache with environment variable fallback."""
    
def save_json_cache(cache_file: Path, cache: dict) -> None:
    """Save dictionary to JSON cache file."""
```
**Benefit**: Reusable cache operations for other modules

### 3. Extract Generic API Pagination
**Current**: Pagination logic in `fetch_raindrops()` (lines 101-151)
**Move to utils.py**:
```python
def paginate_api_request(fetch_func, max_items=None, page_size=50) -> list:
    """Generic pagination pattern for any API."""
```
**Benefit**: Reusable pagination for future API integrations

### 4. Extract Directory Reset Utility
**Current**: Directory and cache cleanup in `reset_data()` (lines 153-163)
**Move to utils.py**:
```python
def reset_directory_and_cache(directory: Path, cache_file: Path) -> None:
    """Generic pattern for clearing directories and cache files."""
```
**Benefit**: Reusable reset functionality for other content types

## Additional Code Quality Improvements

### 5. Fix Path Hardcoding Issue
**Current**: Hardcoded `/data/content/` paths in raindrop.py (lines 31-32)
**Action**: Add fallback logic similar to generator.py
**Pattern**: Check `/data/content/` first, fallback to local `content/` for development

### 6. Address Magic Numbers
**Current**: `DEFAULT_PAGE_SIZE = 50`, `DEFAULT_FIRST_SYNC_LIMIT = 100`, `FETCH_MULTIPLIER = 2`
**Action**: Move to configuration or environment variables
**Benefit**: More flexible and configurable

### 7. Break Down Long Functions
**Current**: `fetch_raindrops()` is 51 lines (lines 101-151)
**Action**: Extract helper methods for pagination logic
**Benefit**: Improved readability and testability

### 8. Improve Error Handling
**Current**: Generic `Exception` handling in multiple places
**Action**: Create specific exception types for different error scenarios
**Benefit**: Better error diagnosis and handling

## Implementation Priority
1. **High**: Replace duplicate date parsing (quick win)
2. **High**: Fix path hardcoding (fixes local development)
3. **Medium**: Extract JSON cache operations (improves reusability)
4. **Medium**: Extract API pagination (future-proofing)
5. **Low**: Directory reset utility (nice to have)
6. **Low**: Magic numbers and long functions (code quality)

## Notes
- Follow CLAUDE.md guidelines: brief comments, meaningful parameter names
- All extracted functions should be pure utilities (no side effects)
- Maintain backward compatibility during refactoring
- Add unit tests for extracted utilities