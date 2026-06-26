"""
Reproduce the two NATIVE PowerPoint charts (host-city zone load, peak age windows)
as high-res PNGs, using the exact data, bar colors, and Arial font pulled from the
.pptx chart XML so they match the slides as closely as possible.
Run:  python3.9 render_native_charts.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams["font.family"] = "Arial"

BG = "#F0F4F8"        # slide chart background (matches extracted PPT chart images)
TEXT = "#334155"      # slate label text
GRID = "#D8E0EA"

def hbar(path, cats, vals, colors, value_fmt, xlabel, xpad_frac=0.16):
    n = len(cats)
    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    y = range(n)
    bars = ax.barh(y, vals, color=colors, height=0.72, edgecolor="none", zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(cats, fontsize=12.5, color=TEXT)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=TEXT, labelsize=10.5)
    # value labels at bar ends
    xmax = max(vals)
    ax.set_xlim(0, xmax * (1 + xpad_frac))
    for b, v in zip(bars, vals):
        ax.text(v + xmax * 0.012, b.get_y() + b.get_height() / 2,
                value_fmt(v), va="center", ha="left",
                fontsize=11.5, color=TEXT, fontweight="bold", zorder=4)
    ax.set_xlabel(xlabel, fontsize=11.5, color=TEXT, labelpad=8)
    ax.xaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    plt.tight_layout()
    plt.savefig(path, facecolor=BG, bbox_inches="tight", dpi=200)
    plt.close()
    print("wrote", path)

# ---- HOST CITY (chart1, slide 4): athletes per LA28 zone ----
TEAL, GOLD = "#0D9488", "#C9A227"
host_cats = ["San Fernando Valley", "Venice", "Pacific Palisades", "Arcadia", "Anaheim",
             "Pasadena", "Inglewood", "Carson", "Long Beach", "Downtown / Expo"]
host_vals = [72, 110, 120, 200, 283, 609, 1223, 1526, 2455, 4581]
host_colors = [TEAL] * 7 + [GOLD] * 3     # top 3 zones highlighted gold (per chart XML)
hbar("chart_imgs/host_city_zone_load.png", host_cats, host_vals, host_colors,
     value_fmt=lambda v: f"{v:,}", xlabel="Athletes (Rio 2016)")

# ---- PEAK AGE (chart2, slide 10): median medal age, age-graded color ----
age_cats = ["Rhythmic Gym.", "Swimming", "Athletics", "Weightlifting", "Wrestling",
            "Cycling", "Judo", "Shooting", "Equestrian"]
age_vals = [18, 22, 25, 26, 26, 27, 27, 32, 34]
age_colors = ["#0D9488", "#0D9488", "#1A7A6E", "#D97706", "#D97706", "#D97706",
              "#B45309", "#B91C1C", "#991B1B"]   # exact dPt colors from chart XML
hbar("chart_imgs/peak_age_windows.png", age_cats, age_vals, age_colors,
     value_fmt=lambda v: f"{v}", xlabel="Median medal-winning age", xpad_frac=0.10)
