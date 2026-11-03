# Casebook: non-obvious, people-oriented solutions across domains, and the moves behind them

Compiled 2026-10-26. Notes are in English.
Status scale: **Verified** = a primary source or peer-reviewed study supports the core claim. **Partly verified** = the core event is real, but the numbers come from the company, its agency or a blog, or the causal credit is disputed. **Folklore** = no documentary source, or shown to be staged.
Source dates are given where the page or the search result showed one. "n.d." means no date was visible.
Move labels used throughout:
- REFRAME: reframing the problem.
- PERCEPTION: changing perception instead of reality.
- REMOVE-STEP: removing a step or friction.
- OVERLOOKED: using an overlooked resource.
- INVERT: inversion.
- BORROW: borrowing from another domain.
- WEAKNESS→FEATURE: turning a weakness into a feature.
- SOCIAL-NORM: telling people what others do.
- DEFAULT: changing the default.
- DO-IT-BY-HAND: doing it manually, unscalably.
- FAKE-DOOR / DEMO-BEFORE-BUILD: showing the product before building it.
- PIVOT-SIDE-ASSET: building on a side asset of a failed project.
- MAKE-ERROR-VISIBLE / POKA-YOKE: making a mistake impossible or visible.
- GAMIFY / REWARD-THE-GOOD: rewarding the behaviour wanted instead of punishing the opposite.
- GIVE-AWAY: giving away what could be sold.
- PIGGYBACK-HABIT: attaching to an existing routine.

## Key Question 1 — The casebook: verified real cases with the obvious solution, the actual one, the move, the result and the status

### Takeaway
37 cases are listed below. The best-evidenced ones are the policy and health interventions (HMRC letters, Opower, the surgical checklist, defaults, hotel towels) and the AI/engineering ones, which have RCTs, peer-reviewed papers or primary engineering posts. The most-repeated business and marketing anecdotes are mostly real events whose numbers come from the company or its agency. Three famous stories are folklore or staged: the elevator mirrors, the KLM beagle, and the IKEA "legs off to fit the car" detail, which is legend-grade. The urinal fly's 80% figure is unsubstantiated.

### Cited Findings

#### A. Operations and service

**1. Houston airport baggage claim — Partly verified**
- **Obvious fix:** more baggage handlers. The airport did hire them, and the wait fell to about 8 minutes, but complaints continued.
- **What was done:** observation showed about 1 minute of walking and about 7 minutes of standing at the carousel. The airport moved arrival gates farther from baggage claim and sent bags to the outermost carousel, so the walk got longer and the idle wait shorter.
- **Move:** PERCEPTION / REFRAME. The problem was idle waiting, not total time.
- **Result:** complaints reportedly dropped "to near zero". That figure, and "six times longer walk", come from a blog, not from the NYT excerpt. The account traces to Alex Stone, "Why Waiting Is Torture", NYT Sunday Review, 2012-08-18/19, reprinted by APS. The airport's own data were never published.
- Sources: [APS reprint of NYT piece (n.d.)](https://www.psychologicalscience.org/news/why-waiting-is-torture.html); [yourmileagemayvary blog, 2025-08-02](https://yourmileagemayvary.com/2025/08/02/sneaky-way-texas-airport-ended-luggage-complaints/). The NYT original could not be fetched here; nytimes.com blocked the fetch.

**2. Mirrors next to elevators to cut complaints about slow lifts — Folklore**
- **The story:** engineers say the lifts cannot go faster; a psychologist says the tenants are bored, not impatient, so mirrors are installed.
- **Evidence:** none. No named building, date or record exists. An elevator-industry expert calls it an urban myth she has never used. The Otis 1854 "safety demo" is also partly myth; per Andreas Bernard, the famous illustration was drawn in 1978 for Otis.
- **Move, as told:** PERCEPTION.
- Sources: [Marketplace, "The art of elevatoring", 2012-12-04](https://marketplace.org/2012/12/04/art-elevatoring); [Signal v. Noise post 1244 (n.d.)](https://signalvnoise.com/posts/1244-defining-the-problem-of-elevator-waiting-times); [LRB review of Bernard, vol. 36 no. 13 (2014)](https://www.lrb.co.uk/v36/n13/david-trotter/messages-from-the-29th-floor)

**3. Toyota / Shingo poka-yoke — Verified, as documented in Shingo's lineage; the date is partly verified**
- **Obvious fix:** tell workers to pay attention. Management warnings had failed.
- **What was done:** workers kept omitting one of the two springs in a switch. Shingo split the task: first place both springs in a dish or placeholder, then insert them. A spring left in the dish makes the omission visible at once.
- **Move:** MAKE-ERROR-VISIBLE / REMOVE reliance on memory. The fix changes the process, not the person.
- **Detail:** the name changed from baka-yoke ("fool-proofing") to the milder poka-yoke. The 1961 Yamada Electric date rests on a single slide deck.
- Sources: [Wikipedia, Poka-yoke](https://en.wikipedia.org/wiki/Poka-yoke); [Michel Baudin on mistake-proofing, 2014-11-08](https://michelbaudin.com/tag/mistake-proofing/)

**4. Aravind Eye Care — Verified (the model); cost figures vary**
- **Obvious fix:** charity or subsidy for free cataract surgery, which is capacity-limited.
- **What was done:** a McDonald's-style assembly line. One surgeon works with two tables and several nursing teams, doing 6–8 operations an hour against the usual 1. Aurolab makes the lenses in-house: under $10 against about $200 imported, or $2 in another source. Paying patients cross-subsidise the poor; about 60% of patients are free or subsidised.
- **Move:** BORROW (fast food → surgery) + OVERLOOKED (surgeon idle time between cases).
- **Scale:** about 500,000 surgeries a year.
- Sources: [Harvard D3 "McDonaldization of eye care" (n.d.)](https://d3.harvard.edu/platform-rctom/submission/aravind-eye-care-system-mcdonaldization-of-eye-care/); [Kuwait Times / AFP "McSurgery" (n.d.)](https://kuwaittimes.com/mcsurgery-an-indian-hospital-restoring-eyesight-to-millions/); [Hilton Foundation (n.d.)](https://hiltonfoundation.org/?p=3996)

**5. Great Ormond Street Hospital × Ferrari F1 pit stop — Verified collaboration; numbers not found here**
- **Obvious fix:** more training or more staff for the handover from theatre to intensive care.
- **What was done:** the surgeons Martin Elliott and Allan Goldman watched Ferrari pit stops. They redesigned the handover with one coordinator (the anaesthetist, who formally passes command to the ICU doctor), fixed roles and failure planning.
- **Move:** BORROW (motorsport → paediatric cardiac surgery).
- **Result:** an ASQ case study reports fewer errors. The peer-reviewed figures (Catchpole et al., 2007) were not retrieved here; see Gaps.
- Sources: [Kottke, 2025-12](https://kottke.org/25/12/how-ferraris-f1-team-improved-medical-care-for-children); [Sower 2008 PDF, via gwern](https://www.Gwern.net/doc/technology/2008-sower.pdf); [cs4fn "pit stop heart surgery" (n.d.)](https://www.cs4fn.org/chi-med/pitstopheartsurgery.php)

**6. WHO Surgical Safety Checklist — Verified (NEJM 2009)**
- **Obvious fix:** more surgeon skill, technology or staff.
- **What was done:** a one-page checklist at three moments: before anaesthesia, before incision, and before the patient leaves the room. The idea comes from aviation.
- **Move:** BORROW (aviation) + MAKE-ERROR-VISIBLE.
- **Result:** deaths and complications fell by more than a third across 8 hospitals in 8 cities, with 7,688 patients (3,733 before, 3,955 after). The effect was equal in high- and low-income sites. The figures commonly quoted, mortality 1.5%→0.8% and complications about 11%→7%, are not confirmed in these results and should be checked against the paper.
- **Citation:** Haynes et al., NEJM 2009;360:491-9.
- Sources: [Harvard Gazette, 2009-01](https://news.harvard.edu/gazette/story/2009/01/surgical-safety-checklist-drops-deaths-and-complications-by-more-than-one-third/); [PAHO, 2009-01-16](https://www.paho.org/en/news/16-1-2009-safe-surgery-checklist-drops-death-and-surgery-complications-one-third)

**7. Schiphol urinal fly — Partly verified (the intervention is real; the 80% figure is unsubstantiated)**
- **Obvious fix:** more cleaning, or signs asking for aim.
- **What was done:** an etched fly near the drain gives men a target.
- **Move:** PERCEPTION / GAMIFY. A tiny cue replaces an instruction.
- **Attribution:** Aad Kieboom credits the cleaning manager Jos van Bedaf, who drew on army practice from the 1960s.
- **Result:** "80% less spillage" (Kieboom, via NPR) and "8% lower cleaning cost". The Decision Lab notes no pre-intervention measurement. A Schiphol representative could not say where the 80% came from. The fly has since been replaced by a golf hole.
- Sources: [Wikipedia, Urinal target](https://en.wikipedia.org/wiki/Urinal_target); [Works That Work interview (n.d.)](https://worksthatwork.com/1/urinal-fly); [KPBS/NPR, 2009-12-19](https://www.kpbs.org/news/national/2009/12/19/theres-a-fly-in-my-urinal); [The Decision Lab (n.d.)](https://thedecisionlab.com/es/intervention/how-a-picture-of-a-fly-reduced-washroom-cleaning-costs-by-8)

**8. IKEA flat-pack, the Lövet table — Folklore-grade origin; the flat-pack model itself is real**
- **The story:** Gillis Lundgren could not fit the Lövet table in his car, so he took the legs off, and flat-pack furniture was born. Dated 1955 or 1956.
- **Status:** Dezeen and Wallpaper both say "according to legend". Accounts differ on who unscrewed the legs and on the year. IKEA relaunched the table in 2013.
- **Move, as told:** REMOVE (assembly moved to the customer) + WEAKNESS→FEATURE (self-assembly as a price advantage).
- Sources: [Dezeen, 2013-07-22](https://www.dezeen.com/2013/07/22/ikea-revives-three-legged-diy-side-table/); [Wallpaper (n.d.)](https://www.wallpaper.com/design-interiors/ikea-leaf-table)

#### B. Software and product

**9. Airbnb founders photograph New York listings — Partly verified (repeatedly told by the founders; the exact numbers vary)**
- **Obvious fix:** email hosts tips, or write a tutorial.
- **What was done:** Gebbia and Chesky flew to New York, stayed with about 24 hosts, rented a camera, and photographed the listings themselves.
- **Move:** DO-IT-BY-HAND / REFRAME. The problem was presentation, not demand.
- **Result:** New York revenue "doubled" within about a month (Fast Company), or weekly revenue rose to about $400 (First Round account). This led to the Airbnb Photography Program: 2,000+ freelancers and 13,000 listings by 2013.
- Sources: [Fast Company, 2013](https://www.fastcompany.com/3017358/19airbnb); [Snappr (n.d.)](https://www.snappr.com/blog/photography-that-launched-an-empire-how-airbnb-transformed-their-business-with-professional-photography)

**10. Stripe "Collison installation" — Verified (Paul Graham's essay)**
- **Obvious fix:** send prospects a sign-up link.
- **What was done:** "Right then, give me your laptop", and the founders set the user up on the spot.
- **Move:** DO-IT-BY-HAND + REMOVE-STEP (the gap between "yes, I'll try it" and actually trying it).
- **Product side:** "7 lines of code" against competitors' gateway + processor + merchant account. That claim comes from secondary accounts.
- Sources: [Paul Graham, "Do Things That Don't Scale", 2013-07](http://paulgraham.com/ds.html) (stable URL, known; not refetched); [Alexander Jarvis summary (n.d.)](https://www.alexanderjarvis.com/stripe-doing-things-that-dont-scale)

**11. Dropbox explainer video as the MVP — Verified (Houston's own quote)**
- **Obvious fix:** build the hard sync product first and then test demand, or buy ads.
- **What was done:** a 3-minute screencast demo with Easter eggs aimed at the Digg audience.
- **Move:** FAKE-DOOR / DEMO-BEFORE-BUILD + knowing the audience.
- **Result:** "Our beta waiting list went from 5,000 people to 75,000 people literally overnight" (March 2008, Digg). An earlier video had gone to Hacker News in April 2007 with the YC application.
- Sources: [Wikipedia, Timeline of Dropbox](https://en.wikipedia.org/wiki/Timeline_of_Dropbox); [Stay Scrappy (n.d.)](https://stayscrappy.substack.com/p/how-dropbox-got-its-first-users-with)

**12. Slack, from the failed game Glitch; Flickr, from Game Neverending — Verified**
- **Obvious move:** shut down the failed game, or keep iterating on it.
- **What was done:** both times, Butterfield's team spun the internal side tool into the product. Glitch's internal chat became Slack: Glitch closed in late 2012, and Slack launched in August 2013. Game Neverending's photo-sharing features became Flickr, sold to Yahoo in 2005 (some sources say 2004).
- **Move:** PIVOT-SIDE-ASSET / OVERLOOKED.
- Sources: [TechCrunch, "The Slack origin story", 2019-05-30](https://techcrunch.com/2019/05/30/the-slack-origin-story)

**13. Domino's Pizza Tracker — Partly verified (the launch is verified; the sales effects are unverified)**
- **Obvious fix:** deliver faster.
- **What was done:** show the customer the order's progress through each stage, accurate to about 40 seconds.
- **Move:** PERCEPTION. Visible progress makes waiting tolerable. TRANSPARENCY.
- **Dates:** tested in December 2007 and launched in January 2008 (press release dated 2008-01-30). A March 2026 Domino's release says more than 2.5 billion orders have been tracked since 2008. The claim that online orders rose from under 15% to about 20% of sales comes from a consultant's blog only.
- Sources: [Domino's press release via franchising.com, 2008-01-30](https://www.franchising.com/news/20080130_dominos_launches_revolutionary_customer_tool_pizza.html); [Nasdaq/Domino's release (2026)](https://www.nasdaq.com/press-release/dominosr-updates-its-iconic-industry-first-tracker-even-better-customer-experience); [Aaron Allen blog (n.d.)](https://aaronallen.com/blog/dominos-turnaround)

**14. Gmail "Undo Send" — Verified (how it works)**
- **Obvious fix:** recall the email from the recipient's server, which is technically impossible across providers.
- **What was done:** hold the outgoing message for 5 seconds (later 10, 20 or 30), so "undo" just cancels before sending.
- **Move:** REFRAME / INVERT. Do not recall the sent mail; delay sending.
- **Dates:** Gmail Labs, March 2009; became a general setting in June 2015.
- Sources: [TechCrunch, 2009-03-19](https://techcrunch.com/2009/03/19/gmail-gets-a-panic-button); [The Next Web, 2015-06-23](https://thenextweb.com/google/2015/06/23/gmails-undo-send-feature-finally-graduates-out-of-labs-after-six-years/)

**15. Duolingo notification bandit — Verified (KDD 2020 paper)**
- **Obvious fix:** send more notifications.
- **What was done:** Duolingo treated notification volume as a protected channel and optimised content instead. It used a new bandit algorithm, the "Recovering Difference Softmax", which accounts for novelty decay when the same template repeats.
- **Move:** REFRAME (quality and novelty, not volume) + limit the resource deliberately.
- **Result:** +0.5% total DAU and +2% new-user retention against a strong baseline.
- Sources: [Yancey & Settles, KDD 2020 (PDF)](https://research.duolingo.com/papers/yancey.kdd20.pdf); [Vicki Boykis, "Duo, the Push, and the Bandits" (n.d.)](https://vicki.substack.com/p/duo-the-push-and-the-bandits)

**16. Duolingo streak and streak freeze — Partly verified (the mechanism is documented; freeze-specific numbers were not found)**
- **Obvious fix:** more content, or reminders.
- **What was done:** a streak counter, a "streak saver" notification, and a purchasable freeze that forgives a missed day. A forgiving loss-aversion mechanism keeps people from quitting after one slip.
- **Move:** WEAKNESS→FEATURE (forgiving a lapse) + GAMIFY.
- **Detail:** discussed by Jackson Shuttleworth, Duolingo's streak product lead.
- Sources: [Lenny's Newsletter, "Behind the product: Duolingo streaks" (2024)](https://lennysnewsletter.com/p/behind-the-product-duolingo-streaks); [Gigazine summary, 2024-06-18](https://gigazine.net/gsc_news/en/20240618-duolingo-app-streaks)

**17. Spotify Discover Weekly — Verified (origin and design intent); the first-year figure is not confirmed**
- **Obvious fix:** better search or more editorial playlists.
- **What was done:** a side project became a weekly, finite, personal 30-track "mixtape from a friend" (Matt Ogle). It was a fixed-length weekly ritual, not an endless feed.
- **Move:** SUBTRACTION (finite and weekly instead of infinite) + REFRAME (a friend's mixtape, not "recommendations").
- **Result:** Spotify's engineering blog calls it "one of our most successful feature launches". A 2015 profile cites about 75 million people reached. The figure of 40 million users in the first year was not confirmed.
- Sources: [Spotify Engineering, 2015-11](https://engineering.atspotify.com/2015/11/what-made-discover-weekly-one-of-our-most-successful-feature-launches-to-date); [Quartz, 2015](https://qz.com/571007/the-magic-that-makes-spotifys-discover-weekly-playlists-so-damn-good/)

**18. Amazon 1-Click — Verified (the patent); no public figure on its impact**
- **Obvious fix:** a faster checkout form.
- **What was done:** remove checkout entirely for returning customers by storing payment and address. Patent US 5,960,411, filed 1997 and granted 1999; Apple licensed it in 2000.
- **Move:** REMOVE-STEP.
- Source: [Google Patents US5960411A](https://patents.google.com/patent/US5960411A/en) (stable URL from prior knowledge; not refetched here). The Apple licensing detail is from prior knowledge; see Gaps.

**19. Febreze relaunch — Partly verified (Duhigg's reporting; P&G figures via secondary sources)**
- **Obvious move:** advertise harder that it removes smells. It flopped, because people stop noticing their own home's smell.
- **What was done:** P&G added scent and repositioned the spray as the reward at the end of cleaning: "smells as nice as it looks".
- **Move:** PIGGYBACK-HABIT / REFRAME. Target the routine, not the problem.
- **Result:** relaunched 1998; first-year sales above $230M; later more than $1B a year (secondary sources).
- Sources: [NPR interview with Charles Duhigg, 2012 (transcript)](https://www.npr.org/transcripts/147296743); [LitCharts summary of The Power of Habit, ch. 2 (n.d.)](https://www.litcharts.com/lit/the-power-of-habit/chapter-2-the-craving-brain-how-to-create-new-habits)

#### C. Marketing

**20. Burger King "Whopper Detour" (FCB New York, December 2018) — Verified (the awards); results are company-reported**
- **Obvious move:** a discount campaign promoting the app.
- **What was done:** the 1-cent Whopper unlocked only within 600 ft of a McDonald's, using geofencing.
- **Move:** OVERLOOKED (the rival's 14,000 locations as the media) + INVERT.
- **Result:** Adweek reports 1.5M app downloads; the agency claims more than 6M in a week. The app was number one in Food & Drink within hours. Earned impressions were 3.3–3.5B, reported as "$37M earned media" or "37:1 ROI". At Cannes 2019 it won the Titanium, Direct and Mobile Grand Prix.
- Sources: [Adweek, 2019-06](https://www.adweek.com/creativity/whopper-detour-burger-kings-masterpiece-of-trolling-wins-direct-grand-prix-at-cannes/); [Contagious, Mobile winners 2019](https://www.contagious.com/article/news-and-views/cannes-lions-mobile-winners-2019-whopper-detour-burger-king-2a7cb5c5f3f5426bb043c1471050ba45); [agency page (n.d.)](https://www.agencycompile.com/agencies/fcb-new-york/content/the-whopper-detour)

**21. Dove "Real Beauty Sketches" (Ogilvy Brasil, 2013) — Verified (the award and reach, which are brand-reported)**
- **Obvious move:** show diverse models.
- **What was done:** an FBI-trained forensic artist drew women from their own description and from a stranger's. The stranger's sketch was kinder.
- **Move:** REFRAME (the "enemy" is self-perception) + an experiment as the ad.
- **Result:** 114M views in the first month and 163M by June 2013 (Dove/Google figures); 4.6B media impressions. Titanium Grand Prix at Cannes 2013.
- Sources: [Wikipedia](https://en.wikipedia.org/wiki/Dove_Real_Beauty_Sketches); [Think with Google case (n.d.)](https://thinkwithgoogle.com/marketing-strategies/video/dove-real-beauty-sketches); [MediaPost, 2013-06](https://www.mediapost.com/publications/article/203151/unilevers-dove-beauty-wins-cannes-titanium-gra.html)

**22. Avis "We try harder" (DDB, 1962) — Partly verified**
- **Obvious move:** claim to be the best.
- **What was done:** admit being No. 2, and turn it into the reason Avis tries harder.
- **Move:** WEAKNESS→FEATURE.
- **Result:** from a $3.2M loss to a $1.2M profit, reported as the first profit in more than a decade. Hertz's lead against Avis is often cited as narrowing from 61–29 to 49–36 over 1963–66, but another source gives Avis 11%→25%, so the share figures conflict.
- Sources: [Wikipedia, William Bernbach](https://en.wikipedia.org/wiki/William_Bernbach); [Cullman Times (n.d.)](https://cullmantimes.com/?p=52223); [Sam Thomas Davies (n.d.)](https://www.samuelthomasdavies.com/damaging-admissions)

**23. Tesco Homeplus subway virtual store (Cheil, Seoul, 2011) — Partly verified (agency-reported)**
- **Obvious move:** open more stores; Homeplus was No. 2 to E-Mart.
- **What was done:** life-size photos of shelves on subway platform walls. Commuters scanned QR codes and the groceries were delivered home.
- **Move:** OVERLOOKED (commuters' dead time and wall space) + REFRAME (the store comes to the shopper).
- **Result:** online sales +130% and registered members +76% (November 2010 to January 2011, agency figures); 10,287 smartphone visits. Expanded to 20 locations in 2012.
- Sources: [MIT Technology Review, 2011-07-05](https://www.technologyreview.com/2011/07/05/22522/virtual-grocery-shopping/); [Ads of the World](https://www.adsoftheworld.com/campaigns/subway-virtual-store); [Business Today case, 2015-02-06](https://www.businesstoday.in/magazine/lbs-case-study/story/case-study-tesco-virtually-created-new-market-based-on-country-lifestyle-143807-2015-02-06)

**24. KLM "Lost & Found" beagle (DDB & Tribal, 2014) — Folklore / staged**
- **The video:** a beagle, "Sherlock", returns lost items to passengers at Schiphol.
- **Status:** KLM confirmed the dog was not part of the team: "purely used to symbolize" the real Lost & Found team. The agency called it a mascot.
- **Use:** an example of a fabricated "creative solution" that circulates as real.
- Sources: [Q13 Fox, 2014-09-24](https://q13fox.com/2014/09/24/hoax-worlds-cutest-dog-reuniting-travelers-with-lost-items-was-all-a-lie/); [Vulcan Post (2014)](https://vulcanpost.com/32711/sherlock-beagle-lost-found-untrue/)

**25. Volvo gives away the three-point seat-belt patent — Verified**
- **Obvious move:** license the patent for royalties, as a competitive edge.
- **What was done:** Nils Bohlin's belt (US patent 3,043,625, filed 1959-08-17, granted 1962-07-10) was made an open patent, free for other manufacturers.
- **Move:** GIVE-AWAY. Safety becomes a category standard and the brand's identity.
- **Result:** Volvo claims more than a million lives saved; that is a company estimate. A widely shared quote attributed to a 1959 Volvo executive actually dates from a 2013 retrospective; do not use it.
- Sources: [Hagerty UK (2019)](https://www.hagerty.co.uk/articles/automotive-history/sixty-years-of-volvos-seatbelt-patent/); [Lemelson-MIT (n.d.)](https://lemelson.mit.edu/resources/nils-bohlin); [Truth or Fiction (n.d.)](https://www.truthorfiction.com/?p=129349)

#### D. Public policy and behaviour

**26. HMRC tax-reminder letters with social norms (BIT, 2011–12) — Verified (RCT; figures as reported in summaries)**
- **Obvious fix:** harsher threats or penalties.
- **What was done:** a line added to the letter: "9 out of 10 people pay their tax on time…", in national, postcode and town versions.
- **Move:** SOCIAL-NORM.
- **Scale:** 140,000 debts worth £290M.
- **Result:** payment within 6 weeks rose from 67.5% (control) to 72.5% (national), 79% (postcode) and 83% (home town), about +15 percentage points.
- Sources: [Donald Marron, 2012-07-09](https://dmarron.com/2012/07/09/how-behavioral-science-can-improve-tax-policy/); [Tax Policy Center (n.d.)](https://taxpolicycenter.org/taxvox/can-behavioral-science-improve-tax-compliance); [Exeter TARC paper (n.d.)](https://www.exeter.ac.uk/media/universityofexeter/businessschool/documents/centres/tarc/research/social_norms_and_tax_compliance.pdf)

**27. Speed Camera Lottery (Stockholm, October 2010; Kevin Richardson's idea for VW's "Fun Theory") — Partly verified (a real 3-day trial; the result is VW's own)**
- **Obvious fix:** more speed cameras and fines.
- **What was done:** speeders' fines funded a lottery for drivers who kept to the limit.
- **Move:** INVERT / REWARD-THE-GOOD.
- **Result:** 24,857 cars over 3 days; average speed fell from 32 to 25 km/h, which is −22% (Grist) or −21.6% (VW). Only a 3-day promotional test; there is no long-term data, and it was never adopted as permanent policy as far as found.
- Sources: [Grist, 2010-12-03](https://grist.org/article/2010-12-03-driving-the-speed-limit-for-fun-and-profit/); [Love the Work / Cannes entry](https://lovethework.com/work-awards/entries/the-speed-camera-lottery-95205); [Jalopnik (n.d.)](https://www.jalopnik.com/2253199/cameras-sweden-stockholm-speed-lottery-fun-theory/)

**28. Bogotá traffic mimes (Mayor Antanas Mockus, 1995–) — Partly verified (the mimes are real; causal credit is shared)**
- **Obvious fix:** more police and fines. The police were seen as corrupt.
- **What was done:** about 20 mimes at first, later about 400, publicly mocked jaywalkers and bad drivers. Accounts say some dismissed traffic officers retrained as mimes. Citizens also got thumbs-up/down cards.
- **Move:** PERCEPTION / SOCIAL-NORM (public shame and play instead of fines).
- **Result:** traffic deaths fell from about 1,300 a year to about 600 by around 2003 (World Bank, Mockus). The rate fell from 22 to 7 per 100k over 1996–2006 (ODI). ODI credits wider governance reforms too.
- Sources: [World Bank blog (n.d.)](https://blogs.worldbank.org/en/developmenttalk/road-not-shared-turning-arts-help-increase-pedestrian-safety); [ODI feature (n.d.)](https://www.odi.org/features/securing-safe-roads/road-safety-bogota); [Columbia JIA, Mockus (n.d.)](https://jia.sipa.columbia.edu/news/building-citizenship-culture-bogota)

**29. Organ donation defaults (Johnson & Goldstein, Science 2003-11-21) — Verified, with nuance**
- **Obvious fix:** awareness campaigns.
- **What was done:** compare opt-in and opt-out countries. Consent is near-universal under opt-out and many times lower under opt-in.
- **Move:** DEFAULT.
- **Nuance:** a 2019 review finds consent and transplant rates higher under presumed consent, but the default is "one factor among many" for actual donations. Critics note the famous chart measures registration, not organs.
- Sources: [Columbia Business School press release (n.d.)](https://business.columbia.edu/press-release/cbs-press-releases/opt-out-best-plan-donors); [Behavioral Science & Policy review, 2019/2020 (PDF)](https://behavioralpolicy.org/wp-content/uploads/2020/01/Does-changing-defaults-save-lives_-Effectd-of-presumed-consent-organ-donation-policies.pdf); [critique, jcx.au (n.d.)](https://blog.jcx.au/posts/does-presuming-you-can-take-a-persons-organs-save-lives.html)

**30. Save More Tomorrow (Thaler & Benartzi, Journal of Political Economy 2004) — Verified, but evidence quality is rated low**
- **Obvious fix:** urge people to save more now.
- **What was done:** employees pre-commit to raising their savings rate from future pay rises, so take-home pay never falls.
- **Move:** REFRAME (in time) + uses loss aversion and inertia.
- **Result:** in the best subgroup, joiners at one firm went from 3.5% to 13.6% by the fourth raise. The firm's average went from 4.4% to 10.6%; at a second site, from 5.5% to 5.8% only. The US Department of Labor's evidence clearinghouse (CLEAR) rates the causal evidence low. The scheme was built into the Pension Protection Act of 2006.
- Sources: [US DOL CLEAR summary (n.d.)](https://clear.dol.gov/study/save-more-tomorrow%E2%84%A2-using-behavioral-economics-increase-employee-saving-thaler-benartzi-2004); [Wharton BCFG (n.d.)](https://bcfg.wharton.upenn.edu/?p=1496)

**31. Opower home energy reports — Verified (randomised trials)**
- **Obvious fix:** price signals, or conservation tips.
- **What was done:** each bill compares the household with its neighbours, with a smiley for efficient homes.
- **Move:** SOCIAL-NORM.
- **Result:** −1.9 to −2.0% energy use (Allcott RCT, about 80,000 Minnesota households). Across more than 110 US utilities, −1–3%. The effect persists: households still saved about 2% after reports stopped, with 10–20% decay a year. A German site showed −0.7% and an Indian site −7%.
- Sources: [J-PAL policy insight (n.d.)](https://www.povertyactionlab.org/policy-insight/reducing-energy-and-water-use-through-information-and-social-comparisons); [MIT CEEPR, Allcott working paper (2009)](https://ceepr.mit.edu/workingpaper/social-norms-and-energy-conservation)

**32. Hotel towel reuse (Goldstein, Cialdini & Griskevicius, Journal of Consumer Research 2008) — Verified (field experiments; a replication exists)**
- **Obvious fix:** an environmental appeal ("save the planet").
- **What was done:** a descriptive norm: "the majority of guests reuse their towels". The strongest version said "most guests who stayed in this room".
- **Move:** SOCIAL-NORM, local.
- **Result:** reuse rose from 35.1% to 44.1% with the norm card; the same-room norm was the most effective. The figure of 49% is not confirmed here. Bohner & Schlüter (2014) replicated the design in German hotels.
- Sources: [ScienceDaily, 2008-08-22](https://www.sciencedaily.com/releases/2008/08/080822160338.htm); [Bohner & Schlüter 2014, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4118982)

#### E. AI or algorithm as the solver (details under Key Question 4)

These five cases are expanded in Key Question 4:
- **33.** DeepMind data-centre cooling.
- **34.** NASA ST5 evolved antenna.
- **35.** Halicin.
- **36.** AlphaDev.
- **37.** AlphaEvolve.

### Inferences
- The best-evidenced cases are policy and behavioural interventions run as RCTs: HMRC, Opower, towels, the checklist. They are also the least "clever-looking". They are cheap changes of wording, default or framing with moderate effects of 2–15 percentage points that compound at scale. A creativity skill should value that: the move is small, and the evidence is strong.
- Marketing cases dominate popular lists, but their numbers are almost always the agency's own, written for award entries such as Cannes and Effie. Treat them as existence proofs of a move, not as effect sizes.
- The "pattern" stories that go viral are often the least verified: mirrors, the urinal 80%, the KLM dog, IKEA's legs. Their shape — one insight, a tiny change, a huge effect — is exactly what makes them memorable, and that shape is a red flag for folklore.
- The most transferable people-oriented insight across cases is diagnosing what the person actually experiences, not the metric. Examples: idle waiting rather than total wait (Houston, Domino's), presentation rather than demand (Airbnb), the reward rather than the problem (Febreze), and fear of a mistake rather than recall (Gmail).

### Gaps
- **Houston:** the original NYT article (2012-08-19, Alex Stone) could not be fetched. No airport data on complaints exists publicly. Treat "complaints to near zero" as anecdotal.
- **Great Ormond Street:** the peer-reviewed numbers (Catchpole et al., Paediatric Anaesthesia 2007) were not retrieved. Prior knowledge says technical errors and information omissions fell substantially, but this was not verified here, so no figures are cited.
- **Surgical checklist:** the exact mortality figures (1.5%→0.8%) were not confirmed from the search results; verify against NEJM 2009;360:491-9.
- **Amazon 1-Click:** no public data on conversion impact; the Apple licence (2000) is from prior knowledge.
- **Duolingo:** freeze-specific retention numbers are not public in the sources found.
- **Spotify:** the claim of "40M users in the first year" is not confirmed.
- **Domino's:** no primary source for the tracker's effect on digital sales share.
- **Speed lottery:** no evidence that any jurisdiction adopted it permanently.
- **Not researched because of the tool budget** (candidates for a later pass): Singapore's 1975 congestion pricing, Guinness "Good things come to those who wait" (WEAKNESS→FEATURE: the 119.5-second pour), Instagram from Burbn (SUBTRACTION), Chicago Lake Shore Drive optical speed bars, and Rwanda's Zipline drones.

## Key Question 2 — Which recurring moves appear most often in the casebook?

### Takeaway
Across the 32 human cases, the most frequent moves are:
- **Changing perception or the experience instead of the physical reality:** about 7 cases.
- **Social norms and defaults**, i.e. changing the choice architecture rather than incentives: about 6.
- **Borrowing a process from another domain:** about 4.
- **Removing a step:** about 4.
- **Doing it by hand / demo-before-build** for early products: about 3.
- **Inversion or rewarding the good:** about 3.
- **Weakness into feature:** about 3.
- **Using an overlooked resource**, often the competitor's or the customer's dead time: about 3.

Nearly every successful case starts from observing what the real person experiences, not from the metric the organisation tracks.

### Cited Findings
The tallies below are my coding of the cases above. Each case can carry several moves; the citations are the case sources in Key Question 1.
- **PERCEPTION / experience (7):**
  - Houston baggage — [APS/NYT](https://www.psychologicalscience.org/news/why-waiting-is-torture.html)
  - Domino's tracker — [press release](https://www.franchising.com/news/20080130_dominos_launches_revolutionary_customer_tool_pizza.html)
  - Urinal fly — [Works That Work](https://worksthatwork.com/1/urinal-fly)
  - Bogotá mimes — [World Bank](https://blogs.worldbank.org/en/developmenttalk/road-not-shared-turning-arts-help-increase-pedestrian-safety)
  - Gmail undo — [TechCrunch](https://techcrunch.com/2009/03/19/gmail-gets-a-panic-button)
  - Dove — [Wikipedia](https://en.wikipedia.org/wiki/Dove_Real_Beauty_Sketches)
  - Elevator mirrors, as folklore.
- **SOCIAL-NORM / DEFAULT (6):**
  - HMRC — [Marron](https://dmarron.com/2012/07/09/how-behavioral-science-can-improve-tax-policy/)
  - Opower — [J-PAL](https://www.povertyactionlab.org/policy-insight/reducing-energy-and-water-use-through-information-and-social-comparisons)
  - Towels — [ScienceDaily](https://www.sciencedaily.com/releases/2008/08/080822160338.htm)
  - Organ defaults — [Columbia](https://business.columbia.edu/press-release/cbs-press-releases/opt-out-best-plan-donors)
  - Save More Tomorrow — [DOL CLEAR](https://clear.dol.gov/study/save-more-tomorrow%E2%84%A2-using-behavioral-economics-increase-employee-saving-thaler-benartzi-2004)
  - Bogotá.
- **BORROW from another domain (4):**
  - Aravind: fast food → surgery — [Harvard D3](https://d3.harvard.edu/platform-rctom/submission/aravind-eye-care-system-mcdonaldization-of-eye-care/)
  - Great Ormond Street: F1 → ICU handover — [cs4fn](https://www.cs4fn.org/chi-med/pitstopheartsurgery.php)
  - Surgical checklist: aviation → surgery — [Harvard Gazette](https://news.harvard.edu/gazette/story/2009/01/surgical-safety-checklist-drops-deaths-and-complications-by-more-than-one-third/)
  - Also the fly as a target from army practice — [Wikipedia](https://en.wikipedia.org/wiki/Urinal_target)
- **REMOVE-STEP / subtraction (4):**
  - Amazon 1-Click — [patent](https://patents.google.com/patent/US5960411A/en)
  - Stripe install on the spot — [PG](http://paulgraham.com/ds.html)
  - Discover Weekly, finite instead of infinite — [Spotify Eng](https://engineering.atspotify.com/2015/11/what-made-discover-weekly-one-of-our-most-successful-feature-launches-to-date)
  - IKEA, legend.
- **DO-IT-BY-HAND / DEMO-BEFORE-BUILD (3):**
  - Airbnb photos — [Fast Company](https://www.fastcompany.com/3017358/19airbnb)
  - Collison install
  - Dropbox video — [Wikipedia timeline](https://en.wikipedia.org/wiki/Timeline_of_Dropbox)
- **INVERT / REWARD-THE-GOOD (3):**
  - Speed lottery — [Grist](https://grist.org/article/2010-12-03-driving-the-speed-limit-for-fun-and-profit/)
  - Gmail, delay instead of recall
  - Whopper Detour, the rival's store as the trigger — [Adweek](https://www.adweek.com/creativity/whopper-detour-burger-kings-masterpiece-of-trolling-wins-direct-grand-prix-at-cannes/)
- **WEAKNESS→FEATURE (3):**
  - Avis No. 2 — [Cullman Times](https://cullmantimes.com/?p=52223)
  - Duolingo freeze, forgiving a lapse — [Lenny's](https://lennysnewsletter.com/p/behind-the-product-duolingo-streaks)
  - IKEA self-assembly, legend.
- **OVERLOOKED RESOURCE (3+):**
  - Whopper Detour, the competitor's locations
  - Tesco subway, commuters' dead time and walls — [MIT TR](https://www.technologyreview.com/2011/07/05/22522/virtual-grocery-shopping/)
  - Slack/Flickr, the side tool of a failed project — [TechCrunch](https://techcrunch.com/2019/05/30/the-slack-origin-story)
  - Aravind, the idle time between operations.
- **MAKE-ERROR-VISIBLE / process over person (2):**
  - Poka-yoke — [Wikipedia](https://en.wikipedia.org/wiki/Poka-yoke)
  - The checklist.
- **PIGGYBACK-HABIT (1):** Febreze — [NPR](https://www.npr.org/transcripts/147296743)
- **GIVE-AWAY (1):** Volvo patent — [Hagerty](https://www.hagerty.co.uk/articles/automotive-history/sixty-years-of-volvos-seatbelt-patent/)

### Inferences
- These moves map neatly onto the published template systems in Key Question 3:
  - REMOVE-STEP ≈ SIT Subtraction.
  - OVERLOOKED RESOURCE ≈ SIT's "closed world" principle together with Task Unification (a resource already in the situation takes on a new job: the competitor's stores, the subway wall).
  - Poka-yoke and Shingo's split task ≈ SIT Division.
  - INVERT ≈ Goldenberg's "Inversion" ad template.
- A recurring pre-move, not a move itself, is **observation of the actual person in the actual situation**. Examples: Houston's time-and-motion of passengers, Airbnb living with 24 hosts, Aravind and Great Ormond Street watching another industry, Shingo watching the line. For a "creativity in solutions" skill, this argues for a mandatory "what does the person actually experience, minute by minute" step before generating options.
- **"Change perception instead of reality" is powerful but ethically double-edged.** The Houston walk is benign. The same move underlies dark patterns. The KLM dog shows the move becoming fabrication. A people-oriented skill should pair PERCEPTION with a check that the person is actually better off, not just quieter.
- **Effect sizes are inversely related to fame.** The famous anecdotes claim 80–100% effects, while RCT-backed nudges deliver 2–15 percentage points. Worth teaching the agent to distrust its own "one weird trick" outputs.

### Gaps
- The tally is my own coding of 32 cases, not a published frequency study. No source was found that counts move frequencies across a large, unbiased sample of real-world (non-advertising) solutions.

## Key Question 3 — Existing taxonomies of creative moves, and the evidence for them

### Takeaway
The best-evidenced taxonomy is the Goldenberg–Mazursky–Solomon "creativity templates" line. It came out of TRIZ via Systematic Inventive Thinking (SIT). Goldenberg, Mazursky & Solomon (1999) showed that 6 templates accounted for about 89% of 200 award-winning ads against about 2.5% of 200 non-winning ads. In an experiment, people trained on the templates produced ads rated more creative than brainstorming groups. The same group's SIT product framework names 5 templates: Subtraction, Division, Multiplication, Task Unification, Attribute Dependency. It was popularised in *Inside the Box* (Boyd & Goldenberg, 2013).

### Cited Findings
- **The advertising paper:** Goldenberg, Mazursky & Solomon, "The Fundamental Templates of Quality Ads", *Marketing Science* 18(3):333–351, 1999. Of 200 award-winning ads, 89% fit six templates; of 200 non-winning ads, only 2.5% did — [RePEc listing](https://ideas.repec.org/a/inm/ormksc/v18y1999i3p333-351.html); [Columbia PDF](https://business.columbia.edu/sites/default/files-efs/pubfiles/3384/fundamental.pdf); [Wylie Communications summary, 2022-11](https://wyliecomm.com/2022/11/creative-templates)
- **"Creative Sparks":** the companion piece by Goldenberg, Mazursky & Solomon in *Science* 285:1495 (1999-09-03) existed and drew letters and replies. One reply, "Meme's the Word", appeared in Science vol. 286, November 1999; another, "Scrutinizing Creativity — Response", appeared in Science 286:2271–2272, 1999-12-01 — [Columbia faculty listing "Scrutinizing Creativity—Response"](https://drupalgsb-dev.cc.columbia.edu/faculty/research/scrutinizing-creativity-response); [Columbia "Meme's the Word"](https://drupalgsb-dev.cc.columbia.edu/faculty/research/memes-word). The Science text itself was not retrieved. Contemporary press framed the result as a computer generating ads using templates — [Deseret News, 1999-09-15](https://www.deseret.com/1999/9/15/19465741/computer-turns-out-to-be-real-whiz-at-creating-ads)
- **The experiment:** template-trained participants produced ads judged more creative and memorable than those of free-association or untrained groups. This is a secondary summary; verify the figures against the paper — [Wylie Communications](https://wyliecomm.com/2022/11/creative-templates)
- **Template names:** a classroom worksheet lists the six as Extreme Consequences, Inversion, Absurd Alternative, Extreme Effort, Consequences, Competition — [CAUL OER worksheet, 2024-12 (PDF)](https://oercollective.caul.edu.au/app/uploads/sites/163/2024/12/Goldenbergs-Templates-DIY-worksheet.pdf). This differs from the names usually attributed to the 1999 paper, given from prior knowledge, not verified here: Pictorial Analogy, Extreme Situation, Consequences, Competition, Interactive Experiment, Dimensionality Alteration. Treat the names as needing a check against the Columbia PDF.
- **Follow-on book:** *Creativity Templates in New Products* (Cambridge University Press, 2002) by the same authors — [Columbia faculty listing](https://drupalgsb-test.paas.cc.columbia.edu/faculty/research/creativity-templates-new-products)
- **SIT's five templates:**
  - **Subtraction:** remove an essential component. Examples given: budget airlines dropping frills; a Philips DVD player without front controls.
  - **Division:** split an element and rearrange it. Example: individually wrapped portions.
  - **Multiplication:** copy a component and change the copy. Example: a dual-scent air freshener that reportedly doubled P&G's share.
  - **Task Unification:** give an existing component a new job. Example: actors playing the instruments when there is no orchestra.
  - **Attribute Dependency:** link two attributes that were independent.
  - The claim: "The majority of new, inventive and successful products result from only five templates" — [Umbrex summary (n.d.)](https://umbrex.com/resources/frameworks/innovation-frameworks/systematic-inventive-thinking/); [Success.com book summary (n.d.)](https://success.com/?p=8077); [SIT site (n.d.)](https://sitsite.com/?p=480)
- **Market effectiveness:** a later student or faculty project tested whether the templates predict market effectiveness, not just awards — [Humber College research page (n.d.)](https://mediaarts.humber.ca/current-students/resources/research/past-projects/can-the-creativity-templates-of-quality-advertising-also-predict-market-effectiveness.html)

### Inferences
- The evidence for templates is strongest for *advertising*: an award criterion with a classification study plus a training experiment. For *products*, the evidence is mostly case-based, consisting of SIT's consultancy cases and the book, not controlled studies.
- For the skill, SIT's "closed world" idea maps directly onto the "use an overlooked resource" move in the casebook. Several cases fit it: the Whopper Detour, the Tesco subway walls, Slack's internal chat, and Aravind's idle time. In each, the resource was already in the situation.
- The behavioural-science toolkits — defaults, social norms, timing, salience; for example BIT's EAST framework, not retrieved here — form a second, better-evidenced taxonomy specifically for *people-oriented* solutions. The casebook suggests a skill should combine the two:
  - SIT templates for changing the thing;
  - behavioural moves for changing the choice context;
  - the PERCEPTION move for changing the experience.

### Gaps
- The full text of "Creative Sparks" (Science, 1999) was not retrieved, so its exact experimental numbers are unverified here.
- The exact names of the six ad templates conflict between sources; check the Columbia PDF.
- TRIZ (Altshuller's 40 inventive principles) is SIT's ancestor. It was not researched in this pass, and no sources were collected on it.
- BIT's EAST framework (Easy, Attractive, Social, Timely) is relevant, but no source was fetched; cite only after checking.
- No controlled study was found showing that template training improves *non-advertising* real-world problem solving.

## Key Question 4 — Credibly documented cases where an AI or algorithmic system produced a non-obvious real-world solution

### Takeaway
There are credible cases, all in domains with a fast, automatic evaluator. Each has a primary source: a company engineering post or a peer-reviewed paper.
- NASA's evolved ST5 antenna flew in 2006.
- DeepMind's cooling control cut cooling energy by up to 40% (2016).
- Halicin was found by deep learning (Cell, 2020).
- AlphaDev's sorting routines went into LLVM libc++ (Nature, 2023).
- AlphaEvolve's Borg scheduling heuristic recovers about 0.7% of Google's fleet compute (2025).

None of these is a *people-oriented* solution in the sense of the human cases (perception, norms). AI's credible wins are in search over well-defined objective spaces.

### Cited Findings
**33. NASA ST5 evolved antenna (2006) — Verified**
- **What happened:** evolutionary algorithms designed an X-band antenna with an odd, bent-wire shape. Three copies flew on Space Technology 5 from March 22 to June 30, 2006, described as the first evolved hardware in space.
- **Speed of redesign:** when the mission requirements changed, new compliant designs were evolved in about 4 weeks.
- **Performance:** one source says it outperformed the contractor's conventional antenna; another says it was comparable.
- Sources: [NASA NTRS 20060024675](https://ntrs.nasa.gov/citations/20060024675); [NASA NTRS 20060015686](https://ntrs.nasa.gov/citations/20060015686); [USU SmallSat 2008](https://digitalcommons.usu.edu/smallsat/2008/all2008/77)

**34. DeepMind data-centre cooling (July 2016) — Verified, company-reported**
- **What happened:** machine learning controlling a live Google data centre cut the energy used for cooling by up to 40%.
- **Caveat:** that is cooling energy, not the total bill.
- Sources: [DeepMind blog, 2016-07-20](https://deepmind.com/blog/article/deepmind-ai-reduces-google-data-centre-cooling-bill-40); [TechCrunch, 2016-07-20](https://techcrunch.com/2016/07/20/google-unleashes-deepmind-on-energy-hungry-datacenter-cutting-cooling-bill-by-40-percent/)

**35. Halicin (Stokes et al., Cell 180(4):688–702, February 2020) — Verified**
- **What happened:** a deep network trained to predict antibacterial activity flagged halicin in the Drug Repurposing Hub. Halicin was originally investigated as a diabetes drug (from prior knowledge, not in the retrieved text). It is structurally unlike known antibiotics and has a novel mechanism: it disrupts the electrochemical gradient across the membrane.
- **Results:** it is active against *M. tuberculosis* and carbapenem-resistant Enterobacteriaceae, and it treated *C. difficile* and pan-resistant *A. baumannii* in mice.
- **Wider screen:** of 107M+ ZINC15 molecules, 23 predictions were tested, and 8 were antibacterial.
- **Status:** not yet an approved drug.
- Sources: [MIT News, 2020-02-20](https://news.mit.edu/index%2ephp/2020/artificial-intelligence-identifies-new-antibiotic-0220); [DSpace@MIT](https://dspace.mit.edu/handle/1721.1/126162); DOI 10.1016/j.cell.2020.01.021.

**36. AlphaDev (Nature, 2023-06-07) — Verified**
- **What happened:** reinforcement learning at the assembly level found sorting routines for 3–5 elements. In LLVM libc++ they are up to 70% faster for short sequences and about 1.7% faster for sequences over 250k. A hashing routine went into Abseil, up to 30% faster in some cases.
- **Non-obvious element:** "swap and copy move" instruction-level shortcuts. That is from prior knowledge; Wikipedia notes the routines were reverse-engineered into C++ before acceptance.
- Sources: [DeepMind blog, 2023-06-07](https://deepmind.google/discover/blog/alphadev-discovers-faster-sorting-algorithms/); [Wikipedia, AlphaDev](https://en.wikipedia.org/wiki/AlphaDev)

**37. AlphaEvolve (DeepMind, 2025-05-14) — Verified, company-reported**
- **Scheduling:** a Gemini-driven evolutionary coding agent found a Borg scheduling heuristic that "continuously recovers, on average, 0.7% of Google's worldwide compute resources". It had been "in production for over a year" at announcement. It was chosen partly because it is "human-readable code: interpretability, debuggability, predictability and ease of deployment".
- **Other results:**
  - a 23% kernel speed-up, giving 1% less Gemini training time;
  - a Verilog rewrite of a TPU arithmetic circuit;
  - multiplying 4×4 complex matrices with 48 scalar multiplications, an improvement on Strassen (1969).
- **Comparison:** the heuristic reportedly beat a deep-RL alternative (secondary source).
- Sources: [DeepMind blog, 2025-05-14 (fetched)](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/); [SSOJet summary (n.d.)](https://ssojet.com/blog/google-deepminds-alphaevolve-a-breakthrough-ai-coding-agent)

### Inferences
- Every credible AI case shares one condition: a **cheap, automatic, trustworthy evaluator** — an antenna simulator, a cooling-energy meter, an assay plus a model, cycle counts, scheduler simulation. AlphaEvolve's own design (LLM proposer plus automated evaluator) makes this explicit. For a creativity skill for an LLM agent, the lesson transfers: non-obviousness becomes credible when each candidate is checked against a concrete test, not judged by how clever it sounds.
- AlphaEvolve chose a *human-readable* heuristic over an opaque one, for deployability. For people-oriented work, the analogous constraint is that the solution has to be explainable to the people affected.
- No credible case was found of an AI system independently originating a people-oriented intervention (a nudge, a reframing, a service redesign) that was then deployed and measured. The documented AI wins are all optimisation or search in technical domains.

### Gaps
- Claims about LLM "co-scientist" systems generating real hypotheses in 2025–2026 were not researched in this pass. Neither were AI-designed interventions in marketing or policy, or any October 2026 updates to AlphaEvolve. A follow-up search is needed before citing any of them.
- The halicin repurposing origin (as a diabetes candidate) is from prior knowledge and was not confirmed in the retrieved text.
- AlphaDev's specific instruction-level tricks ("swap move", "copy move") are from prior knowledge and were not confirmed here.
