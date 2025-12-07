# get_pageviews_all_time.py
import os, json, requests, urllib.parse, time

INPUT_JSON = "data/mushroom_data.json"
OUTPUT_JSON = "data/mushroom_pageviews.json"

API_TEMPLATE = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{project}/all-access/user/{article}/monthly/{start}/{end}"
)

HEADERS = {"User-Agent": "DTU-MushroomGraph/1.0 (contact: your.email@example.com)"}

# --- Helper ---
def extract_title(article_url):
    return urllib.parse.unquote(article_url.split("/")[-1])

def get_all_time_views(title):
    """
    Query monthly pageviews from 2015-07 (start of Wikimedia stats) to now.
    Sum all monthly 'views' to get all-time count.
    """
    from datetime import datetime
    now = datetime.utcnow().strftime("%Y%m%d")
    url = API_TEMPLATE.format(
        project="en.wikipedia.org",
        article=urllib.parse.quote(title, safe=""),
        start="20150701",
        end=now,
    )
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"❌ {title}: HTTP {r.status_code}")
        return None
    data = r.json()
    items = data.get("items", [])
    return sum(item.get("views", 0) for item in items)

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        mushrooms = json.load(f)

    results = []
    for i, entry in enumerate(mushrooms, 1):
        article = entry.get("article")
        name = entry.get("mushroom")
        if not article or not article.startswith("https://en.wikipedia.org/wiki/"):
            print(f"⚠️ Skipping invalid article for {name}")
            continue

        title = extract_title(article)
        total = get_all_time_views(title)
        if total is not None:
            results.append({"mushroom": name, "article": article, "views_all_time": total})
            print(f"[{i}/{len(mushrooms)}] ✅ {name}: {total:,} views")
        else:
            print(f"[{i}/{len(mushrooms)}] ❌ {name}")
        time.sleep(0.3)  # be polite

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Done. Saved results to {OUTPUT_JSON}")
    print(f"Entries processed: {len(results)}")

if __name__ == "__main__":
    main()
