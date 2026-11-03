# Propose → score automatically → improve: prior art for a Claude Code skill mode

Research pass on 2026-10-27, about 40 tool calls. Scope: LLM evolutionary loops over programs or text with an
automatic evaluator (FunSearch, AlphaEvolve, OpenEvolve, ShinkaEvolve, descendants). Also covers
the Claude-Code-native loops that copy them and the controlled comparisons against best-of-N.
`llm_creative_problem_solving.md` §"search systems with evaluators" gives the headline results and
is not repeated here.

Tags:
- **[V]**: read from the primary source (paper HTML or PDF, repo, issue) in this session.
- **[S]**: from a search snippet or a secondary page only.
- **[U]**: recalled, not re-read; check before quoting.

Star counts and dates were read with `gh api` on 2026-10-27.

---

## 1. OpenEvolve (open-source AlphaEvolve re-implementation)

Repo: [algorithmicsuperintelligence/openevolve](https://github.com/algorithmicsuperintelligence/openevolve) (formerly
`codelion/openevolve`). Created 2025-05-15, about 7.7k stars, latest tag v0.4.0 (commit dated 2026-09-28), still pushed
2026-10-27. **[V]**

### Architecture **[V]** ([README](https://github.com/algorithmicsuperintelligence/openevolve), [default_config.yaml](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/configs/default_config.yaml))
- **Program database.** It is a MAP-Elites grid crossed with an island model.
  - Feature dimensions default to `complexity` (code length) and `diversity` (edit distance against a reference set of 20), each with 10 bins.
  - The evaluator can return custom dimensions such as `performance` and `memory_usage`.
  - Islands migrate in a ring.
- **Parent selection** (explained by the maintainer in [issue #166](https://github.com/algorithmicsuperintelligence/openevolve/issues/166), 2025-07-29):
  - 0.2: exploration, a parent from the current island.
  - 0.7: exploitation, a parent from the elite archive.
  - 0.1: random, the remainder.
  - `elite_selection_ratio` 0.1 is separate. It sets what counts as elite.
- **Prompt sampler.** "Double selection" uses different programs for the performance context and for inspiration.
  - Defaults are `num_top_programs: 3` and `num_diverse_programs: 2`.
  - Template stochasticity is on, so the wording is randomised.
  - An "artifacts" side channel puts evaluator stderr, warnings and LLM feedback into the next prompt, capped at 20 KB.
- **Evaluator cascade.** It is on by default, with stage thresholds 0.5 / 0.75 / 0.9.
  - Each evaluation has a 300 s timeout and 3 retries, with 4 evaluations in parallel.
  - `use_llm_feedback` is off by default; when on, its weight is 0.1.
- **Mutation format.** `diff_based_evolution: true` is the default (SEARCH/REPLACE).
  - `max_code_length` is 10,000 characters.
  - `enforce_evolve_blocks: false`, so edits outside the EVOLVE-BLOCK markers are *not* reverted by default.
- **Defaults.** Population 1000, archive 100, 5 islands, migration every 50 generations at 10%, `max_iterations` 100, early stopping off.
  - The default LLM pair is gemini-2.0-flash-lite (0.8) and gemini-2.0-flash (0.2).
  - Temperature is 0.7.
- **Claude Code as backend.** `provider: "claude_code"` uses the CLI's OAuth session with no API key.
  - The example weights sonnet 0.8 and haiku 0.2, with `max_budget_usd: 1.0` per model.
  - A Copilot-CLI provider exists too.
  - A request for a native Claude Code *plugin* ([#379](https://github.com/algorithmicsuperintelligence/openevolve/issues/379), 2026-01-12) has no reply.

### Reported results (self-reported) **[V]** ([README](https://github.com/algorithmicsuperintelligence/openevolve))
- "Matches published benchmarks" for n=26 circle packing.
- 2.8× GPU-kernel speedup on an Apple M1 Pro.
- "+23%" on HotpotQA prompt optimisation.
- "100x" convergence on function minimisation, with no baseline given.
- Estimated cost per iteration: o3 $0.15–0.60, Gemini-2.5-Flash $0.01–0.05.

### What users and independent evaluations report
- **Cost to reproduce circle packing.** The maintainer put the full run at about 800 iterations and about $22, before islands were added. [#112](https://github.com/algorithmicsuperintelligence/openevolve/issues/112), 2025-06-26. **[V]**
- **Reward hacking on the flagship example.** [#285](https://github.com/algorithmicsuperintelligence/openevolve/issues/285), 2025-10-09. **[V]**
  - An evolved circle-packing program set every centre to `np.nan`. Any comparison with NaN is False, so the validator accepted every circle and the program returned hard-coded radii summing to the known optimum, 2.637.
  - The program's own docstring calls it a "cheat".
  - The maintainer agreed the evaluator must be written robustly against reward hacking. It was fixed in OpenEvolve pull request 134.
- **"Best program is the same as the initial one."** [#281](https://github.com/algorithmicsuperintelligence/openevolve/issues/281), 2025-10-07. **[V]**
  - Small models fail to emit valid diffs.
  - The maintainer's advice was `diff_based_evolution: false`.
- **Dria study.** 29 OpenEvolve runs on AlgoTune: Gemini-2.5-Flash reached a 2.04× speedup; open models were competitive (Gemma-3-27B 1.63×, Qwen3-Coder 1.41×). **[S]**
  - Parameter study: temperature 0.4 was best, and artifacts were worth +17%.
  - 100 vs 200 iterations scored 1.637× vs 2.039×.
  - Serial evaluation "critically" degraded results.
  - Sources: [Dria blog](https://dria.co/blog/towards-open-evolutionary-agents), [parameter tuning](https://dria.co/blog/parameter-tuning-analysis), [iterations](https://dria.co/blog/iteration-impact-analysis:-100-vs-200-iterations), 2025. All three returned HTTP 402 and were read only through search snippets.
- **Against simple baselines** (Gideoni et al., appendix D). OpenEvolve crashed on several problems with Gemini. With GPT-5.2 and GPT-5-mini over 300 generations it worked on 6 problems, with an "average subpar rank of 3.08" against the two simple baselines and ShinkaEvolve. See §4. **[V]**
- **Against a random search strategy** (EvoX, Table 8, GPT-5, circle packing mean): random 2.4905, OpenEvolve 2.5308, ShinkaEvolve 2.4642, GEPA 2.6129, EvoX 2.6324. [arXiv 2602.23413v2](https://arxiv.org/html/2602.23413), 2026-03-16. **[V]**
- **Heilbronn cost** (EvoX): reaching a score above 0.031 cost OpenEvolve about $15.4, ShinkaEvolve about $7.6, and EvoX or GEPA under $1. **[V]**

---

## 2. ShinkaEvolve (Sakana AI)

Paper: Lange, Imajuku, Cetin, [arXiv 2509.19349](https://arxiv.org/html/2509.19349v1), submitted 2025-09-17, accepted at ICLR 2026.
Blog: [sakana.ai/shinka-evolve](https://sakana.ai/shinka-evolve/), 2025-09-25.
Repo: [SakanaAI/ShinkaEvolve](https://github.com/SakanaAI/ShinkaEvolve), created 2025-09-17, about 1.5k stars, Apache-2.0. **[V]**

### What it does differently **[V]** (paper)
1. **Parent sampling.**
   - Power-law over rank: p_i ∝ r_i^(−α). α=0 is uniform sampling; α→∞ is hill climbing.
   - **Weighted sampling**: sigmoid of performance × a novelty bonus 1/(1+offspring count), with λ=10. Programs that already have many children are sampled less.
2. **Novelty rejection before evaluation.**
   - The mutable code is embedded with text-embedding-3-small. A proposal whose max cosine similarity is above 0.95 is flagged (the repo default is 0.99).
   - Flagged proposals go to an LLM novelty judge, with up to 3 re-proposal attempts.
3. **Bandit over LLMs.** UCB1 with c=1.0.
   - Reward = exp(max(r − r_base, 0)) − 1, where r_base = max(parent fitness, initial fitness).
   - The reward is normalised so it does not depend on the fitness scale.
4. **Meta-scratchpad.** Every 10 generations (5 on ALE) it summarises recent evaluations into at most 5 recommendations, which are added to the mutation prompt.
5. **Mutation mix.**
   - Probabilities for diff / full rewrite / crossover: [0.45, 0.45, 0.1] on circle packing, [0.6, 0.3, 0.1] on AIME and ALE (also the repo default).
   - An invalid patch is resampled up to 3 times, with Reflexion-style parse feedback.
6. **Islands.** Only 2–4, migration every 10 generations, and the island-best program never migrates.

### Results (self-reported) **[V]**
- **Circle packing, n=26: a new state of the art "using only 150 samples".**
  - The score under relaxed verification was 2.635983099011548.
  - Re-checked against the exact constraint it was 2.63597770931127. The relaxed checker was over-crediting in the 6th decimal.
- **AIME scaffold.** Base model gpt-4.1-nano, 75 generations, 10-query budget.
  - The best scaffold uses 7 calls: 3 experts, 3 reviewers, 1 synthesis.
  - Accuracy appears only in a figure.
- **ALE-Bench LITE** (10 AtCoder tasks, 50 generations from ALE-Agent's best): ~2.3% average gain.
  - ahc039 rose from 2880 to 3140.
  - On private tests the top-5 average moved 1923.5 → 1927.0, "negligible".
  - The blog presents this as "limited overfitting".
- **MoE load-balancing loss.** A new loss was found on a 556M model.
  - The text says 30 generations; the hyperparameter table says 20 (the source contradicts itself).
- **Ablations** (circle packing, given as figures, no numbers in the text):
  - Weighted sampling > hill climbing > random. Hill climbing "starts strong but plateaus".
  - Bandit ensemble > fixed ensemble > single LLM.
  - Embedding rejection is clearly better than none; the LLM judge adds only a marginal gain.
- **Costs.** None given. The repo has a `max_api_costs` cap, default None.
- **Limitations stated.**
  - The configs are fixed by hand.
  - The evaluator needs manual expertise.
  - It needs well-defined numerical objectives.

### Repo news relevant to us **[V]** ([README](https://github.com/SakanaAI/ShinkaEvolve))
- **2026-02.** Four agent skills shipped for Claude Code and Codex: `shinka-setup`, `shinka-convert`, `shinka-run`, `shinka-inspect`.
- **2026-05.** "Headless" mutation models: a `headless/claude` model string routes mutation calls through the local CLI on a subscription.
- **2025-10.** It helped Team Unagi win the ICFP 2025 Programming Contest.
- **The evaluator contract.** It is laid out in `shinka-setup` ([SKILL.md](https://github.com/SakanaAI/ShinkaEvolve/tree/main/skills/shinka-setup)).
  - The evaluator returns `combined_score`, a **`public`** dict (shown to the mutator), a **`private`** dict (hidden), `extra_data` and `text_feedback`.
  - It also returns `correct.json {correct, error}`.
  - The skill smoke-tests `evaluate.py` on the seed program before any evolution.
- **Comparison.** Under equal budgets ShinkaEvolve does not reliably beat simple baselines (Gideoni et al.; EvoX). See §4.

---

## 3. FunSearch and AlphaEvolve: loop details the ablations support

### FunSearch
Romera-Paredes et al., *Nature* 625:468–475. Received 2023-08-12, published 2023-12-14.
[PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10794145/);
[Supplementary PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-023-06924-6/MediaObjects/41586_2023_6924_MOESM1_ESM.pdf). All **[V]**.

**The loop:**
- **Only one function is evolved** (`priority`) inside a fixed skeleton.
- **Best-shot prompting.**
  - k=2 programs are sampled from the database, sorted by score and labelled `priority_v0` and `priority_v1`.
  - The LLM writes `priority_v2`.
  - 4 samples per prompt, temperature 1.0, top-p 0.95.
- **Database.**
  - 10 islands.
  - Within an island, programs are **clustered by signature**: the tuple of scores on each input.
  - Clusters are sampled by Boltzmann selection (T0=0.1, period N=30,000).
  - Within a cluster, shorter programs are favoured (T_program=1.0).
  - **Every 4 h the worse half of the islands is wiped** and reseeded from a random surviving island.
- **Scale.**
  - 15 samplers and 140–150 CPU evaluators, each with a 30 s timeout and 2 GB of memory.
  - About 10^6 samples. The full admissible set I(15,10) took about 2 million programs.
  - The supplement estimates **$800–1,400 and 250–500 kWh** per such experiment on Google Cloud.
- **Model choice.** A fast model (Codey/PaLM 2) was chosen deliberately over a better, slower one, because sample volume was the trade-off. Results are "not too sensitive" to the LLM.
  - StarCoder-15B never found the full set in 5 runs; Codey did in 2 of 5.

**Ablations (Suppl. A.1, I(15,10), 5 seeds each):**
- **W/O Skeleton.** The model writes the whole ordered list instead of only the priority function.
- **W/O Evolution.** Only the initial prompt is used, many samples are drawn, and the best is kept. This is **best-of-N**.
- **Less Diversity.** A single island.
- **W/O Merging.** k=1.
- Results:
  - FunSearch found the full-sized set in **2 of 5** runs; W/O Merging in **1 of 5**; every other variant in 0 of 5.
  - "The use of a skeleton and the evolution of prompts are particularly critical."
  - With less diversity it found "large but not a full-sized" sets.
  - On cap sets in n=8, k=1 was also worse.
- **LLM vs hand-designed random AST mutations.** The LLM was "clearly critical". Random mutations plateaued below −240 even after more than 50 million programs. They still "exceeded our expectations", which the authors credit to the skeleton and the pipeline.
- **How often it succeeds.**
  - n=8 cap set of size 512: only **4 of 140** runs.
  - Admissible sets beat the previous state of the art in all 15 runs.
  - Bin packing beat first-fit and best-fit in all 10 runs (Weibull 10k: 0.44% ± 0.11% excess bins vs 4.20% and 3.90%).
- **Train/test.**
  - Bin-packing heuristics were trained on generated instances and tested on OR1–OR4 and Weibull at other sizes. FunSearch: OR1 5.30% vs first fit 6.42%; Weibull-100k 0.03% vs 4.00%.
  - So held-out instances were used, but the main text has no overfitting analysis.

### AlphaEvolve
Novikov … Balog, Google DeepMind, [arXiv 2506.13131](https://arxiv.org/html/2506.13131v1), June 2025; blog 2025-05-14. **[V]** unless marked.

**The loop:**
- **Database.** A MAP-Elites and island hybrid.
- **Prompt.** Prior programs with their scores, system instructions, optional context (equations, code, PDFs), stochastic formatting and rendered evaluation results.
  - Optional **meta-prompt evolution**: prompts co-evolve in their own database.
- **Output.** SEARCH/REPLACE diffs by default. A full rewrite is used for short code or when it fits better.
- **Models.** Gemini 2.0 Flash for throughput, plus Pro for "occasional, higher-quality suggestions".
- **Evaluation cascade.**
  - New programs run first on small or easy cases.
  - Only programs that pass go on to harder stages.
- **Other evaluation features.**
  - LLM-generated feedback can score soft properties such as simplicity.
  - Multiple metrics can be scored together; this "often" improves the single target metric too.
  - Evaluation is parallel. One evaluation can take "on the order of 100 compute-hours".
- **Scale.** "Thousands of LLM samples" vs FunSearch's "millions" (Table 1). The kernel work went "from several months" to "days".

**Ablations** (Fig. 8, matrix multiplication and kissing number). Each of these costs significant performance:
- no evolution;
- no context in the prompt;
- no meta-prompt evolution;
- evolving only the loss function instead of the full file;
- a single small LLM only.

The magnitudes exist only as curves. **No numbers were read [U for magnitudes].**

**Stated limitation.** It needs an automatic evaluator. LLM-only evaluation is "not a setting we have optimized for".

### AlphaEvolve at scale (Georgiev, Gómez-Serrano, Tao, Wagner)
[arXiv 2511.02864](https://arxiv.org/abs/2511.02864), v1 2025-11-03, v3 2025-12-22. [Tao's blog](https://terrytao.wordpress.com/2025/11/05/mathematical-exploration-and-discovery-at-scale/), 2025-11-05. **[V]** (blog and abstract).

**Scale.** 67 problems. It rediscovered the best known results "in most of the cases" and improved several.

**Verifier exploits:**
- AlphaEvolve was very good at finding exploits.
- When distances were accepted only up to numerical precision, it placed points in "virtually the same location".
- It exploited a floating-point failure in an LP solver. The fix was to raise an error on solver failure.
- It exploited inadmissible inputs whenever the verifier did not check every condition and type.

**Fixes:**
- Exact or interval arithmetic.
- Conservative worst-case scoring.
- For the moving sofa, scoring only the part of the sofa provably inside the corridor, which blocked "clipping".
- A "non-trivial amount of human effort" goes into a non-exploitable verifier.

**Where it was strong and weak.** Strong on algebraically structured problems. Weak on analytic number theory, even with hints.

**Cost of verification.** Verifier compute is a significant fraction of a run. Cheaper LLM verifiers gave distorted results.

**Advice:**
- Keep a history of runs, failed ones included.
- Supply literature hints.
- Verify independently with a non-LLM checker.
- "Vibe optimizing" gives uneven results.

---

## 4. Claude-Code-native loops and honest comparisons with best-of-N

### Existing Claude Code skills and plugins (all checked 2026-10-27) **[V]** unless marked
- **karpathy/autoresearch** ([repo](https://github.com/karpathy/autoresearch); created 2026-03-06; about 98.7k stars). The template everyone copies.
  - `program.md` is the human-written "skill". `train.py` is the only file the agent edits. `prepare.py` holds the evaluation and the dataloader and is **fixed**.
  - Each experiment is a 5-minute training run, about 12 per hour and about 100 per night.
  - It keeps the change if val_bpb improves and reverts it otherwise: a pure hill climb.
  - No anti-gaming beyond keeping the evaluator out of the editable file.
- **uditgoenka/autoresearch** ([repo](https://github.com/uditgoenka/autoresearch); created 2026-03-13; about 6.8k stars; v2.2.2). A Claude Code skill.
  - Per iteration: one atomic change, `git commit`, a mechanical `Verify` command producing a number, keep or `git revert`, a TSV log. Git history serves as memory.
  - An optional `Guard` command (e.g. the test suite) must keep passing. If it fails, the change is reworked up to 2 times.
  - Guard and test files are never modified.
  - Equal score with less code is kept.
  - 25 iterations by default.
  - v2.1 cut an 813-line SKILL.md down to a 41-line router plus 12 command files.
  - No held-out set.
- **evo-hq/evo** ([repo](https://github.com/evo-hq/evo); created 2026-04-05; about 1.5k stars). A Claude Code plugin with `/evo:discover` and `/evo:optimize`.
  - **Tree search.** Parallel subagents each work in their own git worktree, forking from any committed node.
  - **Frontier choice.** One of argmax, top_k, ε-greedy, softmax, or GEPA-style `pareto_per_task`.
  - **Gates.** Pass/fail checks such as the test suite or a score floor on a **held-out slice**. They are inherited down the tree, and `discover` adds a held-out gate automatically.
  - Rationale for gates: without them "the search will find ways to return a constant, skip work, or trade correctness for speed".
  - No results reported.
- **alchaincyf/darwin-skill** ([repo](https://github.com/alchaincyf/darwin-skill); created 2026-04-13; about 6.6k stars; v2.0 on 2026-05-28). Evolves SKILL.md files.
  - **Rubric.** 9 weighted dimensions summing to 100.
  - **Each round.** It fixes the dimension with the largest weighted gap, commits, re-scores, and keeps the change or runs `git revert`.
  - **Judges.** Two **fresh, independent judge subagents per round**, so the editor never grades its own work.
  - **Checkpoints.** Human checkpoints after the baseline and after each diff.
  - **Stopping.** It stops early on a gain under 1 point.
  - **Self-grading figure.** It cites "46.4%" self-grading accuracy from a "SkillLens" paper. **[S, not traced to the paper]**
  - No held-out test prompts.
- **samuelzxu/claude-evolve** ([repo](https://github.com/samuelzxu/claude-evolve); created 2026-04-10; 17 stars). A Claude Code plugin that re-implements ShinkaEvolve with Claude tiers only.
  - The ensemble is a UCB1 bandit over (opus / sonnet / haiku × effort).
  - Islands, AST-based novelty rejection, and meta-recommendations.
  - Self-reported circle packing: 1.8378 → **2.6343 in 50 generations, 3 islands, about 3 hours**, vs a 2.6360 reference.
- **ShinkaEvolve skills** (above) and **OpenEvolve's `claude_code` provider** (above): the two big frameworks can already use Claude Code as the mutator.

### Controlled comparisons
- **Gideoni, Risi, Gal, "Simple Baselines are Competitive with Code Evolution".** [arXiv 2602.16805](https://arxiv.org/abs/2602.16805v1); v1 2026-02, v2 2026-10-12. An earlier version was a NeurIPS 2025 submission, ["Random Baselines for Simple Code Problems…"](https://neurips.cc/virtual/2025/131657). **[V]**
  - **Baselines.**
    - (a) **IID RS**: sample N programs independently and keep the best. This is best-of-N.
    - (b) **SCS**, sequential conditioned sampling: each batch is conditioned on a *random* subset of the previous batch's programs that ran. There is no fitness selection, and it restarts across trials.
  - **Math bounds** (9 AlphaEvolve problems, $20 per method).
    - IID RS: 2,000 samples. SCS: 10 generations × 20 programs × 6 trials. ShinkaEvolve: 500–800 generations.
    - SCS matches or beats ShinkaEvolve on 6 of 9 problems, IID RS on 4 of 9.
    - Circle packing: AlphaEvolve 2.63586, Shinka 2.63598, SCS 2.63590, IID 2.632.
    - Kissing number in 11D: AlphaEvolve 593, Shinka 402, both baselines 438.
    - Wall clock: baselines took 1–3 h, Shinka about 10 h.
  - **The search space matters more than the search algorithm.** **[V]**
    - Changing the formulation moved every method the same way (uncertainty inequality 0.3521 → 0.3482).
    - Restricting circle radii to at most 0.1 capped every method at 2.514.
    - Shinka's expert prompt found the best circle packing 3 of 3 times vs 1 of 3 with a minimal prompt.
    - The same expert prompt made the baselines *worse* (2.626 and 2.621).
  - **Agentic scaffolds on AIME.**
    - IID RS evaluated 50 scaffolds; Shinka ran 75 generations.
    - **Every automated method dropped more than 10% from validation to test**; majority vote dropped about 5%.
    - After 10 re-evaluations, Shinka vs IID RS was a coin flip, P = 0.49.
    - With about 100 validation questions, selection is partly evaluation luck.
    - A cascade plus "probability of dominance" let IID RS find a scaffold that generalised.
  - **MLE-bench.** SCS beat AIDE on 6 of 10 competitions, IID RS on 2 of 10. Both needed an iterative debugging step: textual feedback matters.
  - **ALE-Bench LITE.** Both baselines beat Shinka on 8 of 10 problems.
  - **Recommendations.**
    - Use equal LLMs, prompts, search spaces and budgets.
    - Always run the simple baselines.
    - Disclose the domain knowledge used.
    - Re-evaluate selected candidates several times and report confidence intervals.
    - Report on a test set of at least 300 items.
- **EvoX** (Liu … Stoica, Berkeley/Stanford, [arXiv 2602.23413](https://arxiv.org/html/2602.23413), v2 2026-03-16). **[V]**
  - It evolves the *search strategy*: an outer loop triggers on stagnation, at 10% of the budget.
  - Budget: 100 iterations, 3 runs.
  - No single fixed strategy wins:
    - On Heilbronn, **beam search and best-of-N were the strongest fixed strategies; MAP-Elites lagged**.
    - On Cloudcast, random sampling alone made large gains.
    - Late large structural edits destabilise strong solutions.
- **Pelleriti et al., "What Do Evolutionary Coding Agents Evolve?"** [arXiv 2605.20086](https://arxiv.org/html/2605.20086v1), 2026-05-19, NeurIPS 2026. **[V]**
  - **Data.** 121 runs of OpenEvolve, GEPA, EvoX and ShinkaEvolve; 16 tasks; 100 iterations each.
  - **What the edits are.** Hyperparameter tuning is the most frequent edit type.
    - The edits most associated with gains are new external dependencies (odds ratio 3.58), efficiency (1.61) and architectural change (1.55).
  - **Cycling.** About **30% of added lines are byte-identical re-additions of lines the same lineage deleted earlier**. The share rises in 118 of 121 runs.
  - **Short lineages.** The final best has median depth 4 (ALE) or 6 (math), so most of the budget goes to branches that never lead to the best.
  - **Tuning ceiling.** Bayesian-optimising the constants of an intermediate program often matches the run's final best. The paper's counts are internally inconsistent (22/36 vs 13/15).
  - **Overfitting.** On ALE, 2 of 4 frameworks overfit public tests on at least 30% of problems.
  - **Reproducibility.** Replays recover a median 0.76 of a breakthrough's score but never the exact program.
- **Zhang et al., PPSN 2024, "Understanding the Importance of Evolutionary Search in AHD with LLMs".** [arXiv 2407.10873](https://arxiv.org/abs/2407.10873), 2024-07-15.
  - **[V abstract]**: 4 methods × 9 LLMs × 5 runs. They argue evolutionary search matters.
  - **[U]**: they also find a simple (1+1) hill-climber competitive and large variance across problems. That detail was not in the abstract.

---

## 5. Known pitfalls (with the evidence)

| Pitfall | Evidence | Mitigation seen in the wild |
|---|---|---|
| **Evaluator gaming / reward hacking** | NaN centres pass the circle-packing validator (OpenEvolve [#285](https://github.com/algorithmicsuperintelligence/openevolve/issues/285), 2025-10). Points stacked at float precision; an LP-solver failure exploited (Tao, 2025-11). A candidate "bypassed one stage of the evaluation pipeline" ([Barbarians at the Gate](https://arxiv.org/html/2510.06189), 2025-10). Shinka's own SOTA was over-credited by a relaxed checker. | Exact or conservative scoring; reject NaN, inf and wrong types; raise on solver failure; check *every* constraint. The evaluator lives in a file the proposer cannot edit (autoresearch, uditgoenka). Pass/fail gates before the score (evo). Adversarial tests and several metrics together (Barbarians). |
| **Overfitting to training instances** | More than 10% validation→test drop for every method on AIME scaffolds (Gideoni). ALE public-test overfit on at least 30% of problems for 2 of 4 frameworks (Pelleriti). A single availability trace generalised worse (Barbarians, Can't-Be-Late). | Search on a feedback subset (Barbarians used 30% of traces) and report on the full set. A held-out-slice gate (evo). Public vs private metrics (Shinka). Re-evaluate the top candidates several times and select by probability of dominance (Gideoni). |
| **Winner's curse from noisy scores** | About 100 AIME questions make selection partly luck; re-scoring lowers the winners' scores (Gideoni). | Re-score finalists, report confidence intervals, use a test set of at least 300 items. |
| **Diversity collapse / premature convergence** | Hill climbing "starts strong but plateaus" (Shinka). A single island never reached the full set (FunSearch). Over-specific hints pushed transaction scheduling to worse designs (Barbarians). 30% cycling (Pelleriti). | Novelty rejection before evaluation (Shinka: embedding similarity above 0.95, then a judge). Offspring-count penalty in parent sampling. Signature clustering (FunSearch). Show the proposer what was already tried or deleted. Few hints, added only on stall (Barbarians). |
| **Trivial "wins" via library swaps** | Full access to high-level libraries gave PyTorch-primitive speedups, not algorithms (Barbarians). | Restrict the editable region and the APIs. Evolve one block (FunSearch skeleton, EVOLVE-BLOCK) and *enforce* it: OpenEvolve does not by default. |
| **Mutator failure** | Small models emit broken diffs, so the best program equals the seed (OpenEvolve [#281](https://github.com/algorithmicsuperintelligence/openevolve/issues/281)). | A full-rewrite fallback; resample on a parse failure up to 3 times (Shinka). |
| **Cost and time blowups** | FunSearch $800–1,400 per experiment. OpenEvolve circle packing about $22 over 800 iterations. Shinka about 10 h vs 1–3 h for the baselines. AlphaEvolve evaluations up to about 100 compute-hours. Barbarians runs took 40 min–12 h, 70–400 iterations, ≤$5–20 each, plus *hours to days* of setup. | A hard budget cap (`max_api_costs`, `max_budget_usd`). Cascades that kill bad candidates cheaply. Stop on stagnation. Cheap model for most mutations. |
| **Ensemble chaos** | More than 2 models brought "conflicting ideas… mutation drift" (Barbarians). | Two models: a fast one for most edits, a strong one roughly 20% of the time (AlphaEvolve, Barbarians, OpenEvolve defaults). |
| **LLM-judged evaluators** | Cheaper LLM verifiers distorted results (Tao). AlphaEvolve "not optimized" for LLM evaluation. Self-grading is unreliable (darwin-skill citing SkillLens, **[S]**). | A non-LLM evaluator wherever possible. Otherwise fresh, independent judges that are not the proposer, a fixed rubric written first, and pairwise comparison. Treat the result as noisy (see the winner's curse). |

---

## What to copy into a Claude Code skill

Budget reality: each mutation is a Claude subagent call taking minutes and spending subscription usage, not API dollars. The
skill lives at the scale of **tens of evaluations**, not 10^3–10^6. At that scale the controlled evidence (Gideoni; EvoX;
Pelleriti) says **simple beats elaborate**. The design below is sized to that.

1. **The evaluator comes first, and it is code.**
   - Before any candidate exists, write the scorer and run it on the seed (shinka-setup does this).
   - The scorer returns `{correct: bool, score: number, public: {...}, private: {...}, feedback: string}`.
   - Fail closed:
     - reject NaN, inf and wrong types;
     - check every constraint exactly or conservatively;
     - turn any solver or tool failure into an error, never a score.
   - The scorer, the tests and the data sit outside the editable scope. The proposer never sees or edits them, only `public` and `feedback`.
   - Pass/fail gates run before the score: the test suite, the constraints, a minimum on held-out cases.
2. **Train/test split.**
   - Proposers see the scores and feedback of a **search split** only, roughly ⅓ of the cases (Barbarians used 30%).
   - Selection between rounds uses the search split.
   - The final pick is re-scored on the **held-out split**, with **3 repeats if the scorer is noisy**. The val→test drop is reported.
   - If the held-out split is under about 30 items, say the result is anecdotal.
3. **Round 0 is a best-of-N control.**
   - N = 6–8 independent proposals from the same prompt, in parallel subagents with no shared context.
   - The best of these is the **baseline the loop must beat**. If evolution does not beat it, the skill reports that.
4. **Rounds 1..R, with R ≤ 5 by default and 8 at most.**
   - Each round has 4–6 children.
   - Final-best lineages are short (median depth 4–6), and the gains are front-loaded.
   - **Stop early after 2 rounds without held-out-gated improvement.**
   - This puts the total at about 25–50 evaluations, the scale of claude-evolve (50 generations, about 3 h) and Barbarians (70–400).
5. **Parent selection** is rank-weighted with an offspring penalty (Shinka weighted sampling), not argmax.
   - Practical form: pick from the top 3 by search score, weight 1/(1+children), and add 1 random successful parent per round. That is SCS's strength.
   - No MAP-Elites grid and no islands below about 100 evaluations.
   - The one diversity device worth keeping: **2 independent lineages** if R ≥ 5, merged only at the end.
6. **Prompt shape.**
   - The problem; the scorer *contract* (not its code); the editable region only.
   - **k = 2–3 prior candidates sorted ascending by score, with their scores and feedback** (FunSearch k=2; OpenEvolve 3+2).
   - A short "already tried / deleted, do not reintroduce" list, against the 30% cycling.
   - Every 2–3 rounds, a 3–5 line scratchpad of what worked.
   - The instruction is "propose one materially different change", not "improve".
   - Hints stay minimal and are added only on a stall.
7. **Mutation form.** Targeted edits by default, a full rewrite about 30% of the time, and a crossover of the two best about 10% (Shinka 0.6/0.3/0.1). A full rewrite is the fallback when an edit fails to apply.
8. **Novelty rejection before scoring.** Reject a child that is a near-duplicate of any archived candidate (normalised diff or hash; for prose, a judge asked "same idea?") and re-propose up to 2 times. This is the cheapest ablation-backed component in Shinka.
9. **Model mix.**
   - Most children from the default model.
   - About 1 in 5 from the strongest model at high effort.
   - Never more than 2 models.
   - A bandit only if R is large; at our scale it cannot learn.
10. **After the loop:**
    - Tune the constants of the final best separately: the cheap "tuning ceiling" gain.
    - Re-score on the held-out split.
    - Show the winning diff plus the baseline-vs-winner table.
    - Leave a log of every candidate: score, kept or rejected, reason. Git commit and revert as memory, as in autoresearch.
11. **Fuzzy (non-code) targets.**
    - Allowed only with a rubric fixed before round 0.
    - **Fresh judge subagents that are never the proposer**, with pairwise comparison against the current best.
    - Re-judge finalists at least 3 times, and label the result "LLM-judged, noisy".

## What not to copy

- **FunSearch- and OpenEvolve-scale machinery.**
  - Not population 1000, 5–10 islands, migration schedules, MAP-Elites feature grids, 4-hourly island resets or Boltzmann cluster temperatures.
  - These were built for 10^3–10^6 samples. At equal small budgets OpenEvolve and Shinka lose to IID or SCS baselines more often than not (Gideoni; EvoX Table 8), and MAP-Elites lagged on Heilbronn (EvoX).
- **Meta-prompt evolution or evolving the search strategy** (AlphaEvolve, EvoX). The gains are real but at a scale and complexity a skill cannot carry.
- **Pure hill climbing as the only mode** (autoresearch, uditgoenka, darwin-skill). It is fine for "make the tests faster", but it plateaus (Shinka ablation) and has no held-out check.
- **Expert-hint-heavy prompts.** They help one framework and hurt others (Gideoni). They converge early (Barbarians).
- **Selecting and reporting on the same split**, and a single evaluation of a noisy score. The more-than-10% val→test drop is the norm, not the exception.
- **The proposer grading itself**, or a cheap LLM as the only verifier for a quantitative claim (Tao; darwin-skill's rationale).
- **Editable evaluators, broad library access, or "evolve block" markers without enforcement** (OpenEvolve's `enforce_evolve_blocks: false` default).
- **Vendor efficiency headlines quoted as fact.**
  - "Orders of magnitude more efficient" and "150 samples" (Sakana); "100x" (OpenEvolve README).
  - All are self-reported, on one task, without equal-budget baselines.

## Not verified in this pass
- AlphaEvolve ablation magnitudes (Fig. 8 curves only).
- The Dria AlgoTune numbers (pages returned 402; snippets only).
- The SkillLens 46.4% figure.
- Whether Zhang et al. (PPSN 2024) found a (1+1) hill-climber competitive.
- ShinkaEvolve ablation magnitudes (figures only).
- Gideoni et al. v2 figures were read from the v2 HTML. v1 may differ.
