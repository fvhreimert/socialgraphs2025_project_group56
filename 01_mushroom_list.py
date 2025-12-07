import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json

endpoint_url = "https://query.wikidata.org/sparql"

# SPARQL: Get all mushrooms (with any of P783–P789 properties) and their English Wikipedia article
query = """
SELECT DISTINCT ?item ?itemLabel ?article
WHERE {
  ?item (wdt:P783|wdt:P784|wdt:P785|wdt:P786|wdt:P787|wdt:P788|wdt:P789) [] .
  
  OPTIONAL {
    ?article schema:about ?item ;
             schema:isPartOf <https://en.wikipedia.org/> .
  }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""

def get_results(endpoint_url, query):
    user_agent = f"WDQS-example Python/{sys.version_info[0]}.{sys.version_info[1]}"
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

try:
    results = get_results(endpoint_url, query)
    bindings = results["results"]["bindings"]
    print(f"Successfully fetched {len(bindings)} results.\n")

    # Extract mushroom name and article link
    data = []
    counter = 1

    for result in bindings:
        name = result["itemLabel"]["value"]
        article = result.get("article", {}).get("value", None)

        if article:  # Only keep those with an article
            data.append({
                "mushroom": name,
                "id": counter,
                "article": article
            })
            counter += 1

    df = pd.DataFrame(data)
    print(df.head(10))

except Exception as e:
    print(f"An error occurred: {e}")

# Save as json file
with open("mushroom_data.json", "w") as f:
    json.dump(data, f, indent=2)

# Save as csv file
df.to_csv("data/mushroom_data.csv", index=False)

# Save as json file
with open("data/mushroom_data.json", "w") as f:
    json.dump(data, f, indent=2)
