#!/usr/bin/env bash
# SessionStart hook: note×Instagram 週次コンテンツ生成ルーティーンの自動認識
# このリポジトリのセッション開始時に、未生成の週とルーティーン手順を Claude に伝える。

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROGRESS="$REPO_DIR/進捗メモ.md"

cat <<'EOF'
[週次コンテンツ運用ルーティーンが有効です]
このプロジェクトには note×Instagram 連動の週次自動生成ルーティーンがあります。
- ルール: 自動運用ルーティーン.md / CLAUDE.md / 12週テーママップ.md を参照。
- スケジュール起動(Scheduled session など)で呼ばれた場合、または圭佑から
  「週次ルーティンを実行」と言われた場合は、自動運用ルーティーン.md の手順に従い、
  未生成の最若番の週のテーマパックを生成 → 生成物/第N週/ に保存 → 進捗メモ.md を更新 →
  コミット&プッシュ → 報告、までを実行してください。
EOF

if [ -f "$PROGRESS" ]; then
  echo "--- 進捗メモ.md(生成ログ抜粋)---"
  grep -E "第[0-9]+週|生成ログ" "$PROGRESS" || true
fi
