# Music Organization Example

Example workflow demonstrating how to create large circular layouts and organize data using the my-grid API.

## Overview

This example creates a circular layout with 12 zones (one for each musical key signature) arranged 600 units from the origin, then organizes a sheet music collection into the zones.

## Scripts

### 1. `generate_music_keys_layout.py`

Generates a YAML layout file with 12 zones arranged in a circle.

**Output:** `~/.config/mygrid/layouts/music-keys-circle.yaml`

**Features:**
- 12 zones for key signatures (C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B)
- 600-unit radius from origin
- Each zone: 120×50 units
- Bookmarks: '1'-'9', 'a'-'c' for navigation
- Total canvas span: ~1320 × 1320 units

**Usage:**
```bash
python3 generate_music_keys_layout.py
```

**Load in my-grid:**
```bash
python3 mygrid.py --layout music-keys-circle --server
```

---

### 2. `register_music_bookmarks.sh`

Manually registers bookmarks for all 12 key zones via the API.

**Note:** Only needed for older versions. Current version auto-registers zone bookmarks on layout load.

**Usage:**
```bash
# With my-grid running in --server mode
bash register_music_bookmarks.sh
```

---

### 3. `label_music_zones.sh`

Adds header labels to each key zone via the API.

**Usage:**
```bash
# With my-grid running in --server mode
bash label_music_zones.sh
```

**Adds:**
```
=== KEY OF C ===
=== KEY OF Db ===
...etc
```

---

### 4. `organize_music.py`

Processes sheet music collection data, deduplicates, sorts, and places organized lists into each key zone.

**Features:**
- Parses period-separated song lists
- Deduplicates entries
- Normalizes variations (e.g., "Agnus Dei" vs "Agnes Day")
- Alphabetically sorts
- Numbers each entry
- Sends to appropriate key zone via API

**Usage:**
```bash
# Edit raw_data dictionary with your song lists
# Then run with my-grid in --server mode
python3 organize_music.py
```

**Example output:**
```
 1. Agnus Dei
 2. Amen
 3. Because he lives
 4. Come as you are
 ...
```

---

## Workflow

**Step 1: Generate layout**
```bash
python3 generate_music_keys_layout.py
```

**Step 2: Start my-grid with layout**
```bash
python3 mygrid.py --layout music-keys-circle --server
```

**Step 3: Add labels (optional)**
```bash
bash label_music_zones.sh
```

**Step 4: Organize data**
```bash
# Edit organize_music.py with your data
python3 organize_music.py
```

**Step 5: Navigate**
- Press `'1` to jump to C
- Press `'2` to jump to Db
- ...and so on

---

## API Integration Pattern

All scripts use the TCP API to control my-grid:

```python
import socket

def send_command(cmd):
    """Send command to mygrid via TCP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 8765))
    sock.sendall((cmd + '\n').encode())
    response = sock.recv(4096).decode()
    sock.close()
    return response

send_command(':goto 0 600')
send_command(':text === KEY OF C ===')
```

**Bash equivalent:**
```bash
echo ':goto 0 600' | nc localhost 8765
echo ':text === KEY OF C ===' | nc localhost 8765
```

---

## Results

**Processed:** 127 unique songs from ~290 duplicates
**Canvas size:** 1320 × 1320 units
**Zones:** 12 (120×50 each)
**Bookmarks:** 12 navigation shortcuts

**Key distribution:**
- A major: 16 songs
- Bb major: 1 song
- C major: 19 songs
- D major: 22 songs
- E major: 15 songs
- F major: 10 songs
- G major: 44 songs

---

## Lessons Learned

### Large Canvas Design

**Spacing:**
- 600-unit radius provides good separation
- Zones don't overlap visually
- Easy to work in each area

**Zone sizing:**
- 120×50 gives room for lists
- Viewport (80×23) shows ~60% of zone width
- Pan or bookmark navigation to see full content

**Bookmarks are essential:**
- Instant navigation between distant zones
- Better than panning 600+ units
- Circular arrangement maps well to keys

### API Scripting

**Python is powerful:**
- Full data processing (dedupe, sort, normalize)
- Clean code with functions
- Easy to modify and rerun

**TCP API is simple:**
- Socket connection + send commands
- JSON responses (optional to parse)
- Works from any language

**Helper scripts are valuable:**
- Repeatable data processing
- Version controlled workflow
- Shareable patterns

---

## Customization

**To adapt for your use case:**

1. **Change circle parameters:**
   - Edit `radius` in `generate_music_keys_layout.py`
   - Edit `zone_width` and `zone_height`
   - Edit `keys` array for different categories

2. **Change data processing:**
   - Edit `parse_songs()` in `organize_music.py`
   - Add your own normalization rules
   - Change formatting in `format_list()`

3. **Add more zones:**
   - Extend `keys` array
   - Adjust angle calculation (360 / len(keys))
   - Add more bookmarks (need available keys)

---

## Related

- See `docs/COORDINATES-GUIDE.md` for coordinate system details
- See `CLAUDE.md` for API server documentation
- See default layouts in `src/layouts.py` for more examples
