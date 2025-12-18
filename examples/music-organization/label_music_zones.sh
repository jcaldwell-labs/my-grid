#!/bin/bash
# Add labels to each music key zone

keys=(
  "C:0:600"
  "Db:300:519"
  "D:519:299"
  "Eb:600:0"
  "E:519:-299"
  "F:300:-519"
  "Gb:0:-600"
  "G:-299:-519"
  "Ab:-519:-299"
  "A:-600:0"
  "Bb:-519:300"
  "B:-300:519"
)

for entry in "${keys[@]}"; do
  IFS=':' read -r key x y <<< "$entry"
  echo ":goto $x $y" | nc localhost 8765 >/dev/null 2>&1
  sleep 0.05
  echo ":text === KEY OF $key ===" | nc localhost 8765 >/dev/null 2>&1
  sleep 0.05
done

echo "✓ Added labels to all 12 key zones"
