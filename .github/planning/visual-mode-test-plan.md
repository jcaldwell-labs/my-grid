# Visual Selection Mode - Post-Merge Testing

PR #48 was merged without completing the test plan. This document tracks comprehensive testing of the visual selection feature.

## Test Status

PR #48 merged: 2025-12-16
Test plan items: 0/7 completed at merge time ⚠️

---

## Test Cases

### TC1: Enter/Exit VISUAL Mode

**Steps:**
1. Start my-grid: `python3 mygrid.py`
2. Navigate to any position (e.g., `:goto 10 10`)
3. Press `v` to enter VISUAL mode

**Expected:**
- Mode indicator changes to "VIS"
- Message: "-- VISUAL -- (1x1)"
- Selection starts at 1×1
- Cursor position becomes anchor

**Exit:**
4. Press `Esc`

**Expected:**
- Returns to NAV mode
- Message: "Selection cancelled"
- No cells modified

**Status:** ⬜ Not tested

---

### TC2: Extend Selection with Movement

**Steps:**
1. Enter VISUAL mode at (10, 10)
2. Press `d` (move right) 5 times
3. Press `s` (move down) 3 times

**Expected:**
- Selection grows with each move
- Status shows: "-- VISUAL -- (6x4)" (after movements)
- Selection highlighted in cyan
- Anchor stays at (10, 10)
- Cursor at (15, 13)

**Status:** ⬜ Not tested

---

### TC3: Shrink Selection

**Steps:**
1. Create 6×4 selection (from TC2)
2. Press `a` (move left) 2 times
3. Press `w` (move up) 1 time

**Expected:**
- Selection shrinks
- Status shows: "-- VISUAL -- (4x3)"
- Anchor still at (10, 10)
- Cursor at (13, 12)

**Edge case to test:**
4. Move cursor past anchor (selection inverts)

**Status:** ⬜ Not tested

---

### TC4: Yank Selection

**Setup:**
- Create canvas with some content:
```
:text ABCD
:goto 0 1
:text EFGH
:goto 0 2
:text IJKL
```

**Steps:**
1. Position at (0, 0)
2. Press `v` to enter VISUAL
3. Move to create 4×3 selection
4. Press `y` to yank

**Expected:**
- Mode returns to NAV
- Message: "Yanked 4x3 region (3 lines)"
- Clipboard contains:
  ```
  ABCD
  EFGH
  IJKL
  ```
- Original content unchanged

**Verify clipboard:**
5. `:clipboard`

**Expected:**
- Shows clipboard info with 3 lines

**Status:** ⬜ Not tested

---

### TC5: Delete Selection

**Setup:**
- Create canvas with content (from TC4)

**Steps:**
1. Position at (0, 0)
2. Press `v`
3. Move to create 4×3 selection
4. Press `d` to delete

**Expected:**
- Mode returns to NAV
- Message: "Deleted 4x3 region"
- Selected cells cleared (all empty)
- Canvas shows empty 4×3 area

**Verify:**
5. `:goto 0 0` and check - should be empty

**Status:** ⬜ Not tested

---

### TC6: Fill Selection

**Setup:**
- Clear canvas: `:clear`

**Steps:**
1. Position at (5, 5)
2. Press `v`
3. Move to create 10×5 selection
4. Press `f`

**Expected:**
- Enters COMMAND mode
- Prompt: "Fill character: "

5. Type `#` and press Enter

**Expected:**
- Mode returns to NAV
- 10×5 region filled with '#'
- Message: "Filled 10x5 region with '#'"

**Status:** ⬜ Not tested

---

### TC7: Selection Highlighting

**Setup:**
- Canvas with mixed content and empty cells

**Steps:**
1. Create selection over mixed area (some cells, some empty)
2. Observe visual feedback

**Expected:**
- Selected cells highlighted in cyan background
- Empty cells within selection show as '·' (empty char)
- Cursor position still visible
- Anchor position visible
- Rectangle clearly visible

**Status:** ⬜ Not tested

---

## Edge Cases to Test

### EC1: Zero-Size Selection
**Test:** Move cursor back to anchor (0×0 selection)
**Expected:** ??? (behavior undefined)

### EC2: Selection Across Zones
**Test:** Create selection spanning multiple zones
**Expected:** Works (zones don't affect selection)

### EC3: Selection at Canvas Edges
**Test:** Create selection at very large coordinates (e.g., 10000, -5000)
**Expected:** Works (no bounds checking needed)

### EC4: Selection with Negative Coordinates
**Test:** Create selection from (10, 10) to (-5, -5)
**Expected:** Works (selection normalizes min/max)

### EC5: Selection Inversion
**Test:** Move cursor past anchor (top-right → bottom-left)
**Expected:** Selection inverts correctly

### EC6: Fast Movement in VISUAL
**Test:** Use `WASD` (shift+wasd) for fast selection
**Expected:** Selection extends 10 units per move

---

## Integration Tests

### IT1: Yank + Paste
1. Yank selection
2. Navigate elsewhere
3. `:paste`
**Expected:** Content pastes at new location

### IT2: Fill with Current Colors
1. `:color red`
2. Create selection
3. Press `f`, enter `=`
**Expected:** Region filled with red '=' characters

### IT3: Selection + Save + Reload
1. Create and modify canvas with selection operations
2. `:w visual-test.json`
3. Reload file
**Expected:** All changes persisted

---

## Known Issues to Watch For

### Potential Issue 1: Selection State Leak
**Risk:** Selection object not cleared properly on mode change
**Test:** Enter VISUAL, exit with ESC, enter VISUAL again
**Check:** New selection starts fresh, not reusing old anchor

### Potential Issue 2: Highlight Rendering Conflict
**Risk:** Selection highlight conflicts with zone borders
**Test:** Create selection overlapping zone border
**Check:** Both render correctly

### Potential Issue 3: Yank/Delete at Large Coordinates
**Risk:** Integer overflow or performance issues
**Test:** Selection at coordinates like (100000, 50000)
**Check:** Operations complete without errors

### Potential Issue 4: Fill Command Parsing
**Risk:** Special characters in fill prompt
**Test:** Fill with characters: `'`, `"`, `\`, space
**Check:** All characters handled correctly

---

## Test Results

**Date tested:** _Not yet tested_
**Tester:** _Pending_
**Platform:** _Pending_ (WSL/Linux/Windows)
**Terminal:** _Pending_

**Bugs found:** _None yet_

---

## Recommendation

**Priority: HIGH** - Test visual mode before next release

**Suggested approach:**
1. Run all 7 test cases
2. Test 6 edge cases
3. Run 3 integration tests
4. Document any bugs found
5. Create issues for failures

**If bugs found:**
- Create bug issues with "visual-selection" label
- Reference PR #48
- Consider hotfix PR if critical

---

## Next Steps

- [ ] Execute test plan
- [ ] Document results
- [ ] File bug reports if needed
- [ ] Update this document with findings
- [ ] Consider adding automated tests for visual mode
