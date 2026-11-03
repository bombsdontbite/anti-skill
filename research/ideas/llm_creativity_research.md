# LLM creativity: homogeneity, human comparisons, and techniques with measured effects on originality

Notes compiled 2026-10-26. Two kinds of claims appear below:
- **[V]** means verified in this session against the paper's abstract, HTML or publisher page.
- **[T]** means taken from the researcher's prior knowledge of the paper. The link is to the paper, but the exact number was NOT re-checked in this session. Re-check any [T] number before quoting it as a figure.

The report writer should treat [T] numbers as approximate.

---

## 1. Homogeneity and mode collapse (Artificial Hivemind, RLHF, typicality bias)

### Takeaway
LLM outputs to open-ended prompts are highly similar within a single model and across different model families. Higher temperature or min-p sampling does not fix this without breaking coherence.

There are two documented causes. Preference tuning narrows output distributions (RLHF/alignment). Human preference data itself rewards typical, familiar text: the "typicality bias" measured at α≈0.57–0.65 on HelpSteer. Aligned models are less diverse than their base models, and within a model family, larger models can be *less* diverse.

### Cited Findings

**Artificial Hivemind** (Jiang, Chai, Li, Liu, Fok, Dziri, Tsvetkov, Sap, Albalak, Choi; NeurIPS 2025 Datasets & Benchmarks, Oral; arXiv 2510.22954) [V]
- Dataset: Infinity-Chat, 26,070 real open-ended WildChat queries, of which "Creative Content Generation" is 58.0%. It carries 31,250 human annotations, 25 annotators per item. The study covers 70+ LMs, 25 detailed in the main text — [arXiv abs](https://arxiv.org/abs/2510.22954); [HTML](https://arxiv.org/html/2510.22954v2)
- Method: average pairwise embedding similarity (text-embedding-3-small) over 50 responses per model per query, on 100 queries — [HTML](https://arxiv.org/html/2510.22954v2)
- **Intra-model repetition:** with top-p 0.9 and T=1.0, the average similarity exceeds 0.8 in 79% of cases. With min-p 0.1 and T=2.0, 81% of pairs are still >0.7 and 61.2% are >0.8. The authors note that higher temperatures produce incoherent text — [HTML](https://arxiv.org/html/2510.22954v2)
- **Inter-model homogeneity:** average pairwise similarity between *different* models' responses is 71–82%. Examples: DeepSeek-V3 vs qwen-max 0.82, and DeepSeek-V3 vs GPT-4o 0.81. The 50 most similar responses to a query come from about 8 different source models on average — [HTML](https://arxiv.org/html/2510.22954v2)
- Example: "Write a metaphor about time." Responses from 25 models form two clusters, "time is a river" (dominant) and "time is a weaver" — [HTML](https://arxiv.org/html/2510.22954v2)
- Ensembles: the authors write that model ensembles "may not yield true diversity when their constituents share overlapping alignment and training priors." This is the authors' interpretation, not a tested ensemble experiment — [HTML](https://arxiv.org/html/2510.22954v2)
- Reward models and LM judges are less well calibrated to human ratings on high-disagreement or similar-quality subsets, which are exactly the cases where idiosyncratic preferences matter. The source labels the metric inconsistently (Pearson vs Spearman) — [arXiv abs](https://arxiv.org/abs/2510.22954)

**Typicality bias** (Zhang, Yu, Chong, Sicilia, Tomz, Manning, Shi, "Verbalized Sampling"; arXiv 2510.01171, preprint, v4 July 2026) [V]
- The claim: mode collapse is partly *data-driven*, because annotators systematically favour familiar, high-likelihood text — [arXiv abs](https://arxiv.org/abs/2510.01171)
- Evidence: on HelpSteer, 6,874 correctness-matched pairs give a typicality weight α̂ = 0.57±0.07 with Llama-3.1-405B as the reference model, and 0.65±0.07 with GLM-4.5 (p<10⁻¹⁴). Raw preference for the higher-log-probability response is 51.6–60.8% — [HTML](https://arxiv.org/html/2510.01171)

**RLHF / alignment reduces diversity**
- Kirk et al., "Understanding the Effects of RLHF on LLM Generalisation and Diversity" (ICLR 2024). RLHF improves out-of-distribution generalisation but substantially reduces output diversity versus SFT [T] — [arXiv 2310.06452](https://arxiv.org/abs/2310.06452)
- Padmakumar & He, "Does Writing with Language Models Reduce Content Diversity?" (ICLR 2024). Co-writing with InstructGPT reduced diversity across users' essays; base GPT-3 did not significantly. The homogenization is attributed to feedback-tuned models [T] — [arXiv 2309.05196](https://arxiv.org/abs/2309.05196)
- Mohammadi, "Creativity Has Left the Chat: The Price of Debiasing Language Models" (2024 preprint). Aligned Llama-2 has lower syntactic and semantic diversity than its base model, and its outputs cluster into "attractor states" [T] — [arXiv 2406.05587](https://arxiv.org/abs/2406.05587)
- West & Potts, "Base Models Beat Aligned Models at Randomness and Creativity" (COLM 2025). Base models outperform aligned ones on random number generation, mixed-strategy games and creative writing [T] — [arXiv 2505.00047](https://arxiv.org/abs/2505.00047)
- NoveltyBench (Zhang et al., 2025 preprint). Models generate far less distinct output than humans. Larger models within a family are often *less* diverse than smaller ones [T] — [arXiv 2504.05228](https://arxiv.org/abs/2504.05228)

**Cross-model homogeneity on divergent thinking tests** (Wenger & Kenett, "Large language models are homogeneously creative," *PNAS Nexus* 5(3), March 2026; 22 LLMs vs 102 Prolific humans) [V]
- Within-population variability (cosine distance, higher = more diverse):
  - AUT: 0.459 LLMs vs 0.699 humans (effect size 1.8, p≈3.5e-30)
  - Forward Flow: 0.518 vs 0.642 (effect size 0.87)
  - DAT: 0.632 vs 0.791 (effect size 1.1)
  - Source: [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)
- Individual originality is about the same or slightly higher for LLMs: AUT 0.711 vs 0.696, DAT 0.801 vs 0.753. Forward Flow is lower, 0.603 vs 0.637. The authors' summary: "LLM responses mirror other LLM responses far more than humans do other humans." — [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)

### Inferences
- "Each answer looks creative, the population of answers is uniform" is the consistent pattern across Hivemind, Wenger & Kenett, NoveltyBench and Si et al. (§4).
  - A creativity skill should optimise *set-level* diversity: across candidates, and across sessions and users. Per-response originality alone is not enough.
- Switching models or combining several provides limited diversity, because inter-model similarity is 71–82%.
- LLM judges and reward models are least reliable at exactly the point where a creativity skill needs them, ranking idiosyncratic options. Using a single LLM judge as the "selector" is a risk.

### Gaps
- Hivemind's exact judge/reward-model correlation values sit in its appendix tables and were not extracted.
- I found no direct measurement of homogeneity for frontier 2026 models (e.g., GPT-5.x, Claude 4.x/5.x) beyond Wenger & Kenett's 22 API models.

---

## 2. Verbalized sampling and other diversity techniques: what has measured gains

### Takeaway
- **The best-evidenced cheap technique** is to ask for *several* candidates in one call with explicit probabilities, optionally sampling from the low-probability tail. This is Verbalized Sampling, with 1.6–2.1× diversity in creative writing.
- **Chain-of-thought idea generation** gave the most diverse GPT-4 idea pools in Meincke et al.
- **Multi-agent role-play discussion** shows gains on AUT-type tests.
- **Temperature** has a weak effect on novelty and a reliable cost in coherence.
- **Telling the model to "be creative/bold"** helps individual originality only slightly and leaves group-level uniformity intact.

### Cited Findings

**Verbalized Sampling (VS)** (arXiv 2510.01171, preprint) [V]
- Method: a training-free prompt that makes the model verbalize a distribution, e.g. "Generate 5 jokes about coffee and their corresponding probabilities" — [arXiv abs](https://arxiv.org/abs/2510.01171)
- Variants:
  - VS-Standard: "Tell 5 jokes with their probabilities"
  - VS-CoT: "Think step-by-step, then tell 5 … with probabilities"
  - VS-Multi: follow-up turns of "Tell 5 more with probabilities"
  - Tail sampling: "Generate five responses with probabilities below {threshold}"
  - Source: [HTML](https://arxiv.org/html/2510.01171)
- Diversity is 1.6–2.1× direct prompting in creative writing, covering poems, stories and jokes — [arXiv abs](https://arxiv.org/abs/2510.01171)
- Human-rated diversity, Direct vs VS-Standard on a 1–4 scale (source: [HTML](https://arxiv.org/html/2510.01171)):

  | Task | Direct | VS-Standard |
  |---|---|---|
  | Poem | 1.90 | 2.39 |
  | Story | 2.74 | 3.06 |
  | Joke | 1.83 | 3.01 |

- The "+25.7% human evaluation" headline matches only the poem ratio. Treat it cautiously — [HTML](https://arxiv.org/html/2510.01171)
- VS recovers 66.8% of the base model's diversity — [HTML](https://arxiv.org/html/2510.01171)
- Quality:
  - VS-Standard is comparable to the other methods; VS-CoT gives the highest diversity while keeping quality high on poems.
  - Larger models gain 1.5–2× more diversity from VS ("more capable models benefit more").
  - VS is orthogonal to temperature, top-p and min-p and can be combined with them.
  - Source: [HTML](https://arxiv.org/html/2510.01171)
- Downstream: synthetic math data generated with VS improved average accuracy to 36.1–37.5, versus 30.6 for Direct and 34.3 for Sequence — [HTML](https://arxiv.org/html/2510.01171)
- Baselines compared were Direct, CoT, "Sequence" (k candidates in one call without probabilities) and multi-turn. Sequence is already better than Direct; adding verbalized probabilities adds more — [HTML](https://arxiv.org/html/2510.01171)

**Chain-of-thought for ideation** (Meincke, Mollick & Terwiesch, "Prompting Diverse Ideas: Increasing AI Idea Variance," 2024, arXiv preprint / Wharton working paper) [V for qualitative results]
- GPT-4 idea pools were less diverse than human groups. Prompt engineering substantially improved diversity.
- CoT prompting gave the most diverse ideas of all prompts tested, "came close" to human groups, and produced the most unique ideas.
- Source: [arXiv 2402.01727](https://arxiv.org/abs/2402.01727)
- Exact cosine-similarity numbers and the full list of prompts (personas and others) were not visible on the abstract page. The SSRN page returned 403. My recollection is that persona prompts (e.g., "act like Steve Jobs") helped less than CoT [T] — unverified.

**Temperature** (Peeperkorn, Kouwenhoven, Brown, Jordanous, "Is Temperature the Creativity Parameter of LLMs?", ICCC 2024, Best Student Paper) [V]
- Temperature has a weak positive correlation with novelty, a moderate correlation with *incoherence*, and no significant relationship with typicality or cohesion. The study used a single model and a single narrative task — [arXiv 2405.00492](https://arxiv.org/abs/2405.00492v1); [ICCC paper](https://computationalcreativity.net/iccc24/papers/ICCC24_paper_70.pdf)
- Wenger & Kenett [V], AUT variability against a human level of 0.699:
  - T=0.5: 0.418
  - T=1.0: 0.459
  - T=1.5: 0.544
  - T=2.0: 0.672, statistically equal to humans, but most T=2.0 outputs were gibberish and had to be culled
  - Source: [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)
- Hivemind: min-p at T=2.0 still leaves 61.2% of pairs above 0.8 similarity [V] — [HTML](https://arxiv.org/html/2510.22954v2)
- Min-p sampling was proposed as enabling high-temperature creative generation (Nguyen et al., ICLR 2025 oral) [T] — [arXiv 2407.01082](https://arxiv.org/abs/2407.01082). Its claimed advantages were later disputed as overstated (Schaeffer et al., 2025, "Min-p, Max Exaggeration") [T] — [arXiv 2506.13681](https://arxiv.org/abs/2506.13681)

**"Be creative" instructions** (Wenger & Kenett) [V]
- System prompts on AUT at T=1.0 gave these variability scores:
  - "Not creative": 0.477
  - Baseline: 0.459
  - "More creative": 0.503
  - "Very creative": 0.551
- Individual originality rose from 0.711 to 0.754, but variability stayed well below humans' 0.699.
- Source: [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)

**Multi-agent discussion and role-play** (Lu et al., "LLM Discussion: Enhancing the Creativity of LLMs via Discussion Framework and Role-Play," COLM 2024) [V for qualitative claim]
- Design: three phases (initiation, discussion, convergence) with role-play, giving agents diverse backgrounds and personalities.
- It outperformed single-LLM and existing multi-LLM frameworks on AUT, Similarities, Instances and the Scientific Creativity Test. Evaluation used LLM judges plus a human study.
- Source: [arXiv 2405.06373](https://arxiv.org/html/2405.06373v3)
- Counterpoint: "LLM Review" (2026 preprint) argues that more interaction does not by itself raise creativity, citing human brainstorming research where interacting groups produce fewer and less original ideas. It proposes constrained information flow (blind peer review) instead — [arXiv 2601.08003](https://arxiv.org/html/2601.08003v1)
- A survey of creativity in LLM multi-agent systems notes that agent-originality metrics are still missing — [arXiv 2507.08350](https://web3.arxiv.org/pdf/2507.08350)

**Base-model use** (West & Potts, COLM 2025) [T]
- Base, unaligned models beat aligned models on creativity and randomness. This supports a "draft with a base model, polish with an aligned model" design, where available — [arXiv 2505.00047](https://arxiv.org/abs/2505.00047)

### Inferences
- Ranked by evidence-per-cost for an agent skill:
  1. Ask for N candidates in one call with probabilities, and deliberately sample the low-probability ones (VS).
  2. Add a short reasoning step before generating, and generate ideas in steps (CoT-style; Meincke; VS-CoT).
  3. Assign genuinely different roles or perspectives and constrain the information flow, rather than running free-form chat between agents.
  4. Temperature is a minor lever, best combined with VS rather than used alone.
- Every measured gain is in *diversity or originality as scored by embeddings or LLM judges*. Gains in *usefulness* are mostly not measured, apart from VS's quality checks and the downstream math result.

### Gaps
- I found no rigorous controlled study isolating "retrieval of distant analogies" as an LLM originality technique with effect sizes. It needs a separate search, e.g. analogical prompting (Yasunaga et al. 2023, ICLR 2024), which targets reasoning, not creativity.
- I found no measured effect of iterative self-refinement on *originality*, as opposed to quality. Self-Refine (Madaan et al. 2023) measured quality and preference, not novelty.
- Meincke et al.'s numerical results are unverified because the SSRN page returned 403.

---

## 3. Humans vs LLMs on divergent thinking tests (AUT, TTCT, DAT)

### Takeaway
On standard divergent-thinking tests, GPT-4-class models score above the *average* human, sometimes by a lot. The top 10–20% of humans still match or beat the best models.

On expert-judged creative writing, LLM stories fall well short of professionals. LLMs win on the mean; humans win on the tail and on population diversity.

### Cited Findings
- **Koivisto & Grassini 2023** (*Scientific Reports* 13:13601), "Best humans still outperform artificial intelligence in a creative divergent thinking task" [T]
  - Design: 256 humans vs ChatGPT-3.5, ChatGPT-4 and Copy.ai on the AUT with 4 objects.
  - AI mean scores were higher than the human mean. The best human responses equalled or beat the best chatbot responses in most object/metric combinations.
  - Source: [Nature](https://www.nature.com/articles/s41598-023-40858-3)
- **Hubert, Awa & Zabelina 2024** (*Scientific Reports* 14:3440) [T]
  - Design: GPT-4 vs 151 humans on the AUT, Consequences Task and DAT.
  - GPT-4 was more original and elaborate than humans across tasks. The authors caution that the tests measure potential, not creative achievement.
  - Source: [Nature](https://www.nature.com/articles/s41598-024-53303-w)
- **Bellemare-Pepin, Lespinasse, … Olson, Bengio, Jerbi**, "Divergent creativity in humans and large language models" [V]
  - Venue: arXiv 2405.13012, 2024; published in *Scientific Reports*, January 2026.
  - Design: DAT plus creative writing, comparing LLMs against about 100,000 humans.
  - Findings: GPT-4 exceeds the human average on the DAT, but the most creative humans still outperform all models. Press summaries put this at the top 10%.
  - The authors also show that prompt design and temperature tuning change LLM semantic diversity. A co-author is the DAT's developer (Olson).
  - Sources: [arXiv](https://arxiv.org/abs/2405.13012); [Sci Rep](https://www.nature.com/articles/s41598-025-25157-3); [U of Toronto news](https://www.utoronto.ca/news/ai-more-creative-most-not-all-humans-study)
- **Wenger & Kenett 2026** (*PNAS Nexus*) [V]
  - Individual originality is roughly at parity: LLMs are slightly higher on AUT and DAT and lower on Forward Flow.
  - Group variability is far lower, with effect sizes 0.87–1.8.
  - Source: [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)
- **Chakrabarty et al., "Art or Artifice? LLMs and the False Promise of Creativity"** (CHI 2024) [T]
  - Design: the Torrance Test of Creative Writing (TTCW), 14 binary tests adapted from the TTCT and judged by experts.
  - LLM-generated stories passed 3–10× fewer tests than stories by professional writers.
  - LLMs were also poor at judging TTCW themselves.
  - Source: [arXiv 2309.14556](https://arxiv.org/abs/2309.14556)
- **Holzner, Maier & Feuerriegel 2025 meta-analysis** (arXiv 2505.17241, preprint; 28 studies, 8,214 participants) [V]
  - GenAI vs humans: no significant difference in creative performance, g = −0.05.
  - Source: [arXiv](https://arxiv.org/abs/2505.17241)

### Inferences
- The relevant comparison for an agent skill is the expert or top-decile human, not the average one. That is where LLMs still lose, and it is the bar for "original."
- Divergent-thinking tests scored by semantic distance favour LLMs. They reward word-level distance, which LLMs can optimise, more than insight or usefulness. Expert-judged writing tests (TTCW) are much less favourable.

### Gaps
- I found no large-scale 2025–2026 TTCT (figural) comparison.
- Koivisto & Grassini and Hubert et al. numbers are [T]: the exact per-object results were not re-checked.

---

## 4. Research and product ideation: novel but less feasible, and the execution gap

### Takeaway
LLM research ideas were rated *more novel* than expert ideas at the proposal stage (Si et al., ICLR 2025). Once executed, they lost significantly more of their rating than human ideas did (Si et al., 2025 follow-up).

In product ideation, GPT-4 ideas won on average purchase intent and filled the top decile (Girotra et al.). But AI idea pools are less diverse and contain many duplicates.

### Cited Findings
- **Si, Yang & Hashimoto, "Can LLMs Generate Novel Research Ideas?"** (ICLR 2025) [T]
  - Design: more than 100 NLP researchers wrote and blind-reviewed ideas.
  - AI ideas were rated significantly more novel (p<0.05) and slightly weaker on feasibility.
  - Of about 4,000 generated seed ideas, only about 200 were non-duplicates. This is the agent's lack of diversity at scale.
  - LLM self-evaluation was unreliable.
  - Source: [arXiv 2409.04109](https://arxiv.org/abs/2409.04109)
- **Si, Hashimoto & Yang, "The Ideation-Execution Gap"** (arXiv 2506.20803, June 2025 preprint) [V]
  - Design: 43 expert researchers executed the ideas, then the projects were reviewed.
  - LLM ideas' scores dropped significantly more than human ideas' on novelty, excitement, effectiveness and overall (p<0.05). After execution, human ideas outscored LLM ideas on many metrics.
  - Source: [arXiv](https://arxiv.org/abs/2506.20803)
- **Girotra, Meincke, Terwiesch & Ulrich, "Ideas Are Dimes a Dozen: LLMs for Idea Generation in Innovation"** (2023, SSRN working paper) [T]
  - Design: GPT-4 vs Wharton MBA students' product ideas, judged by consumer purchase intent.
  - GPT-4 ideas had higher average purchase intent. Of the 40 best ideas (top 10%), 35 came from GPT-4.
  - Few-shot examples of good ideas raised quality further but reduced novelty and diversity.
  - Source: [SSRN 4526071](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4526071)
- **Meincke, Mollick & Terwiesch 2024**: GPT-4 idea pools are less diverse than human groups; CoT narrows the gap [V] — [arXiv 2402.01727](https://arxiv.org/abs/2402.01727)
- **Boussioux, Lane, Zhang, Jacimovic & Lakhani, "The Crowdless Future? Generative AI and Creative Problem-Solving"** (*Organization Science*, 2024) [T]
  - Human-AI solutions were rated higher in value and quality, but human crowd solutions were more novel.
  - "Differentiated search" prompting, which asks for ideas that differ from previous ones, raised novelty.
  - Source: [SSRN 4533642](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4533642)

### Inferences
- Pairing "novel" with "unexecuted" is a known trap. A creativity skill should include an explicit feasibility and execution check, a "how would this actually be done / what breaks" pass. It should not trust novelty ratings, especially from LLM judges.
- The duplication finding (about 5% unique) means generating many ideas without deduplication and diversity control wastes most of the budget.

### Gaps
- The exact effect sizes for the execution-gap score drops were not on the abstract page.
- The Boussioux et al. venue, year and numbers are [T].

---

## 5. Diversity reduction when people use AI (homogenization)

### Takeaway
AI help raises the creativity of *individual* outputs, especially for less creative people. It makes outputs *more similar to each other* across people. It can also lower people's unassisted creativity afterwards.

The meta-analytic diversity effect is large: g = −0.86.

### Cited Findings
- **Doshi & Hauser 2024**, "Generative AI enhances individual creativity but reduces the collective novelty of stories" (*Science Advances* 10(28): eadn5290) [T]. The publisher page returned 403, so these numbers were not re-checked.
  - Design: about 293 writers and about 600 evaluators. Writers had access to one or five GPT-4 story ideas.
  - With five ideas, stories were rated about 8% more novel and about 9% more useful.
  - Gains were concentrated among the least creative writers.
  - AI-assisted stories were significantly more similar to each other, roughly a 10% increase in similarity. The authors frame this as a social dilemma: individually better, collectively narrower.
  - Source: [Science Advances](https://www.science.org/doi/10.1126/sciadv.adn5290)
- **Anderson, Shah & Kreminski, "Homogenization Effects of LLMs on Human Creative Ideation"** (ACM Creativity & Cognition 2024) [T]
  - ChatGPT users' ideas were less semantically distinct *across users* than ideas from an Oblique Strategies control.
  - Users also felt less responsible for their ideas.
  - Source: [arXiv 2402.01536](https://arxiv.org/abs/2402.01536)
- **Kumar, Vincentius, Jordan & Anderson, "Human Creativity in the Age of LLMs"** (CHI 2025) [V for design and main claim]
  - Design: 1,100 participants in two pre-registered experiments. Conditions were a direct-answer LLM, a coach-style LLM, and no AI; the final test was unassisted.
  - Assistance gave short-term gains but may hurt independent performance once the AI is removed.
  - A secondary source reports that the exposed groups stayed more homogeneous afterwards and that coaching was not better [unverified].
  - Sources: [arXiv 2410.03703](https://arxiv.org/abs/2410.03703); [ACM DL](https://dl.acm.org/doi/10.1145/3706598.3714198)
- **Holzner et al. 2025 meta-analysis**: human+GenAI vs humans alone g = +0.27 for creative performance, and g = −0.86 for idea diversity [V] — [arXiv 2505.17241](https://arxiv.org/abs/2505.17241)
- **Lee & Chung 2024**, "An empirical investigation of the impact of ChatGPT on creativity" (*Nature Human Behaviour*) [T]
  - Design: five experiments.
  - ChatGPT-assisted ideas were more creative than those from Google-search or no-tool conditions. The gains were incremental rather than radically new ideas.
  - Source: [Nature Hum Behav](https://www.nature.com/articles/s41562-024-01953-1)
- **Ashkinaze et al. 2024**, "How AI Ideas Affect the Creativity, Diversity, and Evolution of Human Ideas" (preprint) [T]
  - Exposure to AI ideas increased *collective* idea diversity in a dynamic multi-round setup, but did not increase individual creativity.
  - This contrasts with Doshi & Hauser. The difference is consistent with AI ideas being one input among many, not the sole source.
  - Source: [arXiv 2401.13481](https://arxiv.org/abs/2401.13481)
- **Zhou & Lee 2024**, "Generative AI, human creativity, and art" (*PNAS Nexus*) [T]
  - About 50k artists. AI adopters' productivity rose about 25% and their works received more favourites.
  - Average content novelty fell over time. Artists who used AI to explore novel ideas did best.
  - Source: [PNAS Nexus](https://academic.oup.com/pnasnexus/article/3/3/pgae052/7618478)
- **Dell'Acqua et al. 2023**, "Navigating the Jagged Technological Frontier" (HBS Working Paper 24-013; 758 BCG consultants) [T]
  - With GPT-4, task quality rose more than 40% inside the frontier.
  - The ideas produced were markedly less variable (more homogeneous) than those of the no-AI group.
  - Source: [SSRN 4573321](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4573321)
- **2026 studies**:
  - A study on perceived human agency found that low-agency LLM use increased idea homogeneity without changing rated creativity [V, from search snippet] — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2713374526000233)
  - A 2026 ACM review argues that the 2022–2026 evidence shows a "reorganization" of creative diversity rather than its loss [V, from search snippet] — [ACM DL](https://dl.acm.org/doi/10.1145/3822301.3822304)
  - A 2026 arXiv preprint finds structural convergence in AI-augmented student essays — [arXiv 2603.21228](https://arxiv.org/pdf/2603.21228)

### Inferences
- An agent skill that hands the *same* few "best" ideas to every user reproduces the Doshi & Hauser dilemma at scale. Varying perspectives per session and preserving the user's own seed both reduce collective homogenization.
- The Kumar et al. "hangover" result argues for a skill that keeps the human generating, for example by asking for the user's own idea first, rather than replacing the human's ideation.

### Gaps
- The exact Doshi & Hauser and Anderson et al. figures need re-checking; the paywalled pages were not fetched.
- The 2026 ACM review's details were seen only in a search snippet.

---

## 6. Human–AI co-creation: which setups worked best

### Takeaway
The evidence most consistently supports these setups:
- **AI as a high-volume, high-variance generator with the human as selector and integrator.** Human+AI g=+0.27 over humans alone.
- **Diverse AI inputs**: multiple personas and many varied ideas instead of one "best" idea. These preserve collective diversity.
- **Human-led framing**, where the human or AI asks questions and the human reframes.

Setups where the AI replaces the human's first draft, or where the human sees one AI idea, homogenize the most.

### Cited Findings
- **Wan & Kalman, "Diverse AI Personas Can Mitigate the Homogenization Effect in Human-AI Collaborative Ideation"** [V]
  - Venue: arXiv 2504.13868; *Computers in Human Behavior: Artificial Humans*, 2026.
  - Design: a replication and extension of Doshi & Hauser. 10 structured personas generated 300 plots.
  - Diverse AI inputs preserved story diversity relative to a human-only baseline, with some evidence of enhancement in the 1-plot condition.
  - No quantitative effect is in the abstract, and there is no single-persona comparison.
  - Source: [arXiv](https://arxiv.org/abs/2504.13868)
- **"Partnering with Generative AI: Human-Led and Model-Led Interaction in Human-AI Co-Creation"** (arXiv 2510.23324, preprint) [V, from search snippet]
  - Question mode and model-led interaction improved idea quality.
  - The paper codes elaboration depth, from echoing AI output to radical reframing.
  - Source: [arXiv](https://arxiv.org/html/2510.23324v3)
- **Doshi & Hauser 2024**: five AI ideas gave larger gains than one [T] — [Science Advances](https://www.science.org/doi/10.1126/sciadv.adn5290)
- **Boussioux et al. 2024**: differentiated-search human-AI co-creation, where each new prompt asks for something different from the previous ideas, improved novelty over independent sampling [T] — [SSRN 4533642](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4533642)
- **Dell'Acqua et al. 2025, "The Cybernetic Teammate"** (HBS Working Paper 25-043; 776 P&G professionals) [T]
  - Individuals with AI matched the performance of two-person teams without AI.
  - AI broke functional silos: R&D and commercial staff proposed more balanced solutions.
  - Source: [SSRN 5188231](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5188231)
- **Holzner et al. 2025**: human+AI beats humans alone (g=0.27) while lowering diversity (g=−0.86) [V] — [arXiv 2505.17241](https://arxiv.org/abs/2505.17241)

### Inferences
- A promising skill pattern:
  1. The user gives their own seed or framing first.
  2. The agent generates a large, deliberately varied pool (VS, with roles or personas), deduplicates it, and spreads the candidates across the embedding space.
  3. The human selects and combines.
  4. The agent critiques feasibility and execution risk (§4).
- The evidence that "AI as critic" beats "AI as generator" is thin. I found no controlled study that measured originality for critic-only AI.

### Gaps
- I found no head-to-head RCT comparing AI-generator+human-selector, AI-critic and AI-coach on originality *and* usefulness together.
  - Kumar et al. compared direct answers vs coach, but with unassisted post-tests.

---

## 7. Techniques tested and found NOT to help (or to help much less than assumed)

### Takeaway
Six things do not deliver the diversity they are assumed to:
- Temperature alone
- Min-p at high temperature
- Telling the model to "be creative/bold"
- Swapping or ensembling aligned models
- Few-shot "good examples"
- Unconstrained multi-agent chat

All give small diversity gains, trade off coherence, or reduce novelty.

### Cited Findings
- **Temperature**:
  - Weak link to novelty, moderate link to incoherence, no link to typicality [V] — [arXiv 2405.00492](https://arxiv.org/abs/2405.00492v1)
  - Reaching human-level AUT variability required T=2.0, where most outputs were gibberish [V] — [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)
- **Min-p / high-temperature sampling**: 61.2% of response pairs still exceed 0.8 similarity at T=2.0 with min-p 0.1 [V] — [Hivemind HTML](https://arxiv.org/html/2510.22954v2). The original min-p claims are disputed [T] — [arXiv 2506.13681](https://arxiv.org/abs/2506.13681)
- **"Be (very) creative / bold" instructions**: minor individual gains; population uniformity stays far from the human level [V] — [PNAS Nexus](https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001)
- **Model ensembles / switching models**: inter-model similarity is 71–82%. The authors' warning that ensembles sharing alignment priors do not yield true diversity is an interpretation, not a tested ensemble experiment [V] — [Hivemind HTML](https://arxiv.org/html/2510.22954v2)
- **Few-shot examples of good ideas**: raised quality and purchase intent but lowered novelty [T] — [SSRN 4526071](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4526071)
- **Unconstrained multi-agent interaction**: argued not to raise creativity by itself; the authors favour constrained information flow (position paper and method, preprint 2026) — [arXiv 2601.08003](https://arxiv.org/html/2601.08003v1)
- **Coach-style LLM assistance**: did not improve later unassisted creativity in Kumar et al. (CHI 2025) [V for main claim] — [arXiv 2410.03703](https://arxiv.org/abs/2410.03703)
- **LLM as the judge of creativity**:
  - Reward models and LM judges are miscalibrated on idiosyncratic or high-disagreement items [V] — [arXiv 2510.22954](https://arxiv.org/abs/2510.22954)
  - LLMs judge TTCW poorly [T] — [arXiv 2309.14556](https://arxiv.org/abs/2309.14556)
  - LLM idea ranking was unreliable in Si et al. [T] — [arXiv 2409.04109](https://arxiv.org/abs/2409.04109)
- **Bigger or more aligned models**: within families, larger models are often less diverse [T] — [NoveltyBench](https://arxiv.org/abs/2504.05228). Aligned models are less creative than base models [T] — [arXiv 2505.00047](https://arxiv.org/abs/2505.00047)

### Inferences
- A skill should not rely on its own "creative" adjectives or on temperature. Structural interventions are what move the needle:
  - several candidates with probabilities, then tail sampling
  - staged reasoning
  - forced differentiation from earlier candidates
  - distinct roles
  - external deduplication and diversity checks
  - human selection
- Self-judging novelty with the same model is unreliable. It should be backed by an embedding-distance check against the pool and against "typical" answers.

### Gaps
- I found no controlled evidence on persona prompting *alone*, outside multi-agent setups, for LLM originality. The Meincke et al. persona results are unverified.
- I found no measured study of "list N then pick the most unusual" as distinct from VS tail sampling. VS's "probabilities below threshold" variant is the closest tested analogue.
