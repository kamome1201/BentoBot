# 🍱 BentoBot

**BentoBot**は、研究室や職場のメンバーがネットワーク内Webページから簡単にお弁当注文・集計・自動発注・履歴管理まで一元化できる半自動注文システムです。

---

## 🚀 特徴

- **Web注文フォーム**（日本語／英語切り替え対応、固定メニュー＋Web取得メニュー）
- **注文内容はローカル保存・GitHub Issue自動記録・管理者用集計画面も標準搭載**
- **Web注文（スクレイピング）は即時自動発注、固定メニューは担当者メール集計通知も可**
- **職場ネットワーク限定公開（Flaskサーバ）、セキュリティも安心**
- **休日や特別日はカレンダー連動で自動メニュー切替**
- **設定は.envファイルで一元管理**

---

## 🗂️ ディレクトリ構成

```
BentoBot/
├── static/
│ ├── menu_today.json
│ ├── calendar_status.json
│ ├── orders.json
│ └── fixed_menu.json
├── templates/
│ ├── order.html
│ └── summary.html
├── webpage.py
├── process_orders.py
├── menu_today.py
├── fetch_calendar_status.py
├── send_fixed_menu_summary.py
├── close_old_issues.py
├── add_english_name_to_menu.py
├── requirements.txt
├── .env
└── README.md
```

---

## 🛠️ セットアップ手順

### 1. 依存パッケージのインストール

```
pip install -r requirements.txt
```


### 2. .envファイルの準備
.envのサンプル：

```
BENTO_EMAIL=your_bento_login@example.com
BENTO_PASSWORD=your_bento_password

GITHUB_TOKEN=ghp_xxxxxxx
REPO=kamome1201/BentoBot

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASS=your_email_password
FROM_ADDR=your_email@example.com
TO_ADDR=manager@example.com
```

### 3. 必要な静的ファイル（static/）・テンプレート（templates/）があるか確認
（なければ空ファイル・雛形でOK）

## 🌐 サーバ起動
```
python webpage.py
```
* 初回起動時は 0.0.0.0:8080 でLAN内全端末からアクセス可
* http://<サーバIP>:8080/order で注文フォーム表示

## 📦 主なスクリプトの役割
* webpage.py　…Flask本体、注文受付・管理画面表示

* menu_today.py　…Webスクレイピング＋固定メニュー統合（menu_today.json生成）

* process_orders.py　…注文履歴・自動GitHub連携・Web注文自動化

* fetch_calendar_status.py　…営業日・特別日カレンダー取得

* send_fixed_menu_summary.py　…固定メニュー注文の集計・担当者メール通知

* add_english_name_to_menu.py　…メニューの英語表記自動付与

* close_old_issues.py　…古い注文Issue自動クローズ

* requirements.txt　…依存パッケージリスト

## 🏁 運用Tips
* 管理者画面は /summary でアクセス可

* 注文失敗時はWeb画面にエラー表示＋GitHub Issueにorder-failedラベル＆コメントが自動付与

* cronやsystemdで定期実行することで完全自動運用も可

* .envは漏洩に注意し、.gitignoreに追加を推奨

* BentoBot自体のレポジトリもprivateにして、外部の人間がIssueに書き込めないようにしましょう

## 📝 ライセンス
MIT License

##👤 作者
kamome1201
（改変・再配布・質問も歓迎ですが、webスクレイピング部分を対象のお弁当屋さん向けにカスタマイズする等、かなりカスタマイズが必要になると思います。ごめんなさい）
