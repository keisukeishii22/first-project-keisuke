#!/usr/bin/env bash
# SessionStart hook: note×Instagram 週次コンテンツ生成ルーティーンの自動認識
# このリポジトリのセッション開始時に、未生成の週とルーティーン手順を Claude に伝える。

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROGRESS="$REPO_DIR/進捗メモ.md"

cat <<'EOF'
[スケジュール運用の案内]
このリポジトリには複数のスケジュールタスク(週次パック素材回収・アフィリエイトnote・ブログ在庫番など)があります。
- スケジュール起動で呼ばれた場合は、起動時のプロンプトの指示に従ってください(このメッセージより優先)。
- 圭佑から「週次ルーティンを実行」と言われた場合は、自動運用ルーティーン.md の現行手順(素材回収型)に従ってください。
- 記録と成果物は Google Drive の「Claude自動運用ハブ」に保存し、スケジュール起動では git へのコミット・プッシュはしません。
- 最新プロンプトは スケジュールタスク設定/ を参照。
EOF

if [ -f "$PROGRESS" ]; then
  echo "--- 進捗メモ.md(生成ログ抜粋)---"
  grep -E "第[0-9]+週|生成ログ" "$PROGRESS" || true
fi
