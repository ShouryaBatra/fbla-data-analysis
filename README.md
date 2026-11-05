# Homestead FBLA Data Analysis — 2025–26

Everything from the Homestead High School FBLA **Data Analysis** team's 2025–26 season: Aaron, Roshan, and Shourya.

**Results:** 🥈 2nd place at the California State Leadership Conference (SLC). Competed at Nationals, but didn't get past prelims.

## Final deliverables

The finished versions of everything are in [`final_deliverables/`](final_deliverables/):

| File                                                                                      | What it is                                                  |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [`data analysis.txt`](final_deliverables/data%20analysis.txt)                             | The presentation script (who says what)                     |
| [`Nationals_three_final copy.pptx`](final_deliverables/Nationals_three_final%20copy.pptx) | The final slide deck                                        |
| [`Technical_Supplement copy.pdf`](final_deliverables/Technical_Supplement%20copy.pdf)     | The technical appendix we handed to judges (Appendices A–D) |

Everything else in the repo is the work that got us to those files.

## The project

The prompt: our "client," SportsFanatics, wanted to know **how historical Olympic data can be used to optimize planning decisions for the 2028 Los Angeles Olympics.**

We used the Olympic athlete-events dataset (1896–2016, Summer Games only) plus World Bank GDP and population data, and made recommendations for three stakeholders:

- **Host city (LA28):** Mapped each sport to its LA28 venue zone and used Rio 2016 athlete counts to measure the load on each zone. Downtown, Long Beach, and Carson end up with over three-quarters of all athletes, so we recommended allocating transit, medical, and security resources by zone load instead of by venue size.
- **National Olympic Committees:** Regression model of expected medals based on GDP per capita and population. It shows which countries over- or underperform their resources, and each underperforming country gets an overperforming peer to benchmark against.
- **NOC strategy types:** KMeans clustering on how a country's medals are spread across sports, which splits countries into _specialists_ (Jamaica, Kenya) and _generalists_ (China, Germany, UK).
- **Athletes:** Peak medal-age windows per sport (median and IQR of medal-winning age), e.g. rhythmic gymnastics peaks around 18, while shooting and equestrian peak around 32–34.

Built with Python, pandas, scikit-learn, and Jupyter.

## What's in the rest of the repo

- **Notebooks:** the actual analysis
  - `olympics_analysis.ipynb`: main exploration and cleaning
  - `gdpRegression.ipynb`: resource-adjusted performance model
  - `olympics_country_specialization_clustering.ipynb`: specialist vs. generalist clustering
  - `LA28_zone_load_analysis (1).ipynb`: host city zone load
  - `charts1–3.ipynb`: chart experiments
- **Scripts:**
  - `build_chart_data.py`, `build_supplement_data.py`: generate the chart and appendix data (`chart_jsons/`, `supplement_data.json`)
  - `render_native_charts.py`: renders chart images into `chart_imgs/`
  - `generate_pdf.py`: builds the Technical Supplement PDF
- **Speech drafts:** `speech.md` (Nationals), `earlier_states_speech.md` and `old_speech.md` (older drafts), `nationals_qa.md` (Q&A prep for judges' questions)
- **Old slide decks:** `REAL_STATES_ONE.pptx` (SLC), `Nationals_one/two/three*.pptx` (Nationals iterations)
- **`datasets/`:** raw data (athlete events, NOC regions, GDP). This folder is gitignored, so it won't show up if you clone the repo.
