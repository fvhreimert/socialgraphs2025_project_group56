# EXPLAINER NOTEBOOK

This notebook is meant as a guideline to the codebase. It contains an explanation of the data retrieval, data analysis, and network creation code. The project investigates the representation of fungal species on Wikipedia, analyzing how taxonomy, morphology, and text sentiment relate to public interest (pageviews).

---

## Project Structure

The repository is organized into two main stages: a **Data Retrieval Pipeline** (Python scripts in the root directory) and a **Network Analysis Suite** (Jupyter notebooks in the `network/` folder).

### Directory Tree
```bash
.
├── 01_mushroom_list.py             # Query Wikidata for species list
├── 02_extract_num_views.py         # Fetch pageview statistics via API
├── 03_download_wiki_html.py        # Scrape raw HTML for parsing
├── 04_parse_html.py                # Extract taxonomy and morphology
├── 05_merge_datasets.py            # Consolidate all data into JSON
├── README.md                       # Project documentation
├── data
│   └── Data_Set_S1.txt             # LabMT sentiment dictionary
└── network
    ├── 00_DATA_CLEANING.ipynb              # Pre-processing raw attributes
    ├── 01_TAXONOMY_DATA_ANALYSIS.ipynb     # Biological hierarchy stats
    ├── 02_MORPHOLOGICAL_DATA_ANALYSIS.ipynb# Physical trait stats
    ├── 03_TEXT_ANALYSIS.ipynb              # TF-IDF and content analysis
    ├── 04_WIKI_LINKS_ANALYSIS.ipynb        # Hyperlink graph construction
    ├── 05_MAKE_NETWORK.ipynb               # Multilayer network creation
    ├── 06_GRAPH_ANALYSIS.ipynb             # Centrality & Assortativity
    ├── 07_SENTIMENT_ANALYSIS.ipynb         # VADER & Word Clouds
    └── mushroom_network_final.pkl          # Final NetworkX graph object

```
---

## 1. Data Retrieval Pipeline

This section explains the data collection workflow and why each step is structured the way it is. The retrieval pipeline is split into five focused scripts, each handling a single responsibility. This improves clarity, reduces coupling across stages, and makes debugging straightforward.

#### 1.1 Collecting the list of mushrooms  
**File: `01_mushroom_list.py`** :contentReference[oaicite:0]{index=0}  
Key points  
- Queries Wikidata with a SPARQL request to retrieve all items tagged with any mushroom related property (P783 to P789).  
- Extracts each item's English Wikipedia article URL.  
- Stores a clean list containing a unique id, the mushroom name, and its article link.  
Reasoning  
- Wikidata provides a consistent and queryable source of structured biological entities, which ensures reproducibility and avoids manual curation.  
- Filtering for items that actually have an English Wikipedia article keeps the dataset aligned with downstream processing requirements.

#### 1.2 Retrieving pageview statistics  
**File: `02_extract_num_views.py`** :contentReference[oaicite:1]{index=1}  
Key points  
- Loads the initial mushroom list and fetches monthly pageview data from the Wikimedia REST API.  
- Aggregates total views across the entire available time range.  
- Handles skipped or invalid pages gracefully and introduces a delay between requests to respect API limits.  
Reasoning  
- Pageviews act as a useful proxy for cultural or scientific interest.  
- Computing totals locally avoids repeated on the fly API calls, improving performance and stability in later analyses.

#### 1.3 Downloading article HTML  
**File: `03_download_wiki_html.py`** :contentReference[oaicite:2]{index=2}  
Key points  
- Reads the article list and extracts each page title.  
- Uses the MediaWiki API `parse` endpoint to download fully rendered HTML for each article.  
- Saves each article as a standalone HTML file in a persistent directory.  
Reasoning  
- Local HTML snapshots guarantee reproducibility, especially since Wikipedia content can change over time.  
- Using rendered HTML instead of raw wikitext simplifies parsing and reduces the need for custom markup handling.

#### 1.4 Parsing biological and morphological information  
**File: `04_parse_html.py`** :contentReference[oaicite:3]{index=3}  
Key points  
- Parses each saved HTML file with BeautifulSoup.  
- Extracts structured taxonomic info from the Speciesbox, morphological traits from the Mycomorphobox, text content, and all internal wiki links.  
- Normalizes common patterns and handles variation across article formats.  
Reasoning  
- Wikipedia infoboxes are semi structured but inconsistent. A dedicated parser allows robust extraction while adapting to layout differences.  
- Storing multiple layers of information supports richer downstream tasks like classification, clustering, and link network analysis.

#### 1.5 Merging all datasets  
**File: `05_merge_datasets.py`** :contentReference[oaicite:4]{index=4}  
Key points  
- Loads the original list, the pageview dataset, and the parsed attribute dataset.  
- Merges them using article URLs and mushroom names as lookup keys.  
- Produces a single consolidated JSON file containing all fields.  
Reasoning  
- A unified dataset is essential for efficient analysis and avoids repeated cross referencing.  
- Using article links and names as keys ensures reliable alignment even when ordering differs across intermediate files.


---

# 2. Data Cleaning

This section outlines how the dataset is cleaned before any network construction. The goal is to transform inconsistent infobox text into structured lists that can be compared across mushrooms. Each subsection describes what is being filtered and why.

## 2.1 Attribute specific cleaning

#### Spore print color
Operations  
- remove fixed prefixes and newline characters  
- split into individual color tokens  
Reason  
- Spore print color often contains ranges or compound expressions. Splitting ensures each color can be treated independently in similarity comparisons.

#### Cap shape
Operations  
- remove prefixes like "Cap is"  
- remove filler words such as "or"  
- split into token lists  
Reason  
- Cap shape is frequently expressed as alternatives or ranges. The goal is to encode each shape as a discrete value.

#### Stipe character
Operations  
- remove several template phrases ("Stipe is", "Stipe has a")  
- remove negations or ambiguous constructions  
- remove text after expressions like "Lacks a"  
- split into tokens  
Reason  
- Stipe descriptions vary more than other fields and contain many narrative phrases. Filtering produces a clean list of structural descriptors.

#### Hymenium type
Operations  
- remove boilerplate prefixes  
- remove problematic infobox fragments that appear in certain pages  
- remove "or"  
- split into tokens  
Reason  
- Hymenium type must be reduced to standard categorical labels without leftover template text.

#### Edibility
Operations  
- normalize keywords such as edible, poisonous, psychoactive  
- remove phrases such as "can cause..."  
- convert special cases to underscore tokens like `not_recommended`  
- remove "but" and "or"  
- split into tokens  
Reason  
- Edibility is often embedded in long sentences with mixed information. Standardized tokens allow direct comparison and later classification.

#### Gill type
Operations  
- wrap the single value into a one element list  
Reason  
- Gill type is usually a single descriptor. Converting to a list maintains uniform structure across all attributes.

#### Ecological type
Operations  
- remove "Ecology is"  
- remove "or"  
- split into tokens  
Reason  
- Ecology is sometimes written as a sentence or with multiple alternatives. Cleaning isolates the specific ecological categories.

#### Conservation status
Operations  
- convert missing values to empty lists  
- split values using the same tokenization pattern  
Reason  
- Status information may contain multiple indicators. Converting to a standardized list ensures consistency for downstream grouping.

## 2.3 Result
After cleaning  
- all morphology and status fields are stored as lists  
- narrative sentences are removed  
- missing values are consistently represented  
- all attributes are ready for network construction, similarity computation, or feature engineering  

---

# 3. Data Analysis

This section introduces the analytical workflows used to study the cleaned dataset. The first subsection covers the taxonomy focused analysis performed in `TAXONOMY_DAT_ANALYSIS.ipynb`. The goal is to understand how species are distributed across taxonomic ranks and how popularity varies within this biological hierarchy.

## 3.1 Taxonomy Analysis

### Dataset preparation
Steps  
- Load the mushroom network and convert all node attributes into a dataframe.  
- Remove entries missing a Species label, since taxonomy based grouping is impossible without it.  
- Ensure `views_all_time` is numeric, filling missing values with zero.  
Reason  
- A consistent dataframe is required for rank based comparisons and aggregation.

### Taxonomic richness
Procedure  
- Define hierarchical ranks from Division to Species.  
- Count the number of unique values for each rank.  
Purpose  
- Quantifies how biologically diverse the dataset is at each level.  
- Helps identify which layers are species rich or species poor.

### Family representation
Procedure  
- Count species per Family and list the ten most represented families.  
Purpose  
- Highlights dominant branches in the dataset and serves as a simple proxy for structural imbalance within the taxonomy.

### Popularity distribution
Procedure  
- Plot a histogram of total pageviews across species using a logarithmic y scale.  
Purpose  
- Popularity is highly skewed. The log scale reveals whether many species get minimal attention while a few attract heavy traffic.

### Average popularity by rank
Procedure  
- Compute the mean pageviews for each unique value in every rank.  
- Plot the top categories per rank.  
Purpose  
- Identifies which divisions, classes, families, etc., contain disproportionately popular species.  
- Helps evaluate whether popularity is concentrated within specific evolutionary lineages.

### Popularity inequality (Gini analysis)
Procedure  
- Use a custom Gini function to quantify inequality in total pageviews within each taxonomic rank.  
- Group species by rank, sum their views, and compute Gini coefficients.  
Purpose  
- Measures how unevenly attention is distributed among branches of the tree of life.  
- A high Gini score means a small subset of groups attracts nearly all attention.  
- Comparing ranks shows whether inequality persists across taxonomic scales.

### Pareto style popularity check
Procedure  
- Sort species by pageviews.  
- Compute cumulative view percentages.  
- Estimate how many species account for 10 percent, 20 percent, and 50 percent of total traffic.  
Purpose  
- Evaluates how extreme the popularity concentration is.  
- Provides intuitive interpretations such as how many species drive half of all Wikipedia interest.

---

## 3.2 Morphology Analysis

### Dataset preparation
Steps  
- Load the mushroom network and convert node attributes into a dataframe.  
- Extract the eight morphological traits stored as list formatted fields.  
Reason  
- Morphology cannot be analyzed in its list form until exploded into individual tokens.

### Morphological richness
Procedure  
- Explode each morphological attribute into one row per trait value.  
- Count unique tokens for each attribute.  
Purpose  
- Quantifies the diversity of morphological descriptors present in the dataset.  
- Identifies attributes with highly varied or very narrow category sets.

### Preliminary popularity analysis
Procedure  
- Explode each morphological attribute and link individual trait values to species level pageviews.  
- Remove empty tokens coming from missing or cleaned fields.  
- Group by trait value and compute mean views and number of species expressing that trait.  
- Filter out rare categories with low sample counts to avoid misleading spikes.  
- Plot trait value popularity using bar charts.  
Purpose  
- Tests whether specific morphological features correspond to higher public interest.  
- Ensures comparisons are not dominated by noisy or sparse categories.

### Popularity inequality (Gini analysis)
Procedure  
- For each attribute, explode all values and sum pageviews per trait category.  
- Compute the Gini coefficient on the resulting distribution.  
Purpose  
- Measures how unequal popularity is within each morphological attribute.  
- High Gini values indicate that one or a few morphological categories dominate attention.

### High resolution trait analysis
Procedure  
- Compute mean, standard deviation, count, and confidence intervals for each morphological trait value.  
- Select the top categories with strongest popularity signals.  
- Plot bar charts with error bars, sample size labels, and Gini scores for context.  
Purpose  
- Produces a clearer and statistically informed comparison of trait level popularity.  
- Reveals whether differences are broad trends or driven by a small number of species.

---

## 3.3 Text Analysis

### Dataset preparation  
Steps  
- Load the mushroom network and convert node attributes into a dataframe.  
- Extract the raw article text and create a cleaned version.  
Reason  
- Wikipedia text contains references, boilerplate phrases, and formatting noise. Cleaning is needed before any linguistic analysis.

### Text cleaning and word count  
Procedure  
- Remove citation markers and stub templates.  
- Normalize whitespace and strip artifacts.  
- Compute article length by counting words in the cleaned text.  
Purpose  
- Produces a consistent corpus for analysis.  
- Word count offers a simple measure of article completeness.

### Length versus popularity  
Procedure  
- Plot word count against total pageviews using log-log scales.  
- Fit a trend line and compute the Spearman correlation.  
Purpose  
- Tests whether longer articles attract more attention.  
- Log scaling allows heavy tailed patterns to be seen more clearly.

### TF-IDF keyword extraction  
Procedure  
- Build a TF-IDF model using custom stopwords to remove Wikipedia boilerplate and generic biological vocabulary.  
- Ignore extremely common or extremely rare words using document frequency thresholds.  
- Extract top TF-IDF terms for the three most popular mushrooms.  
Purpose  
- Identifies distinctive vocabulary associated with high visibility species.  
- Highlights specific ecological, chemical, or morphological themes that contribute to popularity.

### Semantic similarity between species  
Procedure  
- Compute a cosine similarity matrix using TF-IDF vectors.  
- Inspect pairwise similarity and visualize the distribution of similarity scores.  
Purpose  
- Measures how similar species are in textual descriptions.  
- Helps assess whether mushrooms cluster semantically in ways not captured by taxonomy or morphology.

### Word cloud of the top species  
Procedure  
- Select the top fifty most viewed species.  
- Combine their cleaned texts into a single corpus.  
- Generate a word cloud using the extended stopword list.  
Purpose  
- Provides an intuitive overview of terms most associated with the most culturally visible mushrooms.  
- Suppresses trivial biological vocabulary to reveal more meaningful concepts.

### Similarity distribution analysis  
Procedure  
- Plot the histogram of pairwise cosine similarity values.  
- Summarize similarity counts within fixed intervals.  
Purpose  
- Shows whether textual descriptions tend to be unique or homogeneous.  
- Indicates how much semantic redundancy or diversity exists across species.

---

## 3.4 Wikipedia Links Analysis

### Dataset preparation  
Steps  
- Load the mushroom network and convert node attributes into a dataframe.  
- Extract each species' list of outgoing Wikipedia links.  
Reason  
- Link structure provides relational information not captured by taxonomy, morphology, or text.  
- Wikipedia hyperlinks can reveal conceptual proximity and shared contexts between species.

### Link preprocessing  
Procedure  
- Ensure the `wikilinks` field is interpreted as a list of dictionaries rather than a raw string.  
- Convert any serialized list representations back into proper Python objects.  
Purpose  
- Prevents malformed link entries from being treated as text.  
- Ensures downstream filtering and graph construction behave correctly.

### Filtering for in-dataset links  
Procedure  
- Build a set of valid article URLs belonging to mushrooms in the dataset.  
- Map article URLs to mushroom names for readable node labels.  
- Retain only edges in which both the source and target URLs correspond to mushrooms in the final dataset.  
Purpose  
- Restricts the network to internal mushroom to mushroom links.  
- Prevents dilution of the graph with irrelevant pages such as geographic regions, chemicals, or general biology articles.

### Graph construction  
Procedure  
- Add all mushrooms as nodes, even if they have no internal links.  
- Add undirected edges between two mushrooms whenever one links to the other.  
- Remove self links where a page links to itself.  
Purpose  
- Builds a clean hyperlink graph capturing how fungal species reference one another.  
- Retains information about isolated nodes, which may indicate rare or poorly connected species.

### Degree distribution analysis  
Procedure  
- Compute the degree of each node and visualize their distribution.  
Purpose  
- Reveals whether the hyperlink network is highly centralized or broadly connected.  
- Identifies whether a small subset of species act as hubs in the Wikipedia ecosystem.

---

## 3.5 Network Construction

### Dataset preparation  
Steps  
- Load the cleaned mushroom dataset and convert all node attributes into a dataframe.  
- Define attribute groups for taxonomy, morphology, text, and wikilinks.  
Reason  
- A consistent attribute layout is required to compute similarity matrices for each layer.

### Taxonomic network  
Procedure  
- One hot encode Genus, Family, and Order.  
- Compute pairwise similarity using weighted hierarchical overlap, giving highest weight to Genus matches, lower to Family, and lowest to Order.  
- Normalize scores and remove trivial self matches.  
- Add edges only for pairs exceeding a similarity threshold.  
Purpose  
- Captures graded biological relatedness.  
- Prevents overconnection by ignoring overly broad ranks.

### Morphological network  
Procedure  
- Use previously computed Gini coefficients as weights to scale each morphological attribute by its informational value.  
- Convert list based attributes into binary matrices using multilabel encoding.  
- Compute cosine similarity per trait and form a weighted average similarity matrix.  
- Normalize and threshold to generate edges.  
Purpose  
- Models resemblance based on structural and ecological traits.  
- Ensures influential traits contribute more strongly than low variance traits.

### Text network  
Procedure  
- Clean article text and compile an expanded stopword list including taxonomy names, morphology terms, geographic words, and general fillers.  
- Fit a TF IDF model and compute cosine similarity between articles.  
- Zero out self similarity and prune extremely high similarity pairs caused by boilerplate stubs.  
- Add edges for pairs exceeding a semantic similarity threshold.  
Purpose  
- Captures contextual and cultural similarity between species.  
- Adds information unavailable to biological and morphological layers.

### Wikipedia links network  
Procedure  
- Parse external wikilinks and convert serialized lists into proper Python objects.  
- Retain only links whose targets are mushrooms within the dataset.  
- Build an undirected graph and corresponding adjacency matrix.  
Purpose  
- Encodes explicit connections created by Wikipedia editors.  
- Reflects structural proximity derived from hyperlink behavior.

### Composite similarity matrix  
Procedure  
- Combine the raw similarity matrices from taxonomy, morphology, text, and wikilinks using predefined weights.  
- Zero the diagonal and preserve all pairwise similarity values.  
Purpose  
- Produces an integrated similarity representation that blends biological, descriptive, and hyperlink based signals.

### k nearest neighbor backbone  
Procedure  
- For each species, identify the top k similar neighbors from the composite matrix.  
- Add edges to form a sparse backbone graph that retains only the strongest connections.  
Purpose  
- Removes noise and reduces density while preserving core structural relationships.  
- Produces a clearer network suitable for global clustering.

### Community detection  
Procedure  
- Apply Louvain clustering across multiple resolution values.  
- Select the partition with highest modularity.  
- Assign community labels and summarize each group by dominant Family and average popularity.  
Purpose  
- Reveals emergent clusters produced by all similarity layers combined.  
- Provides interpretable groupings grounded in both biological and contextual features.

### Visualization  
Procedure  
- Compute a forceatlas2 layout with strong repulsion to separate clusters.  
- Size nodes by log scaled pageviews and color by community membership.  
- Add rich hover text containing taxonomy, morphology, and popularity information.  
Purpose  
- Produces an interpretable visual summary of the complete multilayer network.  
- Highlights hubs, cluster boundaries, and structural patterns across the dataset.

---

## 4. Graph Analysis

This section details the structural analysis of the constructed mushroom network. The goal is to move beyond simple statistics and understand the relationship between the network's topology and their real-world popularity.

### 4.1 Loading and Centrality Calculation
**File: `06_GRAPH_ANALYSIS.ipynb`** Key points  
- Loads the finalized `mushroom_network_final.pkl` containing all nodes and edges.  
- Computes three distinct centrality metrics for every node: Degree Centrality, PageRank, and Betweenness Centrality.  
- Merges these structural metrics with the views attribute into a unified analysis dataframe.  
Reasoning  
- Centrality metrics quantify "importance" in different ways. A mushroom might have few links but be crucial for connecting two different families.  
- Pre-calculating these metrics allows for rapid correlation testing against pageviews without re-running expensive graph algorithms.

### 4.2 Popularity vs. Structure Correlation
Procedure  
- Log-transforms the view counts to handle the heavy-tailed distribution of popularity.  
- Calculates Spearman rank correlations between popularity and the three centrality metrics.  
- Visualizes these relationships using scatter plots with regression lines and outlier labeling.  
Purpose  
- Tests the hypothesis that well-linked articles are viewed more often.  
- Identifying "Hidden Gems" reveals species that are structurally central to the network but under-appreciated by the public.

### 4.3 Popularity Inequality and Assortativity
Procedure  
- Ranks nodes by both Pageviews and PageRank to identify discrepancies (Hidden Gems vs. Pop Stars).  
- Calculates neighbor popularity: For every node, compute the average view count of its immediate network neighbors.  
- Plots node popularity against neighbor popularity on a log-log scale.  
- Overlays community IDs as colors to detect cluster-specific behavior.  
Purpose  
- Analyzes "assortative mixing," determining if popular mushrooms tend to link primarily to other popular mushrooms.  
- Helps visualize if high-traffic pages form isolated "echo chambers" or if popularity is distributed across the network structure.

### 4.4 Result
After analysis  
- Structural hubs are compared against cultural popularity.  
- The degree of "contagion" (popularity assortativity) is quantified.  
- Clusters are evaluated to see if they are defined by high-traffic hubs or niche scientific groupings.

---

# 5. Text & Sentiment Analysis

This section investigates the contextual content of the network. While the graph analysis focused on connections, this module analyzes the actual text within the articles to understand *what* is being said about these mushroom communities.

## 5.1 Text Preprocessing & Dynamic Stopwords
**File: `07_SENTIMENT_ANALYSIS.ipynb`** Key points  
- Loads the community dataset and applies a standard text cleaning function (removing citations, stubs, and formatting).  
- Constructs a massive "Stopword" list combining:
  - Standard English stopwords.
  - Domain-specific terms (e.g., "mushroom", "fungus", "spore", "gill", "cm").
  - **Dynamic Exclusion:** Iterates through every Taxonomy and Morphology column in the dataframe to add specific mushroom names (e.g., "Amanita", "muscaria") to the ignore list.  
Reasoning  
- Wikipedia articles mention the subject's name frequently. To analyze the *description* rather than the *identity*, we must strip out the mushroom's own name.  
- Removing generic biological terms prevents every word cloud from being dominated by words like "species" or "cap."

## 5.2 Comparative Word Clouds
Key points  
- Selects two distinct communities: The "Amanita Cluster" and the "Psychonaut Cluster."  
- Generates word clouds using custom image masks (shapes of mushrooms) for visual distinctness.  
- Uses the strict stopword list to ensure only descriptive adjectives and nouns remain.  
Reasoning  
- Provides a qualitative sanity check for the clustering.  
- Visualizes the semantic gap: One cluster might feature words like "deadly" and "poison," while another features "psychoactive" and "legal."

## 5.3 Keyword Sentiment (LabMT)
Key points  
- Uses the LabMT (Language Assessment by Mechanical Turk) dictionary, which scores words on a happiness scale.  
- Extracts the top 50 most frequent words for each community.  
- Calculates the average sentiment score of these *specific keywords* only.  
Reasoning  
- Analyzing the "core vocabulary" helps bypass the neutral "encyclopedic tone" of Wikipedia.  
- If the most frequent words in a cluster are "toxin," "fatal," and "liver," the cluster will score negatively even if the sentence structure is neutral.

We found that the LabMT method did not work well on the mushroom articles. So we decided to go with another sentiment approach, the VADER (Valence Aware Dictionary and sEntiment Reasoner).

## 5.4 Full-Text Sentiment (VADER)
Key points  
- Initializes the VADER (Valence Aware Dictionary and sEntiment Reasoner) analyzer.  
- Computes a compound sentiment score (-1 to +1) for the *entire* text of every article.  
- Aggregates the mean sentiment score per community.  
Reasoning  
- VADER is sensitive to intensity and context, capturing a different layer of sentiment than the keyword approach.  
- It tests the hypothesis: Are articles about edible mushrooms written more "positively" than articles about poisonous ones?

## 5.5 Sentiment Visualization
Key points  
- Aggregates sentiment scores, view counts, and dominant families.  
- Visualization: Creates a **Lollipop Chart** ranking communities from most negative (Red) to most positive (Green).  
- Highlights which fungal families are associated with negative vocabulary vs. positive vocabulary.  
Reasoning  
- A ranked list allows for immediate identification of outliers.  
- It confirms whether public interest (views) correlates with sensationalized (negative/scary) content.