#!/usr/bin/env python3
"""Generate a circular layout with 12 areas for musical key signatures."""

import math
import yaml

# 12 key signatures in chromatic order
keys = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Bookmarks for quick navigation (1-9, then a-c)
bookmarks = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c"]

# Radius from origin (in canvas units)
radius = 600

# Zone dimensions (plenty of room to work in each area)
zone_width = 120
zone_height = 50

zones = []

for i, key in enumerate(keys):
    # Calculate position in circle
    # Start at top (90 degrees) and go clockwise
    angle_deg = 90 - (i * 30)  # 30 degrees apart, clockwise
    angle_rad = math.radians(angle_deg)

    x = int(radius * math.cos(angle_rad))
    y = int(radius * math.sin(angle_rad))

    # Center the zone at this position
    zone_x = x - (zone_width // 2)
    zone_y = y - (zone_height // 2)

    zone = {
        "name": f"KEY_{key}",
        "type": "static",
        "x": zone_x,
        "y": zone_y,
        "width": zone_width,
        "height": zone_height,
        "bookmark": bookmarks[i],
        "description": f"Key of {key} - organize lists and ideas here"
    }
    zones.append(zone)

# Create the layout structure
layout = {
    "name": "music-keys-circle",
    "description": "12 musical key signatures arranged in a circle around origin",
    "cursor": {
        "x": 0,
        "y": 0
    },
    "zones": zones
}

# Write to YAML
output_path = "/home/be-dev-agent/.config/mygrid/layouts/music-keys-circle.yaml"
with open(output_path, 'w') as f:
    yaml.dump(layout, f, default_flow_style=False, sort_keys=False)

print(f"Layout created: {output_path}")
print(f"\nKey positions (center of each zone):")
for i, key in enumerate(keys):
    angle_deg = 90 - (i * 30)
    angle_rad = math.radians(angle_deg)
    x = int(radius * math.cos(angle_rad))
    y = int(radius * math.sin(angle_rad))
    print(f"  {key:3s} (bookmark '{bookmarks[i]}'): ({x:4d}, {y:4d})")

print(f"\nTo use this layout:")
print(f"  python mygrid.py")
print(f"  :layout load music-keys-circle")
print(f"\nNavigation:")
print(f"  Press ' followed by 1-9 or a-c to jump to each key")
print(f"  ' + 1 = C")
print(f"  ' + 2 = Db")
print(f"  ... etc")
