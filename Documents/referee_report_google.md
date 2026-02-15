# Technical Review: "Selling FLOPs: A New Export Industry for Developing Countries"

*Reviewer: Senior AI Infrastructure Architect, Google Cloud*

## Summary

This paper proposes a trade model for computing services (FLOPs), arguing that countries with cheap electricity can become compute exporters by building data centers and selling GPU-hours to higher-cost markets. The model decomposes the cost of a GPU-hour into electricity, hardware, and construction, distinguishes latency-insensitive training from latency-sensitive inference, and calibrates across 86 countries. The central pitch is directed at developing countries in Central Asia and elsewhere: build data centers, export compute.

## Assessment

The paper identifies a real opportunity. The explosive growth in AI compute demand is genuine, and the geographic concentration of data center capacity in the United States and Western Europe does create openings for low-cost entrants. The training/inference distinction is directionally correct and captures something important about how AI workloads differ in their geographic constraints. As a policy-oriented framing document, this has value.

However, as someone who has spent years designing, deploying, and operating AI infrastructure at hyperscale, I find the paper's technical model of data center economics to be significantly oversimplified in ways that systematically bias the results toward the paper's desired conclusion. The model treats a GPU-hour as a commodity whose cost is determined by three inputs—and in doing so, it misses the majority of what actually determines where AI compute gets built and whether it can be operated profitably. Let me be specific about where the technical assumptions break down.

## Major Issues

**1. The cost function omits networking, which is the second-largest infrastructure cost and the critical technical constraint for training.**

Equation (2) decomposes the cost of a GPU-hour into electricity, hardware (GPU amortization), and construction. Networking is absent. This is a fundamental omission. In a modern AI training cluster, the high-speed interconnect fabric (InfiniBand or RoCE) typically costs 15–25% of total system cost. An NVIDIA DGX H100 system costs roughly $300,000–$400,000, of which the networking components (NICs, switches, cables) represent $50,000–$80,000. At rack scale, the InfiniBand fabric connecting 1,000+ GPUs costs millions.

More importantly, networking determines whether training can happen at all. Frontier model training requires tight GPU-to-GPU synchronization—during distributed data-parallel training, GPUs exchange gradients at every step, and communication overhead can consume 30–50% of total cycle time on poorly designed networks. The paper assumes training is a homogeneous good that can be produced anywhere with GPUs and electricity. In reality, training requires a tightly coupled cluster with sub-microsecond intra-node latency (NVLink) and low-microsecond inter-node latency (InfiniBand at 400 Gb/s or higher). Building such a cluster in Kyrgyzstan is not a matter of buying GPUs and plugging them in—it requires specialized networking infrastructure that is expensive, hard to source, and demands experienced engineers to deploy and maintain.

The paper should add a networking cost component to equation (2) and discuss the non-cost barriers to building high-performance interconnect fabrics in developing countries.

**2. The training/inference dichotomy is too coarse; it ignores the most important emerging workload category.**

The paper divides AI compute into "training" (latency-insensitive, fully offshorable) and "inference" (latency-sensitive, geographically constrained). This was a reasonable taxonomy in 2023. It is already outdated. The fastest-growing workload category in 2025–2026 is what the industry calls "agentic inference" or "compound AI systems"—long-running, multi-step reasoning tasks that combine inference with tool use, retrieval, and iterative refinement. These workloads are neither pure batch (like training) nor pure real-time (like a single chatbot response). They run for seconds to minutes, tolerate moderate latency, but require sustained GPU allocation and often involve multiple round-trips to external services.

Additionally, fine-tuning and reinforcement learning from human feedback (RLHF) occupy an intermediate position: they are batch-like but require rapid iteration cycles (hours, not weeks), and organizations typically want them close to their data for privacy reasons. The paper's binary split misses this growing middle ground and likely overstates the share of compute that is truly latency-insensitive and freely offshorable.

**3. The 90% GPU utilization assumption is unrealistic for the developing-country context the paper targets.**

The hardware amortization uses β = 90% utilization. Google's own fleet-wide utilization, after years of optimization with custom schedulers, preemptible VMs, and workload packing, runs in the 60–75% range for GPU clusters. Achieving 90% sustained utilization requires sophisticated orchestration software (Kubernetes with custom GPU scheduling, NVIDIA Triton or similar inference servers, job queuing systems like Slurm), 24/7 operations teams, and a deep customer pipeline to keep GPUs busy. A new entrant in Kyrgyzstan or Turkmenistan would likely see utilization rates of 40–60% in the first several years, which roughly doubles the effective hardware cost per useful GPU-hour and erodes most of the electricity cost advantage documented in Table A1.

The paper should present sensitivity analysis at realistic utilization rates (50%, 70%, 90%) and discuss what it takes operationally to achieve high utilization.

**4. The 3-year GPU lifetime is already aggressive, and the technology refresh cycle is accelerating.**

The paper amortizes GPUs over L = 3 years. This matches list depreciation schedules but not the economic reality of the AI hardware market. The H100 shipped in volume in early 2023. By late 2024, the H200 offered 1.5–2× inference throughput for similar power. By mid-2025, the Blackwell B200/GB200 offers 3–4× training throughput per watt. A data center that deployed H100s in 2023 is already at a significant performance disadvantage by 2026.

For a developing-country entrant, this creates a severe problem: the paper's cost advantage is denominated in dollars per GPU-hour, but not all GPU-hours are equal. A buyer choosing between a $1.13/hr H100 GPU-hour in Kyrgyzstan and a $1.25/hr B200 GPU-hour in Germany would rationally choose Germany because the B200 delivers 3× the FLOPs per hour. The paper treats FLOPs as homogeneous, but GPU generations are not. A cost model that accounts for FLOPs/dollar rather than just dollars/GPU-hour would significantly alter the country rankings, because developing countries are likely to lag in hardware refresh cycles due to supply chain constraints and capital access.

**5. The model completely ignores software stack, operational complexity, and reliability.**

Running a hyperscale data center is not primarily a construction and electricity problem. It is a software and operations problem. The cost function captures three physical inputs but ignores the operational overhead that determines whether a facility can actually sell GPU-hours at competitive quality levels. This includes cluster management software (job scheduling, resource allocation, monitoring), machine learning platform services (managed training, inference endpoints, model registries), security and compliance infrastructure (SOC 2, ISO 27001, data encryption at rest and in transit), redundancy and failover systems (N+1 power, network redundancy, automated recovery), and customer-facing APIs, billing, and SLA management.

At Google Cloud, our operational overhead per GPU-hour is substantial—and it scales sublinearly, meaning hyperscalers have massive cost advantages from operating tens of thousands of GPUs with shared platform teams. A new entrant operating 53,000 GPUs (the paper's reference facility) would need to build this entire software and operations stack from scratch or license it, adding significant cost that does not appear in equation (2).

**6. Grid reliability is acknowledged but not modeled, and it dominates the investment decision for the countries the paper highlights.**

The paper mentions grid reliability in passing but does not incorporate it into the cost function. For the developing countries the paper targets, this is the elephant in the room. Kyrgyzstan experiences seasonal power shortages in winter when hydropower output drops. Turkmenistan's grid is unreliable. Pakistan, Nigeria, and Ethiopia have frequent outages. For an AI training workload, a 30-second power interruption can corrupt a training run that has been running for days, destroying millions of dollars of GPU-time unless the facility has UPS systems and checkpoint recovery infrastructure. The cost of ensuring 99.99% uptime through redundant power, UPS, backup generators, and automatic transfer switches is significant and varies enormously across countries—yet it is absent from the model.

The paper should either incorporate a reliability adjustment into the cost function (effectively an uptime premium) or at minimum present the reliability profiles of the countries it recommends as compute exporters.

**7. The latency model is technically inaccurate for modern inference architectures.**

The paper models inference latency as round-trip ping time between countries. This captures network propagation delay but misses the dominant source of inference latency in practice: compute time on the GPU itself. For a large language model, a single inference request (generating a paragraph of text) involves hundreds of sequential forward passes, each taking 10–50 ms of GPU time. Total time-to-first-token is typically 100–500 ms for a large model, and total generation time can be 2–10 seconds. The network round-trip of 20–150 ms is meaningful but is not the dominant component.

This matters because the paper's latency degradation parameter (τ = 0.0008 per ms, so 100 ms adds 8% cost) may overstate the penalty of geographic distance for inference. If compute latency is 500 ms and network latency adds 100 ms, the total latency increase is only 17%, not a qualitatively different user experience. The paper's finding that inference "organizes into regional hubs" may be less pronounced when compute latency is properly accounted for, which would expand the geographic radius from which inference can be competitively served.

## Minor Issues

1. **The H100 reference hardware is already outdated.** The calibration uses H100 at $25,000 list price, but street prices have fallen to $18,000–$22,000, and Blackwell systems are shipping. The paper should either update to current hardware or discuss how hardware generation transitions affect the results.

2. **Water consumption is mentioned once but not modeled.** Modern GPU data centers using evaporative cooling consume 3–5 liters of water per kWh. For a 40 MW facility, that is roughly 3–5 million liters per day. Several of the paper's cheapest producers (Iran, Turkmenistan, Egypt, Saudi Arabia) are severely water-scarce. Liquid cooling reduces but does not eliminate water needs, and it adds significant capital cost.

3. **The "50 permanent staff" figure for a hyperscale facility is misleading.** This counts on-site operations staff but excludes the remote engineering teams (network operations, security operations, software platform, capacity planning) that are essential to running the facility. The total labor requirement per facility, including shared services, is closer to 200–400 FTEs.

4. **The paper does not discuss data egress costs.** Moving training data to a remote data center and retrieving results incurs bandwidth costs. For a frontier training run with petabytes of training data, the cost of data transfer to Kyrgyzstan over limited international bandwidth could be substantial and time-consuming.

5. **GPU export controls are more nuanced than presented.** The paper treats export controls as raising the effective ρ for sanctioned countries. In practice, the October 2022 and October 2023 U.S. export controls create a hard binary constraint: H100-class GPUs cannot legally be shipped to certain countries at all. For countries under the "GPU cap" rules (which as of 2025 cover a growing list of jurisdictions), the relevant question is not cost but availability. The paper should map the export control landscape more carefully.

6. **The paper ignores the role of cloud provider relationships.** In practice, most AI compute is consumed through cloud platforms (AWS, Azure, Google Cloud), not purchased as raw GPU-hours from independent facilities. A data center in Kyrgyzstan would need to either become a cloud provider (enormously expensive) or convince a hyperscaler to colocate there. The paper's implicit assumption that GPU-hours are a fungible commodity tradeable on spot markets does not match the industry's contract-heavy, relationship-driven structure.

7. **The PUE model should account for altitude.** Several Central Asian countries highlighted by the paper (Kyrgyzstan, Tajikistan) have data center candidate sites at high altitude (>1,000 m), where reduced air density impairs air cooling effectiveness, partially offsetting the temperature advantage.

## Literature Suggestions

The paper should engage with the following technical and policy literature:

- **Barroso, L. A., U. Hölzle, and P. Ranganathan (2018).** *The Datacenter as a Computer: Designing Warehouse-Scale Machines*, 3rd ed. Morgan & Claypool. *The standard reference on data center economics and design from Google engineers. Would ground the cost model in operational reality.*

- **Patterson, D., et al. (2022).** "The Carbon Footprint of Machine Learning Training Will Plateau, Then Shrink." *IEEE Computer*, 55(7): 18–28. *Addresses the energy and environmental dimensions of AI compute that the paper's developing-country framing needs to engage with.*

- **Jouppi, N., et al. (2023).** "TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings." *Proceedings of ISCA 2023*. *Illustrates how custom silicon (Google TPUs) complicates the GPU-centric cost model—not all FLOPs are NVIDIA FLOPs.*

- **RAND Corporation, Pilz et al. (2025).** *AI's Power Requirements Under Exponential Growth.* *Already cited, but the paper should engage more deeply with RAND's capacity constraint analysis.*

- **Jevons, W. S. (1865).** *The Coal Question.* *Classic reference on resource efficiency paradoxes. Relevant to whether cheaper compute will increase or redistribute demand—the paper assumes fixed demand shares, but Jevons' paradox suggests that cheaper compute in developing countries could create new local demand rather than export capacity.*

## Recommendation

**Major Revision.** The paper asks an important and timely question. The training/inference distinction and the sovereignty premium are genuine contributions. But the cost model is too simplified to support the paper's quantitative claims. Adding networking costs, realistic utilization rates, hardware refresh cycles, grid reliability, and operational overhead would likely compress the already-thin cost advantages further and substantially narrow the set of countries for which FLOP exporting is genuinely viable. The paper would be stronger if it acknowledged these complexities, presented a more complete total-cost-of-ownership model, and framed its results as upper-bound estimates of developing-country export potential rather than point predictions.

The core insight—that the geography of AI compute is not fixed and that energy costs create openings for new entrants—is correct and important. But the practical barriers to entry are primarily operational and institutional, not the physical-input costs that the model captures. A revised version that confronts this gap would be a valuable contribution to both the economics and technology policy literatures.
