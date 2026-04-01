from __future__ import annotations

import os
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ATHLETE_PATH = DATA_DIR / "athlete_events.csv"
NOC_PATH = DATA_DIR / "noc_regions.csv"
EXTERNAL_PATH = DATA_DIR / "external_context.csv"


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing required file: {path}. Put the Kaggle CSV in the data folder."
        )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    require_file(ATHLETE_PATH)
    require_file(NOC_PATH)
    require_file(EXTERNAL_PATH)

    athletes = pd.read_csv(ATHLETE_PATH)
    noc = pd.read_csv(NOC_PATH)
    ext = pd.read_csv(EXTERNAL_PATH)

    athletes = athletes.merge(noc[["NOC", "region"]], on="NOC", how="left")
    athletes["region"] = athletes["region"].fillna(athletes["NOC"])
    athletes["is_medalist"] = athletes["Medal"].notna().astype(int)
    athletes["is_female"] = (athletes["Sex"] == "F").astype(int)
    athletes["BMI"] = athletes["Weight"] / ((athletes["Height"] / 100) ** 2)
    athletes.loc[~np.isfinite(athletes["BMI"]), "BMI"] = np.nan
    return athletes, noc, ext


def save_plot(filename: str, title: str, xlabel: str = "", ylabel: str = "") -> None:
    plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close()


def chart_gender_parity(athletes: pd.DataFrame) -> pd.DataFrame:
    summer = athletes[athletes["Season"] == "Summer"].copy()
    yearly = (
        summer.groupby("Year")
        .agg(female_share=("is_female", "mean"), athletes=("ID", "count"))
        .reset_index()
    )
    plt.figure(figsize=(10, 6))
    plt.plot(yearly["Year"], yearly["female_share"] * 100, marker="o")
    plt.axhline(50, linestyle="--")
    save_plot(
        "01_gender_parity_trend.png",
        "Female Participation Share in Summer Olympics Over Time",
        "Year",
        "Female Share (%)",
    )
    return yearly


def chart_medal_efficiency(athletes: pd.DataFrame) -> pd.DataFrame:
    summer = athletes[athletes["Season"] == "Summer"].copy()
    noc_perf = (
        summer.groupby("region")
        .agg(
            athletes=("ID", "count"),
            medalists=("is_medalist", "sum"),
            avg_age=("Age", "mean"),
        )
        .reset_index()
    )
    noc_perf = noc_perf[noc_perf["athletes"] >= 150]
    noc_perf["medal_efficiency"] = noc_perf["medalists"] / noc_perf["athletes"]
    top = noc_perf.sort_values("medal_efficiency", ascending=False).head(15)

    plt.figure(figsize=(11, 7))
    plt.barh(top["region"], top["medal_efficiency"] * 100)
    plt.gca().invert_yaxis()
    save_plot(
        "02_top_nocs_medal_efficiency.png",
        "Top NOCs by Medal Efficiency (min. 150 athlete entries)",
        "Medalists per 100 athlete entries",
        "NOC Region",
    )
    return noc_perf.sort_values("medal_efficiency", ascending=False)


def chart_age_profile(athletes: pd.DataFrame) -> pd.DataFrame:
    sport_age = (
        athletes.groupby("Sport")
        .agg(avg_age=("Age", "mean"), athlete_count=("ID", "count"))
        .reset_index()
        .dropna()
    )
    sport_age = sport_age[sport_age["athlete_count"] >= 500]
    top_oldest = sport_age.sort_values("avg_age", ascending=False).head(12)

    plt.figure(figsize=(11, 7))
    plt.barh(top_oldest["Sport"], top_oldest["avg_age"])
    plt.gca().invert_yaxis()
    save_plot(
        "03_age_profile_by_sport.png",
        "Oldest-Average Olympic Sports (min. 500 athlete entries)",
        "Average Age",
        "Sport",
    )
    return sport_age.sort_values("avg_age", ascending=False)


def build_noc_cluster_table(athletes: pd.DataFrame) -> pd.DataFrame:
    summer = athletes[athletes["Season"] == "Summer"].copy()
    latest_year = summer["Year"].max()
    recent = summer[summer["Year"] >= latest_year - 20]

    noc_features = (
        recent.groupby("region")
        .agg(
            athletes=("ID", "count"),
            medalists=("is_medalist", "sum"),
            female_share=("is_female", "mean"),
            avg_age=("Age", "mean"),
            sports=("Sport", pd.Series.nunique),
        )
        .reset_index()
        .dropna()
    )
    noc_features = noc_features[noc_features["athletes"] >= 40].copy()
    noc_features["medal_efficiency"] = noc_features["medalists"] / noc_features["athletes"]

    model_features = noc_features[
        ["athletes", "medal_efficiency", "female_share", "avg_age", "sports"]
    ]
    scaler = StandardScaler()
    X = scaler.fit_transform(model_features)

    kmeans = KMeans(n_clusters=4, n_init=20, random_state=42)
    noc_features["cluster"] = kmeans.fit_predict(X)

    label_map = {}
    cluster_summary = (
        noc_features.groupby("cluster")
        .agg(athletes=("athletes", "mean"), medal_efficiency=("medal_efficiency", "mean"))
        .reset_index()
        .sort_values(["medal_efficiency", "athletes"], ascending=False)
    )
    names = [
        "Elite Efficient",
        "Large Delegation",
        "Emerging Balanced",
        "Niche / Developing",
    ]
    for i, row in cluster_summary.iterrows():
        label_map[row["cluster"]] = names[min(i, len(names) - 1)]
    noc_features["cluster_label"] = noc_features["cluster"].map(label_map)

    plt.figure(figsize=(10, 7))
    for label in noc_features["cluster_label"].unique():
        subset = noc_features[noc_features["cluster_label"] == label]
        plt.scatter(subset["athletes"], subset["medal_efficiency"] * 100, label=label)
    plt.legend()
    save_plot(
        "04_noc_clusters.png",
        "NOC Clusters: Delegation Size vs Medal Efficiency",
        "Athlete Entries (recent Summer Games)",
        "Medal Efficiency (%)",
    )

    noc_features.sort_values(["cluster_label", "medal_efficiency"], ascending=[True, False]).to_csv(
        OUT_DIR / "noc_cluster_table.csv", index=False
    )
    return noc_features


def chart_opportunity_score(
    athletes: pd.DataFrame, noc_clusters: pd.DataFrame, external: pd.DataFrame
) -> pd.DataFrame:
    summer = athletes[athletes["Season"] == "Summer"].copy()
    recent = summer[summer["Year"] >= summer["Year"].max() - 20]

    noc_summary = (
        recent.groupby("region")
        .agg(
            athletes=("ID", "count"),
            medalists=("is_medalist", "sum"),
            female_share=("is_female", "mean"),
            sports=("Sport", pd.Series.nunique),
        )
        .reset_index()
    )
    noc_summary = noc_summary[noc_summary["athletes"] >= 40].copy()
    noc_summary["medal_efficiency"] = noc_summary["medalists"] / noc_summary["athletes"]

    completed = float(external.loc[external["metric"] == "projects_completed_28x28", "value"].iloc[0])
    in_progress = float(external.loc[external["metric"] == "projects_in_progress_28x28", "value"].iloc[0])
    foreign_born = float(external.loc[external["metric"] == "la_county_foreign_born_share", "value"].iloc[0])

    transit_readiness = completed / (completed + in_progress)
    multilingual_support = foreign_born / 100.0
    venue_reuse_bonus = 1.0

    noc_summary["delegation_scale_norm"] = noc_summary["athletes"] / noc_summary["athletes"].max()
    noc_summary["medal_eff_norm"] = noc_summary["medal_efficiency"] / noc_summary["medal_efficiency"].max()
    noc_summary["gender_balance_norm"] = 1 - (noc_summary["female_share"] - 0.5).abs() / 0.5
    noc_summary["sport_diversity_norm"] = noc_summary["sports"] / noc_summary["sports"].max()

    host_context_score = 0.4 * transit_readiness + 0.3 * multilingual_support + 0.3 * venue_reuse_bonus

    noc_summary["la28_opportunity_score"] = (
        0.35 * noc_summary["delegation_scale_norm"]
        + 0.30 * noc_summary["medal_eff_norm"]
        + 0.15 * noc_summary["gender_balance_norm"]
        + 0.20 * noc_summary["sport_diversity_norm"]
    ) * host_context_score * 100

    top = noc_summary.sort_values("la28_opportunity_score", ascending=False).head(15)
    plt.figure(figsize=(11, 7))
    plt.barh(top["region"], top["la28_opportunity_score"])
    plt.gca().invert_yaxis()
    save_plot(
        "05_la28_opportunity_score.png",
        "Top Delegations by Composite LA28 Opportunity Score",
        "Opportunity Score",
        "NOC Region",
    )
    return noc_summary.sort_values("la28_opportunity_score", ascending=False)


def chart_heat_risk_proxy(athletes: pd.DataFrame) -> pd.DataFrame:
    # Simple proxy for sports likely to need hydration/recovery support in warm-weather planning.
    # This is NOT medical advice; it is a planning heuristic using body size and outdoor-event intuition.
    outdoor_keywords = [
        "Athletics", "Cycling", "Rowing", "Triathlon", "Football", "Hockey",
        "Beach Volleyball", "Equestrian", "Sailing", "Canoeing", "Surfing"
    ]

    sport_profiles = (
        athletes.groupby("Sport")
        .agg(avg_weight=("Weight", "mean"), avg_height=("Height", "mean"), athlete_count=("ID", "count"))
        .reset_index()
        .dropna()
    )
    sport_profiles = sport_profiles[sport_profiles["athlete_count"] >= 100]
    sport_profiles["outdoor_flag"] = sport_profiles["Sport"].isin(outdoor_keywords).astype(int)
    sport_profiles["heat_risk_proxy"] = (
        0.5 * (sport_profiles["avg_weight"] / sport_profiles["avg_weight"].max()) +
        0.2 * (sport_profiles["avg_height"] / sport_profiles["avg_height"].max()) +
        0.3 * sport_profiles["outdoor_flag"]
    )
    top = sport_profiles.sort_values("heat_risk_proxy", ascending=False).head(12)

    plt.figure(figsize=(11, 7))
    plt.barh(top["Sport"], top["heat_risk_proxy"])
    plt.gca().invert_yaxis()
    save_plot(
        "06_sport_heat_risk_proxy.png",
        "Sport Heat-Logistics Risk Proxy for LA28 Planning",
        "Composite Risk Proxy",
        "Sport",
    )
    return sport_profiles.sort_values("heat_risk_proxy", ascending=False)


def export_summary(
    gender_trend: pd.DataFrame,
    medal_eff: pd.DataFrame,
    sport_age: pd.DataFrame,
    clusters: pd.DataFrame,
    opp: pd.DataFrame,
    heat: pd.DataFrame,
) -> pd.DataFrame:
    summary_rows = [
        {
            "finding": "Latest female participation share",
            "value": round(gender_trend.iloc[-1]["female_share"] * 100, 2),
            "notes": f"Year {int(gender_trend.iloc[-1]['Year'])}",
        },
        {
            "finding": "Most medal-efficient NOC",
            "value": medal_eff.iloc[0]["region"],
            "notes": round(medal_eff.iloc[0]["medal_efficiency"] * 100, 2),
        },
        {
            "finding": "Oldest-average sport",
            "value": sport_age.iloc[0]["Sport"],
            "notes": round(sport_age.iloc[0]["avg_age"], 2),
        },
        {
            "finding": "Highest LA28 opportunity score",
            "value": opp.iloc[0]["region"],
            "notes": round(opp.iloc[0]["la28_opportunity_score"], 2),
        },
        {
            "finding": "Highest heat-logistics proxy sport",
            "value": heat.iloc[0]["Sport"],
            "notes": round(heat.iloc[0]["heat_risk_proxy"], 3),
        },
        {
            "finding": "Largest cluster label by count",
            "value": clusters["cluster_label"].value_counts().idxmax(),
            "notes": int(clusters["cluster_label"].value_counts().max()),
        },
    ]
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DIR / "final_summary.csv", index=False)
    return summary


def main() -> None:
    athletes, _, external = load_data()
    gender_trend = chart_gender_parity(athletes)
    medal_eff = chart_medal_efficiency(athletes)
    sport_age = chart_age_profile(athletes)
    clusters = build_noc_cluster_table(athletes)
    opp = chart_opportunity_score(athletes, clusters, external)
    heat = chart_heat_risk_proxy(athletes)
    summary = export_summary(gender_trend, medal_eff, sport_age, clusters, opp, heat)

    print("Done. Files written to outputs/")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
