#!/usr/bin/env bash
# Usage: tools/screenshot_scene.sh res://scenes/world/wrackmouth.tscn 23 /tmp/night.png [wait]
# Renders a scene at a given hour on a throwaway copy of the project (like run_tests.sh), so an open
# editor keeps its .godot cache. The editor API's screenshot routes only capture the editor window.
# Needs a display; the window is created at the project's 640x360 size scaled up by the stretch mode.
set -euo pipefail

if [ "$#" -lt 3 ]; then
	echo "usage: $0 <scene.tscn> <hour 0-23> <out.png> [wait]" >&2
	exit 2
fi
src="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
out="$(realpath -m "$3")"

export XDG_DATA_HOME="$tmp/data" XDG_CONFIG_HOME="$tmp/config" XDG_CACHE_HOME="$tmp/cache"
mkdir -p "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
cp -r "$src" "$tmp/project"
rm -rf "$tmp/project/.godot" "$tmp/project/.git" "$tmp/project/addons/godot_mcp_enhanced"
sed -i '/godot_mcp_enhanced/d' "$tmp/project/project.godot"

godot --headless --path "$tmp/project" --import > "$tmp/import.log" 2>&1 || { tail -20 "$tmp/import.log"; exit 1; }
timeout 60 godot --path "$tmp/project" --script "$src/tools/screenshot_scene.gd" -- "$1" "$2" "$out" "${4:-}" > "$tmp/run.log" 2>&1 || true
[ -s "$out" ] || { tail -20 "$tmp/run.log"; echo "no screenshot written" >&2; exit 1; }
echo "$out"
