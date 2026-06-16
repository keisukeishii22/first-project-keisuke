#!/usr/bin/env python3
"""
石善建設 note×Instagram 週次コンテンツ自動生成スクリプト
毎週日曜に GitHub Actions から呼び出される。
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).parent.parent


def get_next_week_number(memo: str) -> int:
    """進捗メモの生成ログから、次に生成すべき週番号を返す。"""
    generated = set()
    for line in memo.splitlines():
        m = re.match(r'\|\s*第(\d+)週\s*\|', line)
        if m:
            generated.add(int(m.group(1)))
    return max(generated) + 1 if generated else 1


def extract_week_section(theme_map: str, week_num: int) -> str:
    """12週テーママップから指定週のセクションを抽出する。"""
    pattern = rf'(## 第{week_num}週:.+?)(?=\n## 第\d+週:|\n---|\Z)'
    m = re.search(pattern, theme_map, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_common_rules(theme_map: str) -> str:
    """共通ルールセクションを抽出する。"""
    m = re.search(r'## 共通ルール(.+?)(?=\n## 第1週:)', theme_map, re.DOTALL)
    return m.group(1).strip() if m else ""


def generate_pack(client: anthropic.Anthropic, week_num: int, week_theme: str, common_rules: str) -> dict:
    """Claude API を呼び出してテーマパック4点を生成し、セクション辞書で返す。"""
    prompt = f"""あなたは石善建設(南房総の工務店・3代目 圭佑)の note×Instagram 連動コンテンツ担当です。

## 共通ルール(すべての生成物に適用)
{common_rules}

## 今週のテーマ(第{week_num}週)
{week_theme}

## 生成指示
インタビュー回答が未提供のため「素材待ちドラフト」として生成してください。
圭佑の実体験を入れる箇所は「【ここに実体験:〇〇】」で明示してください。
補助金・法令・税制・許可制度に数値や要件を書く場合は「公開前に一次情報で確認」と注記してください。
固有名詞(取引先・チェーン名・契約詳細)は伏せ、一般論＋体験談の形にしてください。

以下の区切り記号を必ず使い、4つのセクションを順番に出力してください:

===NOTE_START===
(note記事下書き: タイトル案3本・リード文・本文構成・CTA・共通ルール適合チェックリスト)
===NOTE_END===

===REEL_START===
(リール台本2本: 各30〜45秒。フック→本編→CTA。撮影場所の注記あり)
===REEL_END===

===CAROUSEL_START===
(カルーセル構成案: 表紙+5枚+CTA)
===CAROUSEL_END===

===STORIES_START===
(ストーリーズ告知文: 3〜4枚の連投。ティザー・本投稿告知・エンゲージ用・フォロー誘導)
===STORIES_END===
"""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text

    def extract(start_tag: str, end_tag: str) -> str:
        m = re.search(rf'{re.escape(start_tag)}(.+?){re.escape(end_tag)}', text, re.DOTALL)
        return m.group(1).strip() if m else text

    return {
        "note":     extract("===NOTE_START===",     "===NOTE_END==="),
        "reel":     extract("===REEL_START===",     "===REEL_END==="),
        "carousel": extract("===CAROUSEL_START===", "===CAROUSEL_END==="),
        "stories":  extract("===STORIES_START===",  "===STORIES_END==="),
    }


def write_files(week_num: int, pack: dict, today: str) -> None:
    """生成物/第N週/ 配下に4ファイルを書き出す。"""
    out_dir = REPO_ROOT / f"生成物/第{week_num}週"
    out_dir.mkdir(parents=True, exist_ok=True)

    draft_notice = (
        f"# 第{week_num}週 テーマパック({today} 自動生成)\n\n"
        "> ⚠️ 素材待ちドラフト。`【ここに実体験:〇〇】` の箇所に圭佑の実体験(数字・情景・セリフ)を追記し、"
        "ファクトチェックのうえ投稿してください。\n\n"
    )

    (out_dir / "note記事.md").write_text(draft_notice + pack["note"],     encoding="utf-8")
    (out_dir / "リール台本.md").write_text(draft_notice + pack["reel"],   encoding="utf-8")
    (out_dir / "カルーセル構成.md").write_text(draft_notice + pack["carousel"], encoding="utf-8")
    (out_dir / "ストーリーズ告知.md").write_text(draft_notice + pack["stories"], encoding="utf-8")


def update_progress_memo(week_num: int, today: str) -> None:
    """進捗メモ.md の生成ログ表に1行追記する。"""
    path = REPO_ROOT / "進捗メモ.md"
    content = path.read_text(encoding="utf-8")

    new_row = f"| 第{week_num}週 | {today} | 素材待ちドラフト生成済み | インタビュー回答到着後に実体験を肉付け |\n"

    # テーブルのヘッダー区切り行の直後に挿入
    sep_pattern = r'(\| 週 \|.+?\n\|[-| ]+\n)'
    m = re.search(sep_pattern, content, re.DOTALL)
    if m:
        pos = m.end()
        content = content[:pos] + new_row + content[pos:]
    else:
        content += "\n" + new_row

    path.write_text(content, encoding="utf-8")


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    today = date.today().isoformat()

    theme_map  = (REPO_ROOT / "12週テーママップ.md").read_text(encoding="utf-8")
    memo       = (REPO_ROOT / "進捗メモ.md").read_text(encoding="utf-8")

    week_num = get_next_week_number(memo)

    if week_num > 12:
        print("12週すべて生成済みです。スキップします。")
        Path(".week_number").write_text("0")
        return

    print(f"第{week_num}週のテーマパックを生成中...")

    week_theme   = extract_week_section(theme_map, week_num)
    common_rules = extract_common_rules(theme_map)

    if not week_theme:
        print(f"Error: 第{week_num}週のテーマが見つかりません", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    pack   = generate_pack(client, week_num, week_theme, common_rules)

    write_files(week_num, pack, today)
    update_progress_memo(week_num, today)

    # ワークフローのコミットメッセージ用
    Path(".week_number").write_text(str(week_num))

    print(f"✅ 第{week_num}週パック生成完了 → 生成物/第{week_num}週/")


if __name__ == "__main__":
    main()
