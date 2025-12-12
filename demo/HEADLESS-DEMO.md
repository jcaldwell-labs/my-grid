# Headless Demo System

Generate my-grid tutorial content without requiring a terminal or curses interface.

## What is Headless Mode?

Unlike VHS recording which captures a live terminal session, **headless mode** generates tutorial content programmatically:

- ✅ **No terminal required** - Runs in CI/CD pipelines
- ✅ **No curses dependency** - Works in any environment
- ✅ **Deterministic output** - Same content every time
- ✅ **Fast generation** - Completes in <1 second
- ✅ **Multiple formats** - Markdown, plain text, or custom

## Quick Start

### Generate Tutorial

```bash
# Generate both markdown and text formats
demo/generate-tutorial.sh

# Markdown only
demo/generate-tutorial.sh markdown

# Plain text only
demo/generate-tutorial.sh text

# Copy to root as README-TUTORIAL.md
demo/generate-tutorial.sh readme
```

### Direct Python Usage

```bash
# Markdown output
python3 src/headless_demo.py markdown tutorial.md

# Text output
python3 src/headless_demo.py text tutorial.txt

# Default output (my-grid-tutorial.md in current directory)
python3 src/headless_demo.py markdown
```

## Output Formats

### Markdown (`tutorial.md`)

```markdown
# my-grid Tutorial

*An ASCII Canvas Editor for the Aspiring Hitchhiker*

## 1. Getting Started - Don't Panic!

Welcome to my-grid...

**Commands:**
\`\`\`
python mygrid.py
\`\`\`

**Canvas Output:**
\`\`\`
┌──────────┐
│  Hello!  │
└──────────┘
\`\`\`
```

**Best for:**
- GitHub README
- Documentation websites
- Wiki pages
- Blog posts

### Plain Text (`tutorial.txt`)

```
===============================================================================
MY-GRID TUTORIAL
An ASCII Canvas Editor for the Aspiring Hitchhiker
===============================================================================

1. GETTING STARTED - DON'T PANIC!

Welcome to my-grid...

Commands:

    python mygrid.py

Canvas Output:

    ┌──────────┐
    │  Hello!  │
    └──────────┘
```

**Best for:**
- Email distribution
- Man pages
- Terminal viewing
- Print documentation

## Tutorial Content

The generated tutorial covers:

### 1. Getting Started
- Installation and startup
- Opening files
- First steps

### 2. The Five Modes
- NAV - Navigation mode
- EDIT - Edit mode
- PAN - Pan mode
- COMMAND - Command mode
- MARK - Bookmark mode

### 3. Drawing Your First Box
- Using `:rect` command
- Labeled boxes
- Live examples

### 4. System Architecture Diagram
- Complete real-world example
- Three-tier architecture
- Connections and labels

### 5. Bookmarks
- Setting marks
- Jumping to marks
- Managing bookmarks

### 6. Grid Overlay
- Major/minor grids
- Origin markers
- Custom intervals

### 7. Fast Navigation
- Normal vs. fast movement
- Goto command
- Pan mode

### 8. Saving and Loading
- File formats
- Git integration
- Auto-saving

### 9. Export and Import
- Text export
- Including in documentation
- Import workflow

### 10. Advanced Tips
- Y-axis direction
- Custom origin
- The ultimate answer (42!)

### 11. Getting Help
- F1 help screen
- Command-line help
- Version info

## Easter Eggs

The tutorial includes Hitchhiker's Guide to the Galaxy references:

1. **"Don't Panic!"** - Opening message
2. **Towel references** - "Always know where your towel is"
3. **42** - "The Answer to Everything"
4. **Vogon references** - "Less destructive than Vogon constructor fleet"
5. **Heart of Gold** - "Improbability Drive" navigation
6. **Restaurant at the End of the Universe** - Location matters
7. **Infinite space quote** - About the infinite canvas
8. **Ludicrous speed** - Fast navigation reference
9. **"So long and thanks for all the fish"** - Closing message
10. **Hidden :goto 42 42** - Try it in my-grid!

## API Reference

### HeadlessDemo Class

```python
from headless_demo import HeadlessDemo

# Create demo instance
demo = HeadlessDemo()

# Draw components
demo.draw_box(10, 5, 20, 5, "Frontend")
demo.draw_arrow(30, 7, 50, 7)

# Export to text
output = demo.export_to_text()
print(output)

# Export specific bounds
output = demo.export_to_text(bounds=(0, 0, 80, 20))

# Clear canvas
demo.clear()
```

### TutorialGenerator Class

```python
from headless_demo import TutorialGenerator

# Create generator
generator = TutorialGenerator()

# Generate tutorial content
generator.generate_basics_tutorial()

# Output as markdown
markdown = generator.generate_markdown()
print(markdown)

# Output as plain text
text = generator.generate_plain_text()
print(text)
```

### Convenience Function

```python
from headless_demo import generate_tutorial

# Generate and save
generate_tutorial('markdown', 'tutorial.md')
generate_tutorial('text', 'tutorial.txt')

# Print to stdout (no file)
generate_tutorial('markdown')  # Uses default name
```

## Customization

### Add New Tutorial Sections

Edit `src/headless_demo.py`:

```python
class TutorialGenerator:
    def generate_basics_tutorial(self):
        # ... existing sections ...

        # Add custom section
        self.demo.clear()
        # ... draw custom example ...

        self.add_section(
            "Custom Feature",
            "Description of your feature...",
            example_code="""
            :custom-command arg1 arg2
            """,
            canvas_output=self.demo.export_to_text(),
            notes="Helpful tip about this feature"
        )
```

### Change Easter Eggs

Search for Hitchhiker's Guide references in `src/headless_demo.py`:

```python
# Modify docstrings
"""DON'T PANIC - this is completely automated."""

# Modify section titles
"Getting Started - Don't Panic!"

# Modify notes
notes="ESC is your towel - always brings you back to safety"
```

### Custom Output Format

Extend `TutorialGenerator`:

```python
class TutorialGenerator:
    def generate_html(self) -> str:
        """Generate HTML tutorial document."""
        output = ['<html><body>']

        for section in self.sections:
            output.append(f'<h2>{section["title"]}</h2>')
            output.append(f'<p>{section["description"]}</p>')

            if section['example_code']:
                output.append(f'<pre><code>{section["example_code"]}</code></pre>')

            # ... etc ...

        output.append('</body></html>')
        return '\n'.join(output)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Generate Documentation

on:
  push:
    branches: [ main ]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Generate Tutorial
        run: |
          pip install -r requirements.txt
          demo/generate-tutorial.sh readme

      - name: Commit Tutorial
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add README-TUTORIAL.md
          git commit -m "Update tutorial documentation" || true
          git push
```

### GitLab CI Example

```yaml
generate_docs:
  stage: docs
  script:
    - pip install -r requirements.txt
    - demo/generate-tutorial.sh markdown
    - cp demo/output/tutorial.md public/
  artifacts:
    paths:
      - public/
```

## Comparison: VHS vs Headless

| Feature | VHS Recording | Headless Generation |
|---------|---------------|---------------------|
| Terminal required | ✅ Yes | ❌ No |
| Curses dependency | ✅ Yes | ❌ No |
| CI/CD friendly | ⚠️ Limited | ✅ Perfect |
| Output format | Video (MP4, GIF) | Text (MD, TXT) |
| Generation time | ~90 seconds | <1 second |
| File size | 5-50 MB | <100 KB |
| Deterministic | ⚠️ Timing-dependent | ✅ Always same |
| Best for | Showcase videos | Documentation |

### When to Use Each

**Use VHS Recording when:**
- Creating demo videos for YouTube, README, social media
- Showing real-time interaction
- Demonstrating smooth animations
- Visual appeal is priority

**Use Headless Generation when:**
- Creating text documentation
- Running in CI/CD pipelines
- Updating README automatically
- Distributing via email/text
- Needing fast, deterministic output

## Use Cases

### 1. Automated README Updates

```bash
# In CI/CD pipeline
demo/generate-tutorial.sh readme
git add README-TUTORIAL.md
git commit -m "Update tutorial"
```

### 2. Static Site Documentation

```bash
# Generate for Jekyll/Hugo/MkDocs
demo/generate-tutorial.sh markdown
cp demo/output/tutorial.md docs/tutorial.md
```

### 3. Email Distribution

```bash
# Generate plain text version
demo/generate-tutorial.sh text

# Send via email
mail -s "my-grid Tutorial" team@example.com < demo/output/tutorial.txt
```

### 4. Man Page Generation

```bash
# Generate text, convert to man page
demo/generate-tutorial.sh text
# Use pandoc or similar to convert to man format
pandoc demo/output/tutorial.txt -t man -o my-grid.1
```

### 5. PDF Generation

```bash
# Markdown to PDF
demo/generate-tutorial.sh markdown
pandoc demo/output/tutorial.md -o tutorial.pdf
```

## Performance

Headless generation is extremely fast:

```
$ time demo/generate-tutorial.sh both

real    0m0.234s
user    0m0.189s
sys     0m0.042s
```

Compare to VHS recording (~75-90 seconds for similar content).

## Troubleshooting

### ImportError: No module named 'canvas'

Make sure you're running from the project root:

```bash
cd ~/projects/active/my-grid
python3 src/headless_demo.py markdown
```

### Empty Canvas Output

Check that the demo is actually drawing content:

```python
demo = HeadlessDemo()
demo.draw_box(10, 5, 20, 5, "Test")
output = demo.export_to_text()
print(repr(output))  # Should not be empty
```

### Formatting Issues

If output looks wrong, check bounds:

```python
# Use explicit bounds
output = demo.export_to_text(bounds=(0, 0, 100, 30))
```

## Credits

Headless demo system inspired by the jcaldwell-labs-media skill's approach to automation, but optimized for text-based output instead of video recording.

**Easter eggs** courtesy of Douglas Adams and The Hitchhiker's Guide to the Galaxy.

---

**Status**: ✅ Production Ready

**Last Updated**: 2025-12-12

**Dependencies**: None (uses only my-grid core components)

**Python Version**: 3.12+
