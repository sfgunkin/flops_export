# Referee Report: "Selling FLOPs: A New Export Industry for Developing Countries"

*Reviewer: Paul Krugman*

## Summary

This paper develops a capacity-constrained Ricardian trade model in which countries produce and export computing services (FLOPs), with costs driven by electricity prices, climate (through cooling needs), and construction costs. The model distinguishes between latency-insensitive training (which can be offshored freely) and latency-sensitive inference (which degrades with distance), adds a sovereignty premium for domestic sourcing preference, and calibrates for 86 countries. The central policy claim is that cheap-energy developing countries—particularly in Central Asia—could convert electricity cost advantages into a new digital export industry.

## Assessment

This is a timely and genuinely interesting paper. The core question—can countries export computing power the way they export commodities?—is important and, to my knowledge, has not been formalized in a trade model before. The distinction between training and inference as two "goods" with different trade cost structures is clever and captures something real about the economics of AI infrastructure. The calibration is detailed and plausible. There is a publishable paper here.

That said, I have significant concerns about the modeling choices, the relationship between the model and the calibration, and whether the paper's most striking claims are robust to relaxing assumptions that currently do a lot of heavy lifting. The paper is stronger as a conceptual contribution—establishing that compute trade is a coherent subject for trade theory—than as a quantitative guide to which countries will actually become FLOP exporters. Let me be specific.

## Major Issues

**1. The Ricardian framework is too thin for the phenomenon being studied.**

The paper models FLOP production as a perfectly competitive, constant-returns, homogeneous-good industry. This is the classic Ricardian setup, and it delivers clean propositions. But the actual AI compute market is dominated by a handful of hyperscalers (AWS, Azure, Google Cloud, CoreWeave) with massive scale economies, proprietary networks, long-term contracts, and significant market power. The model's competitive framing—countries line up on a supply curve and trade at marginal cost—ignores the industrial organization of this industry entirely.

This matters because the paper's key policy message is directed at developing countries: build data centers, sell FLOPs. But the question of whether Kyrgyzstan can capture 26% of global inference demand is not primarily a question about electricity costs. It is a question about whether hyperscalers will locate there, whether the institutional environment supports billion-dollar irreversible investments, and whether network effects and agglomeration economies favor incumbents. I have, of course, spent some time on the question of increasing returns and geography. The paper cites my 1991 *JPE* paper on increasing returns and economic geography, but only in passing. The agglomeration forces that create Silicon Valley, or for that matter the clustering of data centers in Northern Virginia, are not incidental to the story—they may be the story.

I would urge the author to at least discuss what an increasing-returns version of this model would look like. Would the clean "supply curve" result survive if there were fixed costs of entry, network externalities in connectivity, or learning-by-doing in data center operations? My suspicion is that the competitive model overstates the opportunities for peripheral countries precisely because it assumes away the centripetal forces that concentrate this industry in rich countries.

**2. The cost variation is too compressed to drive the results the paper claims.**

Look at Table A1: the cheapest producer (Iran, $1.10/hr) is only 20% cheaper than the most expensive (Greenland, $1.32/hr). This is a remarkably narrow range for a model that is supposed to explain dramatic trade patterns. Hardware costs ($1.06/hr) are uniform and dominant, so electricity and construction variation operates on a small residual. The paper finds that a 10% sovereignty premium shifts 64% of countries to domestic production—which is another way of saying that the cost advantages are so thin that a modest preference for local sourcing wipes them out.

This raises a question the paper does not adequately address: if cost differences are this small, why would any country bother with the institutional overhead of becoming a compute exporter rather than just building domestic capacity? The answer presumably involves scale—even small per-unit margins become large in absolute terms at data center scale—but the model does not formalize this. More troubling, the compressed cost range means that the calibration results are extremely sensitive to input assumptions. A $0.01/kWh change in electricity price, or a modest revision to PUE parameters, can move a country from "exporter" to "importer." The paper should present systematic sensitivity analysis, not just the robustness checks mentioned in footnotes.

**3. The paper needs to engage with Eaton and Kortum (2002).**

This is the most significant omission in the literature review. The paper develops a multi-country Ricardian model with geographic trade barriers—which is precisely what Eaton and Kortum (2002, *Econometrica*) did in their celebrated gravity model. The relationship between this paper and Eaton-Kortum should be made explicit. Is this a special case? A variant? How does the paper's iceberg cost formulation for inference compare to Eaton-Kortum's iceberg transport costs? Similarly, the paper's continuum-of-countries approach with a cost ranking echoes Dornbusch, Fischer, and Samuelson (1977, *AER*), the seminal Ricardian continuum-of-goods model, which is also uncited. For a paper that claims to offer "the first trade model of compute," these foundational references cannot be absent.

Additionally, the paper should cite Costinot, A., J. Donaldson, and I. Komunjer (2012, *Review of Economic Studies*), who provided the modern empirical framework for multi-country Ricardian comparative advantage, and Arkolakis, C., A. Costinot, and A. Rodríguez-Clare (2012, *AER*), who showed a class of trade models deliver equivalent welfare formulas. Positioning relative to these canonical references would sharpen the contribution.

**4. Demand is exogenous and static, which undermines the policy implications.**

The model takes demand as given (proportional to existing installed capacity) and asks where supply should locate. But the paper's own argument is that FLOP exporting is a *new* industry that countries should invest in. This creates a tension: if Kyrgyzstan has 5 MW of capacity today (Table A2), its demand share is 0.0%, yet the paper claims it could capture 26% of global inference demand. These two facts live in different parts of the model—existing capacity determines demand shares, while the cost function determines export potential—but the disconnect is jarring.

More importantly, AI compute demand is growing explosively and shifting geographically. A static model calibrated to 2024 capacity shares may be misleading about 2030 trade patterns. Endogenizing demand—even crudely, say proportional to GDP or digital adoption—would strengthen the paper's forecasting credibility.

**5. The sovereignty premium does too much work and too little work simultaneously.**

The sovereignty premium λ is modeled as a uniform ad valorem markup on foreign-sourced compute. This is elegant but masks enormous heterogeneity. The paper acknowledges in passing that λ is "effectively infinite" between adversaries (US–Iran) and "near zero" between EU allies. But it then calibrates with a uniform 10%. Since the sovereignty premium is the single parameter that determines whether most countries produce domestically or import, using a uniform value is a significant limitation.

More fundamentally, data sovereignty is not well modeled as a cost markup. It is a regulatory constraint: the EU's GDPR does not make foreign compute 10% more expensive—it makes certain transfers *illegal* absent adequacy decisions. The paper's iceberg formulation treats sovereignty as a tariff-equivalent, which is a standard trick in trade theory, but it obscures the binary nature of many data governance regimes. I would like to see at least a discussion of how the results change under a regime-based sovereignty specification (e.g., free trade within blocs, infinite barriers across certain pairs).

## Minor Issues

1. **Proposition 5 is stated imprecisely.** The claim that "the set of training exporters is a subset of inference exporters for nearby markets" needs qualification. A country could be a training exporter (globally cheapest) but fail to serve inference to a distant demand center due to the latency ceiling. The proposition holds only for "proximate" demand centers, which should be defined formally (i.e., those within the latency threshold).

2. **The PUE specification is acknowledged as a simplification (footnote 7), but the robustness check is buried.** Capping PUE at 1.20 (universal liquid cooling) changes rankings negligibly, which is good news—but this check should be in the main text, not a footnote, given how prominently climate enters the model.

3. **The welfare cost of sovereignty (10.1% of compute spending) is stated without adequate context.** Is this large or small relative to, say, the welfare cost of trade barriers in goods? Comparison to estimates from Eaton-Kortum or Arkolakis-Costinot-Rodríguez-Clare would be informative.

4. **Table A1 dual ranking notation (e.g., "2(18)") is confusing on first read.** Consider separating the baseline and cost-recovery rankings into separate columns or presenting two tables.

5. **The paper's revenue estimates for Kyrgyzstan (footnote 5) use hyperscaler retail rates as an upper bound, which is misleading.** A Kyrgyz facility selling wholesale would earn far less. The paper acknowledges this but leads with the headline number ($630–950 million), which risks overselling.

6. **The assumption that GPU prices are uniform globally needs more discussion.** Beyond export controls, logistics, insurance, and local distribution markups can raise GPU costs significantly in developing countries. Even a 5–10% GPU price premium would substantially erode the thin cost advantages documented in Table A1.

7. **The conclusion's claim that FLOP exporting is "the digital equivalent of resource-based industrialization" is provocative and appealing but undersupported.** Resource-based industrialization has a complex, often disappointing track record (the resource curse literature is large). The paper should engage with this, perhaps citing van der Ploeg, F. (2011, *Journal of Economic Literature*) on the resource curse, and discuss whether FLOP exporting might share some of the same risks—Dutch disease from concentrated export revenues, institutional degradation, volatility.

## Literature Suggestions

The following papers should be cited and engaged with:

- **Eaton, J., and S. Kortum (2002).** "Technology, Geography, and Trade." *Econometrica*, 70(5): 1741–1779. *The foundational multi-country Ricardian gravity model. The paper's framework is a special case and should be positioned accordingly.*

- **Dornbusch, R., S. Fischer, and P. Samuelson (1977).** "Comparative Advantage, Trade, and Payments in a Ricardian Model with a Continuum of Goods." *American Economic Review*, 67(5): 823–839. *The classic continuum-of-goods Ricardian model. The cost ranking and marginal exporter logic in this paper closely parallels DFS.*

- **Costinot, A., J. Donaldson, and I. Komunjer (2012).** "What Goods Do Countries Trade? A Quantitative Exploration of Ricardo's Ideas." *Review of Economic Studies*, 79(2): 581–608. *Modern empirical test of multi-country Ricardian comparative advantage.*

- **Arkolakis, C., A. Costinot, and A. Rodríguez-Clare (2012).** "New Trade Models, Same Old Gains?" *American Economic Review*, 102(1): 94–130. *Welfare implications of Ricardian trade models under iceberg costs.*

- **van der Ploeg, F. (2011).** "Natural Resources: Curse or Blessing?" *Journal of Economic Literature*, 49(2): 366–420. *Relevant to the paper's claim about FLOP exporting as resource-based industrialization.*

## Recommendation

**Major Revision.** The paper addresses a timely and important question, develops a clean if stylized model, and provides a serious calibration. The core idea—that trade theory has something to say about where AI compute locates—is valuable and, to my knowledge, novel. However, the paper needs to (i) engage with the foundational Ricardian trade literature it builds on (Eaton-Kortum, DFS), (ii) confront the industrial-organization realities that its competitive framework abstracts from, (iii) present systematic sensitivity analysis, and (iv) temper some of its more striking quantitative claims, which rest on thin cost advantages and a uniform sovereignty premium. A revised version that addresses these concerns would be a strong contribution to a literature that, given the pace of AI investment, will only become more important.
