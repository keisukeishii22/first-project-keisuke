#!/usr/bin/env bash
# SessionStart hook: note×Instagram 週次コンテンツ生成ルーティーンの自動認識
# このリポジトリのセッション開始時に、未生成の週とルーティーン手順を Claude に伝える。

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROGRESS="$REPO_DIR/進捗メモ.md"

cat <<'EOF'
[週次コンテンツ運用ルーティーンが有効です]
このプロジェクトには note×Instagram 連動の週次自動生成ルーティーンがあります。
- ルール: 自動運用ルーティーン.md / CLAUDE.md / 12週テーママップ.md / 文章スタイルガイド.md を参照。
- スケジュール起動(Scheduled session など)で呼ばれた場合、または圭佑から
  「週次ルーティンを実行」と言われた場合は、自動運用ルーティーン.md の手順に従い、
  まず生成ゲート(未公開ドラフトが3週分を超えていたら新規生成せず報告のみ)を通したうえで、
  未生成の最若番の週のテーマパックを生成 → 生成物/第N週/ に保存 → 進捗メモ.md を更新 →
  コミット&プッシュ → 報告、までを実行してください。
EOF

if [ -f "$PROGRESS" ]; then
  echo "--- 進捗メモ.md(生成ログ抜粋)---"
  grep -E "第[0-9]+週|生成ログ" "$PROGRESS" || true

  UNPUBLISHED=$(grep -E '^\|\s*第[0-9]+週' "$PROGRESS" | grep -c '未公開' || true)
  if [ "${UNPUBLISHED:-0}" -gt 3 ]; then
    echo ""
    echo "⚠️ 未公開ドラフトが ${UNPUBLISHED} 週分あります(基準:3週)。"
    echo "生成ゲートにより新規生成は停止中です。公開と未回答週のインタビュー回答を優先してください。"
  fi
fi
