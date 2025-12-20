#!/bin/bash
# Lissajous Desert Performance - Warm, flowing patterns
# Evokes desert landscapes through flowing, organic curves
# Watch the LISSAJOUS zone for morphing parametric beauty

LISSAJOUS_PORT=9998
DELAY=5  # Seconds between changes (slower for contemplation)

echo "🏜️  Starting Lissajous desert performance..."
echo "Watch the LISSAJOUS zone for warm, flowing patterns"
echo "Press Ctrl+C to stop"
echo ""

# Function to send parameter
send_param() {
    local param=$1
    local value=$2
    echo "[$(date +%H:%M:%S)] Setting $param = $value"
    echo "{\"command\":\"set_param\",\"param\":\"$param\",\"value\":$value}" | nc localhost $LISSAJOUS_PORT > /dev/null 2>&1
    sleep $DELAY
}

# Desert journey - smooth, organic curves inspired by sand dunes and heat waves

echo "Phase 1: Desert dawn - simple, gentle curves"
send_param "freq_x" 1.0
send_param "freq_y" 1.0
send_param "phase" 0.0
echo "  (Perfect circle - the rising sun)"

echo ""
echo "Phase 2: Sand dunes - gentle rolling waves"
send_param "freq_x" 2.0
send_param "freq_y" 1.0
send_param "phase" 1.57
echo "  (2:1 ratio - gentle undulation)"

echo ""
echo "Phase 3: Heat shimmer - flowing figure-eight"
send_param "freq_x" 1.0
send_param "freq_y" 2.0
send_param "phase" 0.78
echo "  (1:2 ratio - heat waves rising)"

echo ""
echo "Phase 4: Desert wind - spiral formation"
send_param "freq_x" 3.0
send_param "freq_y" 2.0
send_param "phase" 1.0
echo "  (3:2 ratio - wind-carved patterns)"

echo ""
echo "Phase 5: Oasis ripples - expanding circles"
send_param "freq_x" 4.0
send_param "freq_y" 3.0
send_param "phase" 1.57
echo "  (4:3 ratio - water spreading)"

echo ""
echo "Phase 6: Midday complexity - intricate patterns"
send_param "freq_x" 5.0
send_param "freq_y" 4.0
send_param "phase" 0.5
echo "  (5:4 ratio - desert fractal complexity)"

echo ""
echo "Phase 7: Sandstorm building - increasing density"
send_param "freq_x" 7.0
send_param "freq_y" 5.0
send_param "phase" 2.0
echo "  (7:5 ratio - swirling patterns)"

echo ""
echo "Phase 8: Peak storm - maximum complexity"
send_param "freq_x" 8.0
send_param "freq_y" 7.0
send_param "phase" 2.5
send_param "points" 700
echo "  (8:7 ratio - dense mesh, many particles)"

echo ""
echo "Phase 9: Storm passing - simplifying"
send_param "freq_x" 5.0
send_param "freq_y" 3.0
send_param "phase" 1.2
send_param "points" 500
echo "  (5:3 ratio - calming down)"

echo ""
echo "Phase 10: Desert sunset - classic beauty"
send_param "freq_x" 3.0
send_param "freq_y" 4.0
send_param "phase" 1.57
echo "  (3:4 ratio - timeless elegance)"

echo ""
echo "Phase 11: Twilight - simple return"
send_param "freq_x" 2.0
send_param "freq_y" 2.0
send_param "phase" 0.0
echo "  (2:2 circle - the day ends)"

echo ""
echo "Phase 12: Night calm - gentle oval"
send_param "freq_x" 1.0
send_param "freq_y" 1.5
send_param "phase" 0.5
echo "  (1:1.5 ratio - peaceful rest)"

echo ""
echo "🌅 Desert journey complete!"
echo "Total duration: ~$(( DELAY * 36 )) seconds (~3 minutes)"
echo ""
echo "Note: Color scheme currently uses rainbow gradient."
echo "Desert color palette (warm oranges/browns) requires adding color control parameter."
