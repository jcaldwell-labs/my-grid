# Figlet Font Reference

## Overview

The `figlet` command in my-grid creates ASCII art text banners using the figlet tool.

## Command Syntax

```
:figlet TEXT              - Draw with default font (standard)
:figlet -f FONT TEXT      - Draw with specific font
:figlet list              - List available fonts
```

## Available Fonts

We have **17 fonts** available in the system:

| Font | Style | Best For |
|------|-------|----------|
| **banner** | Bold block letters | Headers, titles |
| **big** | Large rounded letters | Prominent text |
| **block** | Underscored block style | Technical look |
| **bubble** | Circular bubble letters | Playful text |
| **digital** | Digital/LCD display | Technical displays |
| **ivrit** | Hebrew-style characters | Special characters |
| **lean** | Italic slanted text | Modern look |
| **mini** | Compact small letters | Space-constrained areas |
| **script** | Cursive handwriting | Elegant text |
| **shadow** | 3D shadowed letters | Depth effect |
| **slant** | Forward italic slant | Dynamic text |
| **small** | Minimal height letters | Inline emphasis |
| **smscript** | Small script style | Compact elegant text |
| **smshadow** | Small with shadow | Compact 3D effect |
| **smslant** | Small slanted | Compact dynamic text |
| **standard** | Classic figlet (default) | General purpose |
| **term** | Terminal-style | System/technical text |

## Visual Examples

### Banner Font
```
 #####
#     #   ##   #    # #####  #      ######
#        #  #  ##  ## #    # #      #
 #####  #    # # ## # #    # #      #####
      # ###### #    # #####  #      #
#     # #    # #    # #      #      #
 #####  #    # #    # #      ###### ######
```

### Big Font
```
  _____                       _
 / ____|                     | |
| (___   __ _ _ __ ___  _ __ | | ___
 \___ \ / _` | '_ ` _ \| '_ \| |/ _ \
 ____) | (_| | | | | | | |_) | |  __/
|_____/ \__,_|_| |_| |_| .__/|_|\___|
                       | |
                       |_|
```

### Block Font
```

  _|_|_|                                      _|
_|          _|_|_|  _|_|_|  _|_|    _|_|_|    _|    _|_|
  _|_|    _|    _|  _|    _|    _|  _|    _|  _|  _|_|_|_|
      _|  _|    _|  _|    _|    _|  _|    _|  _|  _|
_|_|_|      _|_|_|  _|    _|    _|  _|_|_|    _|    _|_|_|
                                    _|
                                    _|
```

### Slant Font
```
   _____                       __
  / ___/____ _____ ___  ____  / /__
  \__ \/ __ `/ __ `__ \/ __ \/ / _ \
 ___/ / /_/ / / / / / / /_/ / /  __/
/____/\__,_/_/ /_/ /_/ .___/_/\___/
                    /_/
```

## Usage Examples

### In my-grid

```bash
# Start my-grid
python3 mygrid.py

# Enter command mode with ':'
# Then type figlet commands:

:figlet Hello World
:figlet -f banner TITLE
:figlet -f slant Project Name
:figlet -f bubble Fun!
:figlet -f digital 12345
```

### Workflow Tips

1. **Headers**: Use `banner` or `big` for section headers
2. **Technical**: Use `digital` or `term` for system/technical text
3. **Compact**: Use `mini`, `small`, or `lean` when space is limited
4. **Visual interest**: Use `shadow`, `slant`, or `bubble` for emphasis
5. **Standard default**: The `standard` font is clean and reliable for most uses

## Interactive Reference Canvas

A full reference canvas with all fonts has been created:

```bash
python3 mygrid.py figlet-reference.json
```

This canvas shows **all 17 fonts** with the sample text "ABCabc" to demonstrate:
- Uppercase letters (ABC)
- Lowercase letters (abc)
- Font size and styling

The fonts are arranged in two columns for easy comparison.

## Font Selection Guide

### When to use each font:

- **Large titles**: banner, big
- **Section headers**: slant, shadow, standard
- **Inline text**: small, mini, smscript
- **Numbers**: digital
- **Fun/Creative**: bubble, script
- **Technical/Code**: block, term, lean
- **3D effects**: shadow, smshadow

## Implementation Details

The figlet integration:
- Located in `src/external.py`
- Uses subprocess to call system `figlet` command
- Returns ExternalToolResult with line-by-line output
- Supports all fonts installed in `/usr/share/figlet/`

## See Also

- `CLAUDE.md` - Main project documentation
- `src/external.py` - External tool integration code
- `:box` command - ASCII box frames (pairs well with figlet)
- `:tools` command - Check if figlet is installed
