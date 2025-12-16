# my-grid Roadmap

## Vision

**my-grid** is a spatial ASCII canvas editor with vim-style navigation, enabling:
- Infinite 2D workspace for notes, diagrams, and data visualization
- Real-time integration with external processes (FIFO, sockets, commands)
- Layout-based workspaces for monitoring, development, and collaboration
- Terminal-native with no external dependencies beyond Python + curses

Inspired by Jef Raskin's "The Humane Interface" - spatial navigation over window management.

---

## Recent Accomplishments (Sprint 5+)

### ✅ Zone System Enhancements
- FIFO zones for real-time external communication
- Socket zones for network integration
- PTY zones for interactive terminals
- Watch zones with configurable refresh intervals
- Layout save/load with YAML support

### ✅ Bug Fixes (Dec 2024)
- Fixed clipboard paste method (`canvas.set_char` → `canvas.set`)
- Fixed zone buffer trimming (now respects `max_lines` config)
- FIFO/PTY/Socket zones now keep full 1000-line buffers
- `:yank zone` now captures complete buffer, not just visible content

### ✅ Documentation
- Comprehensive ZONES-REFERENCE.md (17KB guide)
- FIGLET-REFERENCE.md for ASCII art fonts
- DASHBOARD-QUICKSTART.md for getting started
- 10+ helper scripts for demos and testing

### ✅ Developer Experience
- `--server` mode for continuous screen updates (20 FPS)
- API server for external tool integration
- Demo system with showcase capabilities
- Working examples and tutorials

---

## Current State

### What Works Well
✅ Core canvas and viewport mechanics
✅ Vim-style navigation and modes
✅ Zones with dynamic content (7 types)
✅ Layout system for workspace templates
✅ External tool integration (figlet, boxes)
✅ FIFO/Socket real-time communication
✅ Project save/load (JSON format)
✅ Bookmarks for quick navigation

### Known Limitations
⚠️ FIFO/PTY zones Unix-only (WSL works)
⚠️ No built-in scrollback viewer for long zone buffers
⚠️ Color support limited (curses basic colors only)
⚠️ No multi-user/collaboration features
⚠️ No undo/redo system

---

## Roadmap

### Phase 1: Core Stability (Current)
**Goal: Solid foundation, bug-free basics**

- [x] Fix zone buffer management
- [x] Fix clipboard operations
- [x] Comprehensive documentation
- [ ] Automated test coverage >80%
- [ ] Performance profiling and optimization
- [ ] Handle edge cases (empty zones, large buffers)
- [ ] Improve error messages and user feedback

### Phase 2: Layout System Polish (Next)
**Goal: Make layouts the primary workflow**

- [x] Fix layout loading to auto-start FIFO/Socket zones
- [x] Add `--layout` CLI flag to load on startup
- [x] Layout templates library (5-10 common patterns)
- [ ] Layout validation and error reporting
- [ ] Layout preview before loading
- [ ] Layout migration/upgrade system
- [ ] Hot-reload layouts without restart

### Phase 3: Buffer & History Management
**Goal: Better handling of long-running zones**

- [x] Zone buffer viewer (`:zone buffer NAME`)
- [x] Search within zone buffers
- [x] Export zone buffer to file (`:zone export NAME [FILE]`)
- [ ] Configurable buffer sizes per zone
- [ ] Buffer compression for old content
- [ ] Zone statistics (lines/sec, total received)
- [ ] Circular buffer option vs. linear

### Phase 4: Visual Enhancements
**Goal: Better readability and aesthetics**

- [ ] True color support (24-bit RGB)
- [ ] Zone border customization (styles, colors)
- [ ] Syntax highlighting for code zones
- [ ] ANSI color preservation in PTY/FIFO zones
- [ ] Theme system (dark/light/custom)
- [ ] Font size control (if terminal supports)
- [ ] Unicode box-drawing characters option

### Phase 5: Advanced Zones
**Goal: More zone types and capabilities**

- [ ] HTTP zone (webhook receiver)
- [ ] WebSocket zone (bidirectional)
- [ ] Database query zone (SQL results)
- [ ] Log file tail zone (file watching)
- [ ] Diff zone (compare two sources)
- [ ] Chart zone (ASCII graphs/sparklines)
- [ ] Calendar/time zone

### Phase 6: Collaboration Features
**Goal: Multi-user workflows**

- [ ] Shared canvas over network
- [ ] Cursor positions for multiple users
- [ ] Change tracking and annotations
- [ ] Export to shareable formats (HTML, PNG)
- [ ] Conflict resolution for concurrent edits
- [ ] Session recording/playback

### Phase 7: Extensibility
**Goal: Plugin/scripting system**

- [ ] Python plugin API
- [ ] Custom zone types via plugins
- [ ] Custom commands via plugins
- [ ] Keybinding customization
- [ ] Event hooks (on_zone_update, on_paste, etc.)
- [ ] Lua scripting support?

---

## Use Case Priorities

### 1. System Monitoring Dashboard (HIGH)
**Status: Working, needs polish**
- Watch zones for CPU/memory/disk/network ✅
- FIFO zones for alerts ✅
- Layout templates ✅
- **TODO**: Better default layouts, performance graphs

### 2. Development Workspace (HIGH)
**Status: Working, needs expansion**
- Git status watch zone ✅
- PTY terminal zone ✅
- File listing watch zone ✅
- **TODO**: Test runner integration, build status, LSP output

### 3. Log Aggregation (MEDIUM)
**Status: Partially working**
- FIFO zones for log streams ✅
- Buffer management ✅
- **TODO**: Log filtering, search, timestamps, log rotation

### 4. Note-Taking / Documentation (MEDIUM)
**Status: Basic support**
- Static zones ✅
- Canvas drawing ✅
- **TODO**: Markdown rendering, linking between notes, search

### 5. ASCII Diagrams (LOW)
**Status: Basic support**
- Rectangle drawing ✅
- Line drawing ✅
- Text placement ✅
- External tools (boxes, figlet) ✅
- **TODO**: Shape library, connectors, alignment tools

---

## Technical Debt

### High Priority
- [x] Layout loading needs to start FIFO/Socket handlers
- [ ] Test coverage (currently minimal)
- [ ] Error handling consistency
- [ ] Memory leak investigation (long-running sessions)

### Medium Priority
- [ ] Refactor zone handlers (reduce duplication)
- [ ] Improve API server design
- [ ] Better separation of concerns (main.py is large)
- [ ] Configuration file support

### Low Priority
- [ ] Python type hints coverage
- [ ] Code documentation (docstrings)
- [ ] Performance optimization (profiling needed)

---

## Community & Adoption

### Documentation Needed
- [ ] Video tutorials / screencasts
- [ ] Example workflows with screenshots
- [ ] Plugin development guide
- [ ] Architecture deep-dive

### Distribution
- [ ] PyPI package
- [ ] Homebrew formula (macOS)
- [ ] APT package (Debian/Ubuntu)
- [ ] Docker image
- [ ] Snap/Flatpak?

### Community
- [ ] Contributing guide
- [ ] Issue templates
- [ ] Discussion forum or Discord
- [ ] Showcase gallery (user creations)

---

## Decision Log

### Why FIFO instead of just sockets?
- FIFO is simpler for local scripts
- Lower overhead for same-machine communication
- File-like interface familiar to shell users
- Can still use sockets for remote

### Why curses instead of terminal escape codes?
- Cross-platform abstraction
- Built into Python stdlib
- Handles resize, colors, input consistently

### Why sparse canvas storage?
- Memory efficiency for large canvases
- Instant "clear" operation (just empty dict)
- Natural fit for mostly-empty diagrams

### Why vim-style modes?
- Familiar to target audience
- Clean separation of concerns
- Keyboard-driven (no mouse dependency)

---

## Metrics & Success Criteria

### Technical Metrics
- Frame rate: 20+ FPS in --server mode ✅
- Memory: <100MB for typical session ✅
- Startup time: <500ms ✅
- Test coverage: Target 80% (current: ~20%)

### User Metrics
- Can new user create dashboard in <5 minutes? ✅
- Can user integrate external tool in <2 minutes? ✅
- Is documentation findable and clear? ✅ (new docs)
- Are common tasks <5 keystrokes? Mostly

---

## Open Questions

1. **Multi-canvas**: Should we support multiple canvases in one session?
2. **Scripting**: Python plugins vs. embedded Lua?
3. **Color scheme**: Default dark/light mode preference?
4. **Platform priority**: Focus on Linux/WSL or also native Windows?
5. **Zone defaults**: Should zones auto-start on layout load? (YES, needs fix)
6. **Buffer limits**: Is 1000 lines the right default? Configurable?
7. **Performance**: At what canvas size do we need optimization?

---

## Next Session Priorities

1. ~~**Fix layout loading** - Auto-start FIFO/Socket zones~~ ✅
2. ~~**Add `--layout` CLI flag** - Load layout on startup~~ ✅
3. ~~**Create layout templates** - 5-10 ready-to-use layouts~~ ✅ (9 templates)
4. ~~**Buffer viewer** - `:zone buffer NAME` command~~ ✅
5. ~~**Buffer export** - Export zone buffer to file~~ ✅
6. **Test coverage** - Add unit tests for zone handlers
7. **Layout validation** - Error reporting for invalid layouts

---

## Long-term Vision (1-2 years)

**my-grid becomes:**
- The go-to tool for terminal-based monitoring dashboards
- A spatial note-taking system for developers
- An ASCII art creation platform
- A collaboration tool for distributed teams
- A scriptable terminal multiplexer alternative

**Success looks like:**
- 1000+ GitHub stars
- Active community of plugin developers
- Featured in terminal tool showcases
- Used in production monitoring setups
- Educational content creators using it for demos

---

*Last updated: December 16, 2024*
*Contributors: User + Claude (pairing session)*
