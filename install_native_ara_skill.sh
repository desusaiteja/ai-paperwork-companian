#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_SKILL="$SCRIPT_DIR/skills/ara-tax-gatherer/SKILL.md"
TARGET_DIR="$HOME/.claude/skills/ara-tax-gatherer"
TARGET_SKILL="$TARGET_DIR/SKILL.md"

mkdir -p "$TARGET_DIR"
cp "$SOURCE_SKILL" "$TARGET_SKILL"
rm -f \
  "$TARGET_DIR/NATIVE_ARA_ACTION.md" \
  "$TARGET_DIR/NATIVE_ARA_SETUP.md" \
  "$TARGET_DIR/ara_native_action.json" \
  "$TARGET_DIR/ara_native_handoff.sh" \
  "$TARGET_DIR/demo_one_command.sh"

echo "Installed Ara tax gatherer skill:"
echo "$TARGET_SKILL"
echo ""
echo "Restart Ara if it does not pick up the skill immediately."
