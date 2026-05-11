#!/usr/bin/env python3
"""
清美カレンダーをGoogleカレンダーに自動登録するスクリプト
2025年7月～2026年6月のごみ収集日を登録
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, time
import json

# Google Calendar APIの認証スコープ
SCOPES = ['https://www.googleapis.com/auth/calendar']

# カレンダーの色ID (オプション)
COLORS = {
    'non_flammable': '1',      # 青 - 不燃・有害ごみ
    'cans_bottles': '2',       # 緑 - 空き缶・びん
    'paper_textiles': '5',     # 黄 - 段ボール
    'other_plastic': '6',      # オレンジ - ペットボトル
    'oversized': '8'           # グレー - 粗大ごみ
}

# 2025年7月～2026年6月のごみ収集日
# 画像から読み取った北千葉地区のスケジュール
garbage_schedule = {
    (2025, 7): {
        'non_flammable': [2, 9, 16, 23, 30],
        'cans_bottles': [1, 8, 15, 22, 29],
        'paper_textiles': [3, 10, 17, 24, 31],
        'other_plastic': [4, 11, 18, 25],
        'oversized': [5, 12, 19, 26]
    },
    (2025, 8): {
        'non_flammable': [6, 13, 20, 27],
        'cans_bottles': [5, 12, 19, 26],
        'paper_textiles': [7, 14, 21, 28],
        'other_plastic': [1, 8, 15, 22, 29],
        'oversized': [2, 9, 16, 23, 30]
    },
    (2025, 9): {
        'non_flammable': [3, 10, 17, 24],
        'cans_bottles': [2, 9, 16, 23, 30],
        'paper_textiles': [4, 11, 18, 25],
        'other_plastic': [5, 12, 19, 26],
        'oversized': [6, 13, 20, 27]
    },
    (2025, 10): {
        'non_flammable': [1, 8, 15, 22, 29],
        'cans_bottles': [7, 14, 21, 28],
        'paper_textiles': [2, 9, 16, 23, 30],
        'other_plastic': [3, 10, 17, 24, 31],
        'oversized': [4, 11, 18, 25]
    },
    (2025, 11): {
        'non_flammable': [5, 12, 19, 26],
        'cans_bottles': [4, 11, 18, 25],
        'paper_textiles': [6, 13, 20, 27],
        'other_plastic': [7, 14, 21, 28],
        'oversized': [1, 8, 15, 22, 29]
    },
    (2025, 12): {
        'non_flammable': [3, 10, 17, 24, 31],
        'cans_bottles': [2, 9, 16, 23, 30],
        'paper_textiles': [4, 11, 18, 25],
        'other_plastic': [5, 12, 19, 26],
        'oversized': [6, 13, 20, 27]
    },
    (2026, 1): {
        'non_flammable': [7, 14, 21, 28],
        'cans_bottles': [6, 13, 20, 27],
        'paper_textiles': [1, 8, 15, 22, 29],
        'other_plastic': [2, 9, 16, 23, 30],
        'oversized': [3, 10, 17, 24, 31]
    },
    (2026, 2): {
        'non_flammable': [4, 11, 18, 25],
        'cans_bottles': [3, 10, 17, 24],
        'paper_textiles': [5, 12, 19, 26],
        'other_plastic': [6, 13, 20, 27],
        'oversized': [7, 14, 21, 28]
    },
    (2026, 3): {
        'non_flammable': [4, 11, 18, 25],
        'cans_bottles': [3, 10, 17, 24, 31],
        'paper_textiles': [5, 12, 19, 26],
        'other_plastic': [6, 13, 20, 27],
        'oversized': [7, 14, 21, 28]
    },
    (2026, 4): {
        'non_flammable': [1, 8, 15, 22, 29],
        'cans_bottles': [7, 14, 21, 28],
        'paper_textiles': [2, 9, 16, 23, 30],
        'other_plastic': [3, 10, 17, 24],
        'oversized': [4, 11, 18, 25]
    },
    (2026, 5): {
        'non_flammable': [6, 13, 20, 27],
        'cans_bottles': [5, 12, 19, 26],
        'paper_textiles': [7, 14, 21, 28],
        'other_plastic': [1, 8, 15, 22, 29],
        'oversized': [2, 9, 16, 23, 30]
    },
    (2026, 6): {
        'non_flammable': [3, 10, 17, 24],
        'cans_bottles': [2, 9, 16, 23, 30],
        'paper_textiles': [4, 11, 18, 25],
        'other_plastic': [5, 12, 19, 26],
        'oversized': [6, 13, 20, 27]
    }
}

# ごみの種類と説明
garbage_names = {
    'non_flammable': '【不燃・有害ごみ】',
    'cans_bottles': '【空き缶・びん】',
    'paper_textiles': '【段ボール】',
    'other_plastic': '【ペットボトル】',
    'oversized': '【粗大ごみ】'
}

def authenticate():
    """Google Calendar APIで認証"""
    creds = None

    # 既存の認証情報を読み込む
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 認証情報が有効でない場合は新しく取得
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.jsonが必要です（下記参照）
            if not os.path.exists('credentials.json'):
                print("ERROR: credentials.jsonが見つかりません")
                print("以下の手順でGoogle Calendar APIの認証ファイルを取得してください:")
                print("1. https://console.cloud.google.com/ にアクセス")
                print("2. 新しいプロジェクトを作成")
                print("3. Google Calendar APIを有効化")
                print("4. OAuth 2.0認証情報を作成（デスクトップアプリ）")
                print("5. JSONをダウンロードして、このファイルと同じフォルダにcredentials.jsonとして保存")
                exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 認証情報をキャッシュ
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def create_event(service, title, description, date):
    """イベントを作成"""
    event = {
        'summary': title,
        'description': description,
        'start': {
            'date': date.isoformat(),
        },
        'end': {
            'date': date.isoformat(),
        },
        'transparency': 'transparent',
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return event

def main():
    """メイン処理"""
    print("Googleカレンダーを認証中...")
    creds = authenticate()

    print("Google Calendar APIサービスを構築中...")
    service = build('calendar', 'v3', credentials=creds)

    print("ごみ収集日をGoogleカレンダーに追加中...")

    total_events = 0

    for (year, month), types in garbage_schedule.items():
        for garbage_type, days in types.items():
            for day in days:
                try:
                    # 日付オブジェクトを作成
                    date = datetime(year, month, day).date()

                    # イベントのタイトルと説明
                    title = garbage_names[garbage_type]
                    description = f"{year}年{month}月{day}日のごみ収集日"

                    # イベントを作成
                    create_event(service, title, description, date)
                    total_events += 1

                    print(f"✓ {date} - {title}")

                except Exception as e:
                    print(f"ERROR: {year}年{month}月{day}日のイベント作成に失敗: {e}")

    print(f"\n完了! 合計 {total_events} 個のイベントを追加しました。")

if __name__ == '__main__':
    main()
