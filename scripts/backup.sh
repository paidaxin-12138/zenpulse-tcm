#!/usr/bin/env bash
# 备份运行时数据与向量索引（不含模型权重）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="${1:-$ROOT/backups/tcm-backup-$STAMP}"

mkdir -p "$DEST"

for item in data tcm_knowledge vector_store; do
  src="$ROOT/$item"
  if [[ -d "$src" || -f "$src" ]]; then
    cp -a "$src" "$DEST/"
    echo "  + $item"
  fi
done

echo "Backup complete: $DEST"
