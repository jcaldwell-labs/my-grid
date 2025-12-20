# Issue Backlog Summary - Post Shader Integration

**Date:** 2025-12-19
**Context:** After completing Phase 2 shader integration

---

## New Issues Created

### #54 - SHADER Zone Type (Formalize Integration) [MEDIUM]
**Purpose:** Replace PTY hack with proper zone type
**Benefits:** Cleaner API, state persistence, auto-port management
**Priority:** Medium (polish, but important)
**Labels:** enhancement, priority: medium, area: zones

### #55 - Shader Parameter Presets [MEDIUM]
**Purpose:** Save/load shader configurations
**Benefits:** Quick scene changes, sharing configs, performance prep
**Priority:** Medium (nice productivity boost)
**Labels:** enhancement, priority: medium, area: zones

### #56 - Shader Color Schemes [LOW]
**Purpose:** Themed color palettes (desert, ocean, fire, etc.)
**Benefits:** Contextual aesthetics, branding, accessibility
**Priority:** Low (visual polish)
**Labels:** enhancement, priority: low, area: zones

### #57 - Multi-Shader Composition [LOW]
**Purpose:** One shader modulates another's parameters
**Benefits:** Emergent visuals, reactive systems
**Priority:** Low (experimental, advanced)
**Labels:** enhancement, priority: low, area: zones

---

## Priority Upgrades

### #52 - Event-Driven File Watching → HIGH ⬆️
**Was:** MEDIUM
**Now:** HIGH
**Reason:** Shader development workflow needs instant file watching
- Edit shader scripts → auto-reload
- Monitor shader logs → live display
- Performance script changes → instant feedback

### #51 - API Scripting Guide → HIGH ⬆️
**Was:** MEDIUM
**Now:** HIGH
**Reason:** Powerful API features now exist but undocumented
- Shader control examples
- Socket zone patterns
- Performance scripts as references
- **Critical for showcasing what we built!**

### #21 - Macro Recording → HIGH ⬆️
**Was:** MEDIUM
**Now:** HIGH
**Reason:** Performance scripts prove the macro pattern works
- plasma-performance.sh = 9-phase macro
- lissajous-desert-performance.sh = 12-phase macro
- Record command sequences, replay deterministically

---

## Current High Priority Issues (7 total)

1. **#53** - Visual Selection testing ✅
2. **#52** - Event-driven file watching ⬆️ NEW HIGH
3. **#51** - API scripting guide ⬆️ NEW HIGH
4. **#38** - Test coverage to 80% ✅
5. **#21** - Macro recording ⬆️ NEW HIGH
6. **#20** - Search/Find in canvas ✅
7. **#10** - Undo/Redo ✅

---

## Recommended Next Sprint

**Theme:** Polish & Showcase the Shader Integration

**Sprint Goals:**
1. **#51 - API Scripting Guide** (HIGH)
   - Document shader control
   - Include performance scripts as examples
   - Show socket zone patterns
   - **Deliverable:** Complete API guide with working examples

2. **#38 - Test Coverage** (HIGH)
   - Add tests for ANSI color rendering
   - Test :shader command
   - Test control socket protocol
   - **Target:** 80% coverage maintained

3. **#54 - SHADER Zone Type** (MEDIUM → implement)
   - Formalize the pattern
   - Remove shell script dependency
   - State persistence
   - **Deliverable:** Native SHADER zones working

4. **#55 - Parameter Presets** (MEDIUM)
   - Save/load shader configs
   - Built-in presets (flower, turbulence, etc.)
   - **Deliverable:** `:shader ZONE preset NAME` working

**Stretch:**
- #52 - Event-driven file watching (if time permits)
- #21 - Macro recording (foundation for future)

---

## Issues to Revisit (Lower Priority)

**Keep Open, Monitor Interest:**
- #13 - Mouse support (MEDIUM) - Could be useful
- #14 - HTTP zones (MEDIUM) - Similar to SHADER pattern
- #29 - Help system (LOW) - Nice polish
- #17 - Export formats (LOW) - Nice polish

**Consider Closing (No Traction):**
- #33 - Remote canvas sharing (LOW) - Complex, uncertain need
- #18 - Multi-user collaboration (LOW) - Very complex
- #25 - Plugin system (LOW) - Over-engineering

**Defer (Future Vision):**
- #24 - Layers (LOW) - Interesting but complex
- #30 - ASCII art import (LOW) - Demo feature
- #31 - Presentation mode (LOW) - Niche use case
- #22 - Template library (LOW) - Needs macro system first

---

## Metrics

**Total Open Issues:** 23 (19 existing + 4 new)
**High Priority:** 7 (4 existing + 3 upgraded)
**Medium Priority:** 5 (2 existing + 2 new + 1 existing)
**Low Priority:** 11 (includes 2 new)

**Health:** Good balance
- High priority items are achievable
- Clear next sprint focus
- New issues based on proven patterns
- Backlog trimming candidates identified

---

## Success Indicators

**Short Term (Next Sprint):**
- [ ] API guide published with shader examples
- [ ] Test coverage maintained at 80%+
- [ ] SHADER zone type implemented
- [ ] Parameter presets working

**Medium Term (Next Month):**
- [ ] Macro recording system live
- [ ] Event-driven file watching implemented
- [ ] Community contributions starting
- [ ] 100+ stars on repo (currently growing!)

**Long Term (Q1 2025):**
- [ ] Featured in terminal tool showcases
- [ ] Active community using shader integration
- [ ] Phase 3 features (composition, MIDI) explored
- [ ] Multiple integration examples from community

---

**The shader integration validates my-grid as a serious platform. Focus on documentation and polish to maximize impact!** 🚀
