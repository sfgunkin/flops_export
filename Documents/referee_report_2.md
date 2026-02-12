# Referee Report: "Selling FLOPs: A New Export Industry for Developing Countries"

## Summary

This paper develops a trade model in which countries produce and export computing services (FLOPs), with costs determined by electricity prices, climate, and construction costs. It distinguishes training (latency-insensitive, offshored to cheapest producer) from inference (latency-sensitive, favoring proximity). A sovereignty premium captures preferences for domestic data processing. Calibrating across 82 countries, the paper finds that a handful of cheap-energy developing economies could serve global training needs, while regional inference hubs form around demand centers.

## Assessment

The paper addresses a genuinely important and timely question. The idea of treating FLOPs as a tradeable commodity and embedding data center location decisions in an international trade framework is original and policy-relevant. The paper is well-motivated, with compelling real-world examples (Armenia, Kenya, Malaysia), and the writing is generally clear. The economics profession lacks formal models of the emerging global compute market, and this paper fills that gap.

That said, the model in its current form is quite thin relative to the ambitions of the paper. The theoretical structure is essentially a cost-minimization problem with iceberg trade costs — the "propositions" are direct consequences of the setup rather than non-obvious results. Several of the extensions discussed in Section 7 (endogenous electricity prices, oligopolistic pricing, governance as a cost shifter) would substantially strengthen the model's contribution. The paper would benefit from tighter integration between its rich institutional discussion and the formal model.

## Major Issues

### 1. The Model is Too Static and Deterministic for the Claims Made

The model assigns each demand center a single optimal supplier for each service type. This winner-take-all structure is unrealistic — in practice, buyers diversify across suppliers for resilience, and capacity constraints prevent a single country from serving all global training demand. The paper acknowledges this in the extensions but the current model cannot speak to it.

**Suggestion:** Introduce a CES demand structure or probabilistic sourcing (as in Eaton and Kortum, 2002) so that multiple producers serve each market with shares determined by cost differentials. This would (a) eliminate the knife-edge winner-take-all result, (b) allow you to compute trade shares rather than binary assignments, and (c) provide a natural framework for welfare and counterfactual analysis. The Eaton-Kortum framework, where countries draw productivity from a Fréchet distribution and trade shares are smooth functions of costs and trade barriers, would be a natural fit. It would also give the model testable gravity-equation implications.

### 2. Demand is Exogenous and Undetermined

The model specifies the supply side carefully but says almost nothing about demand. The volume $q_k$ appears in the entry condition (Equation 5) but is never modeled. How large is global compute demand? How is it distributed across countries? How does it grow? Without a demand side, the model cannot generate predictions about trade volumes, revenues, or welfare — only about which country sources from which producer.

**Suggestion:** At minimum, calibrate $q_k$ using observable proxies (GDP, IT spending, cloud market size). Better yet, introduce a simple demand function — e.g., a CES aggregator where firms in country $k$ demand compute as an input to production, with elasticity of substitution between domestic and foreign compute. This would allow you to compute equilibrium trade flows and conduct meaningful counterfactual analysis (e.g., "what happens to Kyrgyzstan's export revenue if the sovereignty premium doubles?").

### 3. The "Propositions" Are Definitional Rather Than Substantive

Proposition 1 states that buyers choose the cheapest supplier — this is the definition of cost minimization, not a result. Proposition 2 states that entry occurs when revenue exceeds fixed cost — this is a standard zero-profit condition. These are not wrong, but labeling them "propositions" overstates their novelty. Real propositions would derive non-obvious comparative statics or characterize equilibrium properties.

**Suggestion:** Derive substantive results. For example: (a) Under what conditions does the set of training exporters form a strict subset of the set of inference exporters (or vice versa)? (b) How does the critical sovereignty premium $\lambda^*$ that shifts a country from import to domestic depend on its cost position? (c) What is the welfare cost of the sovereignty premium? (d) Show formally that the training market is more concentrated than the inference market and derive conditions under which this holds. These would be genuine contributions to trade theory.

### 4. The Sovereignty Premium Is Ad Hoc

The sovereignty premium $\lambda$ is introduced as an exogenous parameter and treated as uniform across all country pairs and service types. In reality, sovereignty concerns are highly heterogeneous: the EU treats data transfers to the US differently from transfers to Central Asia; inference on personal data faces different regulatory barriers than training on public datasets; some countries have mutual adequacy agreements.

**Suggestion:** Make $\lambda$ bilateral ($\lambda_{jk}$) or at least allow it to vary by regulatory-distance categories (e.g., EU-to-EU = 0, EU-to-adequate = low, EU-to-non-adequate = high). The paper already has this notation ($\lambda_{jk}$) in Equation 3 but then collapses it to a scalar. Keeping it bilateral would be more realistic and would generate richer trade patterns. Alternatively, model $\lambda$ as a function of institutional distance (Kaufmann governance indicators, mutual data adequacy agreements, etc.).

### 5. Hardware Cost Uniformity Is Increasingly Unrealistic

The model assumes uniform GPU prices ($\rho$) across countries, but the paper itself acknowledges that US export controls raise effective hardware costs for Iran, Russia, China, and others. This is not a minor caveat — it fundamentally changes the cost ranking for several of the paper's highlighted countries. If Iran's effective $\rho$ is 2× the list price due to grey-market procurement, its status as the cheapest global producer disappears.

**Suggestion:** Introduce a country-specific hardware markup $\mu_j \geq 1$ such that the effective hardware cost is $\mu_j \cdot \rho$. Calibrate $\mu_j > 1$ for sanctioned/controlled countries and show how the cost rankings and trade patterns change. This would be a small model change with large substantive implications and would make the calibration much more credible.

## Minor Issues

### 6. The PUE Model is Overly Simplified

Equation (1) models PUE as a linear function of temperature above a threshold. In reality, PUE depends on humidity, cooling technology choice (evaporative, liquid, immersion), and altitude. The linear specification also implies that a country with 45°C peak summer temperature has PUE = 1.08 + 0.015 × 30 = 1.53, which seems high relative to actual hot-climate data centers using modern liquid cooling (which can achieve PUE ≈ 1.2 even in the Gulf).

**Suggestion:** Consider a concave PUE function (diminishing marginal cooling penalty at higher temperatures), or at minimum discuss the sensitivity of results to the PUE specification. A footnote noting that liquid/immersion cooling technologies could flatten the PUE curve in hot climates would help.

### 7. The Latency Degradation Parameter Needs More Justification

The key parameter $\tau = 0.0008/ms$ is introduced without derivation or empirical support. Where does this number come from? Is it based on user experience studies, cloud pricing data, or engineering specifications? The entire inference trade pattern hinges on this parameter.

**Suggestion:** Provide an explicit justification for the calibration of $\tau$. Ideally, cite empirical work on the economic value of latency (e.g., from financial trading, where Ding et al. (2014) estimate the value of a millisecond, or from web services, where Google/Amazon studies link latency to revenue loss). Show sensitivity analysis across a range of $\tau$ values.

### 8. Construction Cost Imputation is Weak

For 64 of 82 countries, construction costs are predicted from a cross-sectional regression on GDP per capita with $R^2 = 0.43$. This means more than half the variation in construction costs is unexplained, and for the majority of countries in the sample, a key cost component is imputed with substantial noise.

**Suggestion:** Report the regression equation and residuals. Discuss which countries are likely to have large prediction errors (e.g., resource-rich Gulf states with high GDP per capita but potentially low construction costs due to imported labor). Consider adding additional regressors (construction labor costs, steel/cement prices, regulatory indices).

### 9. The Paper Could Better Distinguish Itself from Industry Reports

Parts of the paper — particularly the introduction and data section — read more like an industry white paper than an academic economics paper. The detailed GPU specifications, data center staffing numbers, and investment announcements are interesting context but not essential for the theoretical contribution.

**Suggestion:** Move some of the industry detail to an appendix or footnotes. The introduction should foreground the economic question and model, not GPU wattage. This would also help with length.

### 10. Missing Welfare Analysis

The paper characterizes trade patterns (who sources from whom) but says nothing about welfare. How much do countries gain or lose from compute trade versus autarky? How costly is the sovereignty premium in terms of aggregate compute costs? A simple welfare calculation — total cost of compute under free trade vs. autarky vs. sovereignty premium — would substantially increase the paper's policy relevance.

### 11. The Country Taxonomy Is Underexploited

The four-regime taxonomy (full import, hybrid, full domestic, domestic training/import inference) is interesting but mostly described rather than analyzed. What predicts which regime a country falls into? A regression of regime status on country characteristics (electricity price, temperature, GDP, distance to nearest demand center) would formalize the taxonomy and make it more useful for policy.

## Text Tightening Suggestions

The paper is currently quite long for the weight of its formal model. Several sections could be substantially tightened:

1. **Introduction (Section 1):** Currently ~1,800 words. The first three paragraphs pile on demand statistics (Epoch AI, MarketsandMarkets, Deloitte, IEA, Goldman Sachs, EPRI) that largely repeat the same message: AI compute demand is growing fast. One paragraph with two or three well-chosen numbers would suffice. The Kyrgyzstan revenue calculation (end of Section 1) is compelling but could be a footnote — it breaks the flow before the contributions paragraph.

2. **Related Literature (Section 2):** This section tries to position the paper relative to six different literatures (Goldfarb-Trefler, Korinek-Stiglitz, data center siting, energy demand, trade-in-tasks, value chain upgrading) but engages superficially with each. Consider cutting to the three most important connections (trade-in-tasks, value chain upgrading, data center siting) and engaging more deeply. The Hummels-Schaur parallel (milliseconds vs. days) is clever but the sentence explaining it is already in the literature review and is then repeated in Section 3.

3. **Section 3 (Model Setup):** The first two paragraphs (lines 49–53 in the markdown) are a primer on what a FLOP is and how data centers work. This is useful context for a non-specialist but could be shortened by ~40%. The key model equations (1–3) can be presented more crisply.

4. **Section 7 (Calibration and Discussion):** The governance discussion (political stability, regulatory environment, grid reliability, geopolitical risk, corruption) runs ~800 words and reads as a standalone essay rather than a model-informed analysis. This is all important material, but it would be stronger if it were more tightly integrated with the model — e.g., by showing how the cost rankings change when governance-adjusted costs are used.

5. **Model Extensions subsection:** Currently five paragraphs on future work. Standard journal practice is to keep this to two or three sentences in the conclusion. Either promote one of these extensions into the model (which would strengthen the paper considerably) or summarize them in a single paragraph.

6. **Repetition:** The training/inference distinction is explained at least four times (introduction, Section 3.2, Section 4, and the conclusion). State it clearly once in Section 3.2 and refer back to it.

7. **Sentence-level tightening:** Many sentences use two or three clauses where one would do. For example, "The binding input is cheap electricity, not abundant skilled labor. This means that the human capital constraints that have historically limited export upgrading in developing countries (Hausmann, Hwang, and Rodrik, 2007) are largely absent for FLOP exporting" could become "The binding input is cheap electricity, so the human capital constraints that typically limit export upgrading (Hausmann et al., 2007) are largely absent."

## Literature Suggestions

1. **Eaton, J., and S. Kortum. (2002).** "Technology, Geography, and Trade." *Econometrica*, 70(5): 1741–1779. — The natural probabilistic trade framework for a multi-country model with heterogeneous costs.

2. **Deardorff, A. V. (2017).** "Comparative Advantage in Digital Trade." Working Paper 664, University of Michigan. — Directly addresses whether comparative advantage explains patterns in cloud computing and digital services trade.

3. **Arkolakis, C., A. Costinot, and A. Rodríguez-Clare. (2012).** "New Trade Models, Same Old Gains?" *American Economic Review*, 102(1): 94–130. — Provides the welfare framework your model is missing, applicable across many trade model structures.

4. **Antràs, P. (2003).** "Firms, Contracts, and Trade Structure." *Quarterly Journal of Economics*, 118(4): 1375–1418. — The make-or-buy framework in trade that maps to your Section 5 more directly than Helpman-Melitz-Yeaple.

5. **Ding, S., J. Hanna, and T. Hendershott. (2014).** "How Slow Is the NBBO? A Comparison with Direct Exchange Feeds." *Financial Review*, 49(2): 313–332. — Provides empirical estimates of latency costs that could justify your $\tau$ parameter.

## Recommendation

**Major Revision.** The paper asks an important and timely question, and the basic setup is sound. However, the model needs to be substantially enriched to deliver on its ambitions — at minimum, a probabilistic sourcing structure, calibrated demand, and country-specific hardware costs. The text needs tightening to bring the length in line with the weight of the formal contribution. With these revisions, the paper could make a meaningful contribution to the trade and development literature.
