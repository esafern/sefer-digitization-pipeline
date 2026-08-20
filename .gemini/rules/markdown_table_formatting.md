---
description: Enforce fixed-width column padding and vertically aligned pipes for all markdown tables.
---
# Markdown Table Formatting

1. **Monospace & Reader Compatibility:**
   - Always format markdown tables with fixed-width column padding and vertically aligned pipes (`|`).
   - Never emit collapsed or unpadded tables (e.g. `|a|b|c|`).
   - Proper padding ensures clean, readable display across plain text, monospace terminal output, native macOS markdown editors (such as MarkEdit, MacDown, Typora), and rendered HTML previewers.

2. **Column Alignment Markers:**
   - Use standard GitHub Flavored Markdown alignment indicators in the separator row:
     - Left-aligned text: `:---` or `:-------------------------|`
     - Right-aligned numbers: `---:` or `------------------------:|`
     - Centered content: `:---:` or `:-----------------------:|`
   - Pad the separator hyphens to match the full column width.
