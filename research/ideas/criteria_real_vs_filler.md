# Criteria for a real creative idea vs generic filler, and how idea creativity is evaluated

Notes collected 2026-10-26. Tags: **[EVIDENCE]** = empirical study with data; **[THEORY]** = a definitional or conceptual framework; **[OPINION]** = a practitioner essay or heuristic with no controlled data behind it. Each source carries its date. "(snippet)" marks a claim taken from search-result summaries that I did not read in the primary text, so verify it before quoting.

---

## 1. Standard definitions and dimensions (novelty/originality, usefulness, surprise, feasibility, elaboration) and how they are operationalized

### Takeaway
The field's consensus definition needs two things together: **originality and effectiveness/usefulness** (Runco & Jaeger 2012). Boden adds **surprise** as the experiential marker and splits it into three kinds (combinational, exploratory, transformational). In practice, "originality" is measured three ways: (a) statistical rarity in a pool of responses, (b) subjective human ratings, (c) semantic distance from the prompt. Feasibility and elaboration are scored separately. In a study of expert evaluations, the overall score tracked novelty and excitement and barely tracked feasibility.

### Cited Findings
- [THEORY] Runco & Jaeger's (2012, *Creativity Research Journal*) "standard definition": creativity requires (1) originality and (2) effectiveness. The roots go back to Stein (1953) and Barron (1955). Originality alone is not enough, because random processes produce original things that are not valuable. Source is secondary (an AI-creativity paper citing R&J): [On the Creativity of AI Agents, arXiv 2604.13242 (2026)](https://arxiv.org/pdf/2604.13242); see also [Creativity of Deep Learning, arXiv 2012.02282 (2020)](https://arxiv.org/pdf/2012.02282) (snippet)
- [OPINION/THEORY] Runco himself later criticised the definition as "too objective": it may miss the range of creative activity. Grech (2016) notes that recognition and acceptance of the definition cannot be assumed — [Runco interview, Destination Imagination (undated)](https://www.destinationimagination.org/wp-content/uploads/Navigating-the-Tensions-Inherent-in-Understanding-Creativity-An-Interview-with-Mark-Runco.pdf); [Grech, OAR@UM (2016)](https://www.um.edu.mt/library/oar/handle/123456789/15765) (snippet)
- [THEORY] Boden: different kinds of surprise correspond to different mechanisms of novelty.
  - **Combinational**: combining features of existing concepts.
  - **Exploratory**: new instances inside a conceptual space's existing rules.
  - **Transformational**: changing the space's rules so that the "previously inconceivable" becomes possible.

  An idea that stays inside the "standard, reasonable" space is less surprising and therefore less creative — [On the Creativity of AI Agents, arXiv 2604.13242 (2026)](https://arxiv.org/pdf/2604.13242); [Creativity and Machine Learning: A Survey, arXiv 2104.02726 (2021)](https://arxiv.org/pdf/2104.02726) (snippet)
- [EVIDENCE] Operationalization by rarity ("uniqueness/infrequency scoring") is among the most prominent and the most criticised approaches. Its threshold depends on sample size, and the originality score is confounded with fluency (the number of ideas). Once fluency is partialled out, the reliability of originality scores is usually very low (Benedek et al. 2013). Silvia et al. (2008, *PACA* 2:68–85) proposed **Top-2 scoring** instead: the participant picks their two best ideas, and raters score only those — [Benedek et al. 2013, PMC4001084](https://pmc.ncbi.nlm.nih.gov/articles/PMC4001084); [Silvia, Beaty, Nusbaum 2013, Intelligence](https://beatylab.la.psu.edu/files/2020/08/2013_Silvia_Intelligence.pdf); [Reiter-Palmon et al. scoring review supplement, APA (2019)](https://supp.apa.org/psycarticles/supplemental/aca0000227/ACA-2018-0123_Suppl.docx) (snippet)
- [EVIDENCE] Operationalization of research ideas in Si, Yang & Hashimoto (2024/ICLR 2025): a 1–10 scale on five axes (Novelty, Excitement, Feasibility, Expected effectiveness, Overall). Across reviewers, **Overall correlated with Excitement r=0.854 and with Novelty r=0.725, and with Feasibility only r=0.097**. Expert judges implicitly rate "creativity" as novelty and excitement and give little weight to feasibility — [Si et al., arXiv 2409.04109 HTML (Sep 2024)](https://arxiv.org/html/2409.04109v1)
- [EVIDENCE] LLMs rating originality in science and engineering prioritise uncommonness and remoteness, and they weigh those facets differently from humans — [arXiv 2502.03253 (Feb/May 2025)](https://arxiv.org/pdf/2502.03253) (snippet)
- [EVIDENCE] Product practice: Girotra/Meincke/Terwiesch/Ulrich (Wharton, 2023) measured idea **quality** as purchase intent from a panel of target buyers (college students; product under $50). That is a proxy for "usefulness" — [Wharton Mack Institute (2023)](https://mackinstitute.wharton.upenn.edu/2023/new-working-paper-finds-chatgpt-a-better-innovation-ideator-than-mba-students/)

### Inferences
- For an "is this water?" filter, the minimal axes are: **originality** (relative to a pool, not in the abstract), **appropriateness/usefulness** (solves a real problem under real constraints), **surprise** (did it break a rule of the space, or only recombine inside it?). Feasibility goes on a separate axis, so that "safe and doable" does not stand in for "creative".
- The fluency confound bears directly on AI. A skill that produces 30 ideas will win "originality-by-count" through quantity alone. Comparisons need Top-k: the generator picks its k best, and only those are compared.
- Boden's taxonomy works as a classifier in the filter. Most LLM "creativity" is combinational ("X for Y", "Uber for Z"). An exploratory or transformational move is rarer and is what separates an idea from filler.

### Gaps
- I did not read the original Runco & Jaeger 2012 text or Boden (*The Creative Mind*, 1990/2004); both are cited through secondary sources.
- I did not find Simonton's formalization (originality × utility × surprise, from his 2012/2018 work) in this session.
- I found no single standard operationalization of "elaboration" outside the TTCT.

---

## 2. Evaluation methods: CAT, multiple raters and IRR, semantic distance (SemDis, OCS/Ocsai, DAT), LLM-as-judge and its biases, originality-by-rarity

### Takeaway
The gold standard is **Amabile's CAT**: independent domain experts rate products relative to one another. Experts agree with each other well; novices do not. Automated metrics are well validated for **narrow tasks** (AUT, DAT), with r≈0.8 for the fine-tuned Ocsai on AUT. They are not validated for "product/business ideas". As judges of research and product ideas, **LLMs perform poorly**: in Si et al. their agreement with humans sat at chance level (43–53%), below human-human agreement (56%). They also prefer their own text, the first position and longer answers.

### Cited Findings
**CAT and human raters**
- [EVIDENCE] CAT (Amabile 1982) is often called the "gold standard" of creativity assessment — [Kaufman & Baer, "Who decides what is creative", Rider Univ. PDF](https://www.rider.edu/sites/default/files/2024-05/WhoDecidesWhatIsCreative.pdf) (snippet)
- [EVIDENCE] Experts vs novices (short fiction, 2009): mean ratings differed slightly, the two sets correlated r=.71, and experts were far more consistent with each other. Novice reliability is "potentially problematic". Lee, Lee & Young (2005) on flower designs: novice IRR was low, and expert rater variance was much smaller — [Kaufman, Baer et al., Rider Univ. PDF](https://www.rider.edu/sites/default/files/2024-05/ExpertiseDomains%26CAT.pdf); [CAT raters poems PDF](https://www.rider.edu/sites/default/files/2024-05/CATRatersPoems.pdf) (snippet)
- [EVIDENCE] Kaufman & Baer review: novices are a poor choice of CAT rater, and **quasi-experts** are a compromise between rigour and budget. Different expert groups correlate with each other at r>.40, often >.70 — [Rider Univ. PDFs](https://www.rider.edu/sites/default/files/2024-05/WhoDecidesWhatIsCreative.pdf) (snippet)
- [EVIDENCE] Baer, Kaufman & Gentile: 13 expert judges rated stories, narratives and poems by 8th-graders, with very high IRR — [Rider Univ. PDF](https://www.rider.edu/sites/default/files/2024-05/baerkkaufmangentile.pdf) (snippet)
- [EVIDENCE] Experts' agreement on the novelty of hackathon projects was **low**, and it fell further as the scale got finer: Cohen's κ went from 0.18 to 0.04 — [arXiv 2503.04290 (Mar 2025)](https://arxiv.org/pdf/2503.04290) (snippet)
- [EVIDENCE] In Si et al., agreement between expert reviewers on ideas was a balanced accuracy of **56.1%**. For comparison: NeurIPS 2021 66.0%, ICLR 2024 71.9%, random 50% — [Si et al. (Sep 2024)](https://arxiv.org/html/2409.04109v1)

**Automated semantic metrics**
- [EVIDENCE] **SemDis** (Beaty & Johnson 2021): semantic distance between prompt and response, computed from embeddings. Beaty, Johnson, Zeitlen & Forthmann (2022, *CRJ*) recommend a set of 13 AUT objects with acceptable reliability. These relate moderately to human ratings and to creative personality, and the result replicated in a second sample — [Beaty et al. 2022 CRJ PDF](https://beatylab.la.psu.edu/files/2022/09/2022-Beaty-CRJ.pdf); [ECR Hub summary](https://ecrhub.org/publications/semantic-distance-and-alternate-uses-task-recommendations-reliable-automated) (snippet)
- [EVIDENCE] Multilingual validation of SemDis (Patterson et al. 2023): N=6,522, 12 languages. Its own documentation warns that the models are validated **only for the AUT**, not for other tasks, and that quality varies by language — [SemDis/CAP documentation, PSU](https://cap.ist.psu.edu/static/assets/Documentation.pdf); [Multilingual Semantic Distance, UvA](https://dare.uva.nl/id/0189eff5-8bc5-4ec4-a5a0-d7b8054ef166) (snippet)
- [EVIDENCE] **DSI** (Divergent Semantic Integration; Johnson et al. 2022) is the mean pairwise distance between the words of a long text, used for stories — [SemDis documentation](https://cap.ist.psu.edu/static/assets/Documentation.pdf) (snippet)
- [EVIDENCE] Orwig et al. (2025): about 10,000 responses across three DT tasks. Semantic distance is a strong predictor of creativity ratings, with a non-linear relationship (a "sweet spot") — [CCN 2025 abstract](https://2025.ccneuro.org/abstract_pdf/Orwig_2025_A_sweet_spot_creative_ideation_Non-linear.pdf) (snippet)
- [EVIDENCE] **DAT** (Olson et al., *PNAS* 118(25), 22 Jun 2021): name 10 maximally unrelated nouns, scored by mean GloVe distance. N=8,914 from 98 countries. DAT correlates with AUT and the Bridge-the-Associative-Gap task about as strongly as those two correlate with each other. It needs no human raters, and it measures only one aspect of creativity — [BPS Research Digest (2021)](https://bps.org.uk/research-digest/ability-name-unrelated-words-good-test-creativity); [ScienceAlert](https://www.sciencealert.com/scientists-invented-a-simple-4-minute-test-for-creativity-and-you-can-try-it-out) (secondary)
- [EVIDENCE] **Open Creativity Scoring / Ocsai** (Organisciak et al. 2023): a fine-tuned LLM scorer for AUT, up to **r=.81** with human ratings on held-out data (the developers' own evaluation), 1–5 scale. Independent checks:
  - German data (~50k responses): Ocsai beats GPT-4.
  - Polish data (GPT-3 version): r=.42–.72.
  - Children: generalization is questionable.

  [Ocsai site, Univ. of Denver](https://openscoring.du.edu/ocsai); [MDPI J. Intelligence 13(6):64 (2025)](https://www.mdpi.com/2079-3200/13/6/64) (snippet)

**LLM-as-judge for creativity**
- [EVIDENCE] Si et al.: LLM evaluators against human review scores. GPT-4o direct 50.0%, pairwise 45.0%; Claude-3.5 direct 51.7%, pairwise 53.3%; "AI Scientist" reviewer 43.3%. **All are below the 56.1% human-human agreement.** The authors list "failures of LLM self-evaluation" among their main findings — [Si et al. (Sep 2024)](https://arxiv.org/html/2409.04109v1)
- [EVIDENCE] On AUT, human-LLM agreement τ=0.49 beat human-human τ=0.39. On a complex multi-step creativity task, a few-shot LLM judge reached only Pearson 0.31 with humans — as cited in [Decoupled Analysis-Judging, arXiv 2609.03432 (Sep 2026)](https://arxiv.org/pdf/2609.03432) (snippet)
- [EVIDENCE] In ML-engineering creativity, GPT-5 as judge reached Spearman r=0.732 with human annotations — [arXiv 2608.30047 (Aug 2026)](https://arxiv.org/pdf/2608.30047) (snippet). On Persian literary text, Claude 3.7 Sonnet agreed with humans better than GPT-4o — [arXiv 2509.18401 (2025)](https://arxiv.org/pdf/2509.18401) (snippet). On creative writing, LLM judges struggle with subjective originality ratings, which motivates rater-aware evaluation anchored to humans — [arXiv 2510.05135 (Oct 2025)](https://arxiv.org/html/2510.05135) (snippet)
- [EVIDENCE] **Self-preference bias**: GPT-4 and Llama 2 tell their own text from others' above chance, and the strength of self-recognition correlates linearly with the strength of self-preference (Panickssery, Bowman, Feng, NeurIPS 2024 oral). The effect holds against simple confounders — [arXiv 2404.13076 (Apr 2024)](https://arxiv.org/abs/2404.13076v1); [NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/hash/7f1f0218e45f5414c79c0679633e47bc-Abstract-Conference.html). The bias is stronger in larger models — [arXiv 2504.03846 (2025)](https://arxiv.org/pdf/2504.03846v3) (snippet)
- [EVIDENCE] **Position and verbosity bias** (Zheng et al., MT-Bench, NeurIPS 2023):
  - Position: Claude-v1 and GPT-3.5 prefer the first position. GPT-4 stays consistent under an A/B swap in only 65% of cases with the default prompt. Renaming the assistants changes the verdict (a name bias).
  - Verbosity: a "repetitive list" attack fools Claude-v1 and GPT-3.5 in 91.3% of cases and GPT-4 in 8.7%.
  - Self-enhancement bias is also examined.
  - Overall agreement with humans exceeds 80%, but that is for chat-answer quality, not creativity.

  [arXiv 2306.05685 (Jun 2023)](https://arxiv.org/abs/2306.05685v1) (snippet)
- [EVIDENCE] "Rating Roulette": LLM judges are inconsistent with themselves across repeated runs — [EMNLP Findings 2025](https://aclanthology.org/2025.findings-emnlp.1361.pdf) (title and snippet only)
- [OPINION] A vendor recommendation: validate a judge on 200–500 expert-labelled examples until correlation exceeds 0.85. This is a heuristic, not a research standard — [Openlayer blog (Mar 2026)](https://www.openlayer.com/blog/llm-as-judge-evaluation-guide)

**Originality-by-rarity in the pool (counting duplicates)**
- [EVIDENCE] Si et al.: the agent generated 4,000 seed ideas per topic, deduplicated at cosine ≥ 0.8. **Only 200 of the 4,000 (~5%) were unique.** Duplication rises with generation volume, so the LLM "does not scale" in diversity — [Si et al. (Sep 2024)](https://arxiv.org/html/2409.04109v1)
- [EVIDENCE] Meincke, Mollick & Terwiesch (SSRN, Feb 2024): pools of GPT-4 ideas under various prompts are **less diverse** than pools from groups of people. **Chain-of-Thought** gives the highest diversity among the prompts tested, approaching human groups — [SSRN 4708466](https://papers.ssrn.com/abstract=4708466) (snippet)

### Inferences
- An LLM-as-judge is an inadequate sole arbiter of "is this creative?" for product ideas. At best it agrees with humans as well as humans agree with each other (AUT). On complex ideas it is at chance. It also systematically prefers LLM-style text, longer answers and the first position. In a blind test it can be a pre-filter or a secondary signal, but not the primary verdict.
- Rarity in the pool is the cheapest, bias-free "water" metric for the skill: generate N ideas, embed them, cluster at a threshold (~0.8 cosine as in Si et al.), and count the share of unique clusters and how far each idea sits from the cluster centre of the "baseline" generation (a plain model without the skill). An idea that lands in a cluster the baseline also hits is water by definition.
- Human disagreement about novelty is itself high (κ 0.04–0.18, 56% accuracy). So a blind test needs many raters per idea and coarse scales or pairwise comparisons.

### Gaps
- I did not read Amabile's original 1982/1996 reliability coefficients.
- I found no studies validating SemDis or Ocsai specifically on startup and product ideas. All validation is on AUT, DAT and stories.
- The details of "self-enhancement bias" in Zheng et al. did not come up in the search results.
- I found no direct research on LLM judges preferring LLM-style text **specifically in creativity tasks**. There is the general Panickssery result and the low human-LLM agreement in Si et al.

---

## 3. How product and venture practitioners screen ideas (Graham, Thiel, YC, Mom Test, painted door) and what evidence stands behind them

### Takeaway
Practitioner heuristics are almost all **[OPINION]** essays with no controlled validation. They are useful as questions for a filter: does the idea grow from real experience? Is there a small group that wants it badly? Is there a "secret" or a schlep everyone avoids? The only empirical anchor is consumer **purchase intent** as a quality measure (Wharton). Even it measures attractiveness, not novelty, and it can be gamed by the pitch, though one study ruled the pitch out.

### Cited Findings
- [OPINION] Paul Graham, "How to Get Startup Ideas" (**November 2012**):
  - **Organic** ideas grow from the founders' own experience. "Made-up" or "sitcom" ideas are invented to sound plausible, and they are usually bad.
  - "Live in the future, then build what's missing."
  - **Schlep blindness**: valuable ideas hide behind tedious work everyone avoids (Stripe and payments).
  - The **unsexy filter**: dull problems get dismissed.
  - The **well**: "a small number of people want a large amount" beats broad, weak demand.
  - Ideas that look like a "toy" often turn out to matter.
  - Competitors rarely kill startups.

  [paulgraham.com/startupideas.html](https://paulgraham.com/startupideas.html)
- [OPINION] Peter Thiel, *Zero to One* (2014): "What important truth do very few people agree with you on?" It is hard intellectually, because what school teaches is consensus by definition, and psychologically, because the answer has to be unpopular. Weak answers are the familiar ones ("education is broken"). A good one takes the form "most people believe X, but the truth is the opposite of X" — [Farnam Street (Nov 2015)](https://fs.blog/2015/11/the-single-best-interview-question-you-can-ask/); [Farnam Street "End of hubris" (Dec 2015)](https://fs.blog/2015/12/peter-thiel-end-of-hubris/)
- [OPINION] *The Mom Test* (Rob Fitzpatrick, 2013): rules for getting honest feedback. Ask about the person's life and past behaviour (how they solve it now, what they have bought), not their opinion of your idea, because questions about the idea produce polite lies. "It's not their responsibility to tell you the truth" — [Readingraphics summary](https://readingraphics.com/book-summary-the-mom-test/); [Shortform](https://www.shortform.com/blog/the-mom-test-book/); [tldv.io](https://tldv.io/pl/blog/the-mom-test/) (secondary summaries; the exact wording of the three rules was not verified against the book)
- [OPINION] Painted-door and fake-door tests:
  - A painted door runs outside the product (email, banner, landing page). A fake door sits inside the UI.
  - The main critique is that a click measures curiosity, not willingness to pay. The signal grows stronger along "notify me" → email plus qualifying questions → card or pre-order.
  - One rule of thumb treats conversion under ~2% as noise (from a vendor). Cold traffic typically converts at 2–5%.

  [ProdPad](https://www.prodpad.com/blog/painted-door-test/); [causo.ai (2026)](https://hub.causo.ai/guides/fake-door-smoke-testing-validate-demand-2026); [CleverX](https://cleverx.com/blog/pre-launch-demand-testing-with-real-buyers); [Amplitude](https://amplitude.com/explore/experiment/painted-door-testing) (all vendor blogs, no peer-reviewed data)
- [EVIDENCE] Wharton 2023: in purchase-intent ratings from target consumers, GPT-4 ideas averaged ~49% against 40% for MBA students. Of the top-10% ideas, 35 came from AI and 5 from students — [Wharton Mack Institute (2023)](https://mackinstitute.wharton.upenn.edu/2023/new-working-paper-finds-chatgpt-a-better-innovation-ideator-than-mba-students/); [Knowledge at Wharton](https://knowledge.wharton.upenn.edu/article/is-chatgpt-a-better-entrepreneur-than-most/)
- [EVIDENCE] Terwiesch, Meincke, Girotra, Mollick, Nave & Ulrich (arXiv 2607.27553, **30–31 Jul 2026**), 8 studies:
  - LLM ideas are higher in purchase intent and 7× more likely to land in the top 10%.
  - The advantage is **not** explained by more persuasive pitching.
  - LLM ideas are **less novel individually and less diverse as a set**.
  - Newer models are more diverse but still below humans.
  - Pooling across vendors, prompt engineering and "creative agents" bring diversity close to human levels.

  [arXiv 2607.27553](https://arxiv.org/abs/2607.27553)

### Inferences
- Graham, Thiel and Fitzpatrick turn into **checkable questions** for the filter:
  - Is there a specific person or situation from which the idea "grew", or is it a "sitcom idea"?
  - Is there a non-consensus claim of the form "everyone thinks X, but actually not-X"?
  - Is there a schlep that explains why no one has done it yet?
  - Is there a small group that wants it *badly*?

  The evidence behind these is anecdotal (survivorship from YC portfolios). They should be presented as heuristics, not criteria.
- Wharton shows that "attractive to buyers" and "novel" are different axes, and LLMs win on the first while losing on the second. That is exactly the definition of "water": a plausible, attractive, typical idea.

### Gaps
- I found no peer-reviewed study validating painted-door or fake-door tests (false-positive rates).
- I did not fetch YC or Sequoia materials (e.g. the YC "Startup School" idea-evaluation lectures, Sequoia's "Why now?"), so I cannot cite them.
- I found no studies on the predictive power of Graham's or Thiel's heuristics (do ideas that pass them succeed?).
- The "earned secret" term (Ben Horowitz/a16z?) was not checked; I have no source.

---

## 4. Markers of generic / "AI slop" ideas: overused patterns and how to measure cliché

### Takeaway
Strong evidence shows **homogeneity**: LLM ideas resemble one another more than human ideas resemble each other, across models from different vendors, and even when told to "be creative". **I found no catalogued list** of specific product clichés (gamification, community, personalization) in research. Cliché is measured indirectly: embedding similarity within a pool, the "diversity growth rate", and the share of duplicates.

### Cited Findings
- [EVIDENCE] Wenger & Kenett, "We're Different, We're the Same: Creative Homogeneity Across LLMs" (arXiv 2501.19361, **31 Jan 2025**): on standardized creativity tests, "LLM responses are much more similar to other LLM responses than human responses are to each other", even after controlling for response structure. Using LLMs as creative partners can steer users toward a limited set of outputs **regardless of the model** — [arXiv 2501.19361](https://arxiv.org/abs/2501.19361). Secondary summaries say the tasks were AUT, Forward Flow and DAT across 22 models, and that individual models match humans on originality while the population of responses clusters — [alphaXiv](https://www.alphaxiv.org/abs/2501.19361); [EmergentMind](https://www.emergentmind.com/topics/creative-homogeneity-across-llms) (not verified against the text)
- [EVIDENCE] Doshi & Hauser, *Science Advances* 10(28): eadn5290 (**12 Jul 2024**):
  - Access to AI ideas raised the rated creativity, quality and enjoyment of stories, most of all for less creative writers.
  - AI-assisted stories were **more similar to each other**: a "social dilemma" between individual gain and collective loss of novelty.
  - About 500 writers on Prolific; 3,519 ratings of 293 stories by 600 evaluators (Dryad).

  [Dryad dataset](https://datadryad.org/dataset/doi:10.5061/dryad.qfttdz0pm); [Univ. of Exeter news](https://news.exeter.ac.uk/?p=13749); [PsyPost](https://psypost.org/new-study-on-ai-assisted-creativity-reveals-an-interesting-social-dilemma)
- [EVIDENCE] College admissions essays, 2,200 human vs GPT-4 (*Computers in Human Behavior: Artificial Humans*, 2025), 3 preregistered studies. The "diversity growth rate" metric: each added human essay adds more new ideas than each added GPT-4 essay, and the gap widens with N. **Prompt and parameter tweaks did not close it** — [ScienceDirect S294988212500091X](https://www.sciencedirect.com/science/article/pii/S294988212500091X) (snippet)
- [EVIDENCE] Si et al.: 5% unique ideas out of 4,000 — see §2 — [arXiv 2409.04109](https://arxiv.org/html/2409.04109v1)
- [EVIDENCE] Meincke et al.: when the same prompt is repeated, the model "averages" toward the most likely completions, so variety across sessions drops. CoT partly fixes this — [SSRN 4708466 (Feb 2024)](https://papers.ssrn.com/abstract=4708466) (snippet)
- [EVIDENCE] Anderson et al. (2024; cited in a 2025 review): individual ChatGPT users generate more ideas, but at the group level homogenization grows, because the model proposes similar ideas to different people — (snippet from the search result; I did not find a primary link)
- [OPINION] LLMs give generic creative advice because they are trained on "averaged" internet data, so they reach for common patterns and worn clichés — [Moonb blog](https://www.moonb.io/blog/llms-creative-advice)
- [OPINION] A test of AI business-idea generators (ChatGPT, Gemini): the ideas are "niche, trendy", but with gaps — [Startups.co.uk](https://startups.co.uk/news/i-asked-ai-for-business-ideas/)

### Inferences
- The operational "water" marker is not a word list but **membership in the modal cluster**. For a given prompt, generate a baseline pool (e.g. 50–100 ideas from a plain model, or from several models from different vendors, since homogeneity crosses vendors). Any idea of the skill's that lands in the baseline's dense cluster is water. That is measurable and needs no judge.
- A pattern list (gamification, community, personalization, "AI assistant for X", subscription, marketplace, streaks/badges, "Uber/Tinder for X") can be used as a **heuristic stop-list**, but it has to be marked [OPINION/hypothesis]: I found no source that counts these clichés. Better to build it empirically from the baseline pool (the most frequent n-grams and concepts) for each domain.
- Doshi & Hauser warn that raters rate AI-assisted products **higher** individually. A rater test with no diversity measurement will show the skill "wins" even when it homogenizes. Measure both.

### Gaps
- I found no research or practitioner catalogue of specific overused product and startup patterns from LLMs.
- I did not check the CHB:AH study and the Anderson et al. 2024 paper against the primary text.
- arXiv 2603.21228 (essay homogenization) and 2605.06540 ("Ex Ante Evaluation of AI-Induced Idea Diversity Collapse") appeared in the results but I did not read them.

---

## 5. How to design a fair blind test of two idea generators (with vs without the skill, other models)

### Takeaway
The best template is Si et al. (2024): style normalization so judges cannot tell the sources apart, topic matching, blind expert reviewers (2–4 per idea), a 1–10 scale on separate axes, and a test that controls for each reviewer's leniency. Add CAT practice (independent domain experts or quasi-experts, relative judgment) and LLM-judge bias controls (A/B swaps, length matching, no self-judging). Measure two things: idea quality *and* pool diversity.

### Cited Findings
- [EVIDENCE] Si et al. design:
  - 104 participants: 49 idea writers, 79 reviewers, 24 who did both.
  - 3 conditions × 49 ideas: Human / AI / AI + human rerank.
  - 298 unique reviews, 2–4 per idea; 7 topics with topic distributions matched.
  - **Style normalization**: an LLM rewrote every idea into a common format. In a pilot, experts told AI from human at 50% (chance), and the first author checked content was preserved by hand.
  - Three statistical tests: per review, per idea, and per reviewer comparing conditions within each reviewer to remove leniency differences.
  - Novelty was the only consistently significant effect: AI 5.64 vs Human 4.84; Test 3 Δ=0.94, p<0.01. Feasibility did not differ significantly.

  [arXiv 2409.04109 (Sep 2024)](https://arxiv.org/html/2409.04109v1)
- [EVIDENCE] The authors disclosed their own prior expectations (two expected a null result, one expected AI to win). They say human judgments of novelty are hard even for experts, and propose a follow-up in which ideas are carried out as full projects — [Si et al.](https://arxiv.org/html/2409.04109v1); [arXiv abstract](https://arxiv.org/abs/2409.04109)
- [EVIDENCE] CAT: experts are more reliable than novices; quasi-experts are a compromise — [Kaufman & Baer, Rider PDF](https://www.rider.edu/sites/default/files/2024-05/WhoDecidesWhatIsCreative.pdf) (snippet)
- [EVIDENCE] Finer scales lower agreement on novelty (κ 0.18 → 0.04) — [arXiv 2503.04290](https://arxiv.org/pdf/2503.04290) (snippet)
- [EVIDENCE] Swap A/B positions and watch for verbosity and name bias in an LLM judge — [Zheng et al. 2023](https://arxiv.org/abs/2306.05685v1); a judge must not rate its own model (self-preference) — [Panickssery et al. 2024](https://arxiv.org/abs/2404.13076v1)
- [EVIDENCE] Measure collective diversity alongside individual quality, since they can move in opposite directions — [Doshi & Hauser 2024](https://datadryad.org/dataset/doi:10.5061/dryad.qfttdz0pm); [Terwiesch et al. 2026](https://arxiv.org/abs/2607.27553)
- [EVIDENCE] Top-2/Top-k scoring removes the fluency confound — [Benedek et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC4001084) (snippet)
- [EVIDENCE] Wharton's quality measure is purchase intent from a panel of target users (hundreds of students) — [Wharton Mack Institute](https://mackinstitute.wharton.upenn.edu/2023/new-working-paper-finds-chatgpt-a-better-innovation-ideator-than-mba-students/)

### Inferences (a draft protocol; not a source but a synthesis)
1. **Prompts**: ≥20–30 briefs across different domains, fixed before the run. Si et al. had 7 topics × ~7 ideas, which gave significance only on the largest effect (Δ≈0.8–0.9 on a 10-point scale). For a smaller expected effect, more are needed.
2. **Conditions**: plain model / model + skill / another model / (optionally) a human baseline. Each generator produces N ideas and **picks its own Top-k** (k=2–3), which is what gets rated (removes the fluency advantage).
3. **Blinding**: normalize style and length with a separate model into one template (Si et al.), and check in a pilot that raters cannot guess the source (~50%).
4. **Raters**: ≥3 per idea, domain quasi-experts, not novices. Each rates ideas from several conditions, so leniency can be controlled within rater (Si Test 3). Report IRR (ICC or Krippendorff's α). Novelty agreement is expected to be low.
5. **Scales**: separate axes, Novelty / Usefulness-Appropriateness / Surprise / Feasibility / "would you want this" (purchase intent). Either coarse scales or **pairwise comparisons** with randomized order (Bradley–Terry), since finer scales lowered κ.
6. **Pool metrics with no judge**: share of unique clusters at cosine ≥0.8 (Si), mean pairwise distance within the pool (Meincke, Doshi & Hauser), share of ideas falling into the baseline's dense cluster (the "water" index), and the diversity growth rate as N grows.
7. **LLM judge only as a secondary signal**: a judge from a vendor whose models are not in the test, an A/B swap counted as a win only if both orders agree, controlled length, and its agreement with the human raters reported. If it is not above human-human agreement, it is not used.
8. **Pitfalls**:
   - Raters favour AI-assisted text individually (Doshi & Hauser).
   - Overall correlates with excitement, not feasibility (Si), so a "flashy" idea wins.
   - Authors' prior expectations should be disclosed.
   - Novelty ≠ execution success; the ultimate test is implementation or a real demand test.

### Gaps
- I found no formal power analysis for tests of this kind. The numbers of prompts and raters above are inferences, not a sourced norm.
- I did not check the literature on pairwise vs Likert specifically for creativity (e.g. comparative judgment in CAT).
- I did not find ready-made public protocols for "skill vs baseline" for LLM ideators, apart from the designs of Si et al. and the Wharton papers.
