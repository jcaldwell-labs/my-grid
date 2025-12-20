# Roadmap to GitHub Issues Mapping

This document maps the ROADMAP.md phases to specific GitHub issues for tracking.

---

## Phase 1: Core Stability

**Goal: Solid foundation, bug-free basics**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| ✅ | - | Done | Fix zone buffer management |
| ✅ | - | Done | Fix clipboard operations |
| ✅ | - | Done | Comprehensive documentation |
| 🔄 | [#38](https://github.com/jcaldwell-labs/my-grid/issues/38) | Open | Increase test coverage to 80% |
| 📋 | TBD | Todo | Performance profiling and optimization |
| 📋 | TBD | Todo | Handle edge cases (empty zones, large buffers) |
| 📋 | TBD | Todo | Improve error messages and user feedback |

---

## Phase 2: Layout System Polish

**Goal: Make layouts the primary workflow**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| 🚨 | [#34](https://github.com/jcaldwell-labs/my-grid/issues/34) | Open | **BUG: Layout loading doesn't auto-start FIFO/Socket zones** |
| ⭐ | [#35](https://github.com/jcaldwell-labs/my-grid/issues/35) | Open | Add --layout CLI flag for startup |
| ⭐ | [#37](https://github.com/jcaldwell-labs/my-grid/issues/37) | Open | Create layout template library (5-10 templates) |
| 🔄 | [#39](https://github.com/jcaldwell-labs/my-grid/issues/39) | Open | Hot-reload layouts without restart |
| 📋 | TBD | Todo | Layout validation and error reporting |
| 📋 | TBD | Todo | Layout preview before loading |
| 📋 | TBD | Todo | Layout migration/upgrade system |

---

## Phase 3: Buffer & History Management

**Goal: Better handling of long-running zones**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| ⭐ | [#36](https://github.com/jcaldwell-labs/my-grid/issues/36) | Open | Zone buffer viewer (:zone buffer NAME) |
| 📋 | TBD | Todo | Search within zone buffers |
| 📋 | TBD | Todo | Export zone buffer to file |
| 📋 | TBD | Todo | Configurable buffer sizes per zone |
| 📋 | TBD | Todo | Buffer compression for old content |
| 📋 | TBD | Todo | Zone statistics (lines/sec, total received) |
| 📋 | TBD | Todo | Circular buffer option vs. linear |

---

## Phase 4: Visual Enhancements

**Goal: Better readability and aesthetics**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| 📋 | [#12](https://github.com/jcaldwell-labs/my-grid/issues/12) | Open | Color Support - Curses color pairs |
| 📋 | [#27](https://github.com/jcaldwell-labs/my-grid/issues/27) | Open | Unicode Box Drawing - Extended character sets |
| 📋 | TBD | Todo | True color support (24-bit RGB) |
| 📋 | TBD | Todo | Zone border customization (styles, colors) |
| 📋 | TBD | Todo | Syntax highlighting for code zones |
| 📋 | TBD | Todo | ANSI color preservation in PTY/FIFO zones |
| 📋 | TBD | Todo | Theme system (dark/light/custom) |

---

## Phase 5: Advanced Zones

**Goal: More zone types and capabilities**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| 📋 | [#14](https://github.com/jcaldwell-labs/my-grid/issues/14) | Open | HTTP Zone - Fetch and display URL content |
| 📋 | [#15](https://github.com/jcaldwell-labs/my-grid/issues/15) | Open | Log Zone - Tail files with filtering |
| 📋 | TBD | Todo | WebSocket zone (bidirectional) |
| 📋 | TBD | Todo | Database query zone (SQL results) |
| 📋 | TBD | Todo | Diff zone (compare two sources) |
| 📋 | TBD | Todo | Chart zone (ASCII graphs/sparklines) |
| 📋 | TBD | Todo | Calendar/time zone |

---

## Phase 6: Collaboration Features

**Goal: Multi-user workflows**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| 📋 | [#18](https://github.com/jcaldwell-labs/my-grid/issues/18) | Open | Multi-user Collaboration - Socket-based sync |
| 📋 | [#33](https://github.com/jcaldwell-labs/my-grid/issues/33) | Open | Remote Canvas - Share via URL |
| 📋 | TBD | Todo | Cursor positions for multiple users |
| 📋 | TBD | Todo | Change tracking and annotations |
| 📋 | TBD | Todo | Export to shareable formats (HTML, PNG) |
| 📋 | TBD | Todo | Conflict resolution for concurrent edits |
| 📋 | TBD | Todo | Session recording/playback |

---

## Phase 7: Extensibility

**Goal: Plugin/scripting system**

| Priority | Issue | Status | Description |
|----------|-------|--------|-------------|
| 📋 | [#25](https://github.com/jcaldwell-labs/my-grid/issues/25) | Open | Plugin System - Extensible architecture |
| 📋 | [#32](https://github.com/jcaldwell-labs/my-grid/issues/32) | Open | Scripting - Batch operations and automation |
| 📋 | TBD | Todo | Custom zone types via plugins |
| 📋 | TBD | Todo | Custom commands via plugins |
| 📋 | TBD | Todo | Keybinding customization |
| 📋 | TBD | Todo | Event hooks (on_zone_update, on_paste, etc.) |

---

## Other Feature Requests (Not Yet Prioritized)

| Issue | Description |
|-------|-------------|
| [#10](https://github.com/jcaldwell-labs/my-grid/issues/10) | Undo/Redo - Canvas state history |
| [#11](https://github.com/jcaldwell-labs/my-grid/issues/11) | Visual Selection - Select regions |
| [#13](https://github.com/jcaldwell-labs/my-grid/issues/13) | Mouse Support - Click to position |
| [#16](https://github.com/jcaldwell-labs/my-grid/issues/16) | Image Zone - ASCII art from images |
| [#17](https://github.com/jcaldwell-labs/my-grid/issues/17) | Export Formats - SVG, PNG, PDF |
| [#19](https://github.com/jcaldwell-labs/my-grid/issues/19) | Tmux/Screen Integration |
| [#20](https://github.com/jcaldwell-labs/my-grid/issues/20) | Search/Find in Canvas |
| [#21](https://github.com/jcaldwell-labs/my-grid/issues/21) | Macro Recording |
| [#22](https://github.com/jcaldwell-labs/my-grid/issues/22) | Template Library - Reusable shapes |
| [#23](https://github.com/jcaldwell-labs/my-grid/issues/23) | Git Integration - Diff and status zones |
| [#24](https://github.com/jcaldwell-labs/my-grid/issues/24) | Layers - Organize canvas content |
| [#26](https://github.com/jcaldwell-labs/my-grid/issues/26) | Session Persistence - Auto-save/recovery |
| [#28](https://github.com/jcaldwell-labs/my-grid/issues/28) | Clipboard Integration - System clipboard |
| [#29](https://github.com/jcaldwell-labs/my-grid/issues/29) | Help System - Interactive tutorials |
| [#30](https://github.com/jcaldwell-labs/my-grid/issues/30) | ASCII Art Import - Convert images |
| [#31](https://github.com/jcaldwell-labs/my-grid/issues/31) | Presentation Mode - Slideshow from regions |

---

## Priority Legend

- 🚨 **Critical Bug** - Blocks workflows
- ⭐ **High Priority** - Next up
- 🔄 **In Progress** - Actively working
- ✅ **Done** - Completed
- 📋 **Backlog** - Future work

---

## Next Actions

### Immediate (This Week)
1. Fix [#34](https://github.com/jcaldwell-labs/my-grid/issues/34) - Layout loading bug (critical)
2. Implement [#35](https://github.com/jcaldwell-labs/my-grid/issues/35) - --layout CLI flag
3. Start [#37](https://github.com/jcaldwell-labs/my-grid/issues/37) - Create first 3-5 layout templates

### Short Term (This Month)
4. Implement [#36](https://github.com/jcaldwell-labs/my-grid/issues/36) - Buffer viewer
5. Improve [#38](https://github.com/jcaldwell-labs/my-grid/issues/38) - Test coverage
6. Add [#39](https://github.com/jcaldwell-labs/my-grid/issues/39) - Hot-reload

### Medium Term (Next 2-3 Months)
- Complete Phase 2 (Layout Polish)
- Start Phase 3 (Buffer Management)
- Begin Phase 4 (Visual Enhancements)

---

*Last updated: December 16, 2024*
*See [ROADMAP.md](ROADMAP.md) for detailed vision and plans*
