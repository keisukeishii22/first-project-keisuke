/**
 * 石善建設 note×Instagram 週次コンテンツ
 * GitHub の「生成物/第N週/」を Google ドライブに自動コピーする Apps Script。
 *
 * 仕組み:
 *   公開リポジトリ keisukeishii22/first-project-keisuke の「生成物」フォルダを
 *   GitHub の公開API経由で読み取り、各週の Markdown を Google ドキュメントとして
 *   ドライブの保存先フォルダに作成する(すでに作成済みのものはスキップ)。
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
  var weeks = listGitHubDir(CONTENT_ROOT); // 生成物 直下(第1週, 第2週, ...)
  var created = 0;

  weeks.forEach(function (week) {
    if (week.type !== 'dir') return;
    var weekName = week.name;                 // 例:第3週
    var weekFolder = getOrCreateFolder(parent, weekName);

    var files = listGitHubDir(CONTENT_ROOT + '/' + weekName);
    files.forEach(function (f) {
      if (f.type !== 'file' || !/\.md$/.test(f.name)) return;
      var docName = weekName + '_' + f.name.replace(/\.md$/, ''); // 例:第3週_note記事
      if (weekFolder.getFilesByName(docName).hasNext()) return;   // 既存はスキップ

      var text = UrlFetchApp.fetch(f.download_url).getContentText();
      createGoogleDoc(weekFolder, docName, text);
      created++;
      Logger.log('作成: ' + weekName + '/' + docName);
    });
  });

  Logger.log('同期完了。新規作成 ' + created + ' 件。');
}

// ===== 補助関数 =====

/** GitHub 公開APIで指定パスの中身一覧を取得する。 */
function listGitHubDir(path) {
  var encoded = path.split('/').map(encodeURIComponent).join('/');
  var url = 'https://api.github.com/repos/' + GITHUB_OWNER + '/' + GITHUB_REPO +
    '/contents/' + encoded + '?ref=' + GITHUB_BRANCH;
  var res = UrlFetchApp.fetch(url, {
    headers: { 'User-Agent': 'gas-ishizen', 'Accept': 'application/vnd.github+json' },
    muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log('GitHub取得に失敗 (' + res.getResponseCode() + '): ' + path);
    return [];
  }
  return JSON.parse(res.getContentText());
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
