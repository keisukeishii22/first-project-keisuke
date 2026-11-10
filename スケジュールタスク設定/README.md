# スケジュールタスク設定(2026-11-10 見直し)

4つのスケジュールタスクの最新プロンプトを置く。タスクのプロンプトは Claude のセッションからは書き換えられないため、**圭佑さんが各タスクの編集画面でプロンプト欄を全文入れ替える**。今後プロンプトを直すときも、ここのファイルを更新してから貼り替える。

| タスク(現在の名前) | 貼り付けるファイル | 編集画面 | あわせて変える設定 |
|---|---|---|---|
| 記事作成(日曜) | `1_日曜_週次パック素材回収.md` | https://claude.ai/code/routines/trig_01294shuUHUWBBLK3AK3rSvo | コネクタは Google Drive と Gmail だけ残す(Canva・カレンダーは外す) |
| note記事作成(月曜) | `2_月曜_note記事作成.md` | https://claude.ai/code/routines/trig_01PWjGndsxdyqGYqcXvhLn8m | 変更なし |
| 石善建設ブログ 在庫番 | `3_月2回_ブログ在庫番.md` | https://claude.ai/code/routines/trig_015xKg8Hm2MpdzkYDvdPnSpj | モデルを最新の Sonnet に変更。コネクタは Google Drive と Gmail だけ残す |
| 日本株デイトレ 朝7時レポート | `4_平日朝_日本株レポート.md` | https://claude.ai/code/routines/trig_01JvBwPHMVgyQBucegVKKUXw | 下の注記を参照 |

## 日本株レポートの注記

現在のタスクは、7月から同じ会話に毎朝書き足す設定で、Google Drive もつながっていない。おすすめは、編集画面から**新しいタスクとして作り直す**こと(毎回新しいセッション、Google Drive コネクタあり、プッシュ通知オン、平日 7:00 JST)。作り直したら古いタスクをオフにする。作り直さない場合は、今の会話で「プロンプトをこのファイルの内容に変えて」と依頼すれば、答え合わせと休場日スキップだけは反映できる。

## 記録の置き場所

タスクの記録は Google Drive の「Claude自動運用ハブ」に集約する(GitHub のブランチには書かない)。

- ハブ:https://drive.google.com/drive/folders/1NPuWj05Or4fiiaVxr_VTNAQtzZqcsXt5
- 【圭佑さん記入】運用ステータス:https://docs.google.com/document/d/1_XDBUat6hzSYenowPDwm978AxCzy27FOFM6enw0Ynic/edit
  - 公開状況と「タスクへの追加指示」を書く。全タスクが毎回最初に読む。
  - タスクに「今後はこうして」と伝えたいときは、会話で頼むのではなくここに1行書く(各回は新しいセッションで動くため、会話での依頼は次回に残らない)。

## 環境(Default)の設定

- 許可ホスト:メイン4市・第二メイン3市・千葉県・国交省・国民生活センター・e-Gov・経産省・国税庁・法務省・消費者庁・環境省・JPX を追加済み(2026-11-10)。
- WordPress の認証:ネットワークシークレット(ishizenkensetsu.com)として保存。プロンプトにパスワードは書かない。
