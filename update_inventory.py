import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

URLS = {
    "New": "https://www.parkslincoln.com/new-inventory/index.htm",
    "Pre-Owned": "https://www.parkslincoln.com/used-inventory/index.htm",
}


def parse_inventory():
  inventory = []

  for category, url in URLS.items():
    try:
      resp = requests.get(url, headers=HEADERS, timeout=15)
      soup = BeautifulSoup(resp.text, "html.parser")
      items = soup.select(".item, .vehicle-card, .inventory-item")

      for item in items:
        title = item.select_one(".title, .vehicle-title, h2, h3")
        title_text = title.get_text(strip=True) if title else "Lincoln Vehicle"

        price = item.select_one(".price, .final-price, .internet-price")
        price_text = price.get_text(strip=True) if price else "Call for Price"

        vin_match = re.search(r"[A-HJ-NPR-Z0-9]{17}", item.get_text())
        vin = vin_match.group(0) if vin_match else "N/A"

        # Categorize by Lincoln model line
        model = "Other"
        for candidate in ["Navigator", "Aviator", "Nautilus", "Corsair"]:
          if candidate.lower() in title_text.lower():
            model = candidate
            break

        inventory.append({
            "title": title_text,
            "category": category,
            "model": model,
            "price": price_text,
            "vin": vin,
        })
    except Exception as err:
      print(f"Error fetching {url}: {err}")

  return inventory


def generate_html(data):
  with open("template.html", "r", encoding="utf-8") as f:
    template = f.read()

  json_data = json.dumps(data)
  timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

  output = template.replace("{{INVENTORY_DATA}}", json_data).replace(
      "{{LAST_UPDATED}}", timestamp
  )

  with open("index.html", "w", encoding="utf-8") as f:
    f.write(output)


if __name__ == "__main__":
  data = parse_inventory()
  generate_html(data)
  print(f"Updated index.html with {len(data)} vehicles.")
