"""
Emit the three PowerPoint chart datasets (raw data points, not code) as JSON:
  - peak_age_windows.json
  - country_strategy_clusters.json
  - resource_adjusted_performance.json

Peak-age and cluster points are read straight from supplement_data.json (already
reviewed). The resource-adjusted scatter is recomputed here so it includes EVERY
participating country (the supplement only stores the ranked over/under lists),
using the identical Poisson model as the supplement.

Run:  python3.9 build_chart_data.py
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import KFold, cross_val_predict

DATA = "datasets"
S = json.load(open("supplement_data.json"))

# ===========================================================================
# 1) PEAK AGE WINDOWS  (from supplement_data.json -> appendix D)
# ===========================================================================
age_points = [
    {"sport": r["sport"], "median_age": r["median"], "q1": r["q1"], "q3": r["q3"], "iqr": r["iqr"]}
    for r in S["appendixD"]["rows"]
]
json.dump({
    "description": "Data for the peak age windows chart — median medal-winning age for each "
                   "Summer Olympic sport, with the 25th/75th percentile range (Q1/Q3) and IQR. "
                   "Sorted youngest to oldest. For a simple bar chart use sport -> median_age; "
                   "for a range/error-bar chart use q1 and q3 as the window.",
    "data": age_points,
}, open("peak_age_windows.json", "w"), indent=2)

# ===========================================================================
# 2) COUNTRY STRATEGY CLUSTERS  (from supplement_data.json -> appendix C)
# ===========================================================================
cluster_points = [
    {"country": r["country"], "cluster": r["label"], "total_medals": r["total_medals"],
     "top_sport": r["top_sport"], "top_sport_share_pct": r["top_share"],
     "effective_sports": r["eff_sports"]}
    for r in S["appendixC"]["rows"]
]
json.dump({
    "description": "Data for the country strategy clusters scatter chart — each country labeled "
                   "Specialist or Generalist by how concentrated its all-time Summer medals are. "
                   "Suggested scatter: x = effective_sports (lower = more specialised), "
                   "y = total_medals, color by cluster. top_sport_share_pct is the % of a "
                   "country's medals in its single best sport.",
    "data": cluster_points,
}, open("country_strategy_clusters.json", "w"), indent=2)

# ===========================================================================
# 3) RESOURCE-ADJUSTED MEDAL PERFORMANCE  (recomputed for ALL countries)
#    Identical model to the supplement (Appendix B).
# ===========================================================================
athletes = pd.read_csv(f"{DATA}/athlete_events.csv")
noc = pd.read_csv(f"{DATA}/noc_regions.csv")

df = athletes.merge(noc, on="NOC", how="left").rename(columns={"region": "Country"})
df = df[df["Season"] == "Summer"].copy()
df["Medal_Won"] = df["Medal"].notna().astype(int)

rio = df[df["Year"] == 2016].copy()
rio = rio[rio["Country"].notna()].copy()
participants = rio[["Country"]].drop_duplicates().copy()
rio_medals = rio[rio["Medal"].notna()].copy()
event_cols = ["Games", "Year", "Season", "City", "Sport", "Event", "NOC", "Medal"]
rio_event = rio_medals.drop_duplicates(event_cols).copy()
medals_2016 = rio_event.groupby("Country").size().reset_index(name="Actual_Medals_2016")
cm = participants.merge(medals_2016, on="Country", how="left").fillna({"Actual_Medals_2016": 0})
cm["Actual_Medals_2016"] = cm["Actual_Medals_2016"].astype(int)

def wb_local(path, code):
    d = pd.read_csv(path, skiprows=4)
    out = d[["Country Name", "Country Code", "2016"]].copy()
    out.columns = ["Country_WB", "ISO3_WB", code]
    return out

wb_gdp = wb_local(f"{DATA}/gdp_data/API_NY.GDP.PCAP.CD_DS2_en_csv_v2_432207/API_NY.GDP.PCAP.CD_DS2_en_csv_v2_432207.csv", "NY.GDP.PCAP.CD")
wb_pop = wb_local(f"{DATA}/gdp_data/API_SP.POP.TOTL_DS2_en_csv_v2_430662/API_SP.POP.TOTL_DS2_en_csv_v2_430662.csv", "SP.POP.TOTL")
wb = wb_gdp.merge(wb_pop, on=["Country_WB", "ISO3_WB"], how="outer")
wb = wb[wb["ISO3_WB"].notna()]
wb = wb[wb["ISO3_WB"].str.len() == 3]
agg_keywords = ["income", "IDA", "IBRD", "World", "Euro area", "European Union", "OECD",
                "Arab World", "Sub-Saharan", "Latin America", "Caribbean", "Middle East",
                "North America", "South Asia", "East Asia", "Pacific", "Africa",
                "small states", "Fragile", "Heavily indebted", "countries"]
wb = wb[~wb["Country_WB"].str.contains("|".join(agg_keywords), case=False, na=False)].copy()

name_map = {
    "USA": "United States", "UK": "United Kingdom", "Russia": "Russian Federation",
    "South Korea": "Korea, Rep.", "North Korea": "Korea, Dem. People's Rep.",
    "Iran": "Iran, Islamic Rep.", "Egypt": "Egypt, Arab Rep.", "Venezuela": "Venezuela, RB",
    "Czech Republic": "Czechia", "Slovakia": "Slovak Republic", "Bahamas": "Bahamas, The",
    "Gambia": "Gambia, The", "Laos": "Lao PDR", "Vietnam": "Viet Nam",
    "Syria": "Syrian Arab Republic", "Ivory Coast": "Cote d'Ivoire", "Boliva": "Bolivia",
    "Brunei": "Brunei Darussalam", "Republic of Congo": "Congo, Rep.",
    "Democratic Republic of the Congo": "Congo, Dem. Rep.", "Cape Verde": "Cabo Verde",
    "Kyrgyzstan": "Kyrgyz Republic", "Macedonia": "North Macedonia",
    "Micronesia": "Micronesia, Fed. Sts.",
}
cm["Country_for_join"] = cm["Country"].replace(name_map)
m = cm.merge(wb, left_on="Country_for_join", right_on="Country_WB", how="left")
m = m.dropna(subset=["NY.GDP.PCAP.CD", "SP.POP.TOTL", "Actual_Medals_2016"]).copy()
m = m[(m["NY.GDP.PCAP.CD"] > 0) & (m["SP.POP.TOTL"] > 0)].copy()
m["log_gdp_pc"] = np.log(m["NY.GDP.PCAP.CD"])
m["log_pop"] = np.log(m["SP.POP.TOTL"])
X = m[["log_pop", "log_gdp_pc"]]
y = m["Actual_Medals_2016"]

model = PoissonRegressor(alpha=0.1, max_iter=2000)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
m["Expected_Medals_OOF"] = np.maximum(cross_val_predict(model, X, y, cv=kf, method="predict"), 0)
m["RAPI"] = m["Actual_Medals_2016"] - m["Expected_Medals_OOF"]
m = m.sort_values("RAPI", ascending=False)

rap_points = [
    {"country": r.Country, "expected_medals": round(float(r.Expected_Medals_OOF), 2),
     "actual_medals": int(r.Actual_Medals_2016), "rapi": round(float(r.RAPI), 2),
     "category": "Over baseline" if r.RAPI >= 0 else "Under baseline"}
    for _, r in m.iterrows()
]
json.dump({
    "description": "Data for the resource-adjusted medal performance scatter chart — actual vs "
                   "expected (model-predicted) Rio 2016 medals for every participating country. "
                   "Plot x = expected_medals, y = actual_medals, with a y = x parity line; color "
                   "by category. Points above the line (Over baseline) beat their resource "
                   "baseline; points below (Under baseline) fall short. rapi = actual - expected.",
    "data": rap_points,
}, open("resource_adjusted_performance.json", "w"), indent=2)

# ---- console check ----
print("peak_age_windows.json           :", len(age_points), "sports")
print("country_strategy_clusters.json  :", len(cluster_points), "countries",
      "(", sum(p["cluster"] == "Specialist" for p in cluster_points), "specialist /",
      sum(p["cluster"] == "Generalist" for p in cluster_points), "generalist )")
print("resource_adjusted_performance.json:", len(rap_points), "countries",
      "(", sum(p["category"] == "Over baseline" for p in rap_points), "over /",
      sum(p["category"] == "Under baseline" for p in rap_points), "under )")
print("\nsample age:", age_points[0], age_points[-1])
print("sample cluster:", cluster_points[0])
print("sample rapi top/bottom:", rap_points[0], rap_points[-1])
