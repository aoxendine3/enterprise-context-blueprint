#!/usr/bin/env bash
# xoras_snapshot.sh — Save-point system for Xoras workspace
# Usage: bash ops/scripts/xoras_snapshot.sh "message describing changes"
#        bash ops/scripts/xoras_snapshot.sh list
#        bash ops/scripts/xoras_snapshot.sh restore <tag>
set -euo pipefail

XORAS_ROOT="${XORAS_ROOT:-$HOME/Desktop/Xoras_Workspace}"
VERSIONED="$XORAS_ROOT/xoras-versioned"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Source paths to snapshot
declare -a SOURCES=(
  "$XORAS_ROOT/ELITE_BOW"
  "$XORAS_ROOT/AI_Core/Xoras_Project/xoras-core/Source"
  "$XORAS_ROOT/ops/scripts"
  "$XORAS_ROOT/.sovereign/identity/charter.yaml"
  "$XORAS_ROOT/AGENTS.md"
  "$XORAS_ROOT/ROOTS.md"
  "$XORAS_ROOT/MIGRATION_MANIFEST.md"
)

# Destinations inside versioned repo
declare -a DESTINATIONS=(
  "ELITE_BOW"
  "Source"
  "ops"
  "identity/charter.yaml"
  "AGENTS.md"
  "ROOTS.md"
  "MIGRATION_MANIFEST.md"
)

list_snapshots() {
  cd "$VERSIONED"
  echo "=== XORAS SNAPSHOTS ==="
  git tag --sort=-creatordate | head -30
  echo "---"
  git log --oneline -10
}

restore_snapshot() {
  local tag="$1"
  cd "$VERSIONED"
  if ! git tag -l "$tag" | grep -q .; then
    echo "ERROR: Tag '$tag' not found. Use 'list' to see available snapshots."
    exit 1
  fi
  echo "Restoring $tag to $XORAS_ROOT..."
  git checkout "$tag" -- .
  echo "Restored. Run 'git diff' to see what changed before committing."
}

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <message> | list | restore <tag>"
  exit 1
fi

if [[ "$1" == "list" ]]; then
  list_snapshots
  exit 0
fi

if [[ "$1" == "restore" ]]; then
  restore_snapshot "${2:-}"
  exit 0
fi

MESSAGE="$*"
TAG="snapshot-$TIMESTAMP"

echo "=== XORAS SNAPSHOT ==="
echo "Message: $MESSAGE"
echo "Tag:     $TAG"
echo ""

# Sync each source into versioned repo
# Common excludes for directory syncs (use array to avoid shell glob expansion)
EXCLUDES=(
  --exclude=__pycache__
  --exclude="*.pyc"
  --exclude=".DS_Store"
  --exclude=node_modules
  --exclude=venv
  --exclude=.pytest_cache
  --exclude="*.dSYM"
  --exclude="*.db"
  --exclude="*.db-shm"
  --exclude="*.db-wal"
  --exclude="*.bak"
  --exclude="*.log"
  --exclude="*.err"
  --exclude="*.out"
  --exclude="*.pid"
  --exclude="*.lock"
  --exclude=.env
  --exclude=.git
  --exclude=.qdrant_storage
  --exclude=chroma_db
  --exclude=chroma_db_test
  --exclude=whisper.cpp
  --exclude="*.bin"
  --exclude=backups
  --exclude=temp_models
  --exclude=Allocator
  --exclude=Sentinel_IDS
  --exclude=swarm
  --exclude=dream_cycle
  --exclude=cpp_core
  --exclude=Proof_Of_Concepts
  --exclude=tests
  --exclude=__pycache__
  --exclude=governor_state
  --exclude="*.jsonl"
  --exclude="*.jsonl.gz"
)

for i in "${!SOURCES[@]}"; do
  src="${SOURCES[$i]}"
  dst="$VERSIONED/${DESTINATIONS[$i]}"
  if [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    echo "  [file]  $src -> $dst"
  elif [[ -d "$src" ]]; then
    mkdir -p "$dst"
    # For Source directory: only copy source code files by extension
    # to avoid huge model blobs, databases, compiled binaries
    if [[ "$src" == */Source ]]; then
      find "$src" -maxdepth 1 -type f \( -name '*.py' -o -name '*.cpp' -o -name '*.h' -o -name '*.sh' -o -name '*.json' -o -name '*.md' -o -name '*.cjs' -o -name '*.mjs' -o -name '*.yml' -o -name '*.yaml' -o -name '*.html' -o -name '*.plist' \) ! -name '*.log' ! -name '*.err' ! -name '*.out' ! -name '*.bak' ! -name 'xoras_memory.json' 2>/dev/null | while read -r f; do
        cp -p "$f" "$dst/"
        echo "  [src]   $(basename "$f")"
      done
      # Also copy key subdirectory files (non-heavy)
      for sub in Allocator swarm dream_cycle; do
        if [[ -d "$src/$sub" ]]; then
          mkdir -p "$dst/$sub"
          find "$src/$sub" -type f \( -name '*.py' -o -name '*.json' -o -name '*.yaml' \) 2>/dev/null | while read -r f; do
            mkdir -p "$dst/$(dirname "${f#$src/}")"
            cp -p "$f" "$dst/$(dirname "${f#$src/}")/"
          done
        fi
      done
    else
      rsync -a --delete "${EXCLUDES[@]}" "$src/" "$dst/"
    fi
    echo "  [dir]   $src -> $dst/"
  else
    echo "  [MISS]  $src (skipped)"
  fi
done

# .gitignore for versioned repo
cat > "$VERSIONED/.gitignore" << 'GITIGNORE'
__pycache__/
*.pyc
.DS_Store
GITIGNORE

cd "$VERSIONED"
git add -A
git commit -m "$MESSAGE" --no-verify
git tag -a "$TAG" -m "$MESSAGE"

echo ""
echo "Snapshot saved: $TAG"
echo "  $MESSAGE"
echo "  Files: $(git diff --name-only HEAD~1..HEAD 2>/dev/null | wc -l | tr -d ' ') changed"
echo ""
echo "Use '$0 list' to see all snapshots"
echo "Use '$0 restore $TAG' to roll back to this point"
