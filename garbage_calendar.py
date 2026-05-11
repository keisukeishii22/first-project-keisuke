#!/usr/bin/env python3
"""
清美カレンダーとNavi-ChanスクールをGoogleカレンダーに自動登録するスクリプト
2025年7月～2026年6月のごみ収集日と2026年4月～2027年3月の学校行事を登録
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
    'oversized': '8',          # グレー - 粗大ごみ
    'school_event': '9'        # 赤 - 学校行事
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

# 北子安小学校 2026年度（令和8年度）主な行事
# 長男（悠誠）の学校行事
school_events = [
    # 4月
    (2026, 4, 8, '着任式・始業式', '北子安小学校'),
    (2026, 4, 9, '入学式', '北子安小学校'),
    (2026, 4, 24, '授業参観・学級懇談会・PTA総会', '北子安小学校'),

    # 5月
    (2026, 5, 16, '奉仕作業（低学年保護者）', '北子安小学校'),
    (2026, 5, 27, '運動会', '北子安小学校'),

    # 6月
    (2026, 6, 19, '奉仕作業（高学年保護者）', '北子安小学校'),

    # 7月
    (2026, 7, 18, '1学期終業式', '北子安小学校'),

    # 8月
    (2026, 8, 20, '夏季休業終了', '北子安小学校'),

    # 8月29日は2学期始業式だが、8月20日から夏季休業が終わる
    (2026, 8, 29, '2学期始業式（給食開始）', '北子安小学校'),

    # 10月
    (2026, 10, 18, '北子安地区運動会', '北子安小学校'),

    # 12月
    (2026, 12, 23, '2学期終業式', '北子安小学校'),

    # 1月
    (2027, 1, 7, '3学期始業式（給食開始）', '北子安小学校'),

    # 2月
    (2027, 2, 16, '卒業証書授与式', '北子安小学校'),

    # 3月
    (2027, 3, 23, '修了式・離任式', '北子安小学校'),
]

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

    total_events = 0

    # ごみ収集日をGoogleカレンダーに追加
    print("\nごみ収集日をGoogleカレンダーに追加中...")
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

    # 学校行事をGoogleカレンダーに追加
    print("\n学校行事をGoogleカレンダーに追加中...")
    for year, month, day, title, description in school_events:
        try:
            # 日付オブジェクトを作成
            date = datetime(year, month, day).date()

            # イベントを作成
            full_title = f"【北子安小学校】{title}"
            create_event(service, full_title, description, date)
            total_events += 1

            print(f"✓ {date} - {full_title}")

        except Exception as e:
            print(f"ERROR: {year}年{month}月{day}日の学校行事「{title}」の作成に失敗: {e}")

    print(f"\n完了! 合計 {total_events} 個のイベントを追加しました。")

if __name__ == '__main__':
    main()
