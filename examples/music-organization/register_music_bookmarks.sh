#!/bin/bash
# Register bookmarks for all 12 music key zones

keys=(
  "1:0:600"
  "2:300:519"
  "3:519:299"
  "4:600:0"
  "5:519:-299"
  "6:300:-519"
  "7:0:-600"
  "8:-299:-519"
  "9:-519:-299"
  "a:-600:0"
  "b:-519:300"
  "c:-300:519"
)

for entry in "${keys[@]}"; do
  IFS=':' read -r key x y <<< "$entry"
  echo ":mark $key $x $y" | nc localhost 8765 >/dev/null 2>&1
  sleep 0.05
done

echo "✓ Registered all 12 bookmarks"
echo ':marks' | nc localhost 8765
