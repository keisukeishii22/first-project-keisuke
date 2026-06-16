#!/usr/bin/env python3
"""
生成物/第N週/ の Markdown を Google ドライブにアップロードする。
GitHub Actions から、コンテンツ生成の直後に呼び出される。

認証は「ユーザー自身の OAuth リフレッシュトークン」で行う。
(サービスアカウントは個人 Gmail では容量制限で失敗するため使わない)

必要な環境変数(GitHub Secrets):
  GOOGLE_CLIENT_ID       OAuth クライアント ID
  GOOGLE_CLIENT_SECRET   OAuth クライアントシークレット
  GOOGLE_REFRESH_TOKEN   リフレッシュトークン
  GDRIVE_FOLDER_ID       保存先の親フォルダ ID(石善建設_note×Instagram運用)

これらが未設定の場合は、何もせず正常終了する(Drive 連携は任意)。
"""

import os
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).parent.parent
TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"
DOC_MIME = "application/vnd.google-apps.document"


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def find_or_create_folder(token: str, name: str, parent_id: str) -> str:
    """親フォルダ内の同名サブフォルダを探し、無ければ作成して ID を返す。"""
    headers = {"Authorization": f"Bearer {token}"}
    safe_name = name.replace("'", "\\'")
    q = (
        f"name = '{safe_name}' and '{parent_id}' in parents "
        f"and mimeType = '{FOLDER_MIME}' and trashed = false"
    )
    resp = httpx.get(
        DRIVE_FILES_URL,
        headers=headers,
        params={"q": q, "fields": "files(id,name)"},
        timeout=30,
    )
    resp.raise_for_status()
    files = resp.json().get("files", [])
    if files:
        return files[0]["id"]

    resp = httpx.post(
        DRIVE_FILES_URL,
        headers=headers,
        json={"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def find_existing_doc(token: str, name: str, parent_id: str) -> str | None:
    headers = {"Authorization": f"Bearer {token}"}
    safe_name = name.replace("'", "\\'")
    q = f"name = '{safe_name}' and '{parent_id}' in parents and trashed = false"
    resp = httpx.get(
        DRIVE_FILES_URL,
        headers=headers,
        params={"q": q, "fields": "files(id,name)"},
        timeout=30,
    )
    resp.raise_for_status()
    files = resp.json().get("files", [])
    return files[0]["id"] if files else None


def upload_doc(token: str, name: str, text: str, parent_id: str) -> None:
    """テキストを Google ドキュメントとしてアップロード(同名があれば更新)。"""
    existing = find_existing_doc(token, name, parent_id)
    metadata = {"name": name, "mimeType": DOC_MIME}
    if not existing:
        metadata["parents"] = [parent_id]

    boundary = "----ishizen-drive-boundary"
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{__import__('json').dumps(metadata, ensure_ascii=False)}\r\n"
        f"--{boundary}\r\n"
        "Content-Type: text/plain; charset=UTF-8\r\n\r\n"
        f"{text}\r\n"
        f"--{boundary}--"
    ).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/related; boundary={boundary}",
    }

    if existing:
        url = f"{DRIVE_UPLOAD_URL}/{existing}?uploadType=multipart"
        resp = httpx.patch(url, headers=headers, content=body, timeout=60)
    else:
        url = f"{DRIVE_UPLOAD_URL}?uploadType=multipart"
        resp = httpx.post(url, headers=headers, content=body, timeout=60)
    resp.raise_for_status()


def main() -> None:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    parent_id = os.environ.get("GDRIVE_FOLDER_ID")

    if not all([client_id, client_secret, refresh_token, parent_id]):
        print("Drive 連携の Secrets が未設定のため、アップロードをスキップします。")
        return

    week_file = REPO_ROOT / ".week_number"
    if not week_file.exists():
        print(".week_number が無いためスキップします。")
        return
    week_num = week_file.read_text().strip()
    if not week_num or week_num == "0":
        print("生成された週がないためスキップします。")
        return

    src_dir = REPO_ROOT / f"生成物/第{week_num}週"
    if not src_dir.is_dir():
        print(f"{src_dir} が無いためスキップします。")
        return

    print(f"第{week_num}週のファイルを Google ドライブにアップロード中...")
    token = get_access_token(client_id, client_secret, refresh_token)
    week_folder = find_or_create_folder(token, f"第{week_num}週", parent_id)

    for md_path in sorted(src_dir.glob("*.md")):
        doc_name = f"第{week_num}週_{md_path.stem}"
        text = md_path.read_text(encoding="utf-8")
        upload_doc(token, doc_name, text, week_folder)
        print(f"  - {doc_name} をアップロードしました")

    print("✅ Google ドライブへのアップロード完了")


if __name__ == "__main__":
    main()
