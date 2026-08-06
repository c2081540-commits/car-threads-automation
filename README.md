# car-threads-automation

車アカウント専用のThreads予約投稿システムです。Kai側とはコード、認証情報、予約、画像、投稿履歴を共有しません。

## 初期設定

GitHub Actions Secretsに`THREADS_USER_ID`と`THREADS_ACCESS_TOKEN`を登録し、Variablesに`AUTO_PUBLISH=false`を登録します。最初は`verify`で接続確認し、テスト投稿確認後だけ`AUTO_PUBLISH=true`へ変更します。

## 投稿データ

`data/content_queue.json`へ予約を追加します。完成画像は`generated/weeks/対象週/`へ置きます。投稿番号は`CAR-001`形式、画像名は`YYYYMMDD_HHMM_CAR-001_任意名.png`、画像寸法は1080×1350pxです。

空の予約データは正常です。予約を追加すると、同一日時枠、投稿番号、キー、画像名、画像寸法をActionsが検査します。
