# PTY Zone Roadmap - Path to Full Terminal Support

**Goal:** Run Claude Code, vim, and other interactive terminal apps inside my-grid PTY zones

---

## The Vision

Imagine your my-grid workspace:
- **CLAUDE-LIVE zone** - Running `claude` interactively
- **SHELL zone** - Your development terminal
- **CLAUDE zone** - Captured Claude responses (via hook)
- **PLASMA/LISSAJOUS zones** - Live shaders
- **GIT zone** - Status monitoring

**All in one spatial workspace. Navigate between them with bookmarks. Everything persistent.**

---

## Current State (Partially Working)

**What works:**
- Basic command execution (`ls`, `date`, etc.)
- Output appears in zone
- Can focus/unfocus PTY
- ANSI colors render
- Scrolling with PgUp/PgDn

**What's broken:**
- Interactive menus (Claude Code selection doesn't work)
- Backspace doesn't delete characters visually
- Echo output missing or corrupted
- Text cutoff on left side (carriage return issues)
- Complex apps (vim, nano) won't work

**Root cause:** Line-based processing doesn't handle terminal control sequences

---

## The Solution: pyte Terminal Emulator

**Library:** https://github.com/selectel/pyte
**What it does:** Full VT100/ANSI terminal emulation with screen buffer

**How it works:**
```python
# Create virtual terminal screen
screen = pyte.Screen(80, 24)
stream = pyte.Stream(screen)

# Feed ALL PTY output (including control sequences)
stream.feed(pty_data)

# Get rendered display
lines = [''.join(screen.buffer[y]) for y in range(24)]

# That's it - backspace, cursor positioning, everything works!
```

---

## Implementation Plan (Broken into Issues)

### Issue #59 - Master Planning Issue
Comprehensive overview and strategy

### Issue #60 - Core pyte Integration [HIGH] ⭐ **START HERE**
**Effort:** 2-3 hours
**Impact:** Fixes 80% of problems

**What it does:**
- Add pyte dependency
- Create PTYScreen wrapper class
- Replace line-based reader with screen-based
- Basic testing

**Result after this issue:**
- Backspace works
- Echo works
- Claude Code menus work
- Most terminal apps work

### Issue #61 - Scrollback with pyte (Future)
**Effort:** 1-2 hours
**Impact:** Polished scrolling experience

**What it does:**
- Use pyte's HistoryScreen for scrollback
- Clean scroll key handling
- Visual scroll indicators

**Depends on:** #60

### Issue #62 - Input Focus Polish (Future)
**Effort:** 1-2 hours
**Impact:** Better UX, clearer focus mode

**What it does:**
- Visual focus indicators (colored border?)
- Better status messages
- Clear key routing (what goes to terminal vs my-grid)

**Depends on:** #60

### Issue #63 - Advanced Terminal Support (Future, Optional)
**Effort:** 2-3 hours
**Impact:** vim/nano support

**What it does:**
- Alternative screen buffer (vim uses this)
- Mouse support in terminal
- Resize handling
- Advanced escape sequences

**Depends on:** #60

---

## Recommended Execution

**Week 1: Core Foundation**
- **Day 1:** Implement #60 (core pyte) - 2-3 hours
- **Day 1-2:** Test with Claude Code, bash, python REPL
- **Day 2:** Fix any issues found, write tests

**Week 2: Polish (Optional)**
- **Day 3:** Implement #61 (scrollback) if needed
- **Day 4:** Implement #62 (polish) if needed
- **Day 5:** Test with vim (#63) if needed

**Quick Win Focus:** Just do #60 and test! It might be all we need.

---

## Success Milestones

### Milestone 1: Basic Terminal Apps (Issue #60)
- [ ] `pwd`, `ls`, `echo` work perfectly
- [ ] Backspace visually deletes
- [ ] `echo "test"` shows "test"
- [ ] No text cutoff or corruption
- [ ] python3 REPL works

### Milestone 2: Claude Code Works (Issue #60)
- [ ] Can run `claude` in PTY zone
- [ ] Interactive menus work (arrow keys + Enter)
- [ ] Can see Claude responses
- [ ] Can interact with prompts
- [ ] **Meta: Claude helping build my-grid INSIDE my-grid!**

### Milestone 3: Advanced Apps (Issue #63, Optional)
- [ ] vim opens and is usable
- [ ] nano works
- [ ] htop renders correctly
- [ ] Full terminal emulation

---

## Code Architecture

### Before (Current - Broken)

```
PTY Output → Line Split → Append Lines → Zone Display
             (loses cursor control!)
```

### After (pyte - Correct)

```
PTY Output → pyte Stream → Screen Buffer → Zone Display
             (full terminal emulation!)
```

**Key difference:** pyte maintains a **screen buffer** with cursor, just like a real terminal.

---

## Testing Strategy

### Automated Tests

```python
# tests/test_pty_screen.py
class TestPyteIntegration:
    def test_backspace_handling(self):
        """Test backspace deletes characters."""
        screen = PTYScreen(80, 24)
        screen.feed("test\b")  # Type "test", backspace once
        lines = screen.get_lines()
        assert "tes" in lines[0]  # Last char deleted

    def test_cursor_positioning(self):
        """Test ANSI cursor control."""
        screen = PTYScreen(80, 24)
        screen.feed("ABC\x1b[2DX")  # ABC, move left 2, write X
        lines = screen.get_lines()
        assert "AXC" in lines[0]  # X overwrote B

    def test_interactive_menu(self):
        """Simulate arrow key menu navigation."""
        screen = PTYScreen(80, 24)
        # Feed cursor positioning for menu
        screen.feed("Option 1\n")
        screen.feed("\x1b[1AOption 2\n")  # Cursor up, write Option 2
        # pyte tracks this correctly
```

### Manual Test Checklist

**Basic Commands:**
- [ ] `pwd` - See output
- [ ] `ls` - See file list
- [ ] `echo "hello"` - See "hello"
- [ ] Type `pwd`, backspace to `pw`, type `d` again - Works

**Interactive:**
- [ ] `python3` - REPL prompt appears
- [ ] Type code, see it
- [ ] Get responses
- [ ] Exit works

**Claude Code:**
- [ ] Run `claude`
- [ ] See menu/prompts
- [ ] Arrow up/down between options
- [ ] **Press Enter on option - IT WORKS!**

---

## Migration Strategy

**Backward Compatibility:**

Keep old code temporarily:
```python
USE_PYTE = True  # Feature flag

if USE_PYTE:
    reader_thread = threading.Thread(target=self._pty_reader_pyte, ...)
else:
    reader_thread = threading.Thread(target=self._pty_reader_old, ...)
```

After testing proves pyte works, remove old code.

---

## Effort Summary

**Minimum viable (Issue #60 only):** 2-3 hours
- Gets Claude Code working
- Fixes critical bugs
- Most terminal apps work

**Full polish (All issues):** 6-10 hours
- Perfect scrollback
- Great UX
- vim support

**Recommended:** Start with #60, test with Claude Code, decide if polish is worth it.

---

## Risk Assessment

**Risks:**
- pyte might have bugs (mitigated: battle-tested library)
- Performance overhead (mitigated: pyte is efficient)
- Integration complexity (mitigated: clean API)

**Low risk, high reward!**

---

## Next Actions

**Immediate:**
1. Review this roadmap
2. Review #60 implementation plan
3. Decide: Start #60 now or wait?

**Implementation:**
1. `pip install pyte`
2. Create `src/pty_screen.py`
3. Update PTYHandler
4. Test with Claude Code
5. Celebrate when it works! 🎉

---

**This is the path to running Claude Code inside my-grid. Let's build it right!** 🚀
