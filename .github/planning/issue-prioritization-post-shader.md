# Issue Prioritization - Post Shader Integration

Context: After completing Phase 2 shader integration with live parameter control

## Issues Directly Enhanced by Shader Work

### #52 - Event-Driven File Watching for WATCH Zones [MEDIUM]
**Status:** More relevant now
**Why:** With shaders and performance scripts, efficient file watching becomes important
- Current: Poll-based refresh (interval-based)
- Enhancement: Use inotify/fswatch for instant updates
- **Use case:** Watch shader script changes, auto-reload
- **Priority:** Upgrade to HIGH - improves dev experience

### #14 - HTTP Zone - Fetch and display URL content [MEDIUM]
**Status:** Similar pattern to SHADER zones
**Why:** We now have the pattern for dynamic content zones
- Could use same control socket approach
- Fetch URL, parse, display with ANSI colors
- **Use case:** API monitoring, web scraping, feed readers
- **Keep MEDIUM** - nice-to-have, proven pattern exists

### #51 - API Scripting Guide & Example Library [MEDIUM]
**Status:** CRITICAL NOW
**Why:** We just built amazing API integrations but no docs!
- Need examples: shader control, zone creation, socket integration
- Performance scripts are perfect examples
- **Priority:** Upgrade to HIGH - showcase what we built

---

## High Priority Issues (Core Experience)

### #53 - Testing: Visual Selection Mode Validation [HIGH]
**Current priority:** HIGH ✅
**Keep HIGH** - Quality matters for core features
**Note:** Should be tested/validated soon

### #38 - Increase test coverage to 80% [HIGH]
**Current priority:** HIGH ✅
**Keep HIGH** - With new features (ANSI colors, shader command), coverage likely dropped
**Action:** Add tests for shader integration

### #20 - Search/Find in Canvas [HIGH]
**Current priority:** HIGH ✅
**Keep HIGH** - Essential for large canvases
**Note:** Could build on zone buffer search pattern

### #10 - Undo/Redo - Canvas state history [HIGH]
**Current priority:** HIGH ✅
**Keep HIGH** - Core editor functionality
**Note:** Critical for serious usage

---

## Issues That Could Leverage Shader Tech

### #21 - Macro Recording [MEDIUM → HIGH]
**Upgrade to HIGH**
**Why:** Performance scripts ARE macros!
- Record sequences of :shader commands
- Playback for demos/automation
- Save/load macro files
- **Synergy:** Could record any command sequence, not just shaders

### #16 - Image Zone - ASCII art from images [LOW]
**Status:** Could use zone_renderer pattern
**Why:** Same headless rendering approach as shaders
- Convert image → ASCII → zone display
- Could be animated (image sequence)
- **Keep LOW** - nice demo, not critical

### #17 - Export Formats - SVG, PNG, PDF [LOW]
**Status:** zone_renderer shows the pattern
**Why:** Already have headless rendering logic
- Could export zones as images
- SVG for vector graphics
- **Keep LOW** - polish feature

---

## New Issues to Create (Based on Today's Work)

### NEW: SHADER Zone Type (Phase 3)
**Priority:** MEDIUM
**Description:**
- Dedicated SHADER zone type (not PTY hack)
- Built-in parameter control
- Preset system
- Color scheme selection
- Multiple shaders per zone (layering)

**Benefits:**
- Cleaner API than PTY zones
- Better integration with layouts
- Save/load shader states
- Foundation for Phase 3 features

### NEW: Color Scheme Parameter for Shaders
**Priority:** LOW
**Description:**
- Add `color_scheme` parameter to animations
- Presets: rainbow (default), desert, ocean, fire, monochrome
- Live switching via :shader command

**Use case:** Desert performance actually uses desert colors!

### NEW: Multi-Shader Sync/Composition
**Priority:** LOW
**Description:**
- One shader's output modulates another's parameters
- Example: Plasma intensity controls Lissajous frequency
- Composite zone type

**Use case:** Advanced visual performances, reactive systems

### NEW: Shader Parameter Presets
**Priority:** MEDIUM
**Description:**
- Save/load parameter configurations
- Quick presets: `:shader LISSAJOUS preset flower`
- Macro-like but shader-specific

**Use case:** Quick scene changes, performance preparation

### NEW: MIDI Controller Support for Shaders
**Priority:** LOW (FUN)
**Description:**
- Physical knobs control shader parameters
- Real-time tactile control
- Map MIDI CC to shader params

**Use case:** Live VJ performances, installations

---

## Recommended Priority Changes

### Upgrade These:
- #52 Event-driven file watching: MEDIUM → **HIGH**
- #51 API scripting guide: MEDIUM → **HIGH**
- #21 Macro recording: MEDIUM → **HIGH**

### Keep HIGH:
- #53 Visual selection testing ✅
- #38 Test coverage ✅
- #20 Canvas search ✅
- #10 Undo/redo ✅

### Consider Closing (Low Value):
- #33 Remote canvas sharing - Complex, niche use case
- #18 Multi-user collaboration - Very complex, uncertain need
- #25 Plugin system - Over-engineering without clear need

---

## Suggested Next Sprint

**Focus:** Polish the shader integration and improve dev experience

**Sprint Goals:**
1. Create API scripting guide with shader examples (#51)
2. Add tests for shader integration (#38)
3. Implement event-driven file watching (#52)
4. Create SHADER zone type (#NEW)
5. Add shader parameter presets (#NEW)

**Nice-to-have:**
- Macro recording system (#21)
- Color scheme parameter for shaders (#NEW)

---

## Issue Themes

**Core Editor (Must-Have):**
- #10 Undo/Redo
- #20 Search/Find
- #38 Test coverage
- #53 Visual selection testing

**Zones & Integration (Strength):**
- #52 Event-driven watching
- #14 HTTP zones
- #51 API guide
- NEW: SHADER zone type

**Nice Polish (Lower Priority):**
- #13 Mouse support
- #29 Help system
- #17 Export formats

**Future Vision (Defer):**
- #33 Remote sharing
- #18 Collaboration
- #25 Plugin system

---

## Recommendations

### Immediate Actions:

1. **Create new issues for shader enhancements**
   - SHADER zone type
   - Parameter presets
   - Color scheme control
   - Multi-shader composition

2. **Upgrade priorities:**
   ```bash
   gh issue edit 52 --add-label "priority: high"
   gh issue edit 51 --add-label "priority: high"
   gh issue edit 21 --add-label "priority: high"
   ```

3. **Focus next sprint on:**
   - Documentation (#51) - showcase what we built!
   - Testing (#38, #53) - ensure quality
   - Event watching (#52) - better dev UX
   - SHADER zone type - formalize the pattern

### Consider Closing:

Ask community if anyone cares about #33, #18, #25. If no traction, close as "won't implement" to reduce backlog noise.

---

**The shader integration changes the game - it proves my-grid is a serious platform for live, interactive terminal applications. Let's build on this momentum!** 🚀
