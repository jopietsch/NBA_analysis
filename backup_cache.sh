#!/usr/bin/env bash
# Back up the shared data cache as a tar archive.
#
# Why: the cache is ~68k small files (~300 MB) that take ~13 h to re-download.
# Copying tens of thousands of tiny files is slow everywhere (external drive,
# rsync, cloud); bundling them into one (or a few) tar files makes the backup a
# cheap copy. The files are already zstd-compressed (.csv.zst), so this does NOT
# re-compress (plain tar) — recompressing already-compressed data wastes CPU for
# ~zero gain.
#
# Usage:
#   ./backup_cache.sh                 # one tar of the whole cache -> $BACKUP_DIR
#   ./backup_cache.sh /some/dir       # write the archive(s) to /some/dir
#   ./backup_cache.sh --per-season    # one tar per top-level cache subdir
#                                     # (natural once the per-game files are
#                                     #  sharded into season folders; see the
#                                     #  Phase 4 sharding plan). Immutable past
#                                     #  seasons tar once and never change.
#
# Env:
#   NBA_CACHE_DIR         override the cache location (default: <repo>/cache)
#   NBA_CACHE_BACKUP_DIR  default destination (default: ~/nba_cache_backups)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${NBA_CACHE_DIR:-$REPO/cache}"

PER_SEASON=0
DEST="${NBA_CACHE_BACKUP_DIR:-$HOME/nba_cache_backups}"
for arg in "$@"; do
  case "$arg" in
    --per-season) PER_SEASON=1 ;;
    -h|--help) sed -n '2,25p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) DEST="$arg" ;;
  esac
done

if [ ! -d "$CACHE_DIR" ]; then
  echo "cache dir not found: $CACHE_DIR" >&2; exit 1
fi
mkdir -p "$DEST"
STAMP="$(date +%Y%m%d_%H%M%S)"
CACHE_PARENT="$(cd "$CACHE_DIR/.." && pwd)"
CACHE_NAME="$(basename "$CACHE_DIR")"

human() { du -sh "$1" 2>/dev/null | cut -f1; }

if [ "$PER_SEASON" -eq 1 ]; then
  # Tar each top-level subdirectory of the cache separately, plus one archive
  # for the loose (non-subdir) files. Only useful once the cache has subdirs.
  shopt -s nullglob
  subdirs=("$CACHE_DIR"/*/)
  if [ ${#subdirs[@]} -eq 0 ]; then
    echo "no subdirectories in $CACHE_DIR yet — the cache is still flat."
    echo "falling back to a single whole-cache archive."
    PER_SEASON=0
  else
    for d in "${subdirs[@]}"; do
      name="$(basename "$d")"
      out="$DEST/nba_cache_${name}_${STAMP}.tar"
      tar -cf "$out" -C "$CACHE_DIR" "$name"
      echo "  $out  ($(human "$out"))"
    done
    # loose files (anything directly under the cache, not in a subdir)
    loose_out="$DEST/nba_cache_loose_${STAMP}.tar"
    ( cd "$CACHE_DIR" && find . -maxdepth 1 -type f -print0 \
        | tar -cf "$loose_out" --null -T - ) || true
    [ -s "$loose_out" ] && echo "  $loose_out  ($(human "$loose_out"))"
    echo "per-season backup written to $DEST"
    exit 0
  fi
fi

# Whole-cache single archive.
OUT="$DEST/nba_cache_${STAMP}.tar"
echo "archiving $CACHE_DIR ($(human "$CACHE_DIR")) -> $OUT ..."
tar -cf "$OUT" -C "$CACHE_PARENT" "$CACHE_NAME"
echo "done: $OUT  ($(human "$OUT"))"
echo "restore with:  tar -xf '$OUT' -C '$CACHE_PARENT'"
