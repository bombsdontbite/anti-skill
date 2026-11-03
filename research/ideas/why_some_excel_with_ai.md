# Why some people get remarkable results with AI and others don't

Research date: 2026-10-26. The notes are in English and the final report will be in Russian. Each source carries its date. Where a page could not be fetched (HTTP 403) and a figure comes from a secondary summary or from memory, the entry says so.

---

## 1. Well-documented cases of exceptional AI-assisted work: what the human did and what the AI did

### Takeaway
In every well-documented case, the AI did the generating and the human did everything that decides quality. The human chose the problem, generated far more output than was used, selected from it ruthlessly, did post-production and engineering around the output, and supplied distribution. The more detailed the account, the larger the human share turns out to be.

### Cited Findings
**Film: "Air Head" by shy kids, an early Sora short (2024).**
- Patrick Cederberg said it took "hundreds of generations" to get just under 1.5 minutes of edit. — [Notebookcheck, 2024](https://www.notebookcheck.net/OpenAI-s-Sora-finicky-to-work-with-needs-hundreds-of-prompts-serious-VFX-work-for-under-2-minutes-of-cohesive-story.831515.0.html)
- He estimated the ratio of source footage to final cut at about 300:1, so roughly 0.33% of the output was used. This number comes from reporting based on his fxguide interview, and the fxguide original was not fetched. — [Notebookcheck DE, 2024](https://www.notebookcheck.com/Produzent-des-KI-Kurzfilms-Air-Head-Sora-von-OpenAI-erfordert-hunderte-von-Prompts-und-viel-VFX-Arbeit.832639.0.html)
- The team still had to do conventional post-production: upscaling, stabilisation, colour correction, retiming and VFX to remove unwanted elements. Sora kept producing different balloon heads, so shot-to-shot consistency was a manual fight. The edit was built "found footage" style, by cutting many shots against the voice-over. — [heise, 2024](https://heise.de/-9707198); [CGPress, 2024](https://cgpress.org/archives/shy-kid-on-using-sora-to-create-air-head.html)

**Art: Jason Allen, "Théâtre D'opéra Spatial" (2022 Colorado State Fair winner).**
- His lawsuit says the image went through 624 iterations with Midjourney plus Photoshop work. Reported effort is about 80 hours in one account and more than 110 hours in another. — [Xataka MX](https://www.xataka.com.mx/robotica-e-ia/creador-esta-imagen-uso-photoshop-624-prompts-no-le-conceden-copyright-al-considerarla-obra-ia); [CPR, 2023-09-06](https://cpr.org/2023/09/06/jason-allens-ai-art-won-colorado-fair-feds-deny-copyright-protection/)
- The US Copyright Office refused registration because he would not disclaim the AI-generated portions. The outcome of the lawsuit is not confirmed here. — [CPR, 2023-09-06](https://cpr.org/2023/09/06/jason-allens-ai-art-won-colorado-fair-feds-deny-copyright-protection/)

**Software: Andrej Karpathy, MenuGen (2025-04-27).**
- He wrote no code himself; Cursor and Claude wrote all of it. The local prototype took "very little time." Most of the effort went to things outside the code:
  - API keys and deprecated APIs that the LLM suggested;
  - Vercel environment variables;
  - Clerk authentication, which needed a custom domain, DNS changes and Google OAuth;
  - Stripe, where Claude first matched payments to users by email, a flawed design he had to catch.
- He compares the process to assembling flat-pack furniture. He calls vibe-coded full apps "not a good idea for anything of actual importance" while seeing "clear hints of greatness." — [Karpathy blog, 2025-04-27](https://karpathy.bearblog.dev/vibe-coding-menugen/)

**Software: Karpathy, nanochat (October 2025).**
- He said the repo was "basically entirely hand-written (with tab autocomplete)." He tried agents several times and found them "net unhelpful," possibly because the code is "too far off the data distribution." — [Simon Willison, 2025-10-18](https://simonwillison.net/2025/Oct/18/agi-is-still-a-decade-away/); [ProPakistani, 2025-10-20](https://propakistani.pk/2025/10/20/openai-co-founder-abandons-ai-tools-to-build-chatbot-by-hand/amp/)
- The person who coined "vibe coding" (February 2025) does not use it for novel, dense, hard-to-evaluate code. A commentator reads this as a statement about reliability on unusual code, not as Karpathy giving up on AI coding. — [36kr](https://eu.36kr.com/en/p/3508936344689539)

**Games: Pieter Levels, fly.pieter.com (February–March 2025).**
- He got the first playable version in about three hours of prompting in Cursor, with Three.js. Reports disagree on which model he used (Claude Sonnet 3.7 or Grok 3). — [Indie Hackers](https://www.indiehackers.com/post/pieter-levels-used-ai-to-build-a-viral-flight-simulator-in-3-hours-with-no-background-in-game-development-7CPfMr1yRLEwH6cC8xhE)
- Revenue is self-reported. He posted $87k MRR (about $1M ARR). Another outlet put it near $52k a month, of which only about $360 came from in-game purchases; the rest was ads sold inside the game. — [Indie Hackers](https://www.indiehackers.com/post/pieter-levels-used-ai-to-build-a-viral-flight-simulator-in-3-hours-with-no-background-in-game-development-7CPfMr1yRLEwH6cC8xhE)
- 404 Media's headline: "This game created by AI vibe coding makes $50,000 a month. Yours probably won't." — [404 Media, Emanuel Maiberg, 2025-03-05](https://404media.co/this-game-created-by-ai-vibe-coding-makes-50-000-a-month-yours-probably-wont)
- Coverage attributes the reach to his very large audience and a retweet from Elon Musk. A DEV post headline says revenue "went to zero"; that claim is unverified. — [Indie Hackers](https://www.indiehackers.com/post/pieter-levels-used-ai-to-build-a-viral-flight-simulator-in-3-hours-with-no-background-in-game-development-7CPfMr1yRLEwH6cC8xhE); [DEV](https://dev.to/promptway/he-built-a-flight-simulator-in-three-hours-and-hit-1m-a-year-in-17-days-then-it-went-to-zero-1b1l)

**Software: Simon Willison, "vibe engineering" (2025-10-07; by February 2026 he notes "agentic engineering" as the more common term).**
- His thesis is that "AI tools amplify existing expertise."
- The practices that make senior engineers effective with agents:
  - automated tests, so the agent can verify its own work;
  - planning up front;
  - good documentation;
  - disciplined version control;
  - CI, linting and other automation;
  - a culture of code review;
  - management skills: clear instructions, context and actionable feedback;
  - manual QA;
  - research before coding;
  - preview environments;
  - knowing what to outsource;
  - re-estimating work.
- His framing is that the engineer stays "proudly and confidently accountable for the software they produce." — [Simon Willison, 2025-10-07](https://simonwillison.net/2025/Oct/7/vibe-engineering/)

**Software: Boris Cherny, creator of Claude Code. These details are secondhand write-ups of interviews and posts, not his originals.**
- He starts most sessions in plan mode and iterates until the plan is right, then lets the agent run.
- "Give Claude a way to verify its work… it will 2-3x the quality." Verification here means testing the product as a user would, not only running a test suite.
- He runs many sessions in parallel; one write-up says up to 15.
- His CLAUDE.md is about 100 lines, and each recurring mistake gets added to it.
- Routine work (code review, PR babysitting, CI fixes, rebasing) has moved into automated routines.
- Sources: [Karo Zieminski, Substack](https://karozieminski.substack.com/p/boris-cherny-claude-code-workflow); [The Neuron](https://theneuron.ai/explainer-articles/claude-code-creators-boris-cherny-and-cat-wu-explain-how-to-use-agent-loops/). The "2-3x" figure is his own estimate, not a measurement.

### Inferences
- Allen's 624 iterations and Air Head's roughly 300:1 ratio mean the visible artefact is the top fraction of a percent of what was generated. The skill that matters is selecting, not prompting, and it costs tens of hours even for a single image.
- The Levels case is mostly about distribution, not code. The game is technically simple; the revenue came from an audience he built over years, which turned into advertisers. That cannot be copied by copying the workflow.
- The two Karpathy cases mark the boundary. AI excels at a throwaway prototype in a mainstream stack. It struggles with production plumbing (auth, payments, deployment, the browser) and with novel, off-distribution code. A privacy-critical app with a strict quality bar sits mostly in the second zone.

### Gaps
- I did not fetch the fxguide original for the 300:1 figure.
- I found no independent audit of Levels' revenue; all figures trace back to his own posts.
- I did not find detailed, verified process write-ups for notable AI-made games beyond Levels, or for the long-form AI films of 2025–26 (for example "Critterz"). They were not searched in depth.

---

## 2. Evidence on expertise and taste: does AI help novices and experts differently?

### Takeaway
On narrow, well-defined tasks, the strong and repeated finding is that AI lifts low performers and novices most. On open-ended tasks, such as business decisions, research ideas or writing outside one's field, the benefit depends on whether the person has enough nearby expertise to judge and repair the output. Without that judgment, AI gives no help or makes results worse. The flagship "experts benefit most" study (MIT materials science) was disavowed by MIT and must not be cited.

### Cited Findings
**Dell'Acqua et al., BCG and HBS, "Navigating the Jagged Technological Frontier".**
- Working paper: September 2023. Published in *Organization Science*, March–April 2026, DOI 10.1287/orsc.2025.21838. — [AOM post on the issue, 2026](https://ent.aom.org/discussion/march-april-2026-issue-of-organization-science-3)
- 758 BCG consultants (7% of the consulting force) used GPT-4 on tasks inside the AI's frontier. They completed 12.2% more tasks, 25.1% faster, with more than 40% higher quality. — [Ethan Mollick, One Useful Thing, 2023-09-16](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)
- The lowest-scoring consultants at baseline gained most, about 43%; top performers gained less. Their exact figure is not in Mollick's post; I recall 17% from the abstract but could not verify it because SSRN and HBS returned 403. — [Mollick, 2023-09-16](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)
- On a task just outside the frontier, consultants without AI were correct 84% of the time and those with AI 60–70% of the time. The paper's abstract frames this as 19 percentage points less likely to be correct; I could not fetch the abstract to confirm. — [Mollick, 2023-09-16](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)
- Two successful patterns appeared:
  - **Centaurs** divide the labour strategically. They do what they are strongest at and hand in-frontier subtasks to the AI.
  - **Cyborgs** interleave their work with the AI's at a fine grain, moulding, checking and refining its responses.
  - Source: [Mollick, 2023-09-16](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)

**Brynjolfsson, Li and Raymond, "Generative AI at Work".**
- Working paper: NBER, April 2023, 5,179 customer-support agents. Issues resolved per hour rose 14% on average and 34% for novice and low-skill agents, with minimal impact on experienced, high-skill agents. — [NBER w31161](https://www.nber.org/papers/w31161)
- Published version: QJE 2025, 5,172 agents, 15% average gain. — [SSRN](https://papers.ssrn.com/abstract=4426942)
- Mechanism: the AI spreads the tacit best practices of the top agents to newer ones. — [Stanford HAI](https://hai.stanford.edu/news/will-generative-ai-make-you-more-productive-work-yes-only-if-youre-not-already-great-your-job)

**Noy and Zhang, *Science*, July 2023.**
- 453 college-educated professionals did occupation-specific writing tasks. With ChatGPT, time fell 40% and quality rose 18%, and inequality between workers shrank. ChatGPT mostly substituted for effort rather than complementing skill. — [MIT Economics news, 2023](https://economics.mit.edu/news/study-finds-chatgpt-boosts-worker-productivity-some-writing-tasks)
- Limitation: the tasks needed no factual accuracy or company context, and the output was not fact-checked. — [MIT Economics news, 2023](https://economics.mit.edu/news/study-finds-chatgpt-boosts-worker-productivity-some-writing-tasks)

**Otis, Clarke, Delecourt, Holtz and Koning, Kenyan entrepreneurs (HBS working paper, 2024).**
- A GPT-4 business mentor delivered over WhatsApp had no significant effect on average.
- High performers gained just over 15%. Low performers lost about 8% of revenue (reported as 10% by HBS Working Knowledge and 7.5% by Wharton).
- Both groups asked a similar number of questions. The high performers asked about tractable problems; the strugglers asked about harder ones and could not filter the advice.
- Sources: [Berkeley Haas, 2024-04-01](https://newsroom.haas.berkeley.edu/research/gen-ai-experiment-shows-mixed-results-in-helping-small-businesses-grow/); [HBS Working Knowledge](https://www.library.hbs.edu/working-knowledge/what-happens-when-business-owners-turn-to-chatbots-for-advice); [HKS CID](https://www.hks.harvard.edu/centers/cid/publications/uneven-impact-generative-ai-entrepreneurial-performance)

**Vendraminelli et al., "The GenAI Wall Effect" (Stanford and HBS D^3; working paper 2025; HBR article 2026-04-16).**
- 78 IG Group employees conceptualised and wrote articles. On conceptualising, AI closed the gap: marketers with AI (4.18) slightly beat expert writers with AI (4.12).
- On the writing itself, developers and data scientists ("distant outsiders") got essentially nothing from AI: 3.42 without, 3.38 with. Many pasted the AI output in without being able to judge or refine it.
- The authors' conclusion is that AI's benefit depends on how close the user's expertise is to the task. — [Physician Leaders summary of the HBR piece, 2026](https://www.physicianleaders.org/articles/gen-ai-wont-make-your-employees-experts)

**Trobinger, Doshi and Chai, *Research Policy* 55 (2026) 105575.**
- 310 researchers were randomised to see zero, one or three AI-generated research suggestions.
- Less experienced researchers adopted the suggestions more often and rated them as novel and impactful.
- More experienced researchers judged them as already considered, not ambitious enough, or lacking context.
- Source: [Unite.AI, 2026-07-28](https://www.unite.ai/?p=442595)

**Cui, Demirer, Jaffe, Musolff, Peng and Salz, three Copilot field RCTs (Microsoft, Accenture, a Fortune 100 firm; about 5,000 developers; *Management Science*).**
- Completed pull requests rose about 26% overall.
- Juniors and new hires gained more (reported as 21–40%) than seniors (7–16%).
- At Microsoft, only 44.2% adopted the tool within 29 weeks, and most intent-to-treat estimates there were not significant.
- Sources: [AEA trial registry](https://www.socialscienceregistry.org/trials/14530); [INFORMS supplement](https://pubsonline.informs.org/doi/suppl/10.1287/mnsc.2025.00535/suppl_file/mnsc.2025.00535.sm1.pdf). The junior and senior percentages come from secondary summaries.

**Doshi and Hauser, *Science Advances*, 2024-07-12.**
- About 300 writers in the experiment (500 participants recruited on Prolific). With AI story ideas, judges rated the stories more creative, better written and more enjoyable, and the gain was largest for the least creative writers.
- AI-assisted stories were more similar to each other. Writers are individually better off while the collective pool of novel content narrows.
- Writers using AI did not rate their own stories higher, although external judges did.
- Sources: [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532); [PsyPost](https://psypost.org/new-study-on-ai-assisted-creativity-reveals-an-interesting-social-dilemma)

**Disavowed evidence: Toner-Rodgers, "Artificial Intelligence, Scientific Discovery, and Product Innovation" (MIT, 2024).**
- The paper claimed 44% more materials and 39% more patents, with the top scientists gaining most because of their judgment.
- On 2025-05-16, MIT said it had "no confidence in the provenance, reliability or validity of the data" and asked for withdrawal. The author is no longer at MIT, and the preprint was later reported withdrawn from arXiv.
- Sources: [TechCrunch, 2025-05-17](https://techcrunch.com/2025/05/17/mit-disavows-doctoral-students-paper-on-ai-productivity-benefits); [The Decoder](https://the-decoder.com/mit-says-a-high-profile-ai-productivity-study-used-data-that-cannot-be-trusted/); [Science|Business](https://sciencebusiness.net/news/ai/research-commissioner-appears-cite-discredited-study-ai-speech)
- Commentary still cites it as evidence that "experts benefit most." — [Juan Hevia, Substack](https://juanhevia.substack.com/p/productivity-is-a-positive-sum-game)

### Inferences
- **The two findings reconcile.** On standardised tasks with a known good answer (support tickets, short business writing, in-frontier consulting tasks), AI levels people up. On open-ended creative or product work with no known answer, the bottleneck becomes judging the output, and judgment comes from nearby expertise. The Otis, Wall Effect and Trobinger results all point this way. A person who can tell good from bad gets value; a person who cannot either pastes the output in or adopts mediocre ideas as "novel."
- **The self-assessment gap is a consistent theme:**
  - Doshi and Hauser: writers did not see the quality gain that judges saw.
  - Trobinger et al.: novices over-rated the AI's ideas.
  - METR (section 4): developers believed they were faster when they were slower.
  - People are poor judges of their own AI-assisted output, in both directions.
- **For a solo developer working outside their core expertise** (design, copywriting, marketing, game feel), the Wall Effect predicts the smallest AI uplift exactly in the areas they know least. A domain-expert reviewer or explicit external references substitute for missing taste.
- **Homogenisation** (Doshi and Hauser) means default outputs converge across users. A remarkable result requires pushing away from the model's default.

### Gaps
- I could not fetch the primary Dell'Acqua abstract or paper, so the 17% figure for above-average performers and the 19-percentage-point outside-frontier drop rest on recall and secondary sources.
- I found no rigorous, non-retracted RCT showing that domain experts gain more than novices on creative tasks. Expert advantage appears as better filtering and skepticism, not as a measured larger uplift.

---

## 3. Workflows that recur among high performers

### Takeaway
The recurring pattern is a loop in which the human controls each step:
- frame the problem and the context;
- generate many variants;
- select ruthlessly by human taste;
- verify with a feedback signal the AI cannot fake;
- fix and record the lessons.

Top performers invest most heavily in the verification and selection steps, not in clever prompts.

### Cited Findings
- **Many generations and ruthless selection.** Air Head used about 300:1 footage to final cut and "hundreds of generations" ([Notebookcheck](https://www.notebookcheck.net/OpenAI-s-Sora-finicky-to-work-with-needs-hundreds-of-prompts-serious-VFX-work-for-under-2-minutes-of-cohesive-story.831515.0.html)). Allen made 624 iterations ([CPR](https://cpr.org/2023/09/06/jason-allens-ai-art-won-colorado-fair-feds-deny-copyright-protection/)).
- **Heavy human post-processing.** Air Head needed colour, retiming, stabilisation, VFX cleanup and a found-footage edit ([heise](https://heise.de/-9707198)). Allen did Photoshop work ([Xataka](https://www.xataka.com.mx/robotica-e-ia/creador-esta-imagen-uso-photoshop-624-prompts-no-le-conceden-copyright-al-considerarla-obra-ia)).
- **Verification loops as the main quality lever.** Willison: without tests an agent "may claim something works" when it has not been tested ([Willison, 2025-10-07](https://simonwillison.net/2025/Oct/7/vibe-engineering/)). Cherny (secondhand): verification that tests the product as a user would "2-3x the quality" ([Substack summary](https://karozieminski.substack.com/p/boris-cherny-claude-code-workflow)).
- **Plan first, then execute.** Willison lists planning in advance ([Willison](https://simonwillison.net/2025/Oct/7/vibe-engineering/)). Cherny iterates in plan mode until the plan is right, and then the agent can often finish in one pass ([Smithery skill page](https://smithery.ai/skills/llcoolblaze/boris-workflow)).
- **Rich, concise context that is updated from mistakes.** Cherny keeps a CLAUDE.md of about 100 lines and adds every recurring mistake to it ([mejba.me](https://www.mejba.me/blog/boris-cherny-claude-code-workflow)). Willison counts documentation as a force multiplier ([Willison](https://simonwillison.net/2025/Oct/7/vibe-engineering/)).
- **The human as manager and reviewer, not typist.** Willison: management skills and fast code review predict success ([Willison](https://simonwillison.net/2025/Oct/7/vibe-engineering/)). In the BCG study, both successful patterns (centaur division of labour and cyborg fine-grained checking) keep the human checking the output ([Mollick](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)).
- **Knowing where the frontier is.** In Dell'Acqua, falling asleep at the wheel outside the frontier cost correctness ([Mollick](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)). Karpathy drops agents for off-distribution code ([Willison, 2025-10-18](https://simonwillison.net/2025/Oct/18/agi-is-still-a-decade-away/)). Willison names "knowing what to outsource" as a skill ([Willison](https://simonwillison.net/2025/Oct/7/vibe-engineering/)).
- **Asking AI about tractable sub-problems, not the hardest open question.** This is what separated Otis's high performers from the low performers ([Berkeley Haas](https://newsroom.haas.berkeley.edu/research/gen-ai-experiment-shows-mixed-results-in-helping-small-businesses-grow/)).
- **Organisational foundations amplify gains.** DORA 2025 (nearly 5,000 respondents): "AI's primary role is that of an amplifier," magnifying the strengths of high performers and the dysfunctions of struggling teams. The biggest returns come from the internal platform, workflow clarity and alignment. — [DORA 2025 report PDF](https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf); [Google Cloud blog](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report); [InfoQ, September 2025](https://www.infoq.com/news/2025/09/dora-state-of-ai-in-dev-2025). Caveat: the survey sample is self-selected.

### Inferences
- **Iterate and select applies to creative work.** Both creative cases spend most of their effort on human selection and post-processing; generation is the cheap part.
- **For code, the analogue of selection is verification.** That means tests, previews and hands-on QA. It explains why the gains concentrate among engineers who already had these habits, which is the "amplifier" thesis from both DORA and Willison.
- **What I found little evidence for.** None of the strong sources treat "a secret prompt," "the right model" or "more agents in parallel" as the main differentiator. Mixing models appears only incidentally (Levels reportedly used Claude and Grok). I found no rigorous evidence that multi-model or AI-as-critic setups by themselves drive exceptional results.

### Gaps
- I found no controlled study isolating particular workflow elements (many generations versus few, AI-as-critic, strong constraints) and measuring their effect on creative quality in the wild.
- The Cherny workflow details are secondhand. I did not locate his original posts.

---

## 4. Survivorship bias, demo-ware and exaggeration

### Takeaway
A substantial share of the "unreal" AI results on social media is selected, staged, self-reported or unrepeatable:
- Prominent demos have been shown to be edited or misrepresented.
- The most rigorous field RCT found experienced developers 19% slower with AI while they believed they were 20% faster.
- A highly cited "AI super-boost" study was disavowed for untrustworthy data.
- Viral revenue stories rest on unaudited self-reports and pre-existing audiences.
- Many fast-built apps hide production flaws.

### Cited Findings
**METR randomized trial (early 2025).** Experienced open-source developers took about 19% longer with AI tools (CI +2% to +39%). Afterwards they estimated AI had made them about 20% faster. — [METR, 2026-02-24 update](https://metr.org/blog/2026-02-24-uplift-update/); [ScienceBlog](https://scienceblog.com/t-a-randomized-trial-by-metr-found-that-experienced-developers-completed-real-coding-tasks-19-slower-when-allowed-to-use-ai-tools-yet-afterwards-they-estimated-on-average-that-ai-had-made-them-20-fast/)
- Original setup: 16 developers, 246 tasks, mature repositories they knew well. — [METR, 2025-07-10](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) (not re-fetched in this session; the 16 and 246 figures are from memory of that post)

**METR follow-up (published 2026-02-24).**
- 57 developers (10 returning, 47 new), 143 repositories, more than 800 tasks, from August 2025.
- Point estimates: an 18% speedup for returning developers (CI −38% to +9%) and 4% for new ones (CI −15% to +9%).
- METR calls the data an unreliable signal. Developers refused to take part because they did not want to work without AI, and 30–50% skipped tasks they did not want to do without AI.
- METR thinks the true speedup is probably larger now and that these figures are lower bounds, but calls its own evidence for that "very weak."
- METR now labels the 2025 result historical.
- Source: [METR, 2026-02-24](https://metr.org/blog/2026-02-24-uplift-update/)

**Stack Overflow Developer Survey 2025 (more than 49,000 responses).**
- 84% use or plan to use AI.
- 46% distrust the accuracy of AI tools and 33% trust it; 3% "highly trust."
- The top frustration is "AI solutions that are almost right, but not quite." The share is reported as 66% in coverage and 45% elsewhere, and the two figures may come from different questions.
- 45.2% say debugging AI code takes longer.
- Sources: [Stack Overflow blog, 2025-07-29](https://stackoverflow.blog/2025/07/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here); [VentureBeat](https://venturebeat.com/ai/stack-overflow-data-reveals-the-hidden-productivity-tax-of-almost-right-ai-code)

**Staged and misrepresented demos.**
- Google's Gemini "hands-on" demo (December 2023) was reported by TechCrunch as "pretty much faked." Google acknowledged it prompted the model with still frames and text, not live video. — [TipRanks/The Fly citing TechCrunch](https://www.tipranks.com/news/the-fly/googles-impressive-gemini-demo-faked-techcrunch-reports)
- Cognition's Devin (March 2024): the "Internet of Bugs" analysis of the Upwork demo found Devin did not deliver what the client asked for, and the claimed time did not match. One review was more measured: impressive, but it did not finish the job. — [80.lv](https://80.lv/articles/first-ai-software-engineer-creators-are-accused-of-lying/); [gun.io, May 2024](https://gun.io/news/2024/05/devin-ai/); [Sally Liu, "Anatomy of a viral product video"](https://sallysliu.substack.com/p/devins-viral-recipe)

**The disavowed MIT "AI scientist productivity" paper.** See section 2. — [TechCrunch, 2025-05-17](https://techcrunch.com/2025/05/17/mit-disavows-doctoral-students-paper-on-ai-productivity-benefits)

**Self-reported revenue and audience effects.** Levels' figures are self-reported and inconsistent ($87k MRR versus about $52k a month), and the reach came through his large audience and a retweet from Musk ([Indie Hackers](https://www.indiehackers.com/post/pieter-levels-used-ai-to-build-a-viral-flight-simulator-in-3-hours-with-no-background-in-game-development-7CPfMr1yRLEwH6cC8xhE)). 404 Media's headline was "yours probably won't" ([404 Media, 2025-03-05](https://404media.co/this-game-created-by-ai-vibe-coding-makes-50-000-a-month-yours-probably-wont)).

**Demo-ware that hides production flaws.**
- In 2025, researcher Matt Palmer scanned 1,645 Lovable-built apps and found 170 exposing user data (names, emails, financial information, API keys) through missing or insufficient Supabase Row Level Security. This is CVE-2025-48757, CVSS about 8.26–9.3 depending on the source. — [Superblocks](https://www.superblocks.com/blog/lovable-rls-breach); [Gigazine, 2025-06-02](https://gigazine.net/gsc_news/en/20250602-loveable-ai-made-service-vulnerability)
- A separate platform-level Lovable access-control incident was disclosed on 2026-04-20; its scope is disputed. — [Bastion](https://bastion.tech/blog/lovable-april-2026-data-breach)
- Karpathy's MenuGen: the demo was fast, the production plumbing slow ([Karpathy, 2025-04-27](https://karpathy.bearblog.dev/vibe-coding-menugen/)).

**Generation-to-publish ratios.** Air Head used about 0.33% of its generated footage. Social feeds show the selected output, not the hundreds of discarded generations or the hours of post-production ([Notebookcheck DE](https://www.notebookcheck.com/Produzent-des-KI-Kurzfilms-Air-Head-Sora-von-OpenAI-erfordert-hunderte-von-Prompts-und-viel-VFX-Arbeit.832639.0.html)).

### Inferences
- **Several filters stack between reality and the feed:**
  - selection of the best output, often under 1%;
  - selection of the best people (those with an audience, expertise or luck);
  - selection of the best moment (a demo, not month six of maintenance);
  - self-report of results;
  - a perception bias, since even experts overestimate their AI speedup (METR).
- **"It works for them but not for us" is the expected result of comparing yourself with the filtered tail of a distribution.** It is not by itself evidence of doing something wrong.
- **The METR caveat cuts both ways.** By early 2026, METR thinks agents probably speed developers up. Refusing to work without AI is itself a signal. But the measured effects are modest, with wide intervals, far from the "10x" in social posts.
- **The setting matters.** Measured gains are smallest in mature codebases with high quality standards that developers know deeply, where tacit context matters most (the METR 2025 setting). A privacy-critical monorepo with strict gates resembles that setting more than a greenfield weekend toy does.

### Gaps
- I found no systematic study that quantifies what share of viral AI-built claims on X or YouTube are exaggerated.
- I could not verify the 2026 status of individual viral claims, including whether fly.pieter.com revenue fell.
- I did not fetch the original TechCrunch Gemini article or the Internet of Bugs video; both are cited through secondary coverage.

---

## 5. Common failure patterns of people who get generic results

### Takeaway
Generic or mediocre results follow from five habits:
- accepting the first or default output (homogenisation);
- working outside one's own expertise without a way to judge quality, which leads to pasting the output in;
- asking the AI about the hardest open questions and trusting the answer;
- applying AI past its frontier without noticing;
- having no verification signal, so "almost right" output ships.

### Cited Findings
- **Default outputs converge.** AI-assisted stories are more similar to each other ([Doshi and Hauser, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532)).
- **No judgment, no gain.** Distant outsiders saw no improvement in writing quality with AI (3.42 to 3.38), and many pasted the output in unrefined ([Wall Effect / HBR, 2026](https://www.physicianleaders.org/articles/gen-ai-wont-make-your-employees-experts)).
- **Low performers asked AI about harder problems and lost revenue,** about 8% ([Berkeley Haas, 2024](https://newsroom.haas.berkeley.edu/research/gen-ai-experiment-shows-mixed-results-in-helping-small-businesses-grow/)).
- **Novices over-rate AI ideas.** Less experienced researchers adopted AI suggestions and rated them as novel; experienced ones saw them as already considered or unambitious ([Trobinger, Doshi and Chai, 2026](https://www.unite.ai/?p=442595)).
- **Going past the frontier drops correctness,** from 84% to 60–70% on an outside-frontier task ([Mollick, 2023](https://www.oneusefulthing.org/p/centaurs-and-cyborgs-on-the-jagged)).
- **"Almost right" output is the top developer frustration,** and 45% say AI code takes longer to debug ([Stack Overflow 2025](https://stackoverflow.blog/2025/07/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here)).
- **No tests means false claims of success.** Without tests an agent may claim something works that was never tested ([Willison, 2025](https://simonwillison.net/2025/Oct/7/vibe-engineering/)).
- **Off-distribution work defeats agents.** Novel, dense code is where agents were "net unhelpful" for Karpathy ([Willison, 2025-10-18](https://simonwillison.net/2025/Oct/18/agi-is-still-a-decade-away/)).
- **Weak foundations get amplified.** AI magnifies dysfunctions, and local productivity gains are absorbed by downstream problems ([DORA 2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)).
- **Production plumbing hides subtle design errors.** Claude matched payments to users by email ([Karpathy, 2025](https://karpathy.bearblog.dev/vibe-coding-menugen/)). Missing Row Level Security exposed data in 170 Lovable apps ([Superblocks](https://www.superblocks.com/blog/lovable-rls-breach)).

### Inferences
- **The bottleneck is judgment plus feedback loops, not the AI's ability to generate.** The same model gives remarkable results to someone who can generate many variants, recognise the best one, verify it cheaply and knows where the frontier lies, and generic results to someone who cannot.
- **For a solo developer with agents, the likely levers are:**
  - cheap, user-level verification of each change (previews, hands-on checks, not only unit tests);
  - more variants generated and compared in creative and product decisions, instead of accepting the first;
  - external references and taste-holders in areas where they lack expertise (visual design, copy, marketing);
  - applying agents to in-frontier, mainstream tasks while doing novel or critical design themselves;
  - comparing yourself with measured averages (METR, DORA, the RCTs), not with the viral tail.
- **Process overhead is a hypothesis, not a finding.** A heavily gated, high-standard workflow may land in the setting where measured gains are smallest. That makes modest speedups expected, not a sign of failure. I found no source that tested this directly.

### Gaps
- I found no empirical study comparing AI-assisted solo developers with small teams on product outcomes such as shipped features, retention or revenue.
- I found no rigorous data on how often one-person AI-built products succeed commercially versus the overall indie base rate. The survivorship argument here is inferred from case structure, not measured.
