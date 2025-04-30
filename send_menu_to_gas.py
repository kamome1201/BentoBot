import requests

# GAS WebアプリのURL（あなたのデプロイURLに差し替えてください）
GAS_URL = "https://script.google.com/a/macros/nig.ac.jp/s/AKfycbwyJ4NiCV8rKNPk1AtAEhplN2ywofLrZM79062-NKRJTXoTGgarPHUw1A4PwK3igQ/exec"

# スクレイピングして得られたメニュー情報の例
menu_data = [
    {"name": "ヘルシー弁当", "price": 450},
    {"name": "デラックス弁当", "price": 550},
    {"name": "贅沢弁当", "price": 750},
]

# GASにPOSTで送信
response = requests.post(GAS_URL, json=menu_data)

# 結果確認
if response.status_code == 200:
    print("送信成功")
    print(response.text)
else:
    print(f"送信失敗: {response.status_code}")
    print(response.text)
