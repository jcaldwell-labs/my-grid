#!/usr/bin/env python3
"""Organize sheet music collection by key signature."""

import socket
import time

# Raw data by key
raw_data = {
    "A": """The stand. Seas of Crimson. Until the whole world hears. Agnus Dei. Seas of Crimson. God of brilliant lights. Agnus Dei. God of brilliant lights. The stand. You alone can rescue. God of brilliant lights. Come as you are. It is well. Lamb of God. The river. God of brilliant lights. Resurrecting. God of brilliant lights. How great thou art. Because he lives. Amen. It is well. It is well. God of brilliant lights. It is well. The stand. Agnes Day. Lamb of God. Lamb of God. It is well. The stand. Lay me down. Agnes Day. Because he lives. Amen. Come as you are. The river. Come as you are. From the inside out.""",

    "Bb": """hymn 635""",

    "C": """None but Jesus. Till I see you. Man of sorrows. Jesus Christ is risen today. Till I see you. What wondrous love is this. Praise the Father. Praise the Son. Holy, holy, holy. There is nothing like. My lighthouse. Transfiguration. Forever reign. There is nothing like. Anchor. Crown him with many crowns. Grace like rain. Come thou fount of every blessing. Till I see you. Grace like rain. Grace like rain. Anchor. Anchor. Hymn 664. Hymn 481. What wondrous love is this. Man of sorrows. Man of sorrows. Transfiguration. Grace like rain. It is you. Anchor. Till I see you. Forever reign. Jesus Christ is risen today. Holy, holy, holy. There is nothing like. Crown him with many crowns.""",

    "D": """I surrender. Revelation song. Even so come. Ain't no grave. Ever be. Holy fire. I surrender. Better is one day. I surrender. He is faithful. Ain't no grave. In Christ alone. Desert Song. God is great. Oceans where feet may fail. Even so come. Desert Song. Be thou my vision. King of Kings. New wine. Revelation song. Be thou my vision. Even so. New wine. Be thou my vision. God is great. Oceans where feet may fail. Gloria. New wine. In Christ alone. When I survey the Wondrous cross. Gloria. Better is one day. Oceans where feet may fail. Revelation song. Reckless love. God is great. He is faithful. In Christ alone. I surrender. Holy fire. I surrender. Lord, I need you. Desert Song. God is great. Reckless love. Thrive. Thrive. Revelation song. I surrender. Better is one day. In Christ alone. New wine. He is faithful. Even so come. Holy fire. Nail pierced hands. The wonderful cross.""",

    "E": """Show me your glory. All the earth will sing your praises. Show me your glory. All the earth will sing your praises. Take my life. Your grace is enough. Show me your glory. All the earth will sing your praises. He knows my name. Your grace is enough. Desperate people. Hosanna. You'll come. 10 thousand reasons bless the Lord. 10 000 reasons bless the Lord. Savior king. We fall down. Hosanna. You'll come. Hosanna. Desperate people. Surrender. Open the eyes of my heart. Open the eyes of my heart. Open the eyes of my heart. Surrender. Show me your glory. Hosanna. You'll come. Hosanna. All the earth will sing your praises. At the cross, love ran red. Surrender. Hosanna. All the earth will sing your praises. At the cross, love ran red. Surrender. All the earth will sing your praises. Desperate people. Hosanna. Hallelujah sing to Jesus. Your grace is enough. Surrender. Hosanna. Show me your glory. Desperate people.""",

    "F": """Gloria. God rest ye merry gentlemen. Wade in the water. As we seek your face. The river. Watchmen tell us. House of the Lord. Ancient gates. Hymn 390 - Praise to the Lord. Love is here. Love is here. Wade in the water. Wade in the water. Love is here. Love is here. As we seek your face. Love is here. Ancient gates.""",

    "G": """How great is our God. There is a kingdom. Breaking through. My glorious. Only king forever. Holy is the Lord. Song of hope heaven come down. Our God. Oh come, Oh come, Emmanuel. Your face outshines the brightest sun. Dwelling in Beulah land. Who you say I am. My glorious. God of wonders. YOU. Your face outshines the brightest sun. Song of hope heaven come down. God of wonders. My glorious. O come, O, come Emmanuel. Jesus Messiah. Only king forever. YOU. Your face outshines the brightest sun. There is a kingdom. Indescribable. Lay me down. Our God. King forever. How great is our God. Immortal, Invisible. Show me your glory. Lay me down. Hymn 699. Forever. Mighty to save. Only king forever. Who you say I am. Holy is the Lord. Your great name. I will rise. How great is our God. Holy is the Lord. Holy is the Lord. King forever. Only king forever. Who you say I am. Your face outshines the brightest sun. Who you say I am. How great is our God. What child is this. Holy is the Lord. Your great name. Our God. Broken vessels. Amazing grace. Holy is the Lord. Only king forever. Immortal. Invisible. My glorious. Broken vessels, Amazing Grace. Only king forever. Your great name. Song of hope heaven come down. Whom shall I fear God of Angel armies. Days of Elijah. Lay me down. Forever. It is well. Made new. Only king forever. My glorious. Be magnified. My glorious. Soul on fire. Breaking through. You. Only king forever. Broken vessels, Amazing Grace. Might need to save. Mighty to save. Forever. Holy is the Lord. How he loves. I give you my heart. One thing remains, your love never fails. Only king forever. Holy is the Lord. How great is our God. There is a kingdom. Might need to save. Whom shall I fear God of Angel armies. Mighty to save. Breaking through. As we seek your face. Whom shall I fear God of Angel armies. I give you my heart. God of wonders. Your great name. There is a kingdom. Who you say I am. I heard the voice of Jesus say. Who you say I am. How great is our God."""
}

# Key positions (center of each zone)
positions = {
    "C": (0, 600),
    "Db": (300, 519),
    "D": (519, 299),
    "Eb": (600, 0),
    "E": (519, -299),
    "F": (300, -519),
    "Gb": (0, -600),
    "G": (-299, -519),
    "Ab": (-519, -299),
    "A": (-600, 0),
    "Bb": (-519, 300),
    "B": (-300, 519)
}

def send_command(cmd):
    """Send command to mygrid via TCP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 8765))
        sock.sendall((cmd + '\n').encode())
        response = sock.recv(4096).decode()
        sock.close()
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def parse_songs(text):
    """Parse period-separated song list, dedupe, and sort."""
    # Split by periods, strip whitespace, remove empty
    songs = [s.strip() for s in text.split('.') if s.strip()]

    # Normalize variations
    normalized = []
    for song in songs:
        # Handle common variations
        if song.lower().startswith('agnus dei') or song.lower().startswith('agnes day'):
            normalized.append('Agnus Dei')
        elif '10 000 reasons' in song.lower() or '10 thousand reasons' in song.lower():
            normalized.append('10,000 Reasons (Bless the Lord)')
        elif 'o come' in song.lower() and 'emmanuel' in song.lower():
            normalized.append('O Come, O Come Emmanuel')
        elif 'broken vessels' in song.lower() and 'amazing grace' in song.lower():
            normalized.append('Broken Vessels (Amazing Grace)')
        elif song.lower() == 'you' or song.upper() == 'YOU':
            normalized.append('You')
        elif 'even so come' in song.lower():
            normalized.append('Even So Come')
        elif song.lower() == 'even so':
            normalized.append('Even So Come')
        elif 'might need to save' in song.lower():  # Typo for "mighty to save"
            normalized.append('Mighty to Save')
        else:
            # Title case for consistency
            normalized.append(song.strip())

    # Dedupe and sort
    unique = sorted(set(normalized))
    return unique

def format_list(songs, max_width=100):
    """Format song list for canvas."""
    lines = []
    for i, song in enumerate(songs, 1):
        lines.append(f"{i:2d}. {song}")
    return lines

# Process each key
for key in ["A", "Bb", "C", "D", "E", "F", "G"]:
    if key not in raw_data:
        continue

    print(f"\n=== Processing Key of {key} ===")

    songs = parse_songs(raw_data[key])
    print(f"Found {len(songs)} unique songs")

    if key not in positions:
        print(f"Skipping {key} - no position defined")
        continue

    x, y = positions[key]

    # Go to position (offset to top-left of zone)
    send_command(f":goto {x - 55} {y + 20}")
    time.sleep(0.05)

    # Clear area first (just the title line)
    send_command(f":goto {x - 55} {y + 20}")
    time.sleep(0.05)

    # Write songs
    for line in format_list(songs):
        send_command(f":text {line}")
        time.sleep(0.05)
        # Move down one line
        send_command(f":goto {x - 55} {y + 20 - (format_list(songs).index(line) + 2)}")
        time.sleep(0.05)

    print(f"✓ Wrote {len(songs)} songs to {key}")

print("\n✓ All keys processed!")
