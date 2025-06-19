import json
import re
from deep_translator import GoogleTranslator

MENU_FILE = "static/menu_today.json"

def convert_price_to_en(price):
    m = re.match(r"(\d+)\s*円", price)
    if m:
        return f"{m.group(1)} yen"
    return price

def main():
    translator = GoogleTranslator(source="ja", target="en")

    with open(MENU_FILE, encoding="utf-8") as f:
        menu = json.load(f)

    updated = False
    for item in menu:
        if "name" in item and not item.get("name_en"):
            try:
                item["name_en"] = translator.translate(item["name"])
                print(f"Translated: {item['name']} → {item['name_en']}")
                updated = True
            except Exception as e:
                print(f"Translation failed for {item['name']}: {e}")
        if "price" in item and not item.get("price_en"):
            item["price_en"] = convert_price_to_en(item["price"])
            if item["price"] != item["price_en"]:
                print(f"Converted: {item['price']} → {item['price_en']}")
                updated = True

    if updated:
        with open(MENU_FILE, "w", encoding="utf-8") as f:
            json.dump(menu, f, ensure_ascii=False, indent=2)
        print("✅ name_en, price_en fields have been added and saved!")
    else:
        print("No untranslated items found.")

if __name__ == "__main__":
    main()
