#!/usr/bin/env bash
# Runs the headless GDScript tests on a throwaway copy of the project, so a Godot
# editor that has the project open keeps its own .godot cache and addon port.
set -euo pipefail

src="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

export XDG_DATA_HOME="$tmp/data"
export XDG_CONFIG_HOME="$tmp/config"
export XDG_CACHE_HOME="$tmp/cache"
mkdir -p "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"

cp -r "$src" "$tmp/project"
rm -rf "$tmp/project/.godot" "$tmp/project/.git" "$tmp/project/addons/godot_mcp_enhanced"
sed -i '/godot_mcp_enhanced/d' "$tmp/project/project.godot"

godot --headless --path "$tmp/project" --import > "$tmp/import.log" 2>&1 || {
	tail -20 "$tmp/import.log"
	exit 1
}
if grep -qE "SCRIPT ERROR|Failed to load|Parse Error|Compile Error" "$tmp/import.log"; then
	cat "$tmp/import.log"
	exit 1
fi

rc=0
godot --headless --path "$tmp/project" --fixed-fps 60 res://tests/run_tests.tscn > "$tmp/run.log" 2>&1 || rc=$?
cat "$tmp/run.log"
if [ "$rc" -ne 0 ] || grep -qE "SCRIPT ERROR|Failed to load|Parse Error|Compile Error" "$tmp/run.log"; then
	exit 1
fi
if ! grep -q "^Results: [0-9]\+ passed, 0 failed$" "$tmp/run.log"; then
	exit 1
fi
