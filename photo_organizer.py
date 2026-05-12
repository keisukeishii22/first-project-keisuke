#!/usr/bin/env python3
"""
写真整理ツール
- 日付別フォルダに自動分類
- 重複写真の検出
- サイズ・枚数レポート出力
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".gif", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}


def get_exif_date(filepath: Path) -> datetime | None:
    """EXIFメタデータから撮影日時を取得する"""
    if not PILLOW_AVAILABLE:
        return None
    try:
        with Image.open(filepath) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
    return None


def get_file_date(filepath: Path) -> datetime:
    """ファイルの日付を取得する（EXIF優先、なければ更新日時）"""
    exif_date = get_exif_date(filepath)
    if exif_date:
        return exif_date
    return datetime.fromtimestamp(filepath.stat().st_mtime)


def compute_hash(filepath: Path) -> str:
    """ファイルのMD5ハッシュを計算する"""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_media_files(source_dir: Path) -> list[Path]:
    """指定ディレクトリ以下のメディアファイルを再帰的に収集する"""
    all_extensions = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS
    files = []
    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in all_extensions:
            files.append(path)
    return files


def organize_by_date(source_dir: Path, dest_dir: Path, dry_run: bool = False) -> dict:
    """日付別フォルダに写真・動画を整理する"""
    files = find_media_files(source_dir)
    stats = {"moved": 0, "skipped": 0, "errors": 0}

    for filepath in files:
        try:
            date = get_file_date(filepath)
            folder_name = date.strftime("%Y/%Y-%m")
            target_dir = dest_dir / folder_name
            target_path = target_dir / filepath.name

            # 同名ファイルが存在する場合はリネーム
            counter = 1
            while target_path.exists():
                stem = filepath.stem
                target_path = target_dir / f"{stem}_{counter}{filepath.suffix}"
                counter += 1

            if dry_run:
                print(f"[DRY RUN] {filepath} -> {target_path}")
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(filepath, target_path)
                print(f"移動: {filepath.name} -> {folder_name}/")

            stats["moved"] += 1
        except Exception as e:
            print(f"エラー: {filepath.name} - {e}")
            stats["errors"] += 1

    return stats


def find_duplicates(source_dir: Path) -> dict[str, list[Path]]:
    """重複ファイル（同一ハッシュ）を検出する"""
    files = find_media_files(source_dir)
    hash_map: dict[str, list[Path]] = defaultdict(list)

    print(f"{len(files)} 件のファイルをスキャン中...")
    for i, filepath in enumerate(files, 1):
        if i % 50 == 0:
            print(f"  {i}/{len(files)} 件処理済み")
        file_hash = compute_hash(filepath)
        hash_map[file_hash].append(filepath)

    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}


def print_report(source_dir: Path) -> None:
    """ディレクトリの写真・動画レポートを出力する"""
    files = find_media_files(source_dir)
    total_size = sum(f.stat().st_size for f in files)
    by_ext: dict[str, int] = defaultdict(int)
    for f in files:
        by_ext[f.suffix.lower()] += 1

    print("\n===== 写真・動画レポート =====")
    print(f"合計ファイル数 : {len(files)} 件")
    print(f"合計サイズ     : {total_size / (1024 ** 3):.2f} GB")
    print("\n--- 形式別内訳 ---")
    for ext, count in sorted(by_ext.items(), key=lambda x: -x[1]):
        print(f"  {ext:8s}: {count} 件")
    print("=" * 30)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="写真・動画整理ツール")
    subparsers = parser.add_subparsers(dest="command")

    # organize サブコマンド
    org_parser = subparsers.add_parser("organize", help="日付別フォルダに整理する")
    org_parser.add_argument("source", help="整理元ディレクトリ")
    org_parser.add_argument("dest", help="整理先ディレクトリ")
    org_parser.add_argument("--dry-run", action="store_true", help="実際には移動せず確認のみ")

    # duplicates サブコマンド
    dup_parser = subparsers.add_parser("duplicates", help="重複ファイルを検出する")
    dup_parser.add_argument("source", help="スキャン対象ディレクトリ")
    dup_parser.add_argument("--delete", action="store_true", help="重複ファイルを削除する（元ファイルを1つ残す）")

    # report サブコマンド
    rep_parser = subparsers.add_parser("report", help="ファイル数・サイズのレポートを表示する")
    rep_parser.add_argument("source", help="レポート対象ディレクトリ")

    args = parser.parse_args()

    if args.command == "organize":
        source = Path(args.source)
        dest = Path(args.dest)
        if not source.exists():
            print(f"エラー: ディレクトリが見つかりません: {source}")
            return
        stats = organize_by_date(source, dest, dry_run=args.dry_run)
        print(f"\n完了: {stats['moved']} 件移動, {stats['skipped']} 件スキップ, {stats['errors']} 件エラー")

    elif args.command == "duplicates":
        source = Path(args.source)
        if not source.exists():
            print(f"エラー: ディレクトリが見つかりません: {source}")
            return
        duplicates = find_duplicates(source)
        if not duplicates:
            print("重複ファイルは見つかりませんでした。")
            return
        total_wasted = 0
        print(f"\n重複グループ: {len(duplicates)} 件")
        for file_hash, paths in duplicates.items():
            size = paths[0].stat().st_size
            wasted = size * (len(paths) - 1)
            total_wasted += wasted
            print(f"\n  [{len(paths)} 件の重複] {size / 1024:.1f} KB 各")
            for p in paths:
                print(f"    {p}")
            if args.delete:
                for p in paths[1:]:
                    p.unlink()
                    print(f"    削除: {p}")
        print(f"\n節約できる容量: {total_wasted / (1024 ** 2):.1f} MB")

    elif args.command == "report":
        source = Path(args.source)
        if not source.exists():
            print(f"エラー: ディレクトリが見つかりません: {source}")
            return
        print_report(source)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
