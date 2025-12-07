import json

# Load original data with IDs
with open("data/mushroom_data.json", "r") as f:
    main_data = json.load(f)

# Load views dataset
with open("data/mushroom_pageviews.json", "r") as f:
    views_data = json.load(f)

# Load attribute dataset
with open("data/mushroom_attributes.json", "r") as f:
    attribute_data = json.load(f)

# Build lookup based on article
views_lookup = {entry["article"]: entry["views_all_time"] for entry in views_data}
attribute_lookup = {entry["mushroom"]: entry for entry in attribute_data}

# Merge
for item in main_data:
    article = item["article"]
    if article in views_lookup:
        item["views_all_time"] = views_lookup[article]
    else:
        item["views_all_time"] = None   # or 0 if you prefer

    mushroom_name = item["mushroom"]
    if mushroom_name in attribute_lookup:
        item.update(attribute_lookup[mushroom_name])

# Save merged output
with open("data/mushroom_data_merged.json", "w") as f:
    json.dump(main_data, f, indent=2)

print("Merge complete.")
