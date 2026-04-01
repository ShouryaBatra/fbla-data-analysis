# FBLA Data Analysis Project — LA28 Olympic Intelligence Engine

This project generates an FBLA-ready data analysis using the Kaggle Olympic datasets:
- `athlete_events.csv`
- `noc_regions.csv`

## What it does
It builds an outside-the-box story for the 2028 Los Angeles Olympics:
- historical Olympic trend analysis
- gender parity momentum
- age and physical profile patterns by sport
- medal efficiency by National Olympic Committee (NOC)
- unsupervised clustering of NOCs using scikit-learn
- a composite **LA28 Opportunity Score** that blends Olympic history with external host-city context
- saves polished graphs to `outputs/`
- exports summary tables to CSV

## Folder setup
Place your Kaggle files here:
- `data/athlete_events.csv`
- `data/noc_regions.csv`

`external_context.csv` is already included and is based on official LA28 / Metro / Census facts.

## Run
```bash
pip install -r requirements.txt
python fbla_olympic_analysis.py
```

## Main outputs
- `outputs/01_gender_parity_trend.png`
- `outputs/02_top_nocs_medal_efficiency.png`
- `outputs/03_age_profile_by_sport.png`
- `outputs/04_noc_clusters.png`
- `outputs/05_la28_opportunity_score.png`
- `outputs/06_sport_heat_risk_proxy.png`
- `outputs/final_summary.csv`
- `outputs/noc_cluster_table.csv`

## Presentation angle
Recommended thesis:
**LA28 should use predictive athlete-support zoning rather than one-size-fits-all planning.**

That means:
1. Use historical medal depth to identify likely high-volume delegations.
2. Use gender and sport shifts to predict changing service needs.
3. Use sport-specific body/age profiles as a proxy for hydration, recovery, and logistics planning.
4. Match athlete demand with a host-city model built around existing venues, transit buildout, and multilingual support.

## Source notes for external context
- LA28 says the Games use 40+ competition venues and no new permanent venues.
- LA Metro says 9 Twenty-Eight by '28 projects are completed and 19 are in progress.
- U.S. Census QuickFacts reports Los Angeles County is 33.4% foreign-born.

Use these in your bibliography with the official pages.
