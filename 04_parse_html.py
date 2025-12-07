import json
from bs4 import BeautifulSoup
import os

TAXON_KEYS = {
    "kingdom": "Kingdom",
    "division": "Division",
    "phylum": "Phylum",
    "class": "Class",
    "classis": "Class",
    "order": "Order",
    "family": "Family",
    "genus": "Genus",
    "species": "Species",
}

def clean_text(node):
    return node.get_text(" ", strip=True) if node else None


def parse_speciesbox(biota):
    box = {
        "image": None,
        "display_parents": None,
        "genus": None,
        "species": None,
        "authority": None,
        "synonyms_ref": None,
        "synonyms": None,
        "range_map": None,
        "range_map_caption": None
    }

    taxonomy = {}

        # Conservation status
    box["conservation_status"] = None

    # Try three methods in order

    # 1. Text based (rare but keep as fallback)
    for tr in biota.find_all("tr"):
        th = tr.find("th")
        if th and "conservation" in clean_text(th).lower():
            td = tr.find("td")
            if td:
                text = clean_text(td)
                for token in ["GX", "GH", "G1", "G2", "G3", "G4", "G5"]:
                    if token in text:
                        box["conservation_status"] = token
                        break
                if not box["conservation_status"]:
                    box["conservation_status"] = text
            break

    # 2. Image based (NatureServe icons)
    if not box["conservation_status"]:
        for img in biota.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue
            # Extract TNC_Gx from filename
            # Example: Status_TNC_G5.svg
            import re
            match = re.search(r"TNC_(G[0-5H X]{1,2})", src)
            if match:
                box["conservation_status"] = match.group(1)
                break

    # 3. Fallback: look for any G-rank pattern inside src
    if not box["conservation_status"]:
        for img in biota.find_all("img"):
            src = img.get("src", "")
            for token in ["GX", "GH", "G1", "G2", "G3", "G4", "G5"]:
                if token in src:
                    box["conservation_status"] = token
                    break
            if box["conservation_status"]:
                break

    if not biota:
        return box, taxonomy

    img = biota.find("img")
    if img and img.get("src"):
        src = img["src"]
        box["image"] = "https:" + src if src.startswith("//") else src

    for tr in biota.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) == 2:
            left = clean_text(tds[0]).rstrip(":")
            right = clean_text(tds[1])
            if not left or not right:
                continue

            norm = left.lower()
            key = TAXON_KEYS.get(norm)
            if key:
                taxonomy[key] = right
                if key == "Genus" and not box["genus"]:
                    box["genus"] = right
                if key == "Species" and not box["species"]:
                    box["species"] = right

    for th in biota.find_all("th"):
        t = clean_text(th)
        if t and ("Binomial name" in t or "Binomial" in t or "Scientific name" in t):
            tr = th.find_parent("tr")
            nxt = tr.find_next_sibling("tr") if tr else None
            if nxt:
                box["authority"] = clean_text(nxt)
            break

    for img in biota.find_all("img"):
        alt = (img.get("alt") or "").lower()
        if "range" in alt or "distribution" in alt or "map" in alt:
            src = img["src"]
            box["range_map"] = "https:" + src if src.startswith("//") else src
            td = img.find_parent("td")
            if td:
                box["range_map_caption"] = clean_text(td)
            break

    return box, taxonomy


def parse_mycomorphbox(myco_box):
    out = {
        "name": None,
        "whichGills": None,
        "capShape": None,
        "hymeniumType": None,
        "stipeCharacter": None,
        "ecologicalType": None,
        "sporePrintColor": None,
        "howEdible": None,
    }

    if not myco_box:
        return out

    title_th = myco_box.find("th", class_="infobox-above")
    out["name"] = clean_text(title_th)

    for tr in myco_box.find_all("tr"):
        row_text = clean_text(tr) or ""
        row_text_l = row_text.lower()
        td = tr.find("td")
        if not td:
            continue

        val = clean_text(td)

        if "gills" in row_text_l:
            out["whichGills"] = val
        elif "cap" in row_text_l:
            out["capShape"] = val
        elif "hymenium" in row_text_l:
            out["hymeniumType"] = val
        elif "stipe" in row_text_l:
            out["stipeCharacter"] = val
        elif "ecology" in row_text_l:
            out["ecologicalType"] = val
        elif "spore print" in row_text_l:
            out["sporePrintColor"] = val
        elif "edibility" in row_text_l:
            out["howEdible"] = val

    return out

def extract_wiki_links(soup):
    out = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/wiki/"):
            continue
        if ":" in href:  # screens out File:, Help:, Category:, etc.
            continue

        url = "https://en.wikipedia.org" + href
        text = a.get_text(" ", strip=True)

        # skip empty anchor text
        if not text:
            continue

        if url not in seen:
            seen.add(url)
            out.append({
                "url": url,
                "text": text
            })

    return out

def parse_mushroom_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    biota = soup.find("table", class_="infobox biota")

    myco_box = None
    for t in soup.find_all("table", class_="infobox"):
        if "Mycological characteristics" in (t.get_text() or ""):
            myco_box = t
            break

    speciesbox, taxonomy = parse_speciesbox(biota)

    data = {
        "speciesbox": speciesbox,
        "taxonomy": taxonomy,
        "mycomorphbox": parse_mycomorphbox(myco_box),
        "wiki_links": extract_wiki_links(soup),
        "text": "\n".join(
            clean_text(p) for p in soup.find_all("p") if clean_text(p)
        )
    }

    return data


if __name__ == "__main__":
    in_dir = "data/raw_articles_html"
    out_path = "data/mushroom_attributes.json"

    all_entries = []

    for filename in os.listdir(in_dir):
        if not filename.lower().endswith(".html"):
            continue

        in_path = os.path.join(in_dir, filename)

        base = filename[:-5]  # strip .html
        mushroom = base.replace("_", " ")

        parsed = parse_mushroom_html(in_path)

        parsed["mushroom"] = mushroom

        all_entries.append(parsed)

        print(f"Parsed: {filename}")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    print(f"Saved combined JSON → {out_path}")