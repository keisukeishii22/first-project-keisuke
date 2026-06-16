/**
 * 石善建設 note×Instagram 週次コンテンツ
 * GitHub の「生成物/第N週/」を Google ドライブに自動コピーする Apps Script。
 *
 * 仕組み:
 *   公開リポジトリ keisukeishii22/first-project-keisuke の各週の Markdown を
 *   raw.githubusercontent.com から直接読み取り、Google ドキュメントとして
 *   ドライブの保存先フォルダに作成する(すでに作成済みのものはスキップ)。
 *   GitHub API は使わない(Apps Script の共有IPでは回数制限403に当たりやすいため)。
 *   ID・シークレット・トークンは不要(Apps Script が本人として動くため)。
 *
 * 使い方:
 *   1. script.google.com で新規プロジェクトを作り、このコードを丸ごと貼り付ける
 *   2. 関数の選択で「setup」を選び、実行 ▷ を押す
 *   3. 初回だけ Google の許可画面が出るので「許可」する
 *      (「このアプリは確認されていません」と出たら → 詳細 → 安全でないページに移動)
 *   4. これで毎週日曜 朝に自動でドライブへコピーされる(初回分も即コピーされる)
 */

// ===== 設定 =====
var GITHUB_OWNER = 'keisukeishii22';
var GITHUB_REPO = 'first-project-keisuke';
var GITHUB_BRANCH = 'main';
var CONTENT_ROOT = '生成物';                       // リポジトリ内の親フォルダ名
var DRIVE_PARENT_ID = '1LWfpH_93k6aaeQvRukRUvUdkoWaV4-0q'; // 「石善建設_note×Instagram運用」フォルダID
var FILE_STEMS = ['note記事', 'リール台本', 'カルーセル構成', 'ストーリーズ告知']; // 各週の固定ファイル名
var MAX_WEEKS = 16;                                // 1週目から何週目まで探すか(12週+予備)

/**
 * 初回セットアップ:週次トリガーを登録し、すぐに1回同期する。
 * このプロジェクトでは最初に一度だけ実行すればよい。
 */
function setup() {
  // 既存の同名トリガーを消してから登録(重複防止)
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncToDrive') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('syncToDrive')
    .timeBased()
    .everyWeeks(1)
    .onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(10) // 日曜 10時台(JST)。GitHub生成(9時)の後に動かす
    .create();

  Logger.log('週次トリガーを登録しました。続けて初回同期を実行します。');
  syncToDrive();
}

/**
 * GitHub の「生成物/第N週/」をすべてドライブへ同期する。
 * 週次トリガーから自動で呼ばれる。
 */
function syncToDrive() {
  var parent = DriveApp.getFolderById(DRIVE_PARENT_ID);
  var created = 0;
  var emptyStreak = 0; // 連続で1ファイルも無かった週数

  for (var n = 1; n <= MAX_WEEKS; n++) {
    var weekName = '第' + n + '週';
    var weekFolder = null;
    var foundThisWeek = 0;

    FILE_STEMS.forEach(function (stem) {
      var text = fetchRaw(CONTENT_ROOT + '/' + weekName + '/' + stem + '.md');
      if (text === null) return;            // その週にそのファイルが無い
      foundThisWeek++;

      if (!weekFolder) weekFolder = getOrCreateFolder(parent, weekName);
      var docName = weekName + '_' + stem;  // 例:第3週_note記事
      if (weekFolder.getFilesByName(docName).hasNext()) return; // 既存はスキップ

      createGoogleDoc(weekFolder, docName, text);
      created++;
      Logger.log('作成: ' + weekName + '/' + docName);
    });

    // 何週か連続で空なら、それ以降は未生成とみなして打ち切る
    emptyStreak = foundThisWeek === 0 ? emptyStreak + 1 : 0;
    if (emptyStreak >= 2) break;
  }

  Logger.log('同期完了。新規作成 ' + created + ' 件。');
}

// ===== 補助関数 =====

/** raw.githubusercontent.com からファイル本文を取得する。無ければ null。 */
function fetchRaw(path) {
  var encoded = path.split('/').map(encodeURIComponent).join('/');
  var url = 'https://raw.githubusercontent.com/' + GITHUB_OWNER + '/' +
    GITHUB_REPO + '/' + GITHUB_BRANCH + '/' + encoded;
  var res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  return res.getResponseCode() === 200 ? res.getContentText() : null;
}

/** 親フォルダ直下の同名フォルダを取得、無ければ作成する。 */
function getOrCreateFolder(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

/** テキストから Google ドキュメントを作り、指定フォルダに格納する。 */
function createGoogleDoc(folder, name, text) {
  var doc = DocumentApp.create(name);
  doc.getBody().setText(text);
  doc.saveAndClose();
  var file = DriveApp.getFileById(doc.getId());
  folder.addFile(file);
  DriveApp.getRootFolder().removeFile(file); // マイドライブ直下から除く
}
