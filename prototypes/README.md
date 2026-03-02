# Blog Layout Prototypes

This directory contains prototype blog layout variations to test different visual approaches for the blog listing page.

## Prototypes

### 1. Compact Layout (`blog_prototype_1_compact.html`)
- **Ultra-dense listing** with minimal spacing
- Very small fonts (10-13px)
- Inline date and category badges
- Tightest vertical spacing for maximum posts per view

### 2. Grid Layout (`blog_prototype_2_grid.html`)
- **Card-based grid system** with responsive columns
- Posts displayed in cards with hover effects
- Good for visual scanning and touch interfaces
- Automatically adapts columns based on screen size

### 3. Timeline Layout (`blog_prototype_3_timeline.html`)
- **Chronological timeline** with year markers
- Visual timeline with connecting line and dots
- Posts grouped by year with date stamps
- Good for showing progression over time

### 4. Minimal Layout (`blog_prototype_4_minimal.html`)
- **Extremely clean** title + date only
- No excerpts, maximum information density
- Hacker News / Reddit-style simplicity
- Perfect for quick scanning of many posts

### 5. Magazine Layout (`blog_prototype_5_magazine.html`)
- **Featured post** at top with full excerpt
- Secondary posts in smaller grid below
- Magazine-style hierarchy and visual interest
- Good for highlighting latest or important content

## Testing

To test these prototypes:

1. Copy any prototype file to replace `themes/winer/templates/blog_list.html`
2. Run `uv run salasblog2 generate` to rebuild
3. View at `http://localhost:8000/blog/`

## Styling Notes

- All prototypes include embedded CSS for easy testing
- Font sizes range from 9px (minimal) to 18px (magazine featured)
- Responsive breakpoints included for mobile compatibility
- Each maintains the existing pagination structure

## Current Settings

These prototypes work with the current excerpt settings:
- `EXCERPT_LENGTH=80` 
- `EXCERPT_SMART_THRESHOLD=30`

Some layouts (minimal) don't show excerpts at all for maximum density.