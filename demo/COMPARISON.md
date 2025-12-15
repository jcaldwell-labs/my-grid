# Demo Modes Comparison

my-grid has two demo systems: **VHS Recording** and **Headless Generation**. Choose the right one for your needs.

## Quick Comparison

| Feature | VHS Recording | Headless Generation |
|---------|---------------|---------------------|
| **Output** | Video (MP4, GIF) | Text (Markdown, TXT) |
| **Terminal required** | ✅ Yes | ❌ No |
| **Curses required** | ✅ Yes | ❌ No |
| **Generation time** | 75-90 seconds | <1 second |
| **File size** | 5-50 MB | <100 KB |
| **CI/CD friendly** | ⚠️ Limited | ✅ Perfect |
| **Deterministic** | ⚠️ Timing | ✅ Always |
| **Interactive** | ✅ Live demo | ❌ Static |
| **Customization** | Python + VHS tape | Python only |

---

## VHS Recording Mode

### What It Does

Records a live terminal session showing my-grid in action, generating a video file.

### Best For

- 🎥 YouTube videos and video tutorials
- 📱 Social media (Twitter, LinkedIn, Reddit)
- 🌟 GitHub README showcase (embedded video)
- 🎨 Visual presentations and demos
- 🖼️ Marketing and promotional material

### Output

- **Format**: MP4 video, 1920x1080, 30 FPS
- **Duration**: Configurable (typically 75-90 seconds)
- **Size**: 5-50 MB depending on content
- **Location**: `demo/output/*.mp4`

### Quick Start

```bash
# Test 10-second demo
demo/record.sh quick

# Record full 75-second demo
demo/record.sh full

# View output
mpv demo/output/my-grid-productivity-demo.mp4
```

### Pros

✅ **Visual appeal** - Shows real terminal interaction
✅ **Engaging** - Motion and transitions catch attention
✅ **Comprehensive** - Can show complex workflows
✅ **Embeddable** - Works in GitHub README, websites

### Cons

❌ **Slow generation** - 75-90 seconds per recording
❌ **Large files** - 5-50 MB not ideal for documentation
❌ **Terminal required** - Can't run in basic CI/CD
❌ **Platform-specific** - Fonts, colors may vary

### When to Use

Choose VHS when you need:
- Video content for YouTube or social media
- Visual showcase for project README
- Live demonstration of interactions
- Promotional or marketing materials

---

## Headless Generation Mode

### What It Does

Generates tutorial content programmatically without any terminal/curses, producing markdown or text files.

### Best For

- 📖 README files and documentation
- 🤖 CI/CD automated updates
- 📧 Email distribution
- 📝 Man pages and text docs
- 🔄 Git-friendly documentation
- 🌐 Static site generators (Jekyll, Hugo, MkDocs)

### Output

- **Format**: Markdown (.md) or Plain Text (.txt)
- **Duration**: <1 second generation
- **Size**: <100 KB (extremely lightweight)
- **Location**: `demo/output/tutorial.{md,txt}`

### Quick Start

```bash
# Generate both markdown and text
demo/generate-tutorial.sh

# Markdown only
demo/generate-tutorial.sh markdown

# Copy to root as README-TUTORIAL.md
demo/generate-tutorial.sh readme
```

### Pros

✅ **Instant** - Generates in <1 second
✅ **Tiny files** - <100 KB, git-friendly
✅ **No terminal** - Works anywhere, perfect for CI/CD
✅ **Deterministic** - Same output every time
✅ **Searchable** - Text is indexable by search engines
✅ **Multiple formats** - Markdown, text, or custom

### Cons

❌ **Static** - No motion or interaction
❌ **Less engaging** - Plain text vs. video
❌ **Limited showcase** - Can't show smooth animations

### When to Use

Choose Headless when you need:
- Documentation for README, wiki, or docs site
- CI/CD automatic documentation generation
- Text-based distribution (email, man pages)
- Fast iteration on tutorial content
- Git-friendly documentation updates

---

## Side-by-Side Example

### Same Content, Different Formats

**Tutorial Section: "Drawing a Box"**

#### VHS Output (Video)

```
[MP4 Video - 85 seconds total]
- Shows cursor moving to position
- Types: :rect 20 5
- Presses Enter
- Box appears with smooth rendering
- File: my-grid-productivity-demo.mp4 (15 MB)
```

#### Headless Output (Markdown)

```markdown
## 3. Drawing Your First Box

**Commands:**
```
Press: :
Type: rect 20 5
Press: Enter
```

**Canvas Output:**
```
     ┌──────────────────┐
     │                  │
     │  Hello, World!   │
     │                  │
     └──────────────────┘
```

File: tutorial.md (87 KB)
```

---

## Usage Decision Tree

```
Need demo content?
    │
    ├─ For video showcase?
    │   └─ Use VHS Recording
    │      - YouTube, social media, README embed
    │      - Run: demo/record.sh full
    │
    └─ For documentation?
        └─ Use Headless Generation
           - README, wiki, docs site, CI/CD
           - Run: demo/generate-tutorial.sh
```

---

## Combining Both Modes

You can use both! Many projects benefit from having both:

### Typical Setup

```
my-grid/
├── demo/
│   ├── output/
│   │   ├── my-grid-productivity-demo.mp4    # VHS video for README
│   │   ├── tutorial.md                       # Headless markdown
│   │   └── tutorial.txt                      # Headless text
│   └── ...
└── README.md                                  # Links to both
```

### In Your README

```markdown
# my-grid

Terminal-based ASCII canvas editor.

## Quick Demo

![Demo Video](demo/output/my-grid-productivity-demo.mp4)

## Full Tutorial

See [Tutorial](demo/output/tutorial.md) for complete guide.
```

### In CI/CD

```yaml
# .github/workflows/docs.yml
- name: Update Tutorial
  run: demo/generate-tutorial.sh readme

# Record video manually when needed
# (Too slow for automated CI/CD)
```

---

## Performance Comparison

### Generation Time

```bash
$ time demo/generate-tutorial.sh
real    0m0.234s    # Headless: < 1 second

$ time demo/record.sh full
real    1m25.000s   # VHS: 85 seconds
```

### File Size

```
demo/output/tutorial.md              87 KB   (Headless Markdown)
demo/output/tutorial.txt             73 KB   (Headless Text)
demo/output/my-grid-productivity-demo.mp4    15 MB   (VHS Video)
```

### CPU Usage

- **Headless**: Minimal (text processing only)
- **VHS**: Moderate (terminal rendering + video encoding)

---

## Technology Stack

### VHS Recording

- **VHS** (`github.com/charmbracelet/vhs`)
- **ttyd** (terminal emulator)
- **ffmpeg** (video encoding)
- **Python curses** (terminal rendering)

### Headless Generation

- **Python** (core logic only)
- **my-grid components** (Canvas, Viewport)
- **No external dependencies**

---

## Migration Guide

### From VHS to Headless

If you're currently using VHS but want text documentation:

```bash
# Before (VHS)
demo/record.sh full
# Output: demo/output/my-grid-productivity-demo.mp4

# After (Headless)
demo/generate-tutorial.sh
# Output: demo/output/tutorial.md
```

Content will be similar, but static text format instead of video.

### From Headless to VHS

If you want to add video to existing text docs:

```bash
# Current (Headless)
demo/generate-tutorial.sh readme

# Add (VHS)
demo/record.sh full

# Now you have both:
# - README-TUTORIAL.md (text)
# - demo/output/my-grid-productivity-demo.mp4 (video)
```

---

## Easter Eggs

Both modes include Hitchhiker's Guide references!

### In Headless Mode

Look for:
- "Don't Panic!" opening
- Towel references
- "42" - The Answer
- Vogon references
- Try `:goto 42 42` in tutorial

### In VHS Mode

Demo includes:
- Title card references
- Status messages with quotes
- Hidden features at specific timestamps

---

## Recommendations

### For Open Source Projects

**Recommended Setup:**

1. **VHS video** in main README (visual appeal)
2. **Headless tutorial** linked from README (searchable docs)
3. **CI/CD** auto-updates headless tutorial

### For Internal Documentation

**Recommended Setup:**

1. **Headless only** (fast, git-friendly, searchable)
2. Record VHS videos occasionally for training

### For Product Marketing

**Recommended Setup:**

1. **VHS videos** for social media and landing pages
2. **Headless tutorials** for documentation sites

---

## Conclusion

Both modes serve different purposes:

- **VHS** = Visual showcase and engagement
- **Headless** = Documentation and automation

Use both for maximum impact!

---

**Learn More:**

- [VHS Recording Guide](PRODUCTION-GUIDE.md)
- [Headless Generation Guide](HEADLESS-DEMO.md)
- [Demo Overview](README.md)
