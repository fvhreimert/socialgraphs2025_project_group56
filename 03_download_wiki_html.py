import os, time, requests, urllib.parse, json

API_URL = "https://en.wikipedia.org/w/api.php"
SAVE_DIR = "data/raw_articles_html"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Load your Wikidata-derived JSON ---
with open("data/mushroom_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"Number of entries in JSON file: {len(data)}")

# Extract titles from article URLs
def extract_title(article_url):
    """Extract the Wikipedia page title from a full URL."""
    # More robust extraction
    return urllib.parse.unquote(article_url.split("/wiki/")[-1])

titles = []
for entry in data:
    article_url = entry.get("article")
    if article_url and article_url.startswith("https://en.wikipedia.org/wiki/"):
        titles.append(extract_title(article_url))
    else:
        print(f"⚠️ Skipping invalid or missing article for: {entry.get('mushroom', 'Unknown')}")

# --- User-Agent (Wikipedia requirement) ---
session = requests.Session()
session.headers.update({
    "User-Agent": "DTU-MushroomGraph/1.0 (contact: your.email@example.com)"
})

def get_html(title):
    """Fetch the rendered HTML of a Wikipedia page (templates expanded)."""
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "redirects": "true",
    }
    try:
        r = session.get(API_URL, params=params, timeout=30)
        if r.status_code != 200:
            return None
        js = r.json()
        if "error" in js or "parse" not in js:
            return None
        return js["parse"]["text"]["*"]
    except Exception as e:
        print(f"⚠️ Error fetching {title}: {e}")
        return None

def save_html(title):
    """Download and save the HTML for a Wikipedia article title."""
    safe = urllib.parse.unquote(title).replace("/", "_")
    path = os.path.join(SAVE_DIR, f"{safe}.html")

    # Skip if file already exists
    if os.path.exists(path):
        print(f"⏭️  Skipping {title} (already exists)")
        return True

    html = get_html(title)
    if not html:
        print(f"❌ Failed to get {title}")
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    time.sleep(0.5)  # be polite to the API
    return True

failed = []
for i, title in enumerate(titles, start=1):
    ok = save_html(title)
    status = "Saved" if ok else "Failed"
    print(f"[{i}/{len(titles)}] {status} {title}")
    if not ok:
        failed.append(title)

if failed:
    os.makedirs("data", exist_ok=True)
    with open("data/failed_html.json", "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)
    print(f"Completed with {len(failed)} failures.")
else:
    print("Completed successfully.")
