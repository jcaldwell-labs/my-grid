# jcaldwell-labs Organization Guidelines

**Version:** 1.0
**Last Updated:** 2025-12-20
**Purpose:** Standardized guidelines for polishing and organizing projects across the jcaldwell-labs organization

---

## 📋 Table of Contents

1. [Repository Structure](#repository-structure)
2. [README Best Practices](#readme-best-practices)
3. [Documentation Organization](#documentation-organization)
4. [Discoverability Features](#discoverability-features)
5. [Content Strategy](#content-strategy)
6. [GitHub Configuration](#github-configuration)
7. [Launch Checklist](#launch-checklist)
8. [Project Audit Template](#project-audit-template)

---

## 🏗️ Repository Structure

### Root Directory (Keep Minimal)

**Essential Files Only:**
```
/
├── README.md           ← Main entry point (see README guidelines)
├── LICENSE             ← MIT or appropriate license
├── .gitignore          ← Language-specific ignores
├── requirements.txt    ← For Python projects
├── package.json        ← For Node.js projects
├── Cargo.toml          ← For Rust projects
└── llms.txt            ← AI discoverability (see below)
```

**Optional Root Files:**
- `CLAUDE.md` - For projects with complex APIs/architecture
- `CONTRIBUTING.md` - For projects actively seeking contributors
- `CHANGELOG.md` - For versioned releases

**❌ Do NOT keep in root:**
- Planning documents (→ `.github/planning/`)
- Test plans (→ `.github/planning/`)
- Multiple README files (→ `docs/`)
- Roadmaps/backlogs (→ `.github/planning/`)
- Temporary notes (→ `.github/planning/` or delete)

### Documentation Structure

```
docs/
├── README.md              ← Documentation hub/index
├── guides/                ← User guides
│   ├── getting-started.md
│   ├── [feature]-guide.md
│   └── reference.md
├── tutorials/             ← Step-by-step tutorials
│   ├── [tutorial-1].md
│   └── [tutorial-2].md
├── examples/              ← Example projects/use cases
│   ├── [example-1].md
│   └── [example-2].md
└── blog/                  ← Blog posts, articles
    └── [article].md
```

### Internal Planning (Hidden)

```
.github/
├── planning/              ← Internal docs (not visible on main page)
│   ├── ROADMAP.md
│   ├── backlog.md
│   ├── test-plans.md
│   └── sprint-notes.md
├── ISSUE_TEMPLATE/        ← Issue templates
│   ├── bug_report.md
│   └── feature_request.md
└── workflows/             ← GitHub Actions
    └── ci.yml
```

---

## 📄 README Best Practices

### Template Structure

Every README should follow this structure:

```markdown
# Project Name

[Badges: License, Language Version, PRs Welcome, etc.]

**One-line description.** Expanded description with key differentiator.

> *Optional inspirational quote or tagline*

---

## Why [Project Name]?

[Problem statement - what pain does it solve?]

[Solution - how does this project solve it?]

**Perfect for:**
- Use case 1
- Use case 2
- Use case 3

---

## 🎬 Demo

[Screenshot, GIF, or terminal recording]

**Try it yourself:**
```bash
[Quick installation and first command]
```

---

## ⚡ Quick Start

### Installation
[Step-by-step installation]

### First Steps
[Basic usage example]

---

## 🎯 Core Features

[Feature 1 with description]
[Feature 2 with description]
[Feature 3 with description]

---

## 🔧 Use Cases

[Real-world examples with code]

---

## 🆚 Comparison

[Table comparing to alternatives, if applicable]

---

## 📚 Documentation

- [Documentation Hub](docs/README.md)
- [Getting Started](docs/guides/getting-started.md)
- [Reference](docs/guides/reference.md)

---

## 🤝 Contributing

[Contribution guidelines or link to CONTRIBUTING.md]

---

## 🗺️ Roadmap

[Future plans - checkbox list preferred]

---

## 📄 License

[License type] - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

[Credits, inspirations, dependencies]

---

**Star ⭐ this repository if you find it useful!**

Made with ❤️ by [author/organization]
```

### README Checklist

Every README must have:

- [ ] **Badges** - License, language version, build status
- [ ] **One-line hook** - Immediate value proposition
- [ ] **Why section** - Problem/solution explanation
- [ ] **Demo/screenshot** - Visual proof it works
- [ ] **Quick start** - Installation in < 5 minutes
- [ ] **Use cases** - Real-world examples
- [ ] **Documentation links** - Clear navigation
- [ ] **Contributing info** - How to help
- [ ] **Call to action** - "Star if useful"

**Quality Bar:**
- Can a stranger understand what this does in 30 seconds?
- Is there visual proof (screenshot/GIF)?
- Can they try it in < 5 minutes?

---

## 📚 Documentation Organization

### docs/README.md (Navigation Hub)

Every `docs/README.md` should include:

```markdown
# [Project Name] Documentation

Welcome to [project] documentation!

## 📚 Documentation Structure

### Getting Started
- [Main README](../README.md)
- [Getting Started Guide](guides/getting-started.md)

### User Guides
- [Guide 1](guides/guide-1.md)
- [Guide 2](guides/guide-2.md)

### Tutorials
- [Tutorial 1](tutorials/tutorial-1.md)

### Examples
- [Example 1](examples/example-1.md)

## 🗺️ Navigation Guide

### New to [Project]?
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Building Something Specific?
- **Use case 1** → [Link]
- **Use case 2** → [Link]

## 🤝 Contributing Documentation
[How to contribute docs]

**[← Back to Main README](../README.md)**
```

### Documentation Guidelines

**User-Facing Docs (docs/):**
- Clear, beginner-friendly language
- Code examples for every concept
- Step-by-step tutorials
- Real-world use cases

**Internal Planning (.github/planning/):**
- Roadmaps
- Sprint planning
- Issue backlogs
- Test plans
- Architecture decisions (if internal)

**Rule of thumb:**
- If a user would read it → `docs/`
- If only maintainers need it → `.github/planning/`

---

## 🔍 Discoverability Features

### 1. GitHub Topics

**Every project must have 5-10 relevant topics:**

Add via: `Settings → About → Topics`

**Guidelines:**
- Primary language (e.g., `python`, `rust`, `javascript`)
- Primary category (e.g., `terminal`, `web-framework`, `cli-tool`)
- Key features (e.g., `ascii-art`, `monitoring`, `spatial`)
- Related tools (e.g., `vim`, `tmux`, `docker`)
- Use case (e.g., `devops`, `system-admin`)

**Example (my-grid):**
```
python, terminal-editor, vim-style, ascii-art, devops-tools,
curses, spatial-interface, monitoring, tmux-alternative
```

### 2. Repository Description

**Format:** `[What] - [Key Feature/Benefit]`

**Examples:**
- ✅ "Spatial canvas editor for terminals with embedded live zones"
- ✅ "Fast static site generator with zero configuration"
- ❌ "A tool" (too vague)
- ❌ "My project for doing stuff" (unprofessional)

**Length:** 70-120 characters (shows fully in search results)

### 3. llms.txt (AI Discoverability)

**Every project should have `llms.txt` in root:**

```
# Project Name

> One-line description

## What is [Project]?

[2-3 sentence explanation]

## Key Capabilities

- Feature 1
- Feature 2
- Feature 3

## Quick Start

```bash
[Installation command]
[First usage command]
```

## Common Commands

```
[Command 1 with description]
[Command 2 with description]
```

## Use Cases

1. **Use case 1**: [Description]
2. **Use case 2**: [Description]

## Architecture

[Brief architecture overview]

## Repository

[GitHub URL]

## License

[License type]
```

**Why?** AI assistants and search tools increasingly use `llms.txt` for discovery.

### 4. Social Preview Image

**Create a social preview image:**
- Size: 1200×630 px
- Format: PNG or JPG
- Content: Project name + tagline + visual element
- Upload: `Settings → Social preview → Upload an image`

**Tools:**
- Canva (free templates)
- Figma
- Carbon.sh (for code screenshots)

### 5. README Badges

**Recommended badges:**

```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)
```

**Optional badges:**
- Build status (CI/CD)
- Code coverage
- Dependencies status
- Release version
- Download count

**Service:** [shields.io](https://shields.io)

---

## 📝 Content Strategy

### Blog Posts

**Every project should have at least one blog post:**

Location: `docs/blog/[topic].md`

**Blog post checklist:**
- [ ] Explains the "why" (problem statement)
- [ ] Shows real-world use cases
- [ ] Includes code examples
- [ ] Has comparison to alternatives
- [ ] Provides next steps

**Publishing platforms:**
1. Dev.to (primary - developer audience)
2. Medium (cross-post with canonical URL)
3. Personal blog
4. Submit to Hacker News

### Demo Content

**Every project needs visual proof:**

- **Screenshots** - For GUI apps, web projects
- **GIFs** - For terminal apps, interactions
- **Terminal recordings** - Use asciinema for CLI tools
- **Video** - For complex workflows (YouTube)

**Tools:**
- `asciinema` - Terminal recordings
- `terminalizer` - Terminal GIF creation
- `peek` - Screen recording to GIF (Linux)
- `licecap` - GIF recording (Mac/Windows)

### Examples Directory

**Create 2-3 real-world examples:**

Location: `docs/examples/`

**Example types:**
- **Beginner** - Simple, end-to-end example
- **Intermediate** - Real-world use case
- **Advanced** - Complex integration

**Each example should have:**
- Problem statement
- Step-by-step solution
- Full code
- Expected output
- Variations/extensions

---

## ⚙️ GitHub Configuration

### Repository Settings

**About Section:**
- ✅ Description (70-120 chars)
- ✅ Website (if applicable)
- ✅ Topics (5-10)
- ✅ Social preview image

**Features:**
- ✅ Enable Issues
- ✅ Enable Discussions (for community projects)
- ✅ Disable Wiki (unless actively used)
- ✅ Disable Projects (unless actively used)

**Default Branch:**
- ✅ `main` or `master` (be consistent across org)

### Issue Templates

**Create at minimum:**

`.github/ISSUE_TEMPLATE/bug_report.md`
```markdown
---
name: Bug Report
about: Report a bug or issue
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. ...
2. ...

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g. Ubuntu 22.04]
- Version: [e.g. 1.0.0]

**Additional context**
Any other relevant information.
```

`.github/ISSUE_TEMPLATE/feature_request.md`
```markdown
---
name: Feature Request
about: Suggest a new feature
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Problem**
What problem does this solve?

**Proposed Solution**
How should this work?

**Alternatives**
Other approaches you've considered.

**Additional context**
Any other relevant information.
```

### Pull Request Template

`.github/PULL_REQUEST_TEMPLATE.md`
```markdown
## Description

[Describe what this PR does]

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Added tests
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Linked related issues
```

---

## 🚀 Launch Checklist

Use this checklist when preparing a project for public visibility:

### Pre-Launch

- [ ] **README** - Complete with all sections
- [ ] **Documentation** - At least getting-started guide
- [ ] **Demo** - Screenshot, GIF, or recording
- [ ] **License** - Added and badge in README
- [ ] **llms.txt** - Created for AI discovery
- [ ] **docs/README.md** - Navigation hub created
- [ ] **Root cleanup** - Only essential files in root
- [ ] **Planning docs** - Moved to `.github/planning/`

### GitHub Configuration

- [ ] **Description** - Clear, concise (70-120 chars)
- [ ] **Topics** - 5-10 relevant tags added
- [ ] **Social preview** - Image uploaded (1200×630)
- [ ] **Issue templates** - Bug report + feature request
- [ ] **Discussions** - Enabled if community project
- [ ] **Branch protection** - Set up for main branch

### Content

- [ ] **Blog post** - Written in `docs/blog/`
- [ ] **Use cases** - 2-3 real examples documented
- [ ] **Comparison** - To alternatives (if applicable)
- [ ] **Roadmap** - Future plans outlined

### Discoverability

- [ ] **GitHub Explore** - Topics set for discoverability
- [ ] **Google indexing** - README has good keywords
- [ ] **AI discovery** - llms.txt created
- [ ] **Social proof** - Badges in README

### Launch Activities

- [ ] **Dev.to post** - Published blog post
- [ ] **Hacker News** - "Show HN" submission
- [ ] **Reddit** - Posted to relevant subreddits
- [ ] **Twitter/X** - Announcement with demo
- [ ] **Discussions** - Seeded with welcome post

---

## 🔍 Project Audit Template

Use this template when auditing existing projects:

### Repository: `[project-name]`

**Audit Date:** YYYY-MM-DD
**Auditor:** [name]

---

#### 1. README Quality

| Criterion | Status | Notes |
|-----------|--------|-------|
| Has badges | ☐ Yes ☐ No | |
| Clear description | ☐ Yes ☐ No | |
| Demo/screenshot | ☐ Yes ☐ No | |
| Quick start < 5 min | ☐ Yes ☐ No | |
| Use cases shown | ☐ Yes ☐ No | |
| Documentation links | ☐ Yes ☐ No | |

**README Score:** __/6

**Recommended actions:**
- [ ] Add missing badges
- [ ] Create demo GIF
- [ ] Add use cases
- [ ] Other: ___________

---

#### 2. Documentation Organization

| Item | Status | Location |
|------|--------|----------|
| docs/README.md exists | ☐ Yes ☐ No | |
| Getting started guide | ☐ Yes ☐ No | |
| User guides organized | ☐ Yes ☐ No | |
| Examples directory | ☐ Yes ☐ No | |

**Root directory clutter:**
- Files that should move: ___________
- Target location: ___________

**Recommended actions:**
- [ ] Create docs/ structure
- [ ] Move planning docs to .github/planning/
- [ ] Create docs/README.md hub
- [ ] Other: ___________

---

#### 3. Discoverability

| Feature | Status | Quality |
|---------|--------|---------|
| GitHub topics | ☐ Yes ☐ No | __/10 |
| Repository description | ☐ Yes ☐ No | Good/Fair/Poor |
| Social preview image | ☐ Yes ☐ No | - |
| llms.txt exists | ☐ Yes ☐ No | - |
| Blog post | ☐ Yes ☐ No | - |

**Recommended actions:**
- [ ] Add GitHub topics (suggest: _________)
- [ ] Improve description to: ___________
- [ ] Create llms.txt
- [ ] Create social preview
- [ ] Write blog post
- [ ] Other: ___________

---

#### 4. GitHub Configuration

| Setting | Configured | Notes |
|---------|------------|-------|
| Issue templates | ☐ Yes ☐ No | |
| PR template | ☐ Yes ☐ No | |
| Discussions enabled | ☐ Yes ☐ No | |
| Branch protection | ☐ Yes ☐ No | |

**Recommended actions:**
- [ ] Add issue templates
- [ ] Add PR template
- [ ] Enable discussions
- [ ] Other: ___________

---

#### 5. Overall Assessment

**Maturity Level:**
- ☐ **Level 1 (Basic)** - Has README, code works
- ☐ **Level 2 (Functional)** - Has docs, examples
- ☐ **Level 3 (Polished)** - Professional README, organized docs
- ☐ **Level 4 (Launch-Ready)** - Blog post, demos, full discoverability

**Priority for polish:** ☐ High ☐ Medium ☐ Low

**Estimated effort:** _____ hours

**Key improvements needed:**
1. ___________
2. ___________
3. ___________

---

## 📊 Organization-Wide Standards

### Consistency Across Projects

**Standardize these elements:**

1. **License** - Use MIT unless specific reason
2. **Branch naming** - `main` (not master)
3. **Issue labels** - bug, enhancement, documentation, question
4. **Badge style** - shields.io with consistent colors
5. **Documentation structure** - Follow docs/ template
6. **Contributing guidelines** - Standardized CONTRIBUTING.md

### Quality Metrics

Track these for each project:

| Metric | Target |
|--------|--------|
| README completeness | 100% (all sections) |
| Documentation coverage | ≥ 3 guides |
| Demo/visual proof | ≥ 1 (screenshot/GIF) |
| GitHub topics | ≥ 5 |
| Blog posts | ≥ 1 |
| Examples | ≥ 2 |

### Maintenance Cadence

**Quarterly review:**
- [ ] Update README if features changed
- [ ] Check links (docs, external)
- [ ] Update roadmap
- [ ] Review and close stale issues
- [ ] Update dependencies

---

## 🛠️ Tools & Resources

### Documentation

- **Markdown editor:** Typora, Mark Text, or VSCode
- **Diagrams:** Mermaid, Excalidraw, Lucidchart
- **Screenshots:** Flameshot (Linux), Snagit, macOS Screenshot

### Demos

- **Terminal recording:** asciinema, terminalizer
- **GIF creation:** peek, licecap, gifski
- **Video:** OBS Studio, SimpleScreenRecorder

### Graphics

- **Social previews:** Canva, Figma
- **Badges:** shields.io
- **Code screenshots:** Carbon.sh, ray.so

### Writing

- **Grammar:** Grammarly, LanguageTool
- **Readability:** Hemingway Editor
- **Markdown linting:** markdownlint

---

## 📖 Examples from my-grid

Reference the my-grid polish effort as a template:

**What was done:**
1. Enhanced README with badges, comparison table, use cases
2. Created llms.txt for AI discoverability
3. Wrote publication-ready blog post
4. Organized 21 markdown files into structured docs/
5. Moved internal planning to .github/planning/
6. Created docs/README.md navigation hub
7. Updated all links and references

**Commits to reference:**
- `bac6a3b` - README enhancement
- `1952100` - Blog post
- `e22eec2` - Documentation reorganization

**Time investment:** ~2-3 hours
**Result:** Professional, discoverable project

---

## 📝 Templates

All templates are available in this repository:

- `templates/README-template.md`
- `templates/docs-README-template.md`
- `templates/llms-template.txt`
- `templates/blog-post-template.md`
- `templates/CONTRIBUTING-template.md`

---

## 🎯 Success Criteria

A project is "polished" when:

✅ A stranger can understand what it does in 30 seconds
✅ They can try it in under 5 minutes
✅ Documentation is organized and discoverable
✅ Root directory is clean (≤ 5 markdown files)
✅ GitHub is configured with topics, description, preview
✅ At least one blog post or demo exists
✅ Internal planning docs are hidden

---

## 📞 Questions?

For questions about these guidelines:
- Open a discussion in the main organization repo
- Tag: `documentation` or `organization`

---

**Version History:**
- v1.0 (2025-12-20) - Initial guidelines based on my-grid polish effort

**Next Review:** 2026-01-20
