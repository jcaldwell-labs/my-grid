# Middle Grid - A Project Management Realm

**An artistic, functional workspace combining Middle Earth aesthetics with real project management using my-grid zones.**

---

## The Concept

Instead of traditional project boards, navigate a **spatial map** inspired by Middle Earth, where each region represents a different project or workflow:

```
    THE SHIRE          RIVENDELL
    [Household]        [Music Lib]
         |                 |
         └────CROSSROADS───┘  ← You ↔ Claude chat here
                  |
         ┌────────┴────────┬──────────┐
         |                 |          |
      GONDOR       PATHS OF DEAD   MOUNT DOOM
      [Dev]        [my-context]    [Issues]
```

---

## The Regions

### 🏡 **The Shire** - Household Management
- **Zone:** HOUSEHOLD (FIFO)
- **Purpose:** Track items to sort/organize
- **Usage:** `echo "Books - living room shelf" > /tmp/household.fifo`
- **Categories:** Donate, keep, storage, repair

### 🎵 **Rivendell** - Sheet Music Library
- **Zone:** MUSIC (FIFO)
- **Purpose:** Catalog sheet music by key signature
- **Usage:** `echo "Moonlight Sonata - C# minor" > /tmp/music.fifo`
- **Organization:** By key (C, G, D, Am, Em, etc.)

### 🔀 **The Crossroads** - Communication Hub
- **Zones:** CLAUDE_SAYS (FIFO) + YOU_SAY (FIFO)
- **Purpose:** Real-time bidirectional chat
- **Usage:**
  - You send: `echo "Hello!" > /tmp/you-say.fifo`
  - Claude responds in CLAUDE_SAYS zone

### ⚔️ **Gondor** - Development Projects
- **Zone:** DEV_LOG (FIFO)
- **Purpose:** Live development progress updates
- **Shows:** Git commits, build status, test results

### 🌫️ **Paths of the Dead** - my-context Integration
- **Zone:** MY_CONTEXT (PIPE) + CONTEXT_LOG (FIFO)
- **Purpose:** Show active contexts and history
- **Shows:** `my-context list`, context changes

### 🌋 **Mount Doom** - Issue Tracking
- **Zone:** ISSUES (WATCH)
- **Purpose:** GitHub issues to tackle
- **Shows:** Top 5 open issues, auto-refreshes

---

## Quick Start

### 1. Setup
```bash
cd ~/projects/active/my-grid
./middle-grid-setup.sh
```

### 2. Start my-grid
```bash
python3 mygrid.py --server
```

### 3. Build the Map
Copy/paste commands from `middle-grid-zones.txt` into my-grid (in COMMAND mode).

Or manually:
- Press `:` to enter command mode
- Copy a command from the file
- Paste and press Enter
- Repeat for all zones

### 4. Navigate the Realm
Use bookmarks (press `'` + letter):
- `'s` - Jump to Shire (household)
- `'r` - Jump to Rivendell (music)
- `'c` - Jump to Crossroads (chat)
- `'g` - Jump to Gondor (dev)
- `'p` - Jump to Paths (context)
- `'m` - Jump to Mount Doom (issues)

---

## How to Use

### Track Household Items
```bash
echo "[$(date +%H:%M:%S)] Books - sort by genre" > /tmp/household.fifo
echo "[$(date +%H:%M:%S)] Kitchen tools - donate pile" > /tmp/household.fifo
echo "[$(date +%H:%M:%S)] Winter clothes - storage bin" > /tmp/household.fifo
```

### Catalog Sheet Music
```bash
# By key signature
echo "Moonlight Sonata - C# minor" > /tmp/music.fifo
echo "Für Elise - A minor" > /tmp/music.fifo
echo "Canon in D - D major" > /tmp/music.fifo

# With composer
echo "Bach Prelude No.1 - C major - WTC Book 1" > /tmp/music.fifo
```

### Chat with Claude
```bash
# You send
echo "Can you help organize my music by era?" > /tmp/you-say.fifo

# Watch CLAUDE_SAYS zone for response
# (Claude monitors /tmp/you-say.fifo and responds)
```

### Monitor Development
```bash
# Claude sends updates
echo "[12:34:56] 🔨 Starting work on issue #34" > /tmp/dev-progress.fifo
echo "[12:35:23] ✏️  Modified src/layouts.py" > /tmp/dev-progress.fifo
echo "[12:36:45] ✅ Tests passing" > /tmp/dev-progress.fifo
```

### Track Context Changes
```bash
# Hook into my-context
my-context start music-cataloging
echo "[$(date +%H:%M:%S)] Context: music-cataloging" > /tmp/context-events.fifo

my-context note "Organized 10 pieces by key"
echo "[$(date +%H:%M:%S)] Note: Organized 10 pieces" > /tmp/context-events.fifo
```

---

## Advanced Usage

### Save Your Map
After setting up all zones:
```
:layout save middle-grid "Project management realm"
```

### Reload Anytime
```bash
python3 mygrid.py --server
```
Then in my-grid:
```
:layout load middle-grid
```

### Add More Regions
Create new zones anywhere on the canvas:
```
:goto 150 20
:text === LOTHLORIEN ===
:text Creative Projects
:zone fifo CREATIVE 40 12 /tmp/creative.fifo
```

### Export as Documentation
```
:export middle-grid-map.txt
```

---

## File Structure

```
middle-grid-setup.sh       - Setup guide and overview
middle-grid-zones.txt      - Zone commands to paste into my-grid
claude-monitor.sh          - Monitor user messages (for Claude)
bidirectional-chat.sh      - Chat system info

FIFOs created:
/tmp/household.fifo        - Household items
/tmp/music.fifo            - Sheet music catalog
/tmp/you-say.fifo          - User → Claude
/tmp/claude-says.fifo      - Claude → User
/tmp/dev-progress.fifo     - Development updates
/tmp/context-events.fifo   - my-context events
```

---

## Dogfooding Benefits

This setup **dogfoods my-grid** by:

1. **Testing large canvas** - Map spans 150x100+ coordinates
2. **Testing multiple zone types** - FIFO, WATCH, PIPE all in use
3. **Testing real workflows** - Actual projects, not demos
4. **Testing FIFO bidirectional** - Two-way communication
5. **Testing bookmarks** - Quick navigation essential
6. **Testing --server mode** - Continuous updates required
7. **Testing layout save/load** - Preserve complex setup

---

## Why This Works

**Traditional approach:** Separate tools for each project
- Household: Spreadsheet
- Music: Database
- Dev: Terminal
- Chat: Another window

**Middle Grid approach:** Unified spatial workspace
- All projects visible in one canvas
- Navigate spatially (like moving through a world)
- Context preserved (everything stays in place)
- Real-time updates via zones
- Artistic + functional

---

## Ideas for Expansion

### More Realms
- **Moria** - Archived/buried projects (inactive)
- **Fangorn Forest** - Long-term growing projects
- **Isengard** - Automation scripts and tools
- **Grey Havens** - Completed projects (port to archive)

### Enhanced Features
- **Routes/paths** - ASCII paths connecting regions
- **Legends** - Map key explaining symbols
- **Weather** - Zone status indicators (☀️ active, 🌧️ blocked)
- **NPCs** - Automated bots sending updates
- **Quests** - Task lists in each region

### Integration Ideas
- Calendar events → specific regions
- Email → inbox zones
- CI/CD → Gondor development zone
- Smart home → household automation
- Spotify → music library integration

---

## Philosophy

> "Not all those who wander are lost." - J.R.R. Tolkien

Middle Grid embodies **spatial navigation over window management**. Instead of opening/closing apps, you **travel** to your projects. The map becomes a mental model of your work landscape.

**Jef Raskin's vision** (The Humane Interface) + **Tolkien's world-building** = A workspace that's both functional and inspiring.

---

## Let's Explore Together!

Start your my-grid, build the map, and let's dogfood this system as we work on issues #34-39.

**Your journey begins at The Crossroads.** 🗺️

Send me a message: `echo "Hello from Middle Grid!" > /tmp/you-say.fifo`
