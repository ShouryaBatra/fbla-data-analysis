# Nationals Q&A Prep — *Optimizing the 2028 Olympics* (SportsFanatics)

Judge Q&A after the 7-minute presentation. Answers are written to be said out loud in
~15–30 seconds. Stay calm, answer the question that was asked, cite one number, and stop.
If you don't know, say what you *would* do to find out — never bluff a number.

---

## 0. Cheat sheet — numbers to have cold

| Fact | Number |
|---|---|
| Dataset | Kaggle Olympic `athlete_events` — **271,116** athlete-event rows, **1896–2016** |
| External data | World Bank **GDP per capita** (NY.GDP.PCAP.CD) + **population** (SP.POP.TOTL), 2016 |
| Reference Games | **Rio 2016** (most recent complete Summer Games in the data) |
| Athletes mapped to zones | **11,179** across **31 returning LA28 sports** (34 dataset categories) |
| Top-3 zone load | Downtown/Expo + Long Beach + Carson = **~77%** (Downtown alone **~41%**) |
| NOC model | **Poisson regression**, expected medals from log(pop) & log(GDP/cap) |
| Model accuracy | **Out-of-fold R² ≈ 0.80** over **182** countries |
| Clustering | **KMeans, k=2** — **62** countries with ≥20 medals (22 specialist, 40 generalist) |
| Age windows | Median + IQR, sports with **≥100** medal-winning athletes; rhythmic gym **18**, shooting **32**, equestrian **34** |
| Tools | Python · pandas · scikit-learn · Jupyter; everything reproducible in our GitHub repo |

**30-second pitch if asked to recap:** "SportsFanatics asked how historical Olympic data
can improve 2028 planning. We helped three stakeholders: Los Angeles plans resources by where
athletes actually concentrate, NOCs benchmark against resource-similar peers instead of just
spending more, and athlete programs train to sport-specific peak ages. Every recommendation is
a reallocation of existing resources, traceable to our data."

---

## 1. Business / big-picture

**Q: Who is your client and what did they actually ask for?**
SportsFanatics, a sports consulting agency. Their question was: *how can historical Olympic
data optimize planning decisions for the 2028 Olympics?* We turned that into three concrete,
data-driven deliverables for three stakeholders.

**Q: Why these three stakeholders — host city, NOCs, athletes?**
They cover the three levels where 2028 decisions actually get made: the city that runs the
Games operationally, the countries that fund and send teams, and the athletes the whole event
is built around. Together they let one dataset drive value at every level.

**Q: What's the single most important takeaway?**
That smarter Olympic planning is mostly about **reallocating existing resources by evidence**,
not spending more — pre-positioning by athlete load, benchmarking by resource-similar peers,
and training to sport-specific peak ages.

**Q: How would SportsFanatics make money / what's the value?**
We deliver decision-support that's auditable and reusable. The host-city method works for any
future distributed Games, the NOC model works for any country, and the age benchmarks are
global — so it's a repeatable consulting product, not a one-off.

**Q: How would you measure whether a recommendation worked?**
Host city: response times and transport wait times per zone vs. the load index. NOCs: change
in medals-vs-expected (RAPI) over the next cycle. Athletes: selection and peaking aligned to
the sport's window. All measurable against a pre-2028 baseline.

---

## 2. Host city — venue zone load

**Q: Why use Rio 2016 instead of projecting 2028?**
Rio 2016 is the most recent *complete* Summer Games in our dataset, so it's the best real
snapshot of who actually competes in each sport. We then map those athletes onto LA28's own
published venue plan. Using one consistent reference Games also keeps it comparable with our
NOC analysis.

**Q: Sports change between Games — does Rio still represent LA28?**
Yes, for the returning sports, which is what the analysis covers. We checked robustness:
recomputing the zone shares for 2008, 2012, and 2016 gives the same picture every time —
~41% Downtown and ~77% top-3 — so the concentration isn't a one-Games fluke.

**Q: LA28 adds new sports (cricket, flag football, etc.) — doesn't that break this?**
Four of the five added sports aren't in the historical data, so we handle them separately in
Appendix E as a qualitative estimate. They land in outlying zones like Pomona, not the three
high-load zones, so they don't change the core finding. Baseball/softball *are* in the data
(through 2008), so we use their real counts.

**Q: What does "athlete load" mean exactly — isn't a bigger stadium the real constraint?**
That's our whole point. We count **unique athletes** per zone, not seats. Operational load —
transport, medical, security, recovery — scales with *people moving through*, not stadium
capacity. Inglewood has famous venues but sits low; Downtown is the real pressure point.

**Q: Why is the recommendation better than just planning by venue?**
Because load is uneven and not where prestige suggests. A zone-weighted model pre-positions
shuttles, medical, and security *before* opening day in proportion to each zone's athlete load,
instead of reacting once the Games begin — and it's all reallocation of existing budget.

---

## 3. NOC resource-adjusted model

**Q: How does the medal model work?**
We predict how many medals a country is *expected* to win given its population and GDP per
capita, using a Poisson regression. Then RAPI = actual − expected. Positive means
overperforming its resources; negative means underperforming.

**Q: Why Poisson regression and not normal linear regression?**
Medals are **counts** — non-negative whole numbers with lots of zeros. Linear regression can
predict negative medals and assumes constant variance. Poisson is the standard model for count
data: it stays non-negative and its variance scales with the mean, which fits medal data.

**Q: How accurate is the model / how do you know it's not overfit?**
Out-of-fold R² is about **0.80**. "Out-of-fold" means each country's prediction comes from a
model trained on *other* countries via 5-fold cross-validation — so a country never helps
predict itself. That's an honest out-of-sample number, not an inflated in-sample fit.

**Q: Why only population and GDP per capita?**
They're the two cleanest, universally available proxies for a country's resource base — people
and money. Keeping it to two interpretable variables makes the model transparent and avoids
overfitting. Things like sport funding would help but aren't available for every country.

**Q: How do you pick a country's peer?**
For each underperformer we find the *overperforming* country with the most similar resource
profile — nearest in log-population and log-GDP-per-capita space. That guarantees a fair
comparison: same kind of resource base, better results.

**Q: Why Belarus for Jordan specifically?**
Belarus is a close resource-match for Jordan that converts a similar base into more medals by
concentrating on a few winnable disciplines. The point isn't "copy Belarus exactly" — it's
that Jordan's highest-leverage move is to focus investment on a few sports rather than spread
thin. Every underperformer's recommended peer is in Appendix B.

**Q: Russia won 56 medals in 2016 but had doping issues — doesn't that skew the model?**
We use the medals recorded in the historical dataset. Post-Games disqualifications are a known
limitation we'd note. But Russia reads as an overperformer because it has a large, well-funded
sport system — that conclusion is robust to a few contested medals. We could re-run excluding
contested results as an extension.

**Q: Isn't telling a poor country to "copy a peer" correlation, not causation?**
Fair — we're not claiming it guarantees medals. It's decision-support: we surface an
empirically comparable benchmark to study, then the federation makes sport-specific calls. It
beats the status quo of benchmarking against the USA or just enlarging the team.

---

## 4. Clustering — specialist vs. generalist

**Q: What is KMeans and what did you cluster on?**
KMeans is an unsupervised machine-learning method that groups similar data points. We grouped
countries by **how concentrated their medals are across sports** — whether they win in one or
two sports or spread across many.

**Q: Why two clusters (k=2)?**
Because the strategic question is genuinely binary — concentrate or diversify — and the data
separates cleanly into those two groups. Two clusters give the most interpretable, actionable
split for a federation.

**Q: How do you define "specialist" vs "generalist"?**
By concentration: a specialist earns most medals in one or two sports (Jamaica, Kenya in
athletics); a generalist spreads across many (China, Germany, UK). We measure it with a
concentration index — effectively, the number of sports a country meaningfully wins in.

**Q: Is country X correctly classified?**
We only classify countries with **at least 20 medals**, because concentration is unstable when
a country has only a handful — and we sanity-checked the labels against well-known cases. Low-
medal countries are noted in the footnote rather than given a shaky label. Full list in
Appendix C.

**Q: So what — what does a country do with this label?**
Specialists should deepen investment in their strongest sports (elite coaching, sports
science, early talent ID). Generalists should keep a diversified pipeline focused on depth and
consistency. Each plays to existing strengths, so it's feasible without structural overhaul.

---

## 5. Athlete peak age windows

**Q: How did you define a "peak age window"?**
For each sport we take all medal-winning athletes and report the **median** medal-winning age
plus the **interquartile range** — the middle 50%. The median is the typical peak; the IQR is
how wide that window is.

**Q: Why a minimum of 100 medal-winning athletes?**
Reliability. With too few medalists, a couple of outliers swing the median. The 100-medal
threshold keeps every sport in the table statistically stable.

**Q: Median age of medalists isn't the same as the best age to train — confounder?**
True — it's the age at which medals are actually *won*, which is what matters for selection and
peaking. We're not claiming biology; we're giving federations an evidence-based window to align
training intensity and selection criteria, instead of one-size-fits-all.

**Q: Why does this matter for 2028?**
Because development is currently generic. Rhythmic gymnastics peaks ~18 with a tight window;
shooting and equestrian peak ~32–34. A program that peaks a shooter like a gymnast wastes
years. The benchmarks make pipelines sport-specific and are shareable globally.

---

## 6. Data & methodology

**Q: Where's the data from and is it reliable?**
Two sources: the Kaggle Olympic `athlete_events` dataset (120 years, 1896–2016, sourced from
Sports Reference) and the World Bank for GDP per capita and population. Both are standard,
public, citable datasets.

**Q: How did you clean it / handle missing values?**
We merged the athlete data with NOC-to-country mapping, filtered to the Summer Olympics,
de-duplicated team events so a team medal counts once (not once per athlete), and dropped rows
missing the fields a given analysis needed (e.g., age for the age windows).

**Q: How is this reproducible?**
Everything is in our GitHub repo — Jupyter notebooks plus a single script that regenerates
every number in our technical appendix from the raw data. SportsFanatics can audit or extend
any figure.

**Q: "31 returning sports" but "34 categories" — which is it?**
Both. The LA28 program lists 31 returning sports; the dataset labels a few disciplines
separately (Rhythmic Gymnastics and Trampolining under Gymnastics, Beach Volleyball under
Volleyball), which makes 34 categories. We count at the 34-category level so every athlete maps
to exactly one venue.

---

## 7. Limitations (own them — judges reward honesty)

- **Historical data ends at 2016.** No Tokyo or Paris. Rio is the most recent complete Games we
  have; we showed the patterns are stable across 2008–2016.
- **New LA28 sports** (cricket, flag football, lacrosse, squash) aren't in the data — handled
  qualitatively in Appendix E, and they don't change the top-3 concentration.
- **Medal counts are noisy for small countries.** That's exactly why we use out-of-fold
  validation for the model and a 20-medal floor for clustering.
- **The model is a benchmark, not a guarantee** — it tells a country *who* to study, not that
  copying guarantees medals.
- **Recorded medals** don't reflect later disqualifications (e.g., doping reallocations).

If a judge pushes on any of these, agree it's a real limitation, then say how we mitigated it
or how we'd extend the work. That lands better than defending.

---

## 8. Curveballs

**Q: If you had more time/data, what would you add?**
Sport-specific funding data for the NOC model, more recent Games once available, and a simple
cost model so the host-city reallocation has dollar figures attached.

**Q: Is this equitable — are you telling poorer nations to give up on most sports?**
The opposite — we give resource-constrained NOCs a realistic path to medals by focusing limited
budgets where they can actually contend, instead of competing head-to-head with the USA across
every sport. The benchmarks are shared globally, which is the equitable part.

**Q: What was the hardest technical part?**
Making the medal model honest — using out-of-fold predictions so we report real out-of-sample
accuracy (R² ~0.80), and choosing Poisson over linear regression because medals are count data.

**Q: How did you divide the work as a team?**
(Answer naturally — Shourya led data/workflow + host city + clustering, Aaron led the NOC
model, Roshan led the recommendations + athlete age windows. Be ready to speak to any part,
since the appendix documents all of it.)

**Q: Why should a judge trust your numbers?**
Because every figure in our presentation is in the technical appendix we handed you, and every
figure traces back to code and public data in our repo. You can check any of them.

---

## 9. Known soft spots — handle with care (internal note)

- **Jordan → Belarus:** Belarus is a strong, defensible resource-similar overperformer and it's
  what's printed in Appendix B, so you're consistent. If a judge with deep knowledge asks "why
  not an even closer match," pivot to the *principle*: "the method finds the most
  resource-similar overperformer; the takeaway is concentrate, not spread." Don't get pulled
  into defending one country over another.
- **"KMeans-adjusted" wording:** the NOC expected-medals model is **Poisson regression**, not
  KMeans. KMeans is *only* the clustering. If anyone conflates them, calmly separate the two.
- **Clustering uses concentration, not just raw KMeans on every sport:** if pressed on method,
  say "KMeans on each country's medal-concentration profile" — don't over-claim.
- Don't volunteer limitations unprompted during Q&A, but have Section 7 ready if asked.
