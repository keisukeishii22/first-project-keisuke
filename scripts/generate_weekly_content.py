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


# 生成する4つの成果物の定義(キー, タイトル, 個別指示, 最大トークン数)
# note は石善建設HP用ブログとして本文6000〜8000字の長文を書くため、max_tokens を大きく取る。
# (16000 は非ストリーミングでも SDK のHTTPタイムアウトに収まる上限の目安)
DELIVERABLES = [
    ("note", "note記事下書き",
     "石善建設の公式サイト(HP)ブログに載せる読み物記事として、note記事の本文を作成してください。\n"
     "【文量】本文は6000〜8000文字。骨子や箇条書きだけで終わらせず、最後まで書き切った完成本文にすること。\n"
     "【体裁】HPブログらしい丁寧で読みやすい構成にする:\n"
     "  1. タイトル案3本(SEOを意識し、検索されやすい語を自然に含める)\n"
     "  2. リード文(300〜400字。読者の悩みに共感し、この記事で分かることを提示)\n"
     "  3. 目次(見出しの一覧)\n"
     "  4. 本文(## と ### の見出しで章立て。導入→本論→まとめの流れ。段落は3〜5文で改行し、"
     "必要に応じて箇条書き・比較表・チェックリストを使って読みやすくする)\n"
     "  5. まとめ(要点の再整理)\n"
     "  6. CTA(南房総エリアの相談・お問い合わせへ誘導)\n"
     "【トーン】1946年創業の工務店3代目・現場を知る専門家が、これから家を建てる/直す初心者に"
     "『損しない順番と判断』を正直に解説する語り口。煽らず、静かな説得力で。\n"
     "【固有名詞】取引先・チェーン名・契約詳細は伏せ、一般論＋体験談の形にする。"),
    ("reel", "リール台本2本",
     "リール台本を2本作成してください。各30〜45秒。フック→本編→CTA の構成。撮影場所の注記(事務所・倉庫・車内のみ)を添えること。"),
    ("carousel", "カルーセル構成案",
     "カルーセル構成案を作成してください。表紙+5枚+CTA の計7枚分。各ページの見出しと要点を箇条書きで。個人アカウント用。"),
    ("stories", "ストーリーズ告知文",
     "ストーリーズ告知文を作成してください。3〜4枚の連投。ティザー・本投稿告知・エンゲージ用(質問/アンケート)・フォロー誘導 の流れ。"),
]

# 成果物ごとの最大出力トークン数(note は長文HPブログのため大きめ)
MAX_TOKENS = {
    "note": 16000,
    "reel": 4096,
    "carousel": 4096,
    "stories": 4096,
}


def _build_prompt(week_num: int, week_theme: str, common_rules: str, instruction: str) -> str:
    return f"""あなたは石善建設(南房総の工務店・3代目 圭佑)の note×Instagram 連動コンテンツ担当です。

## 共通ルール(すべての生成物に適用)
{common_rules}

## 今週のテーマ(第{week_num}週)
{week_theme}

## 生成指示
インタビュー回答が未提供のため「素材待ちドラフト」として生成してください。
圭佑の実体験を入れる箇所は「【ここに実体験:〇〇】」で明示してください。
補助金・法令・税制・許可制度に数値や要件を書く場合は「公開前に一次情報で確認」と注記してください。
固有名詞(取引先・チェーン名・契約詳細)は伏せ、一般論＋体験談の形にしてください。

## 今回の成果物
{instruction}

成果物の本文のみを Markdown で出力してください(前置き・後書き・コードフェンスは不要)。"""


def generate_pack(client: anthropic.Anthropic, week_num: int, week_theme: str, common_rules: str) -> dict:
    """成果物ごとに個別の API 呼び出しを行い、セクション辞書で返す。

    1回にまとめるとトークン上限で末尾が切れるため、4回に分けて確実に生成する。
    """
    pack = {}
    for key, title, instruction in DELIVERABLES:
        print(f"  - {title} を生成中...")
        prompt = _build_prompt(week_num, week_theme, common_rules, instruction)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=MAX_TOKENS.get(key, 4096),
            messages=[{"role": "user", "content": prompt}],
        )
        # 長文がトークン上限で途中終了した場合に気づけるようにする
        if msg.stop_reason == "max_tokens":
            print(f"    ⚠️ {title}: max_tokens に達して途中で切れた可能性があります")
        pack[key] = msg.content[0].text.strip()
    return pack


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
