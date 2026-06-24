### **Aaron | (Opening / Context)**

Good afternoon judges. I’m Aaron.

I’m Shourya, and I’m Roshan.

Today we will be presenting “optimizing the 2028 Olympics”

Our client, **SportsFanatics,** came to us with a question:

_How can historical Olympic participation and performance data be used to optimize planning decisions for the 2028 Olympics?_

To answer this, we analyzed over a century of Olympic data and focused on three key stakeholders: The **Athletes, The host city of Los Angeles, and the National Olympic Committees, or NOCs**, which represent each country sending athletes

**Shourya | (Data \+ Workflow \+ Reproducibility)**

Here is our workflow. First, we used historical Olympic athlete-event data from 1896 to 2016, along with NOC region data. Then, we merged datasets, filtered the Summer Olympics, and handled missing values. Lastly we analyzed:

- Athlete load across venue zones

- Resource-adjusted medal performance

- Athlete age profiles

- And Country-level medal distributions

For transparency and reproducibility, all of our work is organized in a GitHub repository. We used **Python, Pandas, scikit-learn, and Jupyter notebooks** for data wrangling, visualization, and modeling. Every chart and recommendation can be traced directly back to the code and data used, allowing SportsFanatics to audit or extend our analysis.

### **Roshan | (Host City: The Distributed-Venue Challenge)**

Let's start with the host city, Los Angeles.

LA28 is one of the most geographically distributed Summer Games in modern history — venues are spread across zones from Downtown to Long Beach, Carson, and beyond. So the instinct to plan around the biggest _sports_ misses the real challenge: it's _geography_.

We mapped each sport to its official LA28 venue zone, then measured how athletes concentrate across them.

As you can see, athlete load is sharply uneven. Just three zones — Downtown, Long Beach, and Carson — absorb over **three-quarters** of all athletes. And the heaviest zones aren't the famous venues: the swimming and basketball cluster in Inglewood sits near the bottom.

Downtown alone carries over forty percent. To see why that's an operational pressure point: the LA Convention Center stacks five different sports — nearly thirteen hundred athletes — into one building, in the same zone as the Coliseum's twenty-two hundred track athletes.

### Roshan | (LA Recommendation \+ Resources \+ Global Impact)

So instead of planning by venue size or prestige, we recommend that Los Angeles adopt a **zone-weighted resource allocation model**:

Pre-position athlete shuttles, transit frequency, and dedicated lanes in proportion to each zone's athlete load

Scale medical and recovery capacity to that same load index, not to stadium seating

And weight security and crowd-management staffing toward the three high-load zones — with special attention to the Downtown stack

The resources required are zone-level transport scheduling teams, a load-indexed staffing plan, and venue-cluster medical provisioning — all reallocations of existing Games budget, not new spending.

This is feasible because every weight traces directly to historical athlete data joined to LA28's own published venue plan. And it's a method any future host using a distributed model can apply — pre-positioning resources before opening day rather than reacting once the Games begin.

### **Aaron | (Resource-Adjusted Performance & NOC Constraints)**

Next, we wanted to answer a more strategic question for NOCs:

“Which countries are performing well relative to the resources they have?”

To do that, we added the World Bank external dataset, using each country’s GDP per capita and population. We then used a machine learning regression model to estimate how many medals a country would typically be expected to win given its size and economic capacity.

As you can see in this chart, each point represents a country. The line shows the expected medal level based on resources. Countries above the line are outperforming their resource baseline, while countries below the line are underperforming relative to similar peers.

### **\[New slide\] Aaron | (NOC Recommendation \+ Resources)**

So how can NOCs actually act on this?

For resource-constrained or underperforming NOCs, we recommend benchmarking against overperforming peer countries with similar GDP per capita and population, then reallocating funding toward the systems that are producing better results.

For example, in our model, Jordan sits just below its resource baseline, while its closest overperforming peer with a comparable economic profile is Belarus, which converts a similar resource base into far more medals by concentrating on a few winnable disciplines. That suggests Jordan's highest-leverage move is to focus investment on a small number of sports where it can realistically contend, rather than spreading a limited budget thinly across many.

The resources required include performance analysts, federation-level budgeting decisions, targeted coaching investment, and selective international competition exposure. This approach is feasible because it helps NOCs improve results by reallocating existing resources more strategically, rather than simply increasing delegation size or spending.

### **Shourya | (Clustering: Country Strategy Types)**

We then asked a deeper strategic question:

Do countries succeed using different Olympic strategies?

To answer this, we used **KMeans, an unsupervised machine learning clustering technique**, to group countries based on how their medals are distributed across sports.

As shown in this scatter plot, the clustering reveals two clear groups:

- **Specialist countries**, whose medals are concentrated in one or two sports, like Jamaica and Kenya.

- **Generalist countries**, which earn medals across many sports  
   For example, China, Germany, and the UK.

This distinction reflects fundamentally different **resource allocation models** across countries.

### **Shourya | (Cluster-Based Recommendations \+ Resources)**

For **specialist countries**, we recommend:

- Deepening investment in their strongest sports

- Allocating resources toward elite coaching, sports science support, and early talent identification

For **generalist countries**, we recommend:

- Maintaining diversified investment across multiple sports

- Prioritizing pipeline development, depth, and consistency rather than specialization

These plans require federation-level funding decisions, talent identification systems, and coaching pipelines, and are feasible because they **align with existing national strengths** rather than requiring structural overhauls.

### **Roshan | (Athlete Age Windows \+ Global Impact)**

Finally, we analyzed athlete age profiles by quantifying **peak medal-age windows** for each sport using the median medal-winning age and the interquartile range, which captures the middle 50% of medal-winning athletes. We limited this analysis to sports with sufficient medal data to ensure reliability.

For example:

- **Rhythmic gymnastics** peaks very early, with a median around 18 and a tight age window

- But sports like **shooting and equestrian** peak much later, with medians around 32 and 34, reflecting the value of experience

Globally, this shows that athlete development pipelines should be **sport-specific**, not one-size-fits-all.

### **Roshan | (Athlete Recommendation \+ Resources)**

We recommend that athlete development programs:

- Align training intensity and competition schedules with **sport-specific peak age windows**

- And Adjust selection criteria depending on whether a sport rewards physical peak performance or long-term experience

The resources required include long-term athlete development plans, coaching education, and athlete monitoring systems. This approach is feasible because it relies on **data-informed adjustments to existing pipelines**, not new infrastructure — and these benchmarks can be shared globally with athletes and NOCs.

### **Aaron |(Conclusion / Stakeholder Value)**

By combining historical data and analysis, we show how historical Olympic data can guide smarter planning decisions.

We recommended helping Los Angeles allocate resources by where athletes actually concentrate, help NOCs invest strategically, and help athletes train and peak at the right times.

Together, these insights allow the 2028 Los Angeles Olympics and all **\[Enunciate/Important word\] Global** future Olympic events, to be planned more effectively, sustainably, and equitably.

Lastly, here is our work cited, including datasets, and software used. Thank you for your time.
