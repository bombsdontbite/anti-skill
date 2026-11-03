# LLMs as creative PROBLEM SOLVERS (non-obvious solutions to a given problem), not idea generators

Scope note: idea generation (homogeneity, verbalized sampling, divergent-thinking tests, ideation–execution gap) is covered by a sibling pass and deliberately not repeated. Everything below is about solving a stated problem under constraints. Research done 2026-10-26; ~19 tool calls. "Verified" = the figure was read from the primary source page (arXiv abstract/HTML or the official blog) in this session. "UNVERIFIED" = from memory or a secondary summary, not read from the primary source in this session.

## 1. Benchmarks of creative problem solving: what they found, how LLMs fail, how they compare to humans

### Takeaway
On every benchmark that isolates "non-obvious solution under constraints" (MacGyver, Only Connect Wall, NeoCoder, CreativityBench, BRAINTEASER), frontier LLMs of their time are at or below average humans and well below the best humans. The failure is not lack of ideas: models propose a broad range of unconventional moves but many are physically infeasible, violate stated constraints, or follow a surface-level red herring. Creativity in solving = novelty × feasibility, and models lose mostly on the feasibility/constraint side.

### Cited Findings

**MacGyver** (Tian, Ravichander, Qin, Le Bras, Marjieh, Peng, Choi, Griffiths, Brahman; NAACL 2024; arXiv v4 Feb 2025) — verbal "make do with these objects" problems built to probe functional fixedness.
- 1,683 problems: 1,306 solvable (77.6%), 377 unsolvable (22.4%); 82.2% of the solvable ones need unconventional tool use. — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- Single-effort accuracy on 323 problems (efficient + less efficient + correctly flagged unsolvable): GPT-4 62.4% vs. random human 65.1%; Claude 2 52.7%; GPT-3.5 40.6%; PaLM2 40.6%; Llama2-70b 41.2%. — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- Best-of-several: best GPT-4 92.3% vs. best human 98.8%; best human gives an "efficient" solution 72.8% vs. GPT-4 62.5%. Majority vote: humans 79.3% vs. GPT-4 73.3%. — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- Models are bad at saying "this cannot be solved": GPT-4 flags unsolvable problems 2.1% (random) vs. human 9.9%; PaLM2 0.0%. — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- Qualitative contrast: humans do well on familiar tasks but lack domain knowledge and vary more; LLMs attempt more of the problems, drawing on wider specialised knowledge, but often propose "physically-infeasible actions". — [arXiv abstract](https://arxiv.org/abs/2311.09682)
- GPT-4 zero-shot on all 1,306 solvable problems: only 18.9% efficient solutions, 37.5% infeasible. — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- Error breakdown of 200 infeasible GPT-4 solutions: wrong tool usage 42.4%, goal not reached 17.7%, uses unavailable tools 16.9%, wrong spatial understanding 10.8%, unfaithful to constraints 9.5% (hallucination combined 26.4%). — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- **Asking for more solutions degrades them:** over three iterations of new GPT-4 solutions, feasible + efficient fell 39.1% → 34.7% → 25.4% and infeasible rose 24.0% → 31.7% → 35.7% (200 problems). — [arXiv HTML](https://arxiv.org/html/2311.09682v4)
- Human side: 252 UK Prolific solvers (about six responses per problem) and 160 MTurk verifiers. Note: the source is internally inconsistent; the text says most LLMs score "35–42%" while Claude 2 is 52.7% in Table 5, and the caption says "out of 4" while the text says six responses. — [arXiv HTML](https://arxiv.org/html/2311.09682v4)

**Only Connect Wall (OCW)** (Naeini et al.; NeurIPS 2023 Datasets & Benchmarks per [mlanthology](https://mlanthology.org/neurips/2023/naeini2023neurips-large); arXiv preprint 2306.11167) — group 16 clues into 4 hidden connections; deliberate red herrings (an analogue of the Remote Associates Test); an explicit test of Einstellung and fixation.
- 618 walls; 494-wall test set. GPT-4 (best, 5-shot) solved 7 of 494 walls (~1%) vs. humans 285 of 494 (~58%); correct groups 272 of 1,976 (~14%) vs. humans 1,405 (~71%). — [ar5iv](https://ar5iv.labs.arxiv.org/html/2306.11167)
- Naming the connection: exact match under 15% for GPT-4 and GPT-3.5 vs. human ~80%. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2306.11167)
- **Causal red-herring test:** diluting red herrings (OCW-Randomized) raised GPT-4 from 7 to 68 walls (~10×) and from 269 to 655 groups; removing them entirely (OCW-WordNet) gave 471 walls and 1,926 of 1,976 groups (~97%). The difficulty is the misleading surface associations, not the vocabulary. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2306.11167)
- More in-context examples did not reliably help: GPT-4 peaked at 3–5 shots and dropped at 10 shots (249 groups). — [ar5iv](https://ar5iv.labs.arxiv.org/html/2306.11167)

**NeoCoder + denial prompting** (Lu, Wang, Li, Jiang, Khudanpur, Jiang, Khashabi; NAACL 2025; arXiv 2407.09007v2)
- Method: solve a Codeforces problem → list the techniques used (for-loop, recursion, …) → randomly ban one unused-so-far technique → re-solve; up to 5 rounds. Dataset: 199 Codeforces problems at difficulty 800, 30 human solutions each (~5.9K). — [arXiv HTML](https://arxiv.org/html/2407.09007v2)
- NeoGauge = convergent (correct AND constraint-following) × divergent (uses techniques no human solution used). — [arXiv abstract](https://arxiv.org/abs/2407.09007)
- GPT-4 across denial states 0→5: pass@1 16.1 → 2.1; constraint following 100 → 14.4; convergent 16.2 → 0.0; divergent 4.5 → 15.3; NeoGauge peaks at state 1 (1.4) and hits 0 by state 4. **Banning techniques raises novelty, but correctness and constraint compliance collapse after 1–2 bans.** — [arXiv HTML](https://arxiv.org/html/2407.09007v2)
- With no constraints, models default to common techniques (for-loops), as humans do. Under heavy constraints they make mistakes or copy previous solutions; Llama2-70B asks the user for hints. — [arXiv HTML](https://arxiv.org/html/2407.09007v2)
- GPT-4 is most creative overall; Claude-3 and Llama3-70B match it at state 0 but fall to near zero within two states. LLM divergent creativity is only minimally above the lowest human level, and humans have clearly higher convergent creativity before state 3. Authors: LLMs "barely exhibit human-like creativity". — [arXiv HTML](https://arxiv.org/html/2407.09007v2)

**CreativeMath** (Ye, Gu, Zhao, Yin, Wang; arXiv preprint 2410.18336, Oct 2024; no venue stated) — given k known solutions to a competition math problem, produce a correct, different one.
- 6,469 problems and 14,223 solutions (AMC 8 through IMO); evaluated subset of 400 problems; three LLM judges (GPT-4, Claude 3.5 Sonnet, Gemini 1.5 Pro). — [arXiv HTML](https://arxiv.org/html/2410.18336v1)
- Novelty ratio (share of all outputs that are correct and novel): Gemini-1.5-Pro 66.9%, Llama-3-70B 48.8%, Claude-3-Opus 44.6%, GPT-4o 30.1%, math-specialised 7B–20B models ~12%. — [arXiv HTML](https://arxiv.org/html/2410.18336v1)
- **Showing more reference solutions raises correctness but makes novel solutions harder**: an explicit exploit/explore trade-off. — [arXiv HTML](https://arxiv.org/html/2410.18336v1)
- As difficulty rises, correctness falls (~71.8% AMC 8 → ~35% USAMO/IMO) but the share of correct solutions that are novel rises (~55% → ~83%). ~95% of novel solutions were also distinct from all held-out human solutions ("Novel-Unknown"). — [arXiv HTML](https://arxiv.org/html/2410.18336v1)
- Caveat: novelty is LLM-judged, not human-judged.

**CreativityBench** (Qian, Ha, …, Heng Ji; UIUC / Amazon / Columbia; arXiv preprint 2605.02910v2, May 2026) — tool repurposing grounded in part-level affordances.
- ~14K tasks from a knowledge base of ~4K entities, 26K parts and ~157K affordances; 10 models. — [arXiv HTML](https://arxiv.org/html/2605.02910v2)
- Models pick a plausible object (entity-correct 0.515 on average) but rarely the right part (gold-correct 0.191). Action feasibility is rated 3.59 vs. physical grounding 3.20 (1–5): solutions sound plausible without a physical justification. GPT-5.2 gold-correct 0.182; best Qwen3-32B 0.259. — [arXiv HTML](https://arxiv.org/html/2605.02910v2)
- Failure modes: physical invalidity dominates; over-attributing affordances; ignoring recipient constraints; long-tail affordances harder; **in interactive mode models inspect few entities and commit early to wrong hypotheses** (Qwen3-32B 0.25 → 0.07). — [arXiv HTML](https://arxiv.org/html/2605.02910v2)
- Human comparison not read (outside the fetched part of the page).

**BRAINTEASER** (Jiang et al.; arXiv 2310.05057; EMNLP 2023 per the request; the arXiv page lists no venue) — 1,100 multiple-choice lateral-thinking puzzles (sentence and word types) with semantic and context reconstructions.
- "Significant gap between human and model performance", widening when consistency across the adversarial reconstructions is required. — [arXiv abstract](https://arxiv.org/abs/2310.05057)
- UNVERIFIED (memory, not read from the source): human ~92% vs. ChatGPT ~60% on sentence puzzles; models are much worse on word puzzles; consistency across reconstructions is far lower than single-item accuracy.

### Inferences
- The cross-benchmark pattern is "breadth without grounding". LLMs reach for unconventional moves readily (MacGyver: they attempt more problems; CreativeMath: they produce novel proofs) but fail on feasibility, constraint fidelity and recognising "no solution". A skill for solution creativity should therefore spend its effort on constraint checking and feasibility, not on "be more creative" prompting.
- Fixation in LLMs is mostly to **surface cues in the problem statement** (OCW red herrings) and to **the most common technique** (NeoCoder state 0), and the second is breakable by explicit bans.
- Novelty and correctness trade off under forced novelty: NeoCoder's best point is one ban, and in CreativeMath more references mean more correctness and less novelty. A practical rule: one or two forced departures from the default, each followed by a strict feasibility check.

### Gaps
- No primary-source numbers for the BRAINTEASER human–model gap were read in this session.
- The CreativityBench human baseline was not read.
- No benchmark found that measures solution creativity in product, marketing or operations problems; all of them are physical, coding, math or word-association tasks.
- Results are for 2023–2024 models (GPT-4, Claude 2/3) except CreativityBench (2026, GPT-5.2). I found no published re-runs of MacGyver, OCW or NeoCoder on 2025–2026 reasoning models.

## 2. Functional fixedness, Einstellung and fixation in LLMs: evidence and techniques that break it

### Takeaway
There is causal evidence that LLMs are fixated by misleading cues (OCW: removing red herrings lifts GPT-4 from ~1% to ~95% of walls solved) and default to the most familiar technique (NeoCoder). The tested fixation breakers are explicit bans on the previous approach (denial prompting), divergent-then-convergent prompting, and problem abstraction (step-back). Each buys some novelty or accuracy at a cost, and none removes the fixation.

### Cited Findings
- Red herrings cause fixation: performance jumps once misleading groupings are diluted or removed (7 → 68 → 471 walls solved). — [ar5iv OCW](https://ar5iv.labs.arxiv.org/html/2306.11167)
- Default-technique fixation: unconstrained models use common techniques; bans push them to rarer ones, raising divergent creativity 4.5 → 15.3 for GPT-4. — [NeoCoder HTML](https://arxiv.org/html/2407.09007v2)
- Early commitment: agents in interactive CreativityBench "inspect few entities and commit early to wrong hypotheses", and performance falls sharply versus a static presentation. — [CreativityBench](https://arxiv.org/html/2605.02910v2)
- Anchoring on given solutions: in CreativeMath, more reference solutions in context make novel solutions harder to produce. — [CreativeMath HTML](https://arxiv.org/html/2410.18336v1)
- **Divergent-Convergent Thinking prompt** (generate several candidate uses or approaches, then select and verify): for GPT-4 it cut infeasible solutions by 4.3% and raised efficient ones by 6.5% (180 problems). It helped Claude 2 and Llama2-13b on all dimensions. — [MacGyver HTML](https://arxiv.org/html/2311.09682v4)
- **Iterative Step-Wise Reflection** (check each step's feasibility): cut GPT-4's infeasible solutions by 9.7%; plain "Self-Reflect" gave only +2.2% efficiency and did not help Claude 2 or Llama2-13b. Baselines for these deltas are not stated in the text. — [MacGyver HTML](https://arxiv.org/html/2311.09682v4)
- **Step-back prompting** (first abstract to the governing principle, then solve), PaLM-2L, ICLR 2024: MMLU Physics +7%, Chemistry +11%, TimeQA +27%, MuSiQue +7%. These are accuracy gains, not novelty. — [arXiv 2310.06117](https://arxiv.org/abs/2310.06117)
- A related human-side paper is about users, not models: "Trapped by Expectations: Functional Fixedness in LLM-Enabled Chat Search" (arXiv 2504.02074, 450 participants) found that users' prior expectations constrain how they prompt. — [arXiv 2504.02074](https://arxiv.org/abs/2504.02074)

### Inferences
- Fixation breakers that work have a common shape: **name the default explicitly, then forbid or abstract it**. Denial prompting forbids the used technique; step-back replaces surface features with principles; red-herring removal shows the surface cue is the trap. A skill can do this as: "state the obvious solution → name the assumption or technique it rests on → ban it → re-solve → check constraints".
- Since bans erode constraint following quickly (100% → 46% after two bans for GPT-4), every forced departure needs a re-check against the original constraints.
- Hiding known solutions (CreativeMath) is a cheap novelty lever. Do not paste "how others did it" before the model drafts its own attempt; show prior art afterwards as a novelty filter. (My inference from the k-trade-off; not tested in this form.)

### Gaps
- I found no dedicated 2025–2026 Einstellung study on reasoning models (o-series, Claude thinking) beyond CreativityBench's early-commitment observation.
- I found no direct test of "inversion" or "constraint relaxation" prompts measured on solution novelty.

## 3. Search-based systems that found genuinely new solutions: what made them work, and what transfers without a verifier

### Takeaway
Every verified "genuinely new" LLM-made solution (FunSearch cap sets and bin packing, AlphaEvolve's 4×4 complex matrix multiplication in 48 multiplications, Google scheduling and kernels) came from the same loop: an LLM proposes **programs**, an **automatic evaluator** scores them, the best are fed back as context, and the population evolves over many candidates. The evaluator is the stated main limitation. In fuzzy domains the closest analogue is an LLM-judged tournament (Google's AI co-scientist), whose novelty evidence is thin and self-rated.

### Cited Findings
- **FunSearch** (Romera-Paredes et al., Nature, Dec 2023): a pre-trained LLM (PaLM 2) proposes code, and an automated evaluator "screens out hallucinated or incorrect ideas"; the best programs are fed back each cycle. The user supplies a problem description in code with an evaluation function and a seed program. — [DeepMind blog](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/); [Nature](https://www.nature.com/articles/s41586-023-06924-6)
- FunSearch results: the largest cap sets found in some settings ("largest increase" in 20 years), beating state-of-the-art solvers; bin-packing heuristics that use fewer bins than human-designed ones. Searching over programs gives interpretable, concise outputs whose inspection revealed symmetries that refined the problem. A Dec 2024 follow-up with Gemini 1.5 Flash beat top-percentile human competitors on combinatorial competitive-programming tasks. — [DeepMind blog](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/)
- UNVERIFIED (memory): FunSearch used an island-based evolutionary database and "best-shot" prompting (k=2 prior programs sorted by score), sampling on the order of millions of programs per run.
- **AlphaEvolve** (Novikov … Balog, Google DeepMind; arXiv preprint 2506.13131, June 2025): an evolutionary coding agent in which LLMs edit code under evaluator feedback; 4×4 complex matrices in 48 scalar multiplications, the first improvement over Strassen in 56 years in that setting. — [arXiv abstract](https://arxiv.org/abs/2506.13131)
- AlphaEvolve on 50+ open math problems: matched the best known constructions in ~75% and surpassed them in ~20%. Recovered 0.7% of Google fleet-wide stranded compute on average; 23% average kernel speedup; ~1% less Gemini training time. — [arXiv HTML](https://arxiv.org/html/2506.13131v1)
- AlphaEvolve ablations: removing evolution, removing problem context from prompts, removing meta-prompt evolution, evolving only the loss rather than the full file, and using a single small LLM instead of a small+large mix each cost "a significant improvement". No numbers are given in the text read. — [arXiv HTML](https://arxiv.org/html/2506.13131v1)
- AlphaEvolve's stated main limitation: it needs automatically scorable problems. Where no automated evaluator exists, the problem is out of scope; LLM-provided evaluation is possible but was not the focus. — [arXiv HTML](https://arxiv.org/html/2506.13131v1)
- UNVERIFIED (memory, not fetched): **AlphaDev** (Mankowitz et al., Nature 2023) used RL over assembly with a correctness and latency verifier and found sorting routines for short sequences (reported up to ~70% faster for very short sequences) that were merged into LLVM libc++.
- **Fuzzy-domain analogue: Google AI co-scientist** (Feb 2025, Gemini 2.0, multi-agent; arXiv "Towards an AI co-scientist", preprint). Generation, Reflection (simulated peer review for correctness, quality, originality), Ranking (pairwise-debate Elo tournament) and Proximity (clustering duplicates) agents. The auto-Elo improves with test-time compute. Experts judged novelty and impact on only 11 research goals, and Google says "the sample size was small"; expert preference agreed with the auto-Elo. There were wet-lab validations in three biomedical applications. — [Google Research blog](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) (summarised via search results; the Elo is self-rated, and I found no independent replication)

### Inferences
- Ingredients that made search work: (a) a cheap automatic scorer that rejects hallucinations; (b) many candidates (thousands to millions); (c) selection with the best candidates fed back as context, not just resampling; (d) diversity maintenance (islands or clustering); (e) program-level or structured outputs that can be inspected; (f) mixing models (cheap and wide plus strong and deep).
- What transfers to product, marketing and ops without a verifier: (1) **construct a partial verifier** — hard constraints as a checklist, cost and feasibility estimates, "would this survive the stated constraints" tests; (2) **pairwise tournament judging** instead of absolute scoring (co-scientist Elo), with a separate critic; (3) **de-duplication / clustering** to keep the pool diverse; (4) **feed the top candidates back** for recombination and mutation rather than asking for "more ideas" (MacGyver shows plain iteration degrades feasibility). Without a real verifier, the known risk is that judge and generator share the same biases, so a self-rated Elo can drift toward what the model likes. This is my inference, consistent with Google calling the Elo self-rated.
- The fuzzy-domain step that most reliably raises the hit rate is turning the brief into an **explicit scoring rubric before generating**: the evaluator-first discipline of FunSearch, where the user writes the evaluation function first.

### Gaps
- I found no controlled study showing that LLM-judge evolutionary loops produce human-validated novel solutions in business domains.
- AlphaEvolve's ablation magnitudes are not in the text read (they are in figures). The FunSearch candidate counts were not verified.
- Open-source re-implementations (OpenEvolve, Sakana ShinkaEvolve) were not researched in this pass.

## 4. Prompting and agent techniques tested on problem solving: measured gains on novelty, not just accuracy

### Takeaway
Almost all the classic techniques (tree-of-thoughts, self-consistency, Reflexion, debate, analogical prompting, step-back) were evaluated on **accuracy**, not on originality of the solution. The only direct novelty measurements found are NeoCoder (MCTS, self-correction, planning, sampling) and MacGyver (divergent-convergent, step-wise reflection). There, **no strategy improved novelty and correctness together; only MCTS-style search consistently raised divergent creativity.**

### Cited Findings
- NeoCoder, change in creativity scores vs. baseline:
  - MCTS (CodeGemma-7B): divergent up at every state (+7.79 at state 0), but NeoGauge gains vanish after state 2;
  - self-correction (GPT-3.5): convergent +12.12 at state 0, divergent −1.62 at state 3;
  - planning: convergent +7.07, divergent −1.16 and −1.24;
  - sampling: divergent −0.38, −1.69 and −1.86, convergent −0.50.
  - Conclusion: "no strategy improves both". The text and Table 5 disagree on the sampling figure. — [NeoCoder HTML](https://arxiv.org/html/2407.09007v2); abstract: "advanced reasoning strategies (MCTS, self-correction, etc.)" produced no significant improvement in creativity — [arXiv abstract](https://arxiv.org/abs/2407.09007)
- **Analogical prompting** (Yasunaga et al., ICLR 2024; the model generates 3–5 relevant solved problems and knowledge, then solves) — accuracy only:
  - GSM8K (GPT-3.5): 75.0 (0-shot) / 75.8 (0-shot CoT) / 76.7 (5-shot CoT) / 77.8 (analogical);
  - MATH (GPT-3.5): 33.0 / 33.9 / 34.9 / 37.3;
  - Codeforces (GPT-4) Acc@1/@10: 16/30 (0-shot) vs. 19/37 (knowledge + exemplars), 17/31 (3-shot CoT).
  - Best at K=3–5; better suited to larger LLMs; prompt-sensitive.
  - Of 50 failures: 10 had irrelevant exemplars, 12 had wrong exemplars, and 8 over-relied on a specific exemplar. — [arXiv HTML](https://arxiv.org/html/2310.01714v3); [abstract](https://arxiv.org/abs/2310.01714)
- **Step-back** (ICLR 2024): +7 to +27 points of accuracy on knowledge and reasoning tasks (see §2). — [arXiv](https://arxiv.org/abs/2310.06117)
- **Divergent-convergent and step-wise reflection** on MacGyver: modest feasibility gains (−4.3% and −9.7% infeasible), +6.5% efficient. — [MacGyver HTML](https://arxiv.org/html/2311.09682v4)
- **Multi-agent debate** (Smit et al., ICML 2024, "Should we be going MAD?"): MAD "does not reliably outperform" self-consistency or ensembling. It is hyperparameter-sensitive (tuning agreement levels moved one protocol from worst to best) and costs more calls. — [PMLR](https://proceedings.mlr.press/v235/smit24a.html); [arXiv](https://arxiv.org/pdf/2311.17371). Later work notes agents are easily swayed by peers with wrong conclusions, and that MAD can degrade accuracy. — [iMAD arXiv 2511.11306](https://arxiv.org/pdf/2511.11306); [TACL 2026 (DReaMAD)](https://aclanthology.org/2026.tacl-1.58.pdf) (search-snippet level)
- UNVERIFIED (memory): Tree of Thoughts (Yao et al., NeurIPS 2023), Game of 24 success 4% with CoT vs. 74% with ToT (GPT-4). This is accuracy on a search puzzle; there is no novelty measure.
- UNVERIFIED (memory): Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet" (ICLR 2024). Intrinsic self-correction without external feedback does not improve, and can hurt, reasoning accuracy; reported gains depended on oracle feedback. Cited only as a reference in search results — [Smit et al. context / search](https://iclr.cc/media/iclr-2025/Slides/28079.pdf).

### Inferences
- Techniques that add **search with an external signal** (MCTS against tests, FunSearch or AlphaEvolve against evaluators) raise novelty. Techniques that add **more of the model's own judgement** (self-correction, planning, debate) mostly raise convergence toward the conventional answer and can lower divergence. This fits a picture in which the model's self-critique pulls toward its prior, the "most typical correct" solution.
- Analogical prompting's mechanism (self-generated analogues) is the most promising transferable lever for non-obvious solutions, because it can be steered toward **distant-domain** analogues ("how would a logistics company, an immune system or a casino solve this?"). But it has only been measured for accuracy on near-domain exemplars, and over-reliance on one exemplar is a recorded failure mode.

### Gaps
- I found no study measuring self-consistency, Reflexion or ToT on solution originality.
- I found no controlled test of "inversion" (solve the opposite problem), "constraint relaxation" (drop a constraint, then re-add it) or "problem reformulation" prompts with a novelty metric. They are widely recommended in practitioner guides but untested in the literature found.
- I found no test of distant-domain analogical prompting for novelty.

## 5. What does NOT help (measured)

### Takeaway
Measured non-helpers for solution creativity: more sampling or temperature, plain chain-of-thought, generic self-reflection, planning, multi-agent debate (vs. cheaper ensembles), more in-context examples, more prior solutions in context, model scaling beyond mid-size, and simply asking for further solutions.

### Cited Findings
- More sampling: divergent creativity fell (−0.38 to −1.86). — [NeoCoder HTML](https://arxiv.org/html/2407.09007v2)
- Higher temperature: no reliable gain; more hallucinated entities and parts, especially in small models. — [CreativityBench](https://arxiv.org/html/2605.02910v2)
- Chain-of-thought: −0.012 to +0.039 on tool usage; it improves procedural grounding, not creative reasoning. — [CreativityBench](https://arxiv.org/html/2605.02910v2)
- Self-correction and planning: they raise convergent and lower divergent creativity. — [NeoCoder HTML](https://arxiv.org/html/2407.09007v2). Generic Self-Reflect: +2.2% efficiency for GPT-4 and no help for Claude 2 or Llama2-13b. — [MacGyver HTML](https://arxiv.org/html/2311.09682v4)
- Iteratively asking for new solutions: feasibility falls each round (39.1% → 25.4% feasible and efficient). — [MacGyver HTML](https://arxiv.org/html/2311.09682v4)
- Too many forced bans: constraint following 100% → 14.4%, and models copy earlier solutions. — [NeoCoder HTML](https://arxiv.org/html/2407.09007v2)
- More few-shot examples on OCW: performance drops at 10 shots. — [ar5iv OCW](https://ar5iv.labs.arxiv.org/html/2306.11167)
- More reference solutions: novelty falls. — [CreativeMath](https://arxiv.org/html/2410.18336v1)
- Scaling: Qwen gains ~30% from 4B to 14B but under 5% from 14B to 32B, and GPT-5.2 is not best. — [CreativityBench](https://arxiv.org/html/2605.02910v2)
- Multi-agent debate vs. self-consistency or ensembling: not reliably better, and costlier. — [PMLR](https://proceedings.mlr.press/v235/smit24a.html)
- Interactive or agentic exploration without guidance: early commitment, large drop (0.25 → 0.07). — [CreativityBench](https://arxiv.org/html/2605.02910v2)

### Inferences
- For a "creativity in solutions" skill, the evidence argues against "brainstorm harder" loops, high temperature, or a debate panel as the core mechanism. It argues for: explicit naming and banning of the default (1–2 bans, not 5); divergent-then-convergent with a **hard feasibility and constraint gate**; abstraction (step-back) and distant analogues; withholding known solutions until a first draft exists; pairwise ranking plus de-duplication against a rubric written before generation; and, where any part of the problem can be scored objectively (cost model, simulation, test, A/B proxy), an evaluator-driven loop in the FunSearch/AlphaEvolve style.
- Also build in an explicit "is it solvable as stated / which constraint must give?" check, since models almost never flag unsolvable problems (GPT-4 2.1% in MacGyver).

### Gaps
- All "does not help" findings come from coding, physical or puzzle tasks with older models. Whether 2025–2026 reasoning models change the self-correction or sampling picture for solution novelty is untested in the sources found.
