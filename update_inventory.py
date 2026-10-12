import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}

URLS = {
    'New': 'https://www.parkslincoln.com/new-inventory/index.htm',
    'Pre-Owned': 'https://www.parkslincoln.com/used-inventory/index.htm',
}


def parse_inventory():
  inventory = []

  for category, url in URLS.items():
    try:
      resp = requests.get(url, headers=HEADERS, timeout=20)
      soup = BeautifulSoup(resp.text, 'html.parser')

      # Target Dealer.com's vehicle containers
      items = soup.select(
          'li.inventory-item, div.hproduct, div.item.vehicle, div.vehicle-card'
      )

      # Fallback if wrapped in another container
      if not items:
        items = soup.find_all(
            ['li', 'div'], class_=re.compile(r'inventory-item|hproduct')
        )

      for item in items:
        # Title extraction
        title_el = (
            item.select_one(
                'h2 a, h3 a, .title a, a[href*="inventory/"], [itemprop="name"]'
            )
            or item.select_one('h2, h3, .title')
        )
        title_text = (
            title_el.get_text(strip=True) if title_el else 'Lincoln Vehicle'
        )

        # Price extraction
        price_el = item.select_one(
            '.price, .final-price, .internet-price, .value, [itemprop="price"]'
        )
        price_text = (
            price_el.get_text(strip=True) if price_el else 'Call for Price'
        )

        # VIN matching (standard 17-char VIN)
        raw_text = item.get_text(' ')
        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', raw_text)
        vin = vin_match.group(0) if vin_match else 'In Transit / N/A'

        # Categorize Lincoln model line
        model = 'Other'
        for candidate in ['Navigator', 'Aviator', 'Nautilus', 'Corsair']:
          if candidate.lower() in title_text.lower():
            model = candidate
            break

        inventory.append({
            'title': title_text,
            'category': category,
            'model': model,
            'price': price_text,
            'vin': vin,
        })
    except Exception as err:
      print(f'Error scraping {url}: {err}')

  return inventory


def generate_html(data):
  with open('template.html', 'r', encoding='utf-8') as f:
    template = f.read()

  json_data = json.dumps(data)
  timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')

  output = template.replace('{{INVENTORY_DATA}}', json_data).replace(
      '{{LAST_UPDATED}}', timestamp
  )

  with open('index.html', 'w', encoding='utf-8') as f:
    f.write(output)


if __name__ == '__main__':
  data = parse_inventory()
  generate_html(data)
  print(f'Done. Successfully extracted {len(data)} vehicles.')
