# Backlog Review - December 19, 2025

## Session Summary

Completed trunk-style development of major features:
- PAGER zones with scroll indicator and ANSI color support
- 2d-shell layout for spatial workspace
- Claude Code hook integration (socket zones receive responses)
- atari-style shader integration (live parametric animations)
- :shader command for live parameter control
- Auto-scroll for dynamic zones
- Windows UTF-8 encoding fixes

## Current State

**22 open issues** reviewed and categorized.

### Recommended Immediate Actions

| Action | Issue | Rationale |
|--------|-------|-----------|
| **CLOSE** | #19 Tmux Integration | PTY zones already provide this functionality |
| **CLOSE/MERGE** | #16 Image Zone | Overlaps with #30 ASCII Art Import |
| **FIX** | #50 Bookmark conflict | Bug: '0' and 'a' conflict with nav keys |

### High Priority (Next Sprint)

| # | Title | Status |
|---|-------|--------|
| #53 | Visual Selection Mode Validation | Test plan exists, needs execution |
| #20 | Search/Find in Canvas | Core navigation feature |
| #10 | Undo/Redo | Core editing feature |
| #38 | Test Coverage 80% | Needs scope refinement |

### Medium Priority (Backlog)

| # | Title | Notes |
|---|-------|-------|
| #51 | API Scripting Guide | Update with socket/hook/shader docs |
| #14 | HTTP Zone | Complements PAGER zones |
| #13 | Mouse Support | UX improvement, curses supports it |
| #52 | Event-Driven File Watching | Nice-to-have, polling works |
| #21 | Macro Recording | Defer - complex |

### Low Priority (Future Vision)

| # | Title |
|---|-------|
| #33 | Remote Canvas |
| #31 | Presentation Mode |
| #30 | ASCII Art Import |
| #29 | Help System |
| #25 | Plugin System |
| #24 | Layers |
| #22 | Template Library |
| #18 | Multi-user Collaboration |
| #17 | Export Formats (SVG/PNG) |

## Recent Commits (Trunk-Style)

```
7fc332a docs: Add Phase 2 shader integration summary
bddf73f feat: Add :shader command for live parameter control
989323f docs: Add Windows quick-start guide for testers
f71069e docs: Add Windows testing guide
fc31624 feat: Add auto-scroll to dynamic zones
360c6d4 feat: Add scroll indicator to pager zones
f7ffb78 feat: Add PAGER zone support to layouts
11ebc7b feat: Add PAGER zone type for paginated file viewing
```

## Integration Status

### Working on WSL
- Live shader zones (plasma, lissajous)
- Claude Code hook → socket zone
- PTY zones for interactive shells
- Full spatial AI workspace

### Working on Windows
- Socket zones
- PAGER zones with scroll indicator
- Watch zones
- Zone mode with UTF-8 fix

### Windows Limitations
- No PTY support (use PIPE zones instead)
- Need `send-to-socket.py` instead of `nc`

## Communication Channels

| Port | Purpose |
|------|---------|
| 9999 | Claude Code responses |
| 9998 | Lissajous parameter control |
| 9997 | Plasma parameter control |
| 8765 | API server (optional) |

## Next Session Recommendations

1. Execute visual mode test plan (#53)
2. Fix bookmark conflict bug (#50)
3. Close stale issues (#19, #16)
4. Consider implementing Search (#20) or Mouse Support (#13)
