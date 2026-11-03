# Human creative problem solving and problem reframing: the science, the proven practice, and what an AI agent can be told to do

Scope: solving a *given* problem (insight, fixation, reframing, solving heuristics, behavioural solutions, expertise). Idea-generation methods (SCAMPER, Oblique Strategies, design thinking as ideation) are covered by a sibling pass and left out here.
Research date: 2026-10-26. Each source carries its publication date where it was known. **[UNVERIFIED]** marks a figure seen only in a secondary source or recalled, not confirmed against the primary.

---

## 1. Insight problem solving: impasse, restructuring, functional fixedness, Einstellung, incubation, generic parts technique

### Takeaway
The lab evidence is strongest for two things. First, an early familiar idea actively blocks better ones: Einstellung and functional fixedness, with eye-tracking showing that attention stays on the familiar solution. Second, impasses break when the solver changes the problem's *representation* — relaxing a self-imposed constraint or decomposing a familiar chunk — rather than searching harder in the same space. Two interventions have evidence. The generic parts technique (re-describe each part without its function) gave about 67% more problems solved in one study. Incubation has a small-to-moderate pooled effect (d ≈ 0.29), largest after a long preparation period and with an undemanding filler task.

### Cited Findings
**Representational change (Ohlsson; Knoblich et al.)**
- Ohlsson's representational change theory (1984, 1992) treats insight as removing unnecessary self-imposed constraints and adopting a new conception of the problem. Knoblich, Ohlsson, Haider & Rhenius (1999), *JEP: LMC* 25(6), 1534–1555, propose two mechanisms for breaking an impasse: **constraint relaxation** and **chunk decomposition**. They tested them in 4 experiments with matchstick arithmetic, and the results were consistent with the predictions — [Knoblich et al. 1999, PDF](https://www.kognition.uni-koeln.de/literature/Knoblich_etal_1999.pdf); [CEU record](https://research.ceu.edu/en/publications/constraint-relaxation-and-chunk-decomposition-in-insight-problem-/)
- The constraint types are a value constraint, an operator constraint and a tautology constraint. Problems that need only a narrow constraint relaxed (Type A) were easiest; problems that need a broad one (Type C) were hardest. The chunk example: VI = VII + I is solved by decomposing VII into VI and I — [Knoblich et al. 1999](https://www.kognition.uni-koeln.de/literature/Knoblich_etal_1999.pdf) (details via secondary summaries of the paper)
- Thevenot & Oakhill (2008) argue that constraint relaxation and chunk decomposition also apply to ordinary, incremental problems such as arithmetic word problems, not only to insight problems — cited in the same search result set, [Frontiers 2017](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.02001/pdf) **[secondary]**

**Functional fixedness (Duncker 1945; Adamson 1952)**
- Duncker's candle problem (1945): participants try to attach the candle to the wall directly with tacks, or with melted wax, instead of using the tack box as a shelf — [Wikipedia: Candle problem](https://en.wikipedia.org/wiki/Candle_problem) (accessed 2026-10)
- Adamson (1952) replicated it with 57 subjects, because Duncker's 14 subjects were too few. Time-to-solution was the measure, and the "pre-utilized" (fixed) group was significantly slower — [Wikipedia: Functional fixedness](https://en.wikipedia.org/wiki/Functional_fixedness) **[secondary]**
- Participants given an *empty* tack box were about twice as likely to solve the problem as those given the box used as a container — [Wikipedia: Functional fixedness](https://en.wikipedia.org/wiki/Functional_fixedness) **[secondary; the often-quoted 86% vs 41% split is UNVERIFIED]**

**Einstellung / mental set (Luchins 1942; Bilalić et al. 2008)**
- Luchins (1942), *Psychological Monographs* 54(6), water jars. Subjects trained on B − A − 2C kept using it even when a simpler A + C method (or A − C) existed; untrained controls found the simple method at once. When told "Don't be blind", more than half of the set-bound subjects found the simple solution — [Wikipedia: Einstellung effect](https://en.wikipedia.org/wiki/Einstellung_effect); [Futility Closet, 2022-01-20](https://www.futilitycloset.com/2022/01/20/the-einstellung-effect/) **[exact baseline failure % not verified]**
- Bilalić, McLeod & Gobet (2008), *Cognition* 108, 652–661, on expert chess players. After finding a familiar solution, players *said* they were looking for a better one, but their eye movements stayed on the squares relevant to the solution they already had. This is the mechanism: the first idea steers attention toward consistent information and away from inconsistent information, without the solver being aware of it — [PhilPapers record](https://philpapers.org/rec/BILWGT); [Bilalić et al. 2010, Curr. Dir. Psych. Sci., PDF](https://cognition.aau.at/download/Publikationen/Bilalic/Bilalic_etal_2010b.pdf)
- Sheridan & Reingold (2013), *PLoS ONE*. When the familiar move was good but suboptimal, experts and novices who chose it kept looking at it throughout the trial. When the familiar move was a blunder, all experts avoided it — [PMC3790829](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3790829/) (2013)
- Einstellung is not specific to humans. Naeini et al., "Large Language Models are Fixated by Red Herrings" (NeurIPS 2023 Datasets & Benchmarks), used the Only Connect Wall dataset, with red-herring distractors, and found LLMs fixated by the misleading cues — [arXiv 2306.11167](https://arxiv.org/abs/2306.11167) (2023)

**Incubation (Sio & Ormerod 2009 meta-analysis)**
- Sio & Ormerod (2009), "Does incubation enhance problem solving? A meta-analytic review", *Psychological Bulletin* 135(1), 94–120, DOI 10.1037/a0014212. It found a positive incubation effect overall — [PubMed 19210055](https://pubmed.ncbi.nlm.nih.gov/19210055/); [full text via Gwern](https://www.Gwern.net/doc/psychology/writing/2009-sio.pdf)
- The pooled effect is reported as d ≈ 0.29 (117 studies), low-to-medium — [Sussex figshare](https://sussex.figshare.com/articles/journal_contribution/Does_incubation_enhance_problem_solving_A_meta-analytic_review/23409905) via secondary review **[the effect-size figure is from a secondary citation; another recalled figure, d ≈ 0.17, did not match and is UNVERIFIED]**
- Moderators:
  - A **longer preparation period** before the break gave a larger effect.
  - **Divergent-thinking tasks** benefited more than linguistic or visual insight tasks.
  - For linguistic insight problems, a **low-demand filler task beat rest**.
  - A demanding interpolated task shrank the benefit.

  — [PubMed 19210055](https://pubmed.ncbi.nlm.nih.gov/19210055/); [Psychological Research 2018, s00426-018-0992-9](https://link.springer.com/article/10.1007/s00426-018-0992-9)

**Generic Parts Technique (McCaffrey 2012)**
- McCaffrey (2012), "Innovation Relies on the Obscure: A Key to Overcoming the Classic Problem of Functional Fixedness", *Psychological Science*. Subjects trained in the GPT solved **67% more problems** than untrained controls, on 8 problems, at a solve rate above 80% — [APS press release, 2012-03-06](https://www.psychologicalscience.org/news/releases/stumped-by-a-problem-this-technique-unsticks-you.html); [ScienceDaily, 2012-03-07](https://www.sciencedaily.com/releases/2012/03/120307112749.htm) **[a relative increase; the control group's raw rate is not in the press release]**
- The method:
  1. Break each object into its parts.
  2. Describe each part only by material, shape and size, never by function.
  3. Ask "can this be broken down further?"
  4. Ask "does this description imply a use?" If it does, re-describe the part. For example, "wick" implies lighting, "string" does not, "cotton strands" does not.

  Example problem: fasten two steel rings into a figure-8 using a candle and a match. Wax is too weak to hold them, but the wick, re-described as string, can tie them — [APS press release](https://www.psychologicalscience.org/news/releases/stumped-by-a-problem-this-technique-unsticks-you.html)
- The theory behind it is the "obscure features hypothesis". In an analysis of 1,001 historically important inventions, McCaffrey reports that each innovator noticed an obscure feature or function — [APS press release](https://www.psychologicalscience.org/news/releases/stumped-by-a-problem-this-technique-unsticks-you.html) **[the 1,001-invention analysis is self-reported by the author]**

### Inferences
- These steps can be written as agent instructions:
  - **(a)** After a first solution, explicitly search for evidence that would favour a *different* solution, because the first solution biases what gets looked at.
  - **(b)** List the constraints you assumed and mark each as "given by the problem" or "assumed by me". Relax the assumed ones, the narrowest first.
  - **(c)** Re-describe each resource or component without its function (GPT) before declaring "no solution with available means".
  - **(d)** Re-chunk: break familiar units such as a module, a service, a step or a role into sub-parts.
- An LLM can't wait between attempts, so incubation does not translate directly. The nearest analogue is to separate the first attempt from a later fresh pass with the earlier reasoning hidden or summarised, so the fixating details are "forgotten". This is speculative; the mechanism behind incubation (forgetting fixation versus unconscious work) is still debated.
- Einstellung in LLMs is documented (Naeini 2023), so an agent should not trust its first pattern match on familiar-looking problems.

### Gaps
- The exact per-moderator effect sizes from Sio & Ormerod (2009), and newer incubation meta-analyses after 2009, were not retrieved.
- McCaffrey's raw solve rates (control vs GPT) and sample size were not retrieved from the paper itself.
- Luchins's baseline failure rate and the Adamson 86%/41% figures were not verified.
- No large replications of GPT were found.

---

## 2. Problem framing and reframing: Wedell-Wedellsborg; Getzels & Csikszentmihalyi; the elevator story

### Takeaway
Reframing has strong practitioner support but thin controlled evidence. Its best-known empirical anchor is the Getzels & Csikszentmihalyi problem-finding study of art students. The famous "slow elevator → mirrors" story is an untraceable parable: it is told secondhand from Russell Ackoff onwards, at least to 1963, and no building or date has been found. Wedell-Wedellsborg's own framing is "find a *better* problem, not the *real* one". His seven practices come from consulting experience and are not tested methods.

### Cited Findings
- Wedell-Wedellsborg, "Are You Solving the Right Problems?", *HBR*, January–February 2017 (online 2017-01). In a survey of 106 C-suite executives from 91 companies in 17 countries, 85% agreed their organisations were bad at problem diagnosis and 87% agreed that this carried significant costs — [HBR 2017](https://hbr.org/2017/01/are-you-solving-the-right-problems) **[a convenience survey, not a study of outcomes]**
- The seven practices are:
  1. establish legitimacy (use the elevator story);
  2. bring outsiders in, which he calls the single most helpful practice;
  3. get people's problem definitions in writing;
  4. ask what's missing;
  5. consider multiple categories of cause;
  6. analyse positive exceptions;
  7. question the objective.

  — [HCAMag summary, 2016-12-26](https://www.hcamag.com/asia/news/general/seven-steps-to-reframing-problems/147783); [Business Digest](https://business-digest.eu/_media/HTML%20BD/USBD306021.html)
- Book: *What's Your Problem?* (HBR Press, March 2020). Its method is **Frame → Reframe → Move Forward**. "Reframing is not about finding the real problem; it's about finding a better problem to solve" — [O'Reilly listing](https://oreilly.com/library/view/whats-your-problem/9781633697232); [TD Magazine review](https://td.org/content/td-magazine/reframe-your-view-for-better-solutions)
- The elevator example in Wedell-Wedellsborg: tenants complain the lift is slow; the obvious fixes are a new lift, a stronger motor or a better algorithm; the reframe is that the wait is annoying, so mirrors are installed. He stresses that the first framing isn't wrong — [WEF, 2021-07](https://www.weforum.org/stories/2021/07/to-solve-big-issues-like-climate-change-we-need-to-reframe-our-problems/)
- **The origin of the elevator story is unverified.**
  - Ackoff tells it in *Re-creating the Corporation* (1999), where a young psychologist in personnel suggests mirrors — [Oregon State course page](http://classes.bus.oregonstate.edu/ba465H/Stories/Ackoff%27s%20elevator%20story.htm)
  - Ackoff & Greenberg tell it again in *Turning Learning Right Side Up* (2008) — [Engines of Our Ingenuity, Univ. of Houston](https://engines.egr.uh.edu/episode/2971)
  - Other versions set it in a post-WWII New York office building, or (Larson 1987) in a hotel tower — same sources.
  - A secondary blog traces it to Ackoff's *A Manager's Guide to Operations Research* (1963), where it is already told secondhand, and finds "no building, no year, no complaint log" — [Overcorrected Substack](https://overcorrected.substack.com/p/why-we-love-jumping-to-solutions) **[secondary, unverified]**
- A real reframing case with measured results is Lori Weise's Shelter Intervention Program at Downtown Dog Rescue in Los Angeles. It reframed "irresponsible owners abandon pets" as "poverty and housing crises make owners surrender pets". In a two-month pilot staff intervened in 554 cases, and 448 pets were not surrendered. Nearly 21,000 animals have been kept out of shelters since then. Weise estimates the cost at about $50 per pet, far less than sheltering — [Maddie's Fund, Feb 2016](https://www.maddiesfund.org/starting-and-running-a-shelter-intervention-program.htm?p=topic1); [Ivanhoe, 2019](https://ivanhoe.com/family-health/shelter-intervention-program-sip) **[that Wedell-Wedellsborg uses this case in his writing is from memory, UNVERIFIED]**
- **Problem finding** — Getzels & Csikszentmihalyi, *The Creative Vision* (1976). Art students drew a still life from a set of objects. "Problem-finders" spent longer exploring and rearranging the objects and kept the problem open longer. Their drawings were rated more original, and at follow-up they were more successful as professional artists. Intelligence did not correlate with studio performance or later success — [Project MUSE review of the book](https://muse.jhu.edu/article/599015/summary); [MIT Press Reader](https://thereader.mitpress.mit.edu/?p=19895) **[the follow-up intervals are reported inconsistently, 5–7 years and about 18 years; the effect sizes were not retrieved]**

### Inferences
- These practices can be encoded for an agent:
  1. State the problem in writing in several framings before solving it.
  2. Ask "what's missing from this statement?"
  3. Categorise the possible causes into more than one category.
  4. Look for positive exceptions: when *doesn't* the problem occur?
  5. Question the objective: what is the requester actually trying to achieve?
  6. Take an outsider's view, for example a sub-agent with no context.
- "Better problem, not real problem" is a useful guard. The agent should keep the original framing as a candidate and not dismiss it.
- Getzels & Csikszentmihalyi suggest a behavioural marker: spending longer exploring and restructuring the problem *before* committing. This can be written as "do not commit to a solution until you have manipulated the problem statement".
- The elevator story should be cited in the skill as a parable, not as a case.

### Gaps
- No controlled experiment testing Wedell-Wedellsborg's seven practices was found.
- Meta-analytic evidence on problem finding as a predictor of creative outcomes was not retrieved. The literature exists (e.g., Runco's problem-finding work) but was not checked.
- The original quantitative tables of *The Creative Vision* were not seen.

---

## 3. TRIZ as a solving method

### Takeaway
TRIZ (Altshuller) is a structured *solving* method: it names the contradiction, applies separation principles, states the Ideal Final Result and inventories the resources. Its evidence base is weak and partly self-reported. One controlled multi-site study found TRIZ raised the novelty and variety of solutions and slightly lowered quantity. An analysis of TRIZ's own case studies found the contradiction matrix would have pointed to the documented solution in only 8 of 42 cases. Its parts — "state the contradiction", "the system should do X by itself", "use existing resources" — are more defensible than the matrix.

### Cited Findings
- **Controlled test.** Vargas Hernandez, Schmidt & Okudan Kremer (ASEE 2012; journal version "Systematic Ideation Effectiveness Study of TRIZ", *J. Mechanical Design* 2013) ran experiments at UTEP, Penn State and the University of Maryland. TRIZ improved novelty and variety and slightly reduced quantity, compared with an ad hoc ideation control — [ASEE PEER 21369](https://peer.asee.org/experimental-assessment-of-triz-effectiveness-in-idea-generation); [Kremer bepress](https://works.bepress.com/gul-kremer/30) **[overlapping data, not independent replications]**
- A Penn State comparison of design aids found that TRIZ was the best aid for novelty and a Smartpen the best for quantity — [Springer chapter](https://link.springer.com/10.1007/978-94-017-9112-0_13). An ICED 2017 study found that problem–solution maps enriched by TRIZ contradiction models raised novelty but lowered variety — [Politecnico di Milano repository](https://re.public.polimi.it/handle/11311/1031602)
- **Matrix criticism.** An analysis of 42 TRIZ case studies from TRIZ books found the contradiction matrix would have supported the documented solution in only 8. A few inventive principles covered most solutions, and the link between classification criteria and principles looked "quite random" — [unibz, "How problems are solved in TRIZ"](https://bia.unibz.it/esploro/outputs/conferenceProceeding/How-problems-are-solved-in-TRIZ/991005773526401241). The matrix's reliability "is often questioned" — [unibz journal article](https://bia.unibz.it/esploro/outputs/journalArticle/The-process-for-individuating-TRIZ-Inventive/991006274696801241)
- **Advocate figures.** Darrell Mann (a TRIZ practitioner) reports that Matrix 2003 had 96% relative effectiveness against 18% for the classical matrix, calibrated on patent samples — [TRIZ Journal, "Updating TRIZ: 2006–2008 patent research"](https://the-trizjournal.com/updating-triz-2006-2008-patent-research-findings/) **[not independent]**
- A survey of more than 300 engineers found sharp differences in effectiveness between TRIZ tools — [ASEE PEER](https://peer.asee.org/the-effectiveness-of-triz-from-the-perspective-of-comprehensive-benefits-of-technological-innovation) **[self-reported]**
- A DESIGN 2026 conference experiment on LLM-assisted TRIZ found that LLMs did not always improve design quality on complex tasks. They did reduce cognitive workload and improve the understanding of contradictions — [LUP Lund record](https://lup.lub.lu.se/record/80ee1fac-a63c-4753-a9ad-952675c2433e) **[search snippet; the full paper was not read]**

### Inferences
- For an agent, the strongest TRIZ parts to encode are these:
  - **(1)** State the contradiction explicitly: "improving A worsens B".
  - **(2)** Try to separate the contradicting requirements in time, in space, on condition, or between the whole and its parts, instead of compromising.
  - **(3)** Ideal Final Result: "the function is achieved with no added system". Ask what in the existing system could do it.
  - **(4)** Resource inventory: what is already present, free or wasted that could be used. This overlaps with GPT.
- The 40-principle matrix shouldn't be presented as a reliable lookup. It is at best a prompt list.

### Gaps
- The TRIZ papers were not read in full, and no effect sizes were obtained.
- No study isolating the separation principles or the IFR was found.
- The specific claim that TRIZ was "derived from 40,000 or 200,000 patents" was not verified.

---

## 4. Other solving heuristics: Pólya, inversion, first principles, working backwards, constraints, analogical transfer, adjacent possible

### Takeaway
Analogical transfer has robust lab evidence. People rarely retrieve a relevant analogy spontaneously (about 10% → 30% with a prior analogue, about 75% once told it is relevant). Comparing **two** analogues to induce the shared schema makes spontaneous transfer much more likely. LLMs benefit from self-generating analogous problems. Pólya-style heuristic instruction has mixed evidence; the effect appears to come largely from the metacognitive monitoring, not from the heuristic list. Inversion, first principles, "adjacent possible" and constraint addition are popular but lack controlled evidence in what was found here.

### Cited Findings
**Analogical transfer (Gick & Holyoak 1980, 1983)**
- Gick & Holyoak (1980), "Analogical Problem Solving", *Cognitive Psychology* 12(3), 306–355, used Duncker's radiation problem:
  - About 10% solve it unaided.
  - About 30% solve it after reading the fortress story.
  - About 75% solve it when told the story might help. The failure is in *access*, not storage.

  — [UMich Deep Blue, Gick & Holyoak 1980](https://deepblue.lib.umich.edu/handle/2027.42/23210); [HBCSE review](https://www3.hbcse.tifr.res.in/jrmcont/hpscse/node5.html) **[the round percentages are from reviews; they vary by experiment, e.g. 20% unprompted in Exp. IV and 100% with a hint in Exp. I]**
- Gick & Holyoak (1983), "Schema induction and analogical transfer", *Cognitive Psychology* 15(1), 1–38:
  - With **one** analogue, summarisation instructions, a verbal statement of the principle or a diagram did not help much.
  - With **two** analogues, the same aids became "highly beneficial".
  - The quality of the induced schema strongly predicted transfer.

  — [UMich Deep Blue, 1983](https://deepblue.lib.umich.edu/items/196ea13e-fb69-4a74-a6f9-864c81aed465); [Gwern PDF](https://Www.Gwern.net/doc/psychology/1983-gick.pdf)
- LLM parallel: "analogical prompting" (Yasunaga et al., ICLR 2024, Google DeepMind/Stanford) has the model generate its own relevant example problems before solving. It outperformed 0-shot CoT and manual few-shot CoT on GSM8K, MATH, Codeforces and BIG-Bench — [ICLR 2024 proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/4990dad2c1696224de42573d0222554a-Abstract-Conference.html); [arXiv 2310.01714](https://arxiv.org/html/2310.01714v1) (2023-10)

**Pólya / heuristic instruction**
- Mathematics educators report that the results of heuristic-instruction studies were "disappointingly inconsistent", which they attribute to failing to account for metacognition. Schoenfeld (1985) argued that Pólya's heuristics were too vague to teach as stated and that implementing them was underestimated — [UConn dissertation, 1989](https://digitalcommons.lib.uconn.edu/dissertations/AAI9006699); [Barkatsas, MERGA 1993](https://merga.net.au/wp-content/uploads/DOCS/common/Uploaded%20files/Annual%20Conference%20Proceedings/1993%20Annual%20Conference%20Proceedings/RP_Barkatsas_1993.pdf); [Schoenfeld 1979, heuristics](https://www.ime.usp.br/~alpereir/cursosdosemestre/resprob/schoenfeld_heuristics_79.pdf)
- Comprehension-monitoring training improved developmental-math performance whether or not Pólya's heuristics were included — [UIW dissertation, 2001](https://athenaeum.uiw.edu/uiw_etds/75)

### Inferences
- Analogy is the best-evidenced heuristic to encode. The agent should:
  - **(a)** deliberately retrieve analogous problems from *other* domains, because spontaneous access fails;
  - **(b)** retrieve at least two and state the shared structure (schema) before applying it;
  - **(c)** map the relations, not the surface features.
- A Pólya-style checklist is worth encoding mainly as metacognitive checkpoints: "Do I understand the unknown? Have I seen a related problem? Can I check the result?" It is not a recipe.

### Gaps
- No controlled evidence was retrieved for:
  - inversion (Jacobi's "invert, always invert"; Munger);
  - first-principles reasoning as a trained method;
  - working backwards as a taught heuristic;
  - Kauffman / Steven Johnson's "adjacent possible".

  These should be labelled as practitioner heuristics or concepts in the skill unless another pass finds evidence. The "adjacent possible" is a descriptive concept from theoretical biology and innovation history, not a solving technique.
- Constraint *addition* — evidence that imposing constraints raises creativity, e.g. Haught-Tromp 2017 "Green Eggs and Ham hypothesis", Stokes 2005, Acar et al. 2019 review — was not retrieved. It is recalled, so treat it as UNVERIFIED.
- Constraint *removal* is supported indirectly by constraint relaxation (section 1).

---

## 5. Behavioural / "psycho-logic" solutions: Sutherland; the Behavioural Insights Team

### Takeaway
Sometimes the cheapest solution changes perception or behaviour instead of engineering, as with the elevator mirrors or wifi instead of faster trains. Sutherland's examples are argument and anecdote. Nudge-unit RCTs show that the approach works, but at a much smaller scale than the academic literature suggests. The average effect in nudge-unit trials is 1.4 percentage points, against 8.7 in published papers. A publication-bias-corrected meta-analysis puts the average near zero, with large heterogeneity. Some single cases are large, such as the UK tax letters (about +15 pp).

### Cited Findings
- **Sutherland.** In a 2008 *Spectator* column, Rory Sutherland argued that about £6 billion was spent to cut the Eurostar journey by roughly an hour, when a few million pounds on wifi would have improved the journey more. The "supermodels serving free Château Pétrus for 10% of the cost" version comes from his 2009 TED talk — [Spectator, "The Wiki Man", 2008-04-19](https://spectator.com/article/the-wiki-man-19-april-2008/); [Behavioral Grooves](https://behavioralgrooves.com/?p=726) **[an argument, not a measured case; the "psycho-logic" term is from *Alchemy* (2019), and the exact book quotes were not verified]**
- **BIT / HMRC tax letters.** A randomised trial with about 140,000 delinquent taxpayers measured the share who paid:

  | Letter | Paid |
  |---|---|
  | Control | 67.5% |
  | National social norm ("9 out of 10 pay on time") | 72.5% |
  | Postcode norm | 79% |
  | Home-town norm | 83% |

  — [Policy Options (IRPP), 2013-06](https://policyoptions.irpp.org/2013/06/making-inroads/); [Tax Policy Center](https://taxpolicycenter.org/taxvox/can-behavioral-science-improve-tax-compliance). The academic write-up is Hallsworth, List, Metcalfe & Vlaev (2017), *J. Public Economics*. **Conflicting figure:** a getAbstract summary gives 35.8% → 37.8% [getAbstract](https://www.getabstract.com/fr/resume/the-power-of-experiments/39145). This may come from a different trial or outcome measure, and the primary paper was not retrieved.
- A local replication at Medway Council found that a social-norm letter raised council-tax payments by 19% and a diagram letter by 13% — [LGA case study](https://www.local.gov.uk/case-studies/using-behavioural-insights-collect-council-tax-collection-medway-council)
- **Scale reality.** DellaVigna & Linos (2022), "RCTs to Scale", *Econometrica* 90(1), 81–116, covered 126 RCTs with more than 23 million people from two US nudge units. The average effect was **1.4 pp** (about 8% over control). Nudges published in academic journals averaged **8.7 pp** (about 33%). About 70% of the gap is explained by selective publication combined with low power — [Econometrica 2022](https://www.econometricsociety.org/publications/econometrica/2022/01/01/rcts-scale-comprehensive-evidence-two-nudge-units); [NBER w27594](https://nber.org/papers/w27594)
- **Meta-analytic dispute.** Mertens et al. (2022, *PNAS*) pooled d = 0.43 from 447 effect sizes in 212 publications. Maier et al. (2022, *PNAS*, DOI 10.1073/pnas.2200300119) corrected for publication bias with RoBMA and obtained d ≈ 0.04, "no evidence for nudging" on average. Critics, including Data Colada, note that the average across very heterogeneous interventions is close to meaningless; some nudges work and many don't — [PMC9351501, Maier et al. 2022-07-19](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9351501/); [Behavioral Scientist explainer](https://behavioralscientist.org/making-sense-of-the-do-nudges-work-debate/)

### Inferences
- Encode a "perception and behaviour lens" for the agent: "Could the problem be solved by changing how it is perceived, defaults, timing, the messenger, social proof or friction, rather than by building more capability?" This is a legitimate reframing move, the elevator mirrors in general form.
- Pair the lens with an evidence caveat: expect small effects (1–2 pp at scale) unless the case is like the tax letters, and recommend testing (A/B or RCT) rather than assuming.
- Sutherland's examples are useful for showing the *form* of a solution. They shouldn't be cited as proof that such solutions work.

### Gaps
- The original BIT/HMRC report and Hallsworth et al. (2017) figures were not retrieved, so the 35.8% → 37.8% conflict remains unresolved.
- No measured evaluation of the "elevator mirror" type of perception fix was found.
- Sutherland's *Alchemy* was not read directly.

---

## 6. What separates expert solvers from novices

### Takeaway
Experts represent a problem by its deep structure, the governing principles, while novices represent it by surface features. Expertise also brings stronger Einstellung: experts are more prone to fix on a familiar good-enough solution, and they don't notice the narrowing of their attention. Expert solving is therefore deliberate representation plus a guard against one's own first pattern match.

### Cited Findings
- Chi, Feltovich & Glaser (1981), "Categorization and representation of physics problems by experts and novices", *Cognitive Science* 5(2), 121–152. Eight experts (physics PhD students) and eight novices sorted 24 problems. Novices grouped them by surface features: the objects, the terms, the physical configuration, e.g. "inclined plane". Experts grouped them by the physics principle needed, e.g. conservation of energy — [DTIC report ADA100301](https://apps.dtic.mil/sti/pdfs/ADA100301.pdf); [ASU LCL](https://education.asu.edu/lcl/publications/chi-m-t-h-feltovich-p-glaser-r-1981-categorization-and-representation-physics)
- Replications show that advanced novices sort by a mixture of deep and surface features — [arXiv 1602.08781](https://arxiv.org/pdf/1602.08781) (2016)
- Expertise does not immunise against Einstellung. Expert chess players' attention stayed on the familiar solution while they reported searching for alternatives (Bilalić et al. 2008/2010). When the familiar move was a blunder, experts avoided it; when it was merely suboptimal, they did not (Sheridan & Reingold 2013) — [Bilalić 2010 PDF](https://cognition.aau.at/download/Publikationen/Bilalic/Bilalic_etal_2010b.pdf); [PMC3790829](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3790829/)
- Analogy research agrees: transfer depends on encoding the *relational* structure (schema), not surface similarity (Gick & Holyoak 1983) — [UMich Deep Blue](https://deepblue.lib.umich.edu/items/196ea13e-fb69-4a74-a6f9-864c81aed465)

### Inferences
- Agent rules that follow from this:
  - **(1)** Before solving, classify the problem by its underlying principle or mechanism, not by its domain vocabulary. "This is a queueing or perceived-wait problem", not "this is an elevator problem".
  - **(2)** Decompose the problem into sub-problems and parts. This parallels chunk decomposition and GPT.
  - **(3)** Since LLMs behave like experts with strong priors, apply an explicit "good-enough trap" check: after the first workable solution, generate at least one structurally different alternative and compare them before choosing.
  - **(4)** Know when to drop constraints. Classify each constraint as hard (from the requester or physics) or soft (habit or assumption), and relax the soft ones, narrowest first, when stuck (Knoblich et al. 1999).

### Gaps
- Direct evidence on *how* experts decide to drop constraints (e.g., Schön's reflective practice, Dorst's design frame creation, Cross's work on expert designers) was not retrieved in this pass and would strengthen this section.
- No study comparing expert and novice *reframing* behaviour specifically was found.
