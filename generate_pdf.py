"""
Render the SportsFanatics technical supplement PDF from supplement_data.json.
Run:  python3.9 generate_pdf.py
"""
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, NextPageTemplate,
                                KeepTogether, Image)
from PIL import Image as PILImage
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

D = json.load(open("supplement_data.json"))

# ---------------------------------------------------------------- fonts/colors
pdfmetrics.registerFont(TTFont("Raleway", "datasets/Raleway-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Raleway-Bold", "datasets/Raleway-Bold.ttf"))
pdfmetrics.registerFontFamily("Raleway", normal="Raleway", bold="Raleway-Bold",
                              italic="Raleway", boldItalic="Raleway-Bold")
REG, BOLD = "Raleway", "Raleway-Bold"

NAVY = colors.HexColor("#0d2340")
GOLD = colors.HexColor("#c79a2e")
TEAL = colors.HexColor("#1a8a82")
INK = colors.HexColor("#2b2f36")
MUTE = colors.HexColor("#6b7480")
ROW = colors.HexColor("#f3f5f8")
RULE = colors.HexColor("#d6dbe2")
WHITE = colors.white

# ---------------------------------------------------------------- styles
def P(name, **kw):
    base = dict(fontName=REG, fontSize=9, leading=12.5, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)

body = P("body", alignment=TA_JUSTIFY)
small = P("small", fontSize=7.6, leading=10, textColor=MUTE)
foot = P("foot", fontSize=8, leading=11, textColor=MUTE)
h_app = P("h_app", fontName=BOLD, fontSize=14.5, textColor=NAVY, leading=18,
          spaceBefore=4, spaceAfter=2)
# same look as h_app but excluded from the table of contents
h_app2 = P("h_app2", fontName=BOLD, fontSize=14.5, textColor=NAVY, leading=18,
           spaceBefore=4, spaceAfter=2)
h_sub = P("h_sub", fontName=BOLD, fontSize=10, textColor=TEAL, leading=13,
          spaceBefore=8, spaceAfter=3)
lead = P("lead", fontSize=9, leading=13, textColor=INK, spaceAfter=4)
cell = P("cell", fontSize=8, leading=10)
cellr = P("cellr", fontSize=8, leading=10, alignment=TA_RIGHT)
cellb = P("cellb", fontName=BOLD, fontSize=8, leading=10)
hcell = P("hcell", fontName=BOLD, fontSize=7.6, leading=9.5, textColor=WHITE)
hcellr = P("hcellr", fontName=BOLD, fontSize=7.6, leading=9.5, textColor=WHITE, alignment=TA_RIGHT)
# larger variants for sparse (few-column) tables
cell_lg = P("cell_lg", fontSize=9.7, leading=12.5)
cellr_lg = P("cellr_lg", fontSize=9.7, leading=12.5, alignment=TA_RIGHT)
cellb_lg = P("cellb_lg", fontName=BOLD, fontSize=9.7, leading=12.5)
hcell_lg = P("hcell_lg", fontName=BOLD, fontSize=9, leading=11, textColor=WHITE)
hcellr_lg = P("hcellr_lg", fontName=BOLD, fontSize=9, leading=11, textColor=WHITE, alignment=TA_RIGHT)

PAGE_W, PAGE_H = letter
LM = RM = 0.72 * inch
TM = 0.78 * inch
BM = 0.72 * inch
CONTENT_W = PAGE_W - LM - RM


# ---------------------------------------------------------------- table helpers
def th(text, right=False, big=False):
    if big:
        return Paragraph(text, hcellr_lg if right else hcell_lg)
    return Paragraph(text, hcellr if right else hcell)

def tc(text, align="l", bold=False, big=False):
    if big:
        if align == "r":
            return Paragraph(str(text), cellr_lg)
        return Paragraph(str(text), cellb_lg if bold else cell_lg)
    if align == "r":
        return Paragraph(str(text), cellr)
    return Paragraph(str(text), cellb if bold else cell)

def styled_table(rows, col_widths, aligns, fontsize=8, big=False):
    """rows[0] is header. aligns is list of 'l'/'r' per column."""
    rpad = 6 if big else 3
    hpad = 7 if big else 4.5
    header = [th(h, right=(aligns[i] == "r"), big=big) for i, h in enumerate(rows[0])]
    data = [header]
    for r in rows[1:]:
        data.append([tc(v, align=aligns[i], big=big) for i, v in enumerate(r)])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), hpad),
        ("BOTTOMPADDING", (0, 0), (-1, 0), hpad),
        ("TOPPADDING", (0, 1), (-1, -1), rpad),
        ("BOTTOMPADDING", (0, 1), (-1, -1), rpad),
        ("LEFTPADDING", (0, 0), (-1, -1), 7 if big else 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7 if big else 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, NAVY),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, RULE),
    ]
    t.setStyle(TableStyle(style))
    return t


def multicol(header, rows, col_widths, aligns, ncols=2, gap=0.22 * inch, big=False):
    """Lay rows out in ncols side-by-side blocks as a SINGLE table that splits
    naturally across page breaks (header repeats on each page)."""
    ncell = len(header)
    n = len(rows)
    per = -(-n // ncols)  # ceil
    chunks = [rows[i * per:(i + 1) * per] for i in range(ncols)]
    block_w = (CONTENT_W - gap * (ncols - 1)) / ncols
    scale = block_w / sum(col_widths)
    cw_block = [w * scale for w in col_widths]

    # build combined column widths: [block cols][gap][block cols]...
    colWidths = []
    block_starts = []
    for bi in range(ncols):
        block_starts.append(len(colWidths))
        colWidths += cw_block
        if bi < ncols - 1:
            colWidths.append(gap)

    def make_cell(v, ci):
        return tc(v, align=aligns[ci], big=big)

    # header row
    head_row = []
    for bi in range(ncols):
        for ci in range(ncell):
            head_row.append(th(header[ci], right=(aligns[ci] == "r"), big=big))
        if bi < ncols - 1:
            head_row.append("")
    data = [head_row]
    for i in range(per):
        row = []
        for bi in range(ncols):
            if i < len(chunks[bi]):
                src = chunks[bi][i]
                for ci in range(ncell):
                    row.append(make_cell(src[ci], ci))
            else:
                for ci in range(ncell):
                    row.append("")
            if bi < ncols - 1:
                row.append("")
        data.append(row)

    t = Table(data, colWidths=colWidths, repeatRows=1)
    rpad = 6 if big else 3
    hpad = 7 if big else 4.5
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7 if big else 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7 if big else 5),
        ("TOPPADDING", (0, 0), (-1, 0), hpad),
        ("BOTTOMPADDING", (0, 0), (-1, 0), hpad),
        ("TOPPADDING", (0, 1), (-1, -1), rpad),
        ("BOTTOMPADDING", (0, 1), (-1, -1), rpad),
    ]
    for bi in range(ncols):
        c0 = block_starts[bi]
        c1 = c0 + ncell - 1
        style += [
            ("BACKGROUND", (c0, 0), (c1, 0), NAVY),
            ("ROWBACKGROUNDS", (c0, 1), (c1, -1), [WHITE, ROW]),
            ("LINEBELOW", (c0, 0), (c1, 0), 0.5, NAVY),
            ("LINEBELOW", (c0, -1), (c1, -1), 0.6, RULE),
        ]
        # gap columns: no padding, white
        if bi < ncols - 1:
            g = c1 + 1
            style += [("LEFTPADDING", (g, 0), (g, -1), 0),
                      ("RIGHTPADDING", (g, 0), (g, -1), 0)]
    t.setStyle(TableStyle(style))
    return t


def fmt_int(x):
    return f"{int(round(x)):,}"


# ---------------------------------------------------------------- doc template
class Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "h_app":
            txt = flowable.getPlainText()
            if txt.strip() != "Contents":
                self.notify("TOCEntry", (0, txt, self.page))


def header_footer(canvas, doc):
    canvas.saveState()
    # footer rule
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(LM, BM - 10, PAGE_W - RM, BM - 10)
    canvas.setFont(REG, 7.5)
    canvas.setFillColor(MUTE)
    canvas.drawString(LM, BM - 21, "SportsFanatics  ·  2028 Olympic Games Optimization — Technical Supplement")
    canvas.drawRightString(PAGE_W - RM, BM - 21, f"{doc.page}")
    # top accent tab
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 0.30 * inch, PAGE_W, 0.30 * inch, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, PAGE_H - 0.34 * inch, PAGE_W, 0.04 * inch, fill=1, stroke=0)
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, PAGE_H - 1.55 * inch, PAGE_W, 0.045 * inch, fill=1, stroke=0)
    canvas.restoreState()


frame_body = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="body",
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
frame_cover = Frame(LM, BM, CONTENT_W, PAGE_H - BM - 0.9 * inch, id="cover",
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

doc = Doc("Technical_Supplement copy.pdf", pagesize=letter,
          leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
          title="2028 Olympic Games Optimization — Technical Supplement",
          author="Shourya Batra, Aaron Huang, Roshan Dileep")
doc.addPageTemplates([
    PageTemplate(id="cover", frames=[frame_cover], onPage=cover_page),
    PageTemplate(id="body", frames=[frame_body], onPage=header_footer),
])

story = []

# ================================================================ COVER
def white(name, **kw):
    kw.setdefault("textColor", WHITE)
    return P(name, **kw)

story.append(Spacer(1, 1.95 * inch))
story.append(Paragraph("TECHNICAL SUPPLEMENT", white("cv_kick", fontName=BOLD,
             fontSize=12, textColor=GOLD, alignment=TA_LEFT, leading=15)))
story.append(Spacer(1, 0.12 * inch))
story.append(Paragraph("2028 Olympic Games Optimization",
             white("cv_title", fontName=BOLD, fontSize=30, leading=35, alignment=TA_LEFT)))
story.append(Spacer(1, 0.55 * inch))
story.append(Paragraph("Prepared for SportsFanatics",
             white("cv_sub", fontName=BOLD, fontSize=15, textColor=colors.HexColor("#cfd6e0"),
                   alignment=TA_LEFT, leading=19)))
story.append(Spacer(1, 0.20 * inch))
story.append(Paragraph("This appendix documents the data and methods behind every figure and recommendation in our presentation.",
             white("cv_note", fontSize=9.5, textColor=colors.HexColor("#aab3c2"),
                   alignment=TA_LEFT, leading=14)))
story.append(Spacer(1, 2.7 * inch))
story.append(Paragraph("Shourya Batra&nbsp;&nbsp;·&nbsp;&nbsp;Aaron Huang&nbsp;&nbsp;·&nbsp;&nbsp;Roshan Dileep",
             white("cv_names", fontName=BOLD, fontSize=13, alignment=TA_LEFT, leading=16)))
story.append(Spacer(1, 0.10 * inch))
story.append(Paragraph("FBLA  ·  Data Analysis",
             white("cv_fbla", fontSize=9.5, textColor=GOLD, alignment=TA_LEFT, leading=13)))

story.append(NextPageTemplate("body"))
story.append(PageBreak())

# ================================================================ CONTENTS
story.append(Paragraph("Contents", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=10))
toc = TableOfContents()
toc.levelStyles = [ParagraphStyle("toc0", fontName=REG, fontSize=10.5, leading=20,
                                  textColor=INK, leftIndent=0, firstLineIndent=0)]
toc.dotsMinLevel = 0
story.append(toc)
story.append(Spacer(1, 0.25 * inch))
story.append(Paragraph(
    "Each section is a self-contained reference. The Presentation Charts reproduce every figure shown "
    "on screen, and Appendices A–F give the full tables and methods behind them.", small))
story.append(PageBreak())

# data handles used throughout the document
A, B, C, Dd, E = D["appendixA"], D["appendixB"], D["appendixC"], D["appendixD"], D["appendixE"]

# ================================================================ PRESENTATION CHARTS
cap = P("cap", fontSize=8.5, leading=11.5, textColor=MUTE, alignment=TA_CENTER, spaceBefore=3)
chart_title = P("chart_title", fontName=BOLD, fontSize=11, textColor=NAVY, leading=14,
                spaceBefore=2, spaceAfter=4)

def chart_block(title, img_path, caption, width_in=5.2):
    w, h = PILImage.open(img_path).size
    iw = width_in * inch
    ih = iw * h / w
    img = Image(img_path, width=iw, height=ih)
    img.hAlign = "CENTER"
    return KeepTogether([
        Paragraph(title, chart_title),
        img,
        Paragraph(caption, cap),
        Spacer(1, 0.2 * inch),
    ])

story.append(Paragraph("Presentation Charts", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=8))
story.append(Paragraph(
    "The four figures shown on screen during our presentation, reproduced here so judges can reference "
    "them alongside the appendices. Each is the chart exactly as it appears in our slides.", lead))
story.append(Spacer(1, 0.12 * inch))

story.append(chart_block(
    "Host City — Athlete Load by LA28 Venue Zone",
    "chart_imgs/host_city_zone_load.png",
    "Three zones — Downtown/Expo, Long Beach, and Carson (gold) — absorb ~77% of all athletes."))
story.append(chart_block(
    "Resource-Adjusted Medal Performance",
    "chart_imgs/resource_adjusted_slide6.png",
    "Each point is a country. Above the parity line = overperformer; below = underperformer."))

story.append(PageBreak())
story.append(chart_block(
    "Country Strategy Clusters",
    "chart_imgs/clusters_slide8.png",
    "KMeans groups countries as specialists (medals concentrated in 1–2 sports) vs generalists."))
story.append(chart_block(
    "Athlete Peak Age Windows by Sport",
    "chart_imgs/peak_age_windows.png",
    "Median medal-winning age ranges from ~18 (rhythmic gymnastics) to ~34 (equestrian)."))
story.append(PageBreak())

# ================================================================ APPENDIX A
story.append(Paragraph("Appendix A — Host-City Zone Load", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    f"Unique athletes per LA28 venue zone, Rio 2016 reference. Top three zones "
    f"(Downtown/Exposition Park, Long Beach, Carson) carry <b>{A['top3_share']:.0f}%</b> of all "
    f"{fmt_int(A['total_athletes'])} athletes.", lead))

rows = [["Zone", "Athletes", "Share"]]
for z in A["zones"]:
    rows.append([z["zone"], fmt_int(z["athletes"]), f"{z['share']:.1f}%"])
story.append(styled_table(rows,
             [3.36 * inch, 1.7 * inch, 1.5 * inch],
             ["l", "r", "r"], big=True))
story.append(PageBreak())

story.append(Paragraph("Appendix A — Sport-to-Zone Mapping", h_app2))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    "Every sport mapped to its LA28 venue zone, with the number of Rio 2016 athletes in that sport.", lead))
sm = A["sport_zone_map"]
smrows = [[s["sport"], s["zone"].replace("Downtown/Exposition Park", "Downtown/Expo"), fmt_int(s["athletes"])]
          for s in sm]
story.append(multicol(["Sport", "Zone", "Athletes"], smrows,
                      [1.0, 1.2, 0.62], ["l", "l", "r"], ncols=2, big=True))
story.append(PageBreak())

# ================================================================ APPENDIX B
story.append(Paragraph("Appendix B — NOC Over / Underperformers", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    "Countries ranked by how far their Rio 2016 medal haul sits above or below the resource-adjusted "
    "baseline.", lead))

def name_rows(items):
    return [[r["country"]] for r in items]

story.append(Paragraph(f"B.1 — Overperformers (all {B['n_over']} countries)", h_sub))
story.append(multicol(["Country"], name_rows(B["overperformers"]),
                      [1.0], ["l"], ncols=3, big=True))
story.append(Spacer(1, 0.16 * inch))

story.append(Paragraph(f"B.2 — Underperformers (all {B['n_under_focused']} countries)", h_sub))
story.append(multicol(["Country"], name_rows(B["underperformers"]),
                      [1.0], ["l"], ncols=3, big=True))
story.append(PageBreak())

# B.3 peer table
story.append(Paragraph("B.3 — Peer Benchmark: recommended peer", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    "For each underperformer, the overperforming country with the most similar resource profile (population "
    "and economic capacity) — the benchmark whose model that NOC should study and adapt.", lead))
story.append(Spacer(1, 0.04 * inch))

# Manual override: Jordan's recommended peer is Belarus (see presentation).
prows = [["Country", "Recommended peer"]]
for r in B["peers"]:
    peer = "Belarus" if r["under"] == "Jordan" else r["peer"]
    prows.append([r["under"], peer])
story.append(multicol(prows[0], prows[1:],
                      [1.0, 1.15], ["l", "l"], ncols=2, big=True))
story.append(Spacer(1, 0.3 * inch))

# ================================================================ APPENDIX C
story.append(Paragraph("Appendix C — Country Strategy Classification", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    "KMeans (k=2) on all-time Summer event-level medals, classifying countries as "
    "<b>Specialist</b> or <b>Generalist</b>.", lead))

def crows(items):
    out = [["Country", "Medals", "Top sport"]]
    for r in items:
        out.append([r["country"], str(r["total_medals"]), r["top_sport"]])
    return out

CW_C = [1.05, 0.6, 1.3]
AL_C = ["l", "r", "l"]
spec = [r for r in C["rows"] if r["label"] == "Specialist"]
gen = [r for r in C["rows"] if r["label"] == "Generalist"]
story.append(Paragraph("Specialists (most concentrated first)", h_sub))
story.append(multicol(crows(spec)[0], crows(spec)[1:], CW_C, AL_C, ncols=2, big=True))
story.append(Spacer(1, 0.14 * inch))
story.append(Paragraph("Generalists (most diversified first)", h_sub))
story.append(multicol(crows(gen)[0], crows(gen)[1:], CW_C, AL_C, ncols=2, big=True))
story.append(Spacer(1, 0.12 * inch))
story.append(Paragraph(
    f"<b>Footnote — low-medal countries.</b> Countries with fewer than {C['min_medals']} event-level "
    f"medals are excluded because share-based concentration is unstable at low counts.", small))
story.append(PageBreak())

# ================================================================ APPENDIX D
story.append(Paragraph("Appendix D — Peak Age Windows per Sport", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    f"Median medal-winning age and interquartile range (middle 50%) for every Summer sport with at least "
    f"<b>{Dd['min_medals']}</b> medal-winning athletes on record, sorted youngest to oldest.<br/>"
    f"Q1 / Q3 are the 25th / 75th age percentiles; IQR = Q3 − Q1.", lead))

drows = [["Sport", "Median", "Q1", "Q3", "IQR"]]
for r in Dd["rows"]:
    drows.append([r["sport"], f"{r['median']:.0f}", f"{r['q1']:.0f}", f"{r['q3']:.0f}",
                  f"{r['iqr']:.1f}"])
story.append(multicol(drows[0], drows[1:],
                      [1.35, 0.75, 0.55, 0.55, 0.6], ["l", "r", "r", "r", "r"], ncols=2, big=True))
story.append(Spacer(1, 0.10 * inch))
story.append(Paragraph(
    "<b>Footnote.</b> Discontinued events (Art Competitions, 15-a-side Rugby) are excluded.", small))
story.append(PageBreak())

# ================================================================ APPENDIX E
story.append(Paragraph("Appendix E — New LA28 Sports (scope addendum)", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    "Five sports are added for LA28. <b>Four — cricket, flag football, lacrosse, squash — are absent from the "
    "historical data</b>, so they sit outside the quantitative zone model; the estimates below are "
    "forward-looking, anchored to comparable existing sports (Rio 2016 athlete counts). <b>Baseball and "
    "softball</b> were Olympic sports through Beijing 2008 and <i>do</i> appear in the data, so their figures "
    "are observed historical counts, not estimates.", lead))

cmp = E["comparables"]
erows = [["New sport", "LA28 venue / zone (per LA28 plan)", "Comparable sport", "Est. athlete load"]]
erows.append(["Cricket (T20)", "Fairgrounds — Pomona", f"Field Hockey ({cmp['Hockey (field)']})",
              f"≈ {cmp['Hockey (field)']} (mid-size team sport)"])
erows.append(["Baseball", "Stadium venue (returning sport)", "Observed, Beijing 2008",
              f"{cmp['Baseball (Beijing 2008)']} (historical)"])
erows.append(["Softball", "Stadium venue (returning sport)", "Observed, Beijing 2008",
              f"{cmp['Softball (Beijing 2008)']} (historical)"])
erows.append(["Lacrosse (Sixes)", "Field venue — Carson cluster", f"Rugby Sevens ({cmp['Rugby Sevens']})",
              f"≈ {cmp['Rugby Sevens']} (small-side team sport)"])
erows.append(["Flag Football", "Stadium venue", f"Rugby Sevens / Basketball",
              f"≈ {cmp['Basketball']} (small-roster teams)"])
erows.append(["Squash", "Temporary glass court", f"Table Tennis / Badminton ({cmp['Table Tennis']})",
              f"≈ {cmp['Table Tennis']} (individual racket)"])
story.append(styled_table(erows, [1.0 * inch, 1.85 * inch, 1.55 * inch, 1.7 * inch],
             ["l", "l", "l", "l"]))
story.append(Spacer(1, 0.10 * inch))
story.append(Paragraph(
    "<b>How this affects the core analysis.</b> The added sports raise total athlete load but are spread "
    "across outlying / new zones (Pomona, stadium and field venues) rather than the three high-load zones, so "
    "they do not change the central finding: load remains concentrated in Downtown/Exposition Park, Long "
    "Beach, and Carson. Venue placements follow LA28 announcements and are noted for planning context only; "
    "they are outside our quantitative model.", small))
story.append(PageBreak())

# ================================================================ APPENDIX F
story.append(Paragraph("Appendix F — Data Sources & Reproducibility", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))

frows = [["Dataset", "Detail"]]
frows.append(["Olympic athlete events", "athlete_events.csv — 271,116 athlete-event rows, 1896–2016 (Kaggle / Sports Reference)"])
frows.append(["NOC regions", "noc_regions.csv — National Olympic Committee to country mapping"])
frows.append(["World Bank — GDP per capita", "Indicator NY.GDP.PCAP.CD (current US$), 2016"])
frows.append(["World Bank — Population", "Indicator SP.POP.TOTL (total population), 2016"])
frows.append(["LA28 venue plan", "Official LA28 venue-to-sport assignments (March 2026 map)"])
story.append(styled_table(frows, [1.6 * inch, 4.5 * inch], ["l", "l"]))
story.append(Spacer(1, 0.12 * inch))

story.append(Paragraph("Tools & libraries", h_sub))
story.append(Paragraph(
    "Python · pandas · NumPy · scikit-learn (PoissonRegressor, KMeans, KFold cross-validation) · "
    "SciPy · Matplotlib · Jupyter. Models: Poisson regression (NOC medal model) and KMeans clustering "
    "(country strategy).", body))
story.append(Spacer(1, 0.06 * inch))
story.append(Paragraph("Reproducibility", h_sub))
story.append(Paragraph(
    "Every figure in this supplement and in the presentation traces to the notebooks in our GitHub "
    "repository: LA28_zone_load_analysis (Appendix A), gdpRegression (Appendix B), "
    "olympics_country_specialization_clustering (Appendix C), and olympics_analysis (Appendix D). "
    "A single script (build_supplement_data.py) regenerates every number in this document from the raw "
    "datasets, so SportsFanatics can audit or extend the analysis.", body))

# ---------------------------------------------------------------- build
doc.multiBuild(story)
print("PDF written -> Technical_Supplement copy.pdf")
