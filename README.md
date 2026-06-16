# first-project-keisuke

石善建設(南房総の工務店・3代目 圭佑)の **note×Instagram 連動 週次コンテンツ生成体制**。

## ファイル構成

- `CLAUDE.md` — 運用ルール(Claude Code が常に参照)
- `12週テーママップ.md` — 12週分のテーマ×4展開(note/リール/カルーセル/ストーリーズ)
- `自動運用ルーティーン.md` — 指示がなくても週次で動く手順と起動方法
- `進捗メモ.md` — 生成ログと KPI 記録欄
- `生成物/第N週/` — 各週の生成物(note記事・リール台本・カルーセル構成・ストーリーズ告知)
- `.github/workflows/weekly-content.yml` — 毎週日曜にコンテンツを自動生成する GitHub Actions
- `Googleドライブ同期.gs` — 生成物を Google ドライブへ自動コピーする Apps Script
- `.claude/` — SessionStart フック(ルーティーン自動認識)

## 自動化の全体像

1. **生成**:GitHub Actions が毎週日曜に次の週のコンテンツを生成し `生成物/第N週/` に保存
2. **ドライブ保存**:Google Apps Script(`Googleドライブ同期.gs`)が GitHub の生成物を
   Google ドライブ「石善建設_note×Instagram運用」へ Google ドキュメントとしてコピー

## 毎週の使い方

インタビュー回答を添えてこう打つだけ:

> 第N週のテーマパックを生成。インタビュー回答:①(エピソード)②(感情が動いた瞬間)③(読者への持ち帰り)

指示なしで毎週自動生成するには `自動運用ルーティーン.md` の「起動方法」を参照。
