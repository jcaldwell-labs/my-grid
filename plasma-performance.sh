#!/bin/bash
# Plasma Performance - Subtle parameter shifts for ambient visualization
# Watch the PLASMA zone while this runs for a meditative experience

PLASMA_PORT=9997
DELAY=4  # Seconds between changes

echo "🎨 Starting plasma performance..."
echo "Watch the PLASMA zone for subtle morphing gradients"
echo "Press Ctrl+C to stop"
echo ""

# Function to send parameter
send_param() {
    local param=$1
    local value=$2
    echo "[$(date +%H:%M:%S)] Setting $param = $value"
    echo "{\"command\":\"set_param\",\"param\":\"$param\",\"value\":$value}" | nc localhost $PLASMA_PORT > /dev/null 2>&1
    sleep $DELAY
}

# Gentle performance - subtle frequency shifts
echo "Phase 1: Slow waves (low frequencies)"
send_param "freq_x" 0.05
send_param "freq_y" 0.05
send_param "freq_diag" 0.03
send_param "freq_radial" 0.04

echo ""
echo "Phase 2: Building horizontal flow"
send_param "freq_x" 0.08
send_param "freq_y" 0.06
send_param "freq_diag" 0.05

echo ""
echo "Phase 3: Adding diagonal motion"
send_param "freq_diag" 0.12
send_param "freq_x" 0.10
send_param "freq_radial" 0.08

echo ""
echo "Phase 4: Turbulent complexity"
send_param "freq_x" 0.15
send_param "freq_y" 0.13
send_param "freq_diag" 0.14
send_param "freq_radial" 0.12

echo ""
echo "Phase 5: Peak chaos"
send_param "freq_x" 0.20
send_param "freq_y" 0.18
send_param "freq_diag" 0.17
send_param "freq_radial" 0.15

echo ""
echo "Phase 6: Calming down - vertical emphasis"
send_param "freq_x" 0.08
send_param "freq_y" 0.15
send_param "freq_diag" 0.10

echo ""
echo "Phase 7: Radial burst"
send_param "freq_radial" 0.20
send_param "freq_x" 0.05
send_param "freq_y" 0.05

echo ""
echo "Phase 8: Gentle resolution"
send_param "freq_radial" 0.10
send_param "freq_x" 0.10
send_param "freq_y" 0.10
send_param "freq_diag" 0.08

echo ""
echo "Phase 9: Return to calm"
send_param "freq_x" 0.05
send_param "freq_y" 0.05
send_param "freq_diag" 0.05
send_param "freq_radial" 0.05

echo ""
echo "✨ Performance complete!"
echo "Total duration: ~$(( DELAY * 36 )) seconds"
