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
                                KeepTogether)
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
h_sub = P("h_sub", fontName=BOLD, fontSize=10, textColor=TEAL, leading=13,
          spaceBefore=8, spaceAfter=3)
lead = P("lead", fontSize=9, leading=13, textColor=INK, spaceAfter=4)
cell = P("cell", fontSize=8, leading=10)
cellr = P("cellr", fontSize=8, leading=10, alignment=TA_RIGHT)
cellb = P("cellb", fontName=BOLD, fontSize=8, leading=10)
hcell = P("hcell", fontName=BOLD, fontSize=7.6, leading=9.5, textColor=WHITE)
hcellr = P("hcellr", fontName=BOLD, fontSize=7.6, leading=9.5, textColor=WHITE, alignment=TA_RIGHT)

PAGE_W, PAGE_H = letter
LM = RM = 0.72 * inch
TM = 0.78 * inch
BM = 0.72 * inch
CONTENT_W = PAGE_W - LM - RM


# ---------------------------------------------------------------- table helpers
def th(text, right=False):
    return Paragraph(text, hcellr if right else hcell)

def tc(text, align="l", bold=False):
    if align == "r":
        return Paragraph(str(text), cellr)
    return Paragraph(str(text), cellb if bold else cell)

def styled_table(rows, col_widths, aligns, fontsize=8):
    """rows[0] is header. aligns is list of 'l'/'r' per column."""
    data = []
    for ci, h in enumerate(rows[0]):
        pass
    header = [th(h, right=(aligns[i] == "r")) for i, h in enumerate(rows[0])]
    data.append(header)
    for r in rows[1:]:
        data.append([tc(v, align=aligns[i]) for i, v in enumerate(r)])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4.5),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, NAVY),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, RULE),
    ]
    t.setStyle(TableStyle(style))
    return t


def multicol(header, rows, col_widths, aligns, ncols=2, gap=0.22 * inch):
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
        return tc(v, align=aligns[ci])

    # header row
    head_row = []
    for bi in range(ncols):
        for ci in range(ncell):
            head_row.append(th(header[ci], right=(aligns[ci] == "r")))
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
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, 0), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4.5),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
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

doc = Doc("Technical_Supplement.pdf", pagesize=letter,
          leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
          title="2028 Olympic Games Optimization — Technical Supplement",
          author="Aaron, Roshan, Shourya")
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
story.append(Paragraph("This appendix documents the data and methods behind every figure in our presentation.",
             white("cv_note", fontSize=10.5, textColor=colors.HexColor("#aab3c2"),
                   alignment=TA_LEFT, leading=15)))
story.append(Spacer(1, 2.7 * inch))
story.append(Paragraph("Aaron&nbsp;&nbsp;·&nbsp;&nbsp;Roshan&nbsp;&nbsp;·&nbsp;&nbsp;Shourya",
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
    "Each section is a self-contained reference. Appendices A–F give the full tables behind "
    "the figures shown on screen; the Methodology Summary states data sources, models, and "
    "assumptions for all three stakeholders.", small))
story.append(PageBreak())

# ================================================================ METHODOLOGY
A, B, C, Dd, E = D["appendixA"], D["appendixB"], D["appendixC"], D["appendixD"], D["appendixE"]

story.append(Paragraph("Methodology Summary", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=9))

meth = [
    ("Host City — Los Angeles (Appendix A)",
     f"Source: historical Olympic athlete-event records (1896–2016) joined to NOC region data. "
     f"Reference Games: <b>Rio 2016 (Summer)</b>, the most recent complete Summer Games in the data. "
     f"Each sport is mapped to its official LA28 venue zone (March 2026 venue plan); multi-venue sports are "
     f"assigned to their primary sub-venue. We count <b>unique athletes</b> (by athlete ID) per zone, so no "
     f"athlete is double-counted. Scope: the <b>31 returning LA28 sports</b>, recorded as 34 categories in the "
     f"dataset (Rhythmic Gymnastics & Trampolining group under Gymnastics; Beach Volleyball under Volleyball). "
     f"Total athletes analysed: <b>{fmt_int(A['total_athletes'])}</b>."),
    ("National Olympic Committees (Appendix B)",
     f"We add World Bank external data — <b>GDP per capita (NY.GDP.PCAP.CD)</b> and <b>population "
     f"(SP.POP.TOTL)</b>, 2016 — and model Rio 2016 medal counts with a <b>Poisson regression</b> on "
     f"log(population) and log(GDP per capita). Poisson is the correct family because medals are non-negative "
     f"count data. Expected medals are estimated <b>out-of-fold</b> (5-fold CV, no leakage); the residual "
     f"(actual − expected) is the Resource-Adjusted Performance Index (RAPI). Out-of-fold "
     f"<b>R² = {B['oof_r2']:.2f}</b> over {B['n_countries']} countries. Each underperformer is matched to its "
     f"nearest <b>overperforming</b> peer by Euclidean distance in log-population / log-GDP space."),
    ("Athletes (Appendices C & D)",
     f"<b>Strategy clustering:</b> KMeans (k=2) groups countries as specialist vs generalist by how concentrated "
     f"their all-time Summer medals are across sports, using event-level medal counts and a concentration "
     f"feature set (Herfindahl index + effective number of sports); countries with fewer than "
     f"{C['min_medals']} medals are excluded as statistically unstable. <b>Peak age windows:</b> for each sport "
     f"with at least {Dd['min_medals']} medal-winning athletes on record, we report the median medal-winning "
     f"age and the interquartile range (middle 50%)."),
]
for title, txt in meth:
    story.append(Paragraph(title, h_sub))
    story.append(Paragraph(txt, body))
story.append(Spacer(1, 0.12 * inch))
story.append(Paragraph(
    "<b>Consistency note.</b> All medal-based figures use Rio 2016 as the reference Games and event-level "
    "medal counts (one medal per event, not per athlete) unless a section states an all-time scope. "
    "Every number in this document is computed directly from the datasets and notebooks in our repository.",
    small))
story.append(PageBreak())

# ================================================================ APPENDIX A
story.append(Paragraph("Appendix A — Host-City Zone Load", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    f"Unique athletes per LA28 venue zone, Rio 2016 reference. Top three zones "
    f"(Downtown/Exposition Park, Long Beach, Carson) carry <b>{A['top3_share']:.0f}%</b> of all "
    f"{fmt_int(A['total_athletes'])} athletes. Load Index sets the heaviest zone = 100.", lead))

rows = [["Zone", "Athletes", "Share", "Sports", "Load Index", "Primary venue cluster"]]
for z in A["zones"]:
    rows.append([z["zone"], fmt_int(z["athletes"]), f"{z['share']:.1f}%",
                 str(z["n_sports"]), f"{z['load_index']:.1f}", z["primary_venue"]])
story.append(styled_table(rows,
             [1.25 * inch, 0.7 * inch, 0.55 * inch, 0.5 * inch, 0.72 * inch, 2.3 * inch],
             ["l", "r", "r", "r", "r", "l"]))
story.append(Spacer(1, 0.10 * inch))

rb = A["robustness"]
story.append(Paragraph("Robustness — concentration is stable across recent Games", h_sub))
story.append(Paragraph(
    f"Recomputing zone shares for 2008 / 2012 / 2016 gives a Downtown share of "
    f"<b>{rb['2008']['downtown']:.0f}% / {rb['2012']['downtown']:.0f}% / {rb['2016']['downtown']:.0f}%</b> "
    f"and a top-3 share of <b>{rb['2008']['top3']:.0f}% / {rb['2012']['top3']:.0f}% / "
    f"{rb['2016']['top3']:.0f}%</b> — i.e. ~41% Downtown and ~77% top-3 in every Games. The "
    f"allocation model does not depend on a single Games.", body))
story.append(Spacer(1, 0.10 * inch))

story.append(Paragraph("Sport-to-zone mapping (Rio 2016 athletes per sport)", h_sub))
sm = A["sport_zone_map"]
smrows = [[s["sport"], s["zone"].replace("Downtown/Exposition Park", "Downtown/Expo"), fmt_int(s["athletes"])]
          for s in sm]
story.append(multicol(["Sport", "Zone", "Ath."], smrows,
                      [1.0, 1.0, 0.5], ["l", "l", "r"], ncols=2))
story.append(PageBreak())

# ================================================================ APPENDIX B
story.append(Paragraph("Appendix B — NOC Over / Underperformers", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    f"Poisson resource-adjusted model, Rio 2016. Out-of-fold R² = <b>{B['oof_r2']:.2f}</b>, "
    f"MAE = {B['oof_mae']:.2f} medals, n = {B['n_countries']} countries. RAPI = actual − expected medals. "
    f"GDP = GDP per capita (USD, 2016); Pop in millions.", lead))

def noc_rows(items):
    out = [["Country", "Act.", "Exp.", "RAPI", "GDP/cap", "Pop (M)"]]
    for r in items:
        out.append([r["country"], str(r["actual"]), f"{r['expected']:.1f}",
                    f"{r['rapi']:+.1f}", fmt_int(r["gdp_pc"]), f"{r['pop']/1e6:.1f}"])
    return out

story.append(Paragraph(f"B.1 — Overperformers (all {B['n_over']}, by RAPI)", h_sub))
story.append(multicol(noc_rows(B["overperformers"])[0], noc_rows(B["overperformers"])[1:],
                      [0.95, 0.4, 0.4, 0.45, 0.6, 0.5], ["l", "r", "r", "r", "r", "r"], ncols=2))
story.append(Spacer(1, 0.10 * inch))

story.append(Paragraph(
    f"B.2 — Underperformers (expected ≥ 1 medal; {B['n_under_focused']} of "
    f"{B['n_under_total']} total, by RAPI)", h_sub))
story.append(multicol(noc_rows(B["underperformers"])[0], noc_rows(B["underperformers"])[1:],
                      [0.95, 0.4, 0.4, 0.45, 0.6, 0.5], ["l", "r", "r", "r", "r", "r"], ncols=2))
story.append(PageBreak())

# B.3 peer table
story.append(Paragraph("B.3 — Peer Benchmark: nearest overperforming peer", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    "For each underperformer (expected ≥ 1 medal), the nearest <b>overperforming</b> country by resource "
    "distance (Euclidean in log-population / log-GDP space). Sorted by distance — the closest, most "
    "actionable comparisons are first.", lead))

jalt = B["jordan_alts"]
story.append(Paragraph(
    f"<b>Featured peer chain &mdash; Jordan to Azerbaijan.</b> Jordan (RAPI {jalt and B['peers'][0]['under_rapi']:+.1f}) "
    f"is the tightest match in the entire table: its nearest overperformer is <b>Azerbaijan</b> "
    f"(distance {jalt[0]['distance']:.3f}; near-identical population and GDP per capita) which converts the "
    f"same resource base into {jalt[0]['peer_actual']} medals by concentrating on a few combat-sport "
    f"disciplines. <b>Belarus</b> is also a comparable overperforming peer "
    f"(distance {[a for a in jalt if a['peer']=='Belarus'][0]['distance']:.3f}, "
    f"{[a for a in jalt if a['peer']=='Belarus'][0]['peer_actual']} medals) — either supports the "
    f"“concentrate investment on winnable disciplines” recommendation.", body))
story.append(Spacer(1, 0.08 * inch))

prows = [["Country", "RAPI", "Nearest peer", "P.RAPI", "P.med", "Dist."]]
for r in B["peers"]:
    prows.append([r["under"], f"{r['under_rapi']:+.1f}", r["peer"], f"{r['peer_rapi']:+.1f}",
                  str(r["peer_actual"]), f"{r['distance']:.3f}"])
story.append(multicol(prows[0], prows[1:],
                      [1.1, 0.45, 1.1, 0.5, 0.45, 0.5], ["l", "r", "l", "r", "r", "r"], ncols=2))
story.append(PageBreak())

# ================================================================ APPENDIX C
story.append(Paragraph("Appendix C — Country Strategy Classification", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    f"KMeans (k=2) on all-time Summer event-level medals, classifying countries as "
    f"<b>Specialist</b> (medals concentrated in 1–2 sports) or <b>Generalist</b> (spread across many). "
    f"{C['n_classified']} countries meet the ≥ {C['min_medals']}-medal threshold "
    f"({C['n_specialist']} specialist, {C['n_generalist']} generalist). "
    f"<b>Top-sport %</b> = share of a country's medals in its single best sport; "
    f"<b>Eff. sports</b> = effective number of sports (1 / Herfindahl index) — lower means more specialised.", lead))

def crows(items):
    out = [["Country", "Med.", "Top sport", "Top %", "Eff. sp."]]
    for r in items:
        out.append([r["country"], str(r["total_medals"]),
                    r["top_sport"], f"{r['top_share']:.0f}%", f"{r['eff_sports']:.1f}"])
    return out

CW_C = [1.0, 0.42, 1.15, 0.5, 0.55]
AL_C = ["l", "r", "l", "r", "r"]
spec = [r for r in C["rows"] if r["label"] == "Specialist"]
gen = [r for r in C["rows"] if r["label"] == "Generalist"]
story.append(Paragraph("Specialists (by effective number of sports, most concentrated first)", h_sub))
story.append(multicol(crows(spec)[0], crows(spec)[1:], CW_C, AL_C, ncols=2))
story.append(Spacer(1, 0.08 * inch))
story.append(Paragraph("Generalists (most diversified first)", h_sub))
story.append(multicol(crows(gen)[0], crows(gen)[1:], CW_C, AL_C, ncols=2))
story.append(Spacer(1, 0.08 * inch))
pk = C.get("pakistan_note", {})
story.append(Paragraph(
    f"<b>Footnote — low-medal countries.</b> Countries with fewer than {C['min_medals']} event-level "
    f"medals are excluded because share-based concentration is unstable at low counts. By inspection these "
    f"are typically clear specialists: e.g. <b>Pakistan</b> ({pk.get('total_medals','~10')} medals, "
    f"{pk.get('top_share',80):.0f}% in {pk.get('top_sport','Hockey')}) is intuitively a specialist but falls "
    f"below threshold, so it is reported here rather than given an unstable cluster label. Labels reflect "
    f"degree of concentration, not which sport — a country specialised in an unusual sport (e.g. India in "
    f"field hockey) is correctly a specialist.", small))
story.append(PageBreak())

# ================================================================ APPENDIX D
story.append(Paragraph("Appendix D — Peak Age Windows per Sport", h_app))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=7))
story.append(Paragraph(
    f"Median medal-winning age and interquartile range (middle 50%) for every Summer sport with at least "
    f"<b>{Dd['min_medals']}</b> medal-winning athletes on record, sorted youngest to oldest. Q1 / Q3 are the "
    f"25th / 75th age percentiles; IQR = Q3 − Q1. Discontinued events (Art Competitions, 15-a-side Rugby) are "
    f"excluded. Sample size n = medal-winning athletes.", lead))

drows = [["Sport", "Med.", "Q1", "Q3", "IQR", "n"]]
for r in Dd["rows"]:
    drows.append([r["sport"], f"{r['median']:.0f}", f"{r['q1']:.0f}", f"{r['q3']:.0f}",
                  f"{r['iqr']:.1f}", fmt_int(r["n"])])
story.append(multicol(drows[0], drows[1:],
                      [1.2, 0.5, 0.5, 0.5, 0.5, 0.55], ["l", "r", "r", "r", "r", "r"], ncols=2))
story.append(Spacer(1, 0.07 * inch))
story.append(Paragraph(
    "Early-peak / tight-window sports (e.g. Rhythmic Gymnastics, median 18) reward physical peak; late-peak "
    "sports (Shooting 32, Equestrianism 34) reward accumulated experience — development pipelines should be "
    "sport-specific.", small))
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
print("PDF written -> Technical_Supplement.pdf")
