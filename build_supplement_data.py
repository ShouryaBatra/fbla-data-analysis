"""
Master computation script for the FBLA Data Analysis technical supplement.
Reproduces the exact logic of the repo notebooks, using LOCAL datasets only
(no live World Bank API call). Emits supplement_data.json with every table.
Run:  python3.9 build_supplement_data.py
"""
import json
import numpy as np
import pandas as pd

DATA = "datasets"
OUT = {}

# ----------------------------------------------------------------------------
# Load base data
# ----------------------------------------------------------------------------
athletes = pd.read_csv(f"{DATA}/athlete_events.csv")
noc = pd.read_csv(f"{DATA}/noc_regions.csv")

# ============================================================================
# APPENDIX A  —  HOST-CITY ZONE LOAD  (from LA28_zone_load_analysis.ipynb)
# ============================================================================
rio = athletes[(athletes['Year'] == 2016) & (athletes['Season'] == 'Summer')].copy()

zone_map = {
    'Athletics': 'Downtown/Exposition Park', 'Gymnastics': 'Downtown/Exposition Park',
    'Trampolining': 'Downtown/Exposition Park', 'Rhythmic Gymnastics': 'Downtown/Exposition Park',
    'Boxing': 'Downtown/Exposition Park', 'Weightlifting': 'Downtown/Exposition Park',
    'Fencing': 'Downtown/Exposition Park', 'Judo': 'Downtown/Exposition Park',
    'Table Tennis': 'Downtown/Exposition Park', 'Taekwondo': 'Downtown/Exposition Park',
    'Wrestling': 'Downtown/Exposition Park', 'Badminton': 'Downtown/Exposition Park',
    'Synchronized Swimming': 'Long Beach', 'Water Polo': 'Long Beach',
    'Handball': 'Long Beach', 'Rowing': 'Long Beach', 'Canoeing': 'Long Beach',
    'Sailing': 'Long Beach', 'Beach Volleyball': 'Long Beach', 'Shooting': 'Long Beach',
    'Cycling': 'Carson', 'Hockey': 'Carson', 'Rugby Sevens': 'Carson',
    'Archery': 'Carson', 'Tennis': 'Carson',
    'Swimming': 'Inglewood', 'Basketball': 'Inglewood',
    'Diving': 'Pasadena', 'Football': 'Pasadena',
    'Volleyball': 'Anaheim', 'Equestrianism': 'Arcadia',
    'Golf': 'Pacific Palisades', 'Triathlon': 'Venice',
    'Modern Pentathlon': 'San Fernando Valley',
}
# primary venue note per zone (for narrative)
zone_primary_venue = {
    'Downtown/Exposition Park': 'LA Memorial Coliseum / Convention Center / Crypto.com Arena',
    'Long Beach': 'Long Beach Arena, Marine Stadium & Convention Center pool',
    'Carson': 'Dignity Health Sports Park (CSU Dominguez Hills)',
    'Inglewood': 'SoFi Stadium / Intuit Dome',
    'Pasadena': 'Rose Bowl & Rose Bowl Aquatics Center',
    'Anaheim': 'Honda Center', 'Arcadia': 'Santa Anita Park',
    'Pacific Palisades': 'Riviera Country Club', 'Venice': 'Venice Beach',
    'San Fernando Valley': 'Sepulveda Basin',
}
unmapped = set(rio['Sport'].unique()) - set(zone_map)
assert not unmapped, f"Unmapped sports: {unmapped}"

rio['Zone'] = rio['Sport'].map(zone_map)
total = rio['ID'].nunique()
n_returning_sports = rio['Sport'].nunique()

zone_load = rio.groupby('Zone')['ID'].nunique().sort_values(ascending=False).rename('athletes')
zone_sports = rio.groupby('Zone')['Sport'].nunique().rename('n_sports')
zs = pd.concat([zone_load, zone_sports], axis=1)
zs['share'] = (zs['athletes'] / total * 100).round(1)
zs['load_index'] = (zs['athletes'] / zs['athletes'].max() * 100).round(1)

OUT['appendixA'] = {
    'reference_games': 'Rio 2016 (Summer)',
    'total_athletes': int(total),
    'n_returning_sports': int(n_returning_sports),
    'top3_share': round(float(zs['share'].head(3).sum()), 1),
    'zones': [
        {'zone': z, 'athletes': int(r.athletes), 'share': float(r.share),
         'n_sports': int(r.n_sports), 'load_index': float(r.load_index),
         'primary_venue': zone_primary_venue[z]}
        for z, r in zs.iterrows()
    ],
    'sport_zone_map': [
        {'sport': s, 'zone': zone_map[s], 'athletes': int(rio[rio['Sport'] == s]['ID'].nunique())}
        for s in sorted(zone_map, key=lambda s: (zone_map[s], -rio[rio['Sport'] == s]['ID'].nunique()))
    ],
}

# robustness: top zone & top-3 share across 2008/2012/2016
def zone_shares(year):
    g = athletes[(athletes['Year'] == year) & (athletes['Season'] == 'Summer')].copy()
    g['Zone'] = g['Sport'].map(zone_map)
    g = g.dropna(subset=['Zone'])
    z = g.groupby('Zone')['ID'].nunique()
    return (z / z.sum() * 100)

robust = {}
for yr in [2008, 2012, 2016]:
    s = zone_shares(yr).sort_values(ascending=False)
    robust[yr] = {'downtown': round(float(s.get('Downtown/Exposition Park', 0)), 1),
                  'top3': round(float(s.head(3).sum()), 1)}
OUT['appendixA']['robustness'] = robust

# ============================================================================
# APPENDIX B  —  NOC OVER/UNDERPERFORMERS  (from gdpRegression.ipynb)
# ============================================================================
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.metrics.pairwise import euclidean_distances

df = athletes.merge(noc, on="NOC", how="left").rename(columns={"region": "Country"})
df = df[df["Season"] == "Summer"].copy()
df["Medal_Won"] = df["Medal"].notna().astype(int)

rioB = df[df["Year"] == 2016].copy()
rioB = rioB[rioB["Country"].notna()].copy()
participants = rioB[["Country"]].drop_duplicates().copy()
rio_medals = rioB[rioB["Medal"].notna()].copy()
event_cols = ["Games", "Year", "Season", "City", "Sport", "Event", "NOC", "Medal"]
rio_event_medals = rio_medals.drop_duplicates(event_cols).copy()
medals_2016 = rio_event_medals.groupby("Country").size().reset_index(name="Actual_Medals_2016")
cm = participants.merge(medals_2016, on="Country", how="left").fillna({"Actual_Medals_2016": 0})
cm["Actual_Medals_2016"] = cm["Actual_Medals_2016"].astype(int)

# Local World Bank load (mirror of fetch_wb_indicator_bulk, year=2016)
def wb_local(path, code):
    d = pd.read_csv(path, skiprows=4)
    out = d[["Country Name", "Country Code", "2016"]].copy()
    out.columns = ["Country_WB", "ISO3_WB", code]
    return out

wb_gdp = wb_local(f"{DATA}/gdp_data/API_NY.GDP.PCAP.CD_DS2_en_csv_v2_432207/API_NY.GDP.PCAP.CD_DS2_en_csv_v2_432207.csv", "NY.GDP.PCAP.CD")
wb_pop = wb_local(f"{DATA}/gdp_data/API_SP.POP.TOTL_DS2_en_csv_v2_430662/API_SP.POP.TOTL_DS2_en_csv_v2_430662.csv", "SP.POP.TOTL")
wb = wb_gdp.merge(wb_pop, on=["Country_WB", "ISO3_WB"], how="outer")

wb_clean = wb[wb["ISO3_WB"].notna()]
wb_clean = wb_clean[wb_clean["ISO3_WB"].str.len() == 3]
agg_keywords = ["income", "IDA", "IBRD", "World", "Euro area", "European Union", "OECD",
                "Arab World", "Sub-Saharan", "Latin America", "Caribbean", "Middle East",
                "North America", "South Asia", "East Asia", "Pacific", "Africa",
                "small states", "Fragile", "Heavily indebted", "countries"]
mask = wb_clean["Country_WB"].str.contains("|".join(agg_keywords), case=False, na=False)
wb_clean = wb_clean[~mask].copy()

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
model_df = cm.merge(wb_clean, left_on="Country_for_join", right_on="Country_WB", how="left")

m = model_df.dropna(subset=["NY.GDP.PCAP.CD", "SP.POP.TOTL", "Actual_Medals_2016"]).copy()
m = m[(m["NY.GDP.PCAP.CD"] > 0) & (m["SP.POP.TOTL"] > 0)].copy()
m["log_gdp_pc"] = np.log(m["NY.GDP.PCAP.CD"])
m["log_pop"] = np.log(m["SP.POP.TOTL"])
X = m[["log_pop", "log_gdp_pc"]].copy()
y = m["Actual_Medals_2016"].copy()

model = PoissonRegressor(alpha=0.1, max_iter=2000)
kf = KFold(n_splits=min(5, len(m)), shuffle=True, random_state=42)
m["Expected_Medals_OOF"] = np.maximum(cross_val_predict(model, X, y, cv=kf, method="predict"), 0)
model.fit(X, y)
m["RAPI"] = m["Actual_Medals_2016"] - m["Expected_Medals_OOF"]

oof_r2 = float(r2_score(y, m["Expected_Medals_OOF"]))
oof_mae = float(mean_absolute_error(y, m["Expected_Medals_OOF"]))

def perf_rows(frame):
    return [{
        'country': r.Country, 'actual': int(r.Actual_Medals_2016),
        'expected': round(float(r.Expected_Medals_OOF), 2), 'rapi': round(float(r.RAPI), 2),
        'gdp_pc': round(float(r["NY.GDP.PCAP.CD"]), 0), 'pop': int(r["SP.POP.TOTL"]),
    } for _, r in frame.iterrows()]

over = m[m["RAPI"] > 0].sort_values("RAPI", ascending=False)
under_all = m[m["RAPI"] < 0].sort_values("RAPI", ascending=True)
# Focused underperformers: expected >= 1 medal (drops trivial near-zero micro-states)
under = under_all[under_all["Expected_Medals_OOF"] >= 1.0].copy()

# Peer benchmark (nearest overperformer by resource distance)
peer_df = m[["Country", "log_pop", "log_gdp_pc", "RAPI", "Actual_Medals_2016",
             "Expected_Medals_OOF"]].copy()
over_c = peer_df[peer_df["RAPI"] > 0].copy()
under_c = peer_df[(peer_df["RAPI"] < 0) & (peer_df["Expected_Medals_OOF"] >= 1.0)].copy()

def nearest(u_row, k=1):
    d = euclidean_distances([[u_row["log_pop"], u_row["log_gdp_pc"]]],
                            over_c[["log_pop", "log_gdp_pc"]].values).flatten()
    order = d.argsort()
    return [(over_c.iloc[i], float(d[i])) for i in order[:k]]

peer_rows = []
for _, u in under_c.iterrows():
    peer, dist = nearest(u, 1)[0]
    peer_rows.append({
        'under': u["Country"], 'under_rapi': round(float(u["RAPI"]), 2),
        'peer': peer["Country"], 'peer_rapi': round(float(peer["RAPI"]), 2),
        'peer_actual': int(peer["Actual_Medals_2016"]),
        'distance': round(float(dist), 3),
    })
peer_recs = sorted(peer_rows, key=lambda x: x['distance'])

# Jordan: alternative comparable peer (Belarus), for the speech note
jordan = under_c[under_c["Country"] == "Jordan"].iloc[0]
jtop = nearest(jordan, 5)
jordan_alts = [{'peer': p["Country"], 'distance': round(dd, 3),
                'peer_rapi': round(float(p["RAPI"]), 2), 'peer_actual': int(p["Actual_Medals_2016"])}
               for p, dd in jtop]

OUT['appendixB'] = {
    'reference_games': 'Rio 2016 (Summer, event-level medal counts)',
    'model': 'Poisson regression (alpha=0.1) on log(population) & log(GDP per capita)',
    'n_countries': int(len(m)), 'n_over': int(len(over)),
    'n_under_total': int(len(under_all)), 'n_under_focused': int(len(under)),
    'oof_r2': round(oof_r2, 3), 'oof_mae': round(oof_mae, 3),
    'coef': {'log_pop': round(float(model.coef_[0]), 3), 'log_gdp_pc': round(float(model.coef_[1]), 3)},
    'intercept': round(float(model.intercept_), 3),
    'overperformers': perf_rows(over),
    'underperformers': perf_rows(under),
    'peers': peer_recs,
    'jordan_alts': jordan_alts,
}

# ============================================================================
# APPENDIX C  —  COUNTRY STRATEGY CLASSIFICATION  (corrected, defensible)
# Root-cause fix: original KMeans ran on the full sport-share vector, so it
# split countries by WHICH sport they win in, not HOW concentrated they are.
# A hockey-only nation (Pakistan) landed far from the athletics-specialist
# cluster and got mislabeled "Generalist." Fix: (1) count medals at EVENT level
# (dedupe team rows), (2) cluster on a concentration feature set so the split
# is by degree of specialization.
# ============================================================================
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

dfc = athletes.merge(noc, on="NOC", how="left").rename(columns={"region": "Country"})
dfc = dfc[dfc["Season"] == "Summer"].copy()
dfc = dfc[dfc["Medal"].notna() & dfc["Country"].notna()].copy()
# event-level medals (one medal per event/team, not per athlete)
ev_cols = ["Games", "Year", "Season", "City", "Sport", "Event", "NOC", "Medal"]
ev = dfc.drop_duplicates(ev_cols).copy()

mcs = ev.groupby(["Country", "Sport"]).size().reset_index(name="medals")
tot = mcs.groupby("Country")["medals"].sum().reset_index(name="total")
mcs = mcs.merge(tot, on="Country")
mcs["share"] = mcs["medals"] / mcs["total"]

MIN_MEDALS = 20  # same threshold as clustering notebook; <20 dropped as unstable
elig = tot[tot["total"] >= MIN_MEDALS]["Country"]
mcs_e = mcs[mcs["Country"].isin(elig)].copy()

# per-country concentration features
hhi = mcs_e.groupby("Country")["share"].apply(lambda s: float((s**2).sum())).rename("hhi")
eff = (1.0 / hhi).rename("eff_sports")
topshare = mcs_e.sort_values("share", ascending=False).groupby("Country").first()["share"].rename("top_share")
topsport = mcs_e.loc[mcs_e.groupby("Country")["share"].idxmax()].set_index("Country")["Sport"].rename("top_sport")
feat = pd.concat([tot.set_index("Country")["total"], hhi, eff, topshare, topsport], axis=1).loc[elig]

# KMeans k=2 on the standardized concentration features (HHI + effective sports)
Xc = StandardScaler().fit_transform(feat[["hhi", "eff_sports"]].values)
km = KMeans(n_clusters=2, random_state=42, n_init=10)
feat["cluster"] = km.fit_predict(Xc)
# label by mean effective sports: lower eff -> Specialist
mean_eff = feat.groupby("cluster")["eff_sports"].mean().sort_values()
label_map = {mean_eff.index[0]: "Specialist", mean_eff.index[-1]: "Generalist"}
feat["label"] = feat["cluster"].map(label_map)

feat = feat.sort_values(["label", "eff_sports"])
OUT['appendixC'] = {
    'method': 'KMeans (k=2) on concentration features [HHI, effective sports] over all-time Summer event-level medals',
    'min_medals': MIN_MEDALS,
    'n_classified': int(len(feat)),
    'n_specialist': int((feat["label"] == "Specialist").sum()),
    'n_generalist': int((feat["label"] == "Generalist").sum()),
    'rows': [{
        'country': c, 'label': r.label, 'total_medals': int(r.total),
        'top_sport': r.top_sport, 'top_share': round(float(r.top_share) * 100, 1),
        'hhi': round(float(r.hhi), 3), 'eff_sports': round(float(r.eff_sports), 2),
    } for c, r in feat.iterrows()],
}
# Pakistan footnote: low-count specialist excluded by threshold
pak = mcs[mcs["Country"] == "Pakistan"]
if len(pak):
    pak_total = int(pak["medals"].sum())
    pak_top = pak.sort_values("medals", ascending=False).iloc[0]
    OUT['appendixC']['pakistan_note'] = {
        'total_medals': pak_total, 'top_sport': pak_top["Sport"],
        'top_share': round(float(pak_top["medals"] / pak_total) * 100, 0),
    }

# sanity references for review
OUT['appendixC']['_sanity'] = {c: (feat.loc[c, 'label'] if c in feat.index else 'EXCLUDED(<%d)' % MIN_MEDALS)
                               for c in ['Pakistan', 'India', 'Jamaica', 'Kenya', 'China',
                                         'Germany', 'UK', 'USA', 'Ethiopia', 'Norway', 'Cuba', 'Hungary']}

# ============================================================================
# APPENDIX D  —  PEAK AGE WINDOWS  (from olympics_analysis.ipynb)
# ============================================================================
dfd = athletes.merge(noc, on="NOC", how="left")
dfd["Medal_Won"] = dfd["Medal"].notna().astype(int)
dfd = dfd[dfd["Season"] == "Summer"].copy()   # Summer-only for LA28 consistency
medal_ages = dfd[(dfd["Medal_Won"] == 1) & (dfd["Age"].notna())][["Sport", "Age"]]
MIN_AGE_MEDALS = 100
agg = medal_ages.groupby("Sport")["Age"].agg(
    median="median", q1=lambda x: x.quantile(0.25), q3=lambda x: x.quantile(0.75), n="count"
).reset_index()
agg = agg[agg["n"] >= MIN_AGE_MEDALS]
# Exclude discontinued / non-program events (not on the 2028 program)
DISCONTINUED = {"Art Competitions", "Rugby"}  # 1912-48 arts; 1900-24 15-a-side rugby
agg = agg[~agg["Sport"].isin(DISCONTINUED)].sort_values("median")
OUT['appendixD'] = {
    'min_medals': MIN_AGE_MEDALS,
    'scope': 'All-time Summer Olympic medal-winning athletes (athlete-level), age recorded',
    'rows': [{
        'sport': r.Sport, 'median': round(float(r["median"]), 1),
        'q1': round(float(r.q1), 1), 'q3': round(float(r.q3), 1),
        'iqr': round(float(r.q3 - r.q1), 1), 'n': int(r.n),
    } for _, r in agg.iterrows()],
}

# ============================================================================
# APPENDIX E  —  NEW LA28 SPORTS (scope addendum)
# Comparable-sport load anchors computed from the data (Rio 2016 unique
# athletes; baseball/softball from Beijing 2008, their last Olympic Games).
# ============================================================================
def rio_sport_load(sport):
    return int(rio[rio['Sport'] == sport]['ID'].nunique())

def games_sport_load(sport, year):
    g = athletes[(athletes['Year'] == year) & (athletes['Season'] == 'Summer')]
    return int(g[g['Sport'] == sport]['ID'].nunique())

OUT['appendixE'] = {
    'comparables': {
        'Hockey (field)': rio_sport_load('Hockey'),
        'Rugby Sevens': rio_sport_load('Rugby Sevens'),
        'Basketball': rio_sport_load('Basketball'),
        'Table Tennis': rio_sport_load('Table Tennis'),
        'Badminton': rio_sport_load('Badminton'),
        'Tennis': rio_sport_load('Tennis'),
        'Baseball (Beijing 2008)': games_sport_load('Baseball', 2008),
        'Softball (Beijing 2008)': games_sport_load('Softball', 2008),
    },
}

# ============================================================================
# APPENDIX A reconciliation: 31 returning sports vs 34 dataset categories
# ============================================================================
OUT['appendixA']['scope_note'] = {
    'dataset_categories': int(n_returning_sports),  # 34
    'la28_returning_sports': 31,
    'grouped_disciplines': ['Rhythmic Gymnastics (→ Gymnastics)',
                            'Trampolining (→ Gymnastics)',
                            'Beach Volleyball (→ Volleyball)'],
}

# ============================================================================
# WRITE
# ============================================================================
with open("supplement_data.json", "w") as f:
    json.dump(OUT, f, indent=2)

# ---- console review ----
print("=" * 70)
print("APPENDIX A — zones:", len(OUT['appendixA']['zones']),
      "| total athletes:", total, "| returning sports:", n_returning_sports,
      "| top3 share:", OUT['appendixA']['top3_share'], "%")
print("  robustness:", robust)
print("=" * 70)
print("APPENDIX B — OOF R2:", round(oof_r2, 3), "| MAE:", round(oof_mae, 3),
      "| n:", len(m), "| coef:", OUT['appendixB']['coef'])
print("  #over:", len(over), "#under:", len(under))
jor = [p for p in peer_recs if p['under'] == 'Jordan']
print("  Jordan peer:", jor)
print("  top5 peers by distance:", peer_recs[:5])
print("=" * 70)
print("APPENDIX C — classified:", len(feat),
      "| specialists:", OUT['appendixC']['n_specialist'],
      "| generalists:", OUT['appendixC']['n_generalist'])
print("  SANITY:", OUT['appendixC']['_sanity'])
print("  specialists:", feat[feat.label == 'Specialist'].index.tolist())
print("=" * 70)
print("APPENDIX D — sports:", len(OUT['appendixD']['rows']),
      "| youngest:", OUT['appendixD']['rows'][0], "| oldest:", OUT['appendixD']['rows'][-1])
print("done -> supplement_data.json")
