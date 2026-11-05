# BARS: Blinded AI Review System (`veg/BARS`)

Direct, technically rigorous peer reviews of published manuscripts and preprints in quantitative biology, evolutionary genomics, statistical modeling, bioinformatics, and epidemiology, following the [7-Pillar Rapid Audit, Anti-LLM Trope Mandate, and 3-Section Review Protocol](REVIEW_TEMPLATE.md).

## How to Request a Review

1. Open a new [**Manuscript Review Request Issue**](../../issues/new?template=review_request.yml) with the paper's title, DOI/URL, or preprint identifier.
2. A maintainer periodically runs `scripts/watch_issues.py` to list open `pending-review` issues, runs the LLM reviewer against `REVIEW_TEMPLATE.md`, commits `reviews/YYYY/<slug>/{review.md,metadata.json}`, runs `scripts/update_leaderboard.py`, posts the review as an issue comment and labels the issue `reviewed`. The deterministic de-identification preprocessor ([`scripts/build_deidentified.py`](scripts/build_deidentified.py)) and statistical verification suite ([`scripts/verify_repeatability_and_calibration.py`](scripts/verify_repeatability_and_calibration.py)) are committed in `scripts/`.

Requirements: Python ≥ 3.9; GitHub CLI (`gh`) authenticated (for `watch_issues.py`).

### Model, Harness & Prompt Provenance ([`PROTOCOL.md`](PROTOCOL.md))
* **Model & Execution Harness:** All reviews across the calibration, repeatability, out-of-domain, peer-review value-added, longitudinal secular trend, and blinded self-audit studies were executed using **`Gemini 4 Argon`** via the Antigravity agentic harness with isolated, stateless `anon-reviewer` subagents (`search_web` disabled; filesystem access restricted to the de-identified manuscript and `REVIEW_TEMPLATE.md`).
* **Prompt Provenance (`REVIEW_TEMPLATE.md`):** Commit `01665db` (`9.7 KB`, pure 7-Pillar rubric without calibration outcome tables) was used during the 200-paper calibration study; Commit `2945b80` (`12.8 KB`) was present during Experiments 1–5; in `v1.1`, empirical calibration outcome tables live exclusively in [`CALIBRATION.md`](CALIBRATION.md).
* **Reproducible Verification:** Run `python3 scripts/verify_repeatability_and_calibration.py` to deterministically recompute all pooled and per-cohort $\text{ICC}(2,1)$, $\text{ICC}(2,3)$, sub-score ICCs, Fleiss' $\kappa$, Held-Out calibration sensitivity matrices (`CALIBRATION.md` §7), and Stage-1 vs. Stage-2 OOD metrics directly from the committed JSON files.

---

## Empirical Calibration & Literature Error Estimation ($N = 200$ Study)

Full protocol, ground-truth selection criteria, double-blinded de-identification experiments, held-out expansion validation (`ANON_76–200`, $\text{Held-Out AUC} = 0.9824$), and complete sensitivity matrices (`PMC8135569` label sensitivity, internal vs. upstream definitions, Cohort B control composition, and Europe PMC volume reweighting) are documented in [**`CALIBRATION.md`**](CALIBRATION.md) (and [`calibration/SUMMARY_FOR_COLLEAGUES.txt`](calibration/SUMMARY_FOR_COLLEAGUES.txt)):

| Cohort / Stratum | $N$ | Mean Score (/10) | Median | Strict Failure ($<5.0$) | Major Flaw ($<6.5$) | Diagnostic Summary |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Cohort A: Known Invalid / Refuted** | $50$ | **4.42** | **4.10** | **66.0%** (*70.2%–75.0% internal*) | **80.0%** (*85.1%–88.6% internal*) | Retracted or formally refuted studies ($\text{ROC-AUC} = 0.969$; Held-Out $\text{AUC} = 0.982$) |
| **Cohort B: Validated Controls** | $50$ | **8.64** | **8.85** | **0.0%** ($\text{Sp} = 100\%$) | **4.0%** ($\text{Sp} = 96\%$) | 31 independent primary controls: mean $8.56$, $\text{Sp}_{<5.0} = 100\%$ (`CALIBRATION.md` §7.5) |
| **Cohort C: Stratified Wild Sample** | $100$ | **5.47** | **5.40** | **43.0%** ($\pm 8.5\%$) | **70.0%** ($\pm 8.3\%$) | Rogan-Gladen $\hat{\pi}_{\text{true}} = 57.3\%\text{--}65.2\%$ ($<5.0$); EPMC volume-weighted `<5.0` = **54.9%** |
| ↳ *Molecular Evolution (Wild)* | $20$ | **6.90** | **6.50** | **5.0%** ($1/20$) | **45.0%** ($9/20$) | Highest methodological rigor in wild sample |
| ↳ *Viral Evolution (Wild)* | $20$ | **5.97** | **6.35** | **35.0%** ($7/20$) | **55.0%** ($11/20$) | Moderate rigor; clock/recombination & power flaws in lower tail |
| ↳ *Statistical Genetics / GWAS (Wild)* | $20$ | **5.37** | **5.40** | **40.0%** ($8/20$) | **75.0%** ($15/20$) | Frequent in-sample GWAS feature-selection leakage & MR violations |
| ↳ *Cancer & Microbiome (Wild)* | $20$ | **4.78** | **4.60** | **60.0%** ($12/20$) | **85.0%** ($17/20$) | Pervasive batch/antibiotic confounding, kitome & cage pseudoreplication |
| ↳ *Transcriptomics & CompBio ML (Wild)* | $20$ | **4.33** | **4.20** | **75.0%** ($15/20$) | **90.0%** ($18/20$) | Circular LASSO/Cox pipelines, pseudoreplication & text-table sign flips |

### Intra-Agent Test–Retest Repeatability ([`REPEATABILITY.md`](REPEATABILITY.md))
Across **$N = 30$ stratified manuscripts** (10 Cohort A, 10 Cohort B, 10 Cohort C across all 5 domains) evaluated in **$K = 3$ independent, freshly re-anonymized blinded waves (`90` reviews total; raw reviews and JSON committed in [`repeatability/`](repeatability/))**:
* **Per-Cohort vs. Pooled Reliability Breakdown (Headline for Wild Screening = `Cohort C`):**
  * **Cohort C (Uncurated Wild Literature, $n = 10 \times 3$):** Single-run **$\text{ICC}(2,1) = 0.8583$** ($\text{ICC}(3,1) = 0.8502$), 3-run ensemble **$\text{ICC}(2,3) = 0.9479$**, residual $\text{SD}_e = 0.63$ pts (mean per-paper $\text{SD} = 0.52$ pts), unanimous 3/3 binary agreement = **`80.0%` (`8/10`)** at both `< 5.0` ($\kappa = 0.729$) and `< 6.0` ($\kappa = 0.659$).
  * **Cohort A (Known Flawed/Retracted, $n = 10 \times 3$):** **$\text{ICC}(2,1) = 0.9200$**, **$\text{ICC}(2,3) = 0.9718$**, residual $\text{SD}_e = 0.43$ pts (`100%` unanimous at `< 6.0`).
  * **Cohort B (Validated Controls, $n = 10 \times 3$):** **$\text{ICC}(2,1) = 0.8636$**, **$\text{ICC}(2,3) = 0.9500$**, residual $\text{SD}_e = 0.24$ pts (`100%` unanimous at `< 5.0` and `< 6.0`).
  * **Pooled Stratified Sample ($N = 30 \times 3$):** **$\text{ICC}(2,1) = 0.9671$** ($\text{ICC}(3,1) = 0.9691$; $\text{ICC}(2,3) = 0.9888$), residual $\text{SD}_e = 0.46$ pts (`Mean |ΔS| = 0.49`), Fleiss' $\kappa = 0.864$ (`< 5.0`) and $\kappa = 0.910$ (`< 6.0`; `28/30` [`93.3%`] unanimous).
* **Sub-Score Reliability ($\text{ICC}(2,1)$ Pooled / Cohort C):** Rigor = **`0.9692` / `0.8439`** | Claims = **`0.9585` / `0.8467`** | Biology = **`0.9544` / `0.8014`** | Reproducibility = **`0.9139` / `0.8383`**.

### Out-of-Domain Generalization Across 3 Untested Fields ([`OOD_GENERALIZATION.md`](OOD_GENERALIZATION.md))
Applying our Two-Stage Adaptive Blinded Protocol (`88` reviews total committed in [`ood/`](ood/): Stage 1 single-pass on all 60 papers + Stage 2 3-run ensemble resolution on the 14 borderline papers with $5.2 \le S_1 \le 6.8$) to **$N = 60$ random wild manuscripts (`20` per field)** from three adjacent fields outside our calibration benchmark extends the wild sample to **$N = 160$ manuscripts across 8 quantitative domains** (reporting **Stage-1+2 Consensus [Stage-1 Single-Pass in brackets]** side-by-side):

| Out-of-Domain Stratum ($n = 20$ Each) | Mean Score (/10) [Stage-1] | Median [Stage-1] | Strict Failure ($<5.0$) [Stage-1] | Calibrated Failure ($<6.0$) [Stage-1] | Major Flaw ($<6.5$) [Stage-1] | Dominant Domain-Specific Failure Modes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Ecology & Macroevolution** | **5.19** [`5.33`] *(excl. `D20`: `5.01` [`5.16`])* | **4.80** [`5.05`] | **55.0%** [`40.0%`] ($11/20$ [$8/20$]) | **75.0%** [`75.0%`] ($15/20$) | **75.0%** [`75.0%`] ($15/20$) | `MaxEnt` overfitting ($p>n$), roadside bias, static altitude in warming projections, area arithmetic errors |
| **Neuroscience & Neuroimaging** | **4.88** [`4.99`] | **4.80** [`4.80`] | **50.0%** [`50.0%`] ($10/20$) | **80.0%** [`70.0%`] ($16/20$ [$14/20$]) | **85.0%** [`75.0%`] ($17/20$ [$15/20$]) | Circular ROI double-dipping ("voodoo correlations"), unnested CV leakage, copy-pasted HC follow-up tables |
| **Structural Bioinfo & AI Drug Discovery** | **4.56** [`4.65`] | **4.67** [`4.75`] | **60.0%** [`55.0%`] ($12/20$ [$11/20$]) | **80.0%** [`75.0%`] ($16/20$ [$15/20$]) | **85.0%** [`80.0%`] ($17/20$ [$16/20$]) | PDBbind–CASF pocket homology leakage, transductive DTI kernel leakage, docking to wrong PDB target |
| **All OOD Combined ($N = 60$)** | **4.88** [`4.99`] | **4.80** [`5.00`] | **55.0%** [`48.3%`] ($33/60$ [$29/60$]) | **78.3%** [`73.3%`] ($47/60$ [$44/60$]) | **81.7%** [`76.7%`] ($49/60$ [$46/60$]) | Age-adjusted $\rho(\text{Cites/Yr}, S) = +0.40$ ($p = 0.0016$); within-2024 $\rho = +0.27$, within-2025 $\rho = +0.35\text{--}0.39$ |
| **All 8 Domains Combined ($N = 160$)** | **5.25** [`5.29`] | **5.02** [`5.10`] | **47.5%** [`45.0%`] ($76/160$ [$72/160$]) | **67.5%** [`65.6%`] ($108/160$ [$105/160$]) | **74.4%** [`72.5%`] ($119/160$ [$116/160$]) | Consistent split between mechanistic models vs. formulaic template pipelines (`MaxEnt`, LASSO, docking, rs-fMRI) |

### Value-Added of Human Peer Review: Paired Preprint vs. Published Audit & Human Peer Review Files ([`PEER_REVIEW_VALUE_ADDED.md`](PEER_REVIEW_VALUE_ADDED.md))
Across **$N = 20$ version-blinded Preprint (`v1`) $\rightarrow$ Final Published Journal pairs (`40` full-text manuscripts)** split across two disjoint waves (`PR_W1_01`–`PR_W1_20` and `PR_W2_01`–`PR_W2_20`) and compared against **$210+$ pages of verbatim Human Peer Review Files** (`PLoS Pathogens`, `eLife`, `Nature Communications`, `Nature Cell Biology`, and `Nature`):
* **Overall Peer-Review Treatment Effect ($\Delta S = S_{\text{published}} - S_{\text{preprint}}$):** **`+0.65 ± 0.69` points** (Preprint Mean `6.53` $\rightarrow$ Published Mean `7.18`, Median $\Delta S = +0.65$, paired $t = 4.27, p = 0.0004$; Wilcoxon $p = 0.0003$).
* **Where the Gain Comes From:** **`38.2%` (`+0.25` pts)** of the total score increase comes from **Reproducibility & Technical Execution** (replacing missing preprint accessions with live GEO/SRA/PRIDE/Zenodo accessions at publication), **`32.8%` (`+0.215` pts)** from **Methodological & Statistical Rigor**, **`22.1%` (`+0.145` pts)** from **Claim–Evidence Alignment**, and only **`6.9%` (`+0.045` pts)** from **Data Integrity & Biological Plausibility**. (Caveat: preprint inputs may have lost Data Availability sections; see spond/gemini-reviews#2.)
* **Tier 1/2 (Selective Flagship/Society, $n=10$) vs. Tier 3 (Megajournal / Open-Threshold, $n=10$):**
  * **Selection Effect:** Tier 1/2 papers start **`+1.21` points higher as preprints** (`7.13` vs. `5.92`).
  * **Treatment Effect:** Tier 1/2 peer review adds **`+0.85` points** ($p = 0.0049$; **`+0.59` pts non-reproducibility scientific gain**), resolving the sole `< 6.0` preprint (`PAIR_07`, *NAR*, `5.2 -> 7.3`). Tier 3 peer review adds **`+0.46` points** ($p = 0.0427$), of which **`52.2%` (`+0.24` pts) is purely Data Availability deposition** (`+0.22` pts non-reproducibility gain), with no net change in the Tier 3 `< 6.0` rate (5/10 → 5/10): one preprint crossed above 6.0 (`PAIR_19` `5.8 -> 6.5`) and one published paper fell below (`PAIR_13` `6.1 -> 5.8`); both shifts are within single-run noise.
* **Blinded AI Reviewer vs. Verbatim Published Human Referee Reports ($N = 100$ Open-Review Cohort: `50` Selective Flagship/Society vs. `50` Megajournal):**
  * **Score Divergence by Venue Tier:** Selective Flagship/Society papers (`eLife`, `PLOS Biology`, `PLOS Genetics`, `PLOS Pathogens`, `PLOS Computational Biology`, $n=50$) average **`7.49 ± 1.38 / 10`** (`Core8 = 5.87 / 8.0`, median `7.75`, `< 5.0` = `8.0%`, `< 6.5` = `14.0%`, median human referee report length = `3,977` words), whereas Open-Review Megajournal papers (`PLOS ONE`, $n=50$) average **`5.01 ± 1.69 / 10`** (`Core8 = 3.79 / 8.0`, median `5.10`, `< 5.0` = `48.0%`, `< 6.5` = `76.0%`, median human referee report length = `2,462` words; $\Delta = +2.48$ pts, $p = 2.1 \times 10^{-12}$).
  * **AI Recall of Human Critiques (`363` substantive critiques across `261` human reviewers):** Single-pass blinded AI review independently recalled **`97.9%` (`95 / 97`)** of all substantive human referee critiques that remained unresolved in the published manuscript (`85` Direct Match + `10` Partial Match; `78.2%` [`284 / 363`] across all critiques including `266` pre-publication revision items), while identifying **`385` additional mathematical, statistical, and experimental design flaws (`3.85 per paper`)** that escaped all human referees and editors.
  * **Human Referee Depth & Anomalies:** In Selective Flagship/Society venues, **`72.0%` (`36/50`)** of human referee records were `Thorough Technical` and **`0.0%` (`0/50`)** were `Superficial/Boilerplate` (`1/50` [`2.0%`] reviewer anomaly). In Open-Review Megajournals, only **`12.0%` (`6/50`)** were `Thorough Technical`, **`38.0%` (`19/50`)** were `Superficial/Boilerplate`, and **`58.0%` (`29/50`)** exhibited severe human peer-review anomalies (`19` generic/suspect boilerplate or raw LLM-prompt-leaked reviews, `6` coercive self-citation/irrelevant citation demands, and `4` single-reviewer acceptances on quantitatively flawed studies).

### Secular Quality Trends (`1991–2025`, $N = 915$ Verified Full-Text) & Structural Covariate Decomposition ($N = 1,076$ Wild Manuscripts) ([`SECULAR_TRENDS_AND_COVARIATES.md`](SECULAR_TRENDS_AND_COVARIATES.md))
Across **$N = 915$ verified full-text, temporally and metadata-blinded manuscripts** (after strictly scrubbing 85 archival 1990s/early-2000s records whose Europe PMC XML lacked main body text) sampled across seven 5-year windows (`1991–1995` to `2021–2025`, `226–233` papers across 4 continuous core tracks) and pooled with our `101` Cohort C and `60` OOD wild papers (**$N = 1,076$ Wild Manuscripts total**):
* **35-Year Quality Decline (`1991–2025`, $N = 915$):** Mean Composite Score fell from **`7.63 ± 1.25`** (`Core8 = 6.24 / 8.0`, median `7.95`, `< 5.0` = `3.9%`) in the **1990s (`1991–1999`, $n = 154$)**—and **`7.61 ± 1.43`** in `1991–1995` ($n=73$), **`7.47 ± 1.22`** in `1996–2000` ($n=124$)—through **`6.76 ± 1.48`** in the **2000s ($n=249$)** and **`6.56 ± 1.63`** in the **2010s ($n=239$)** down to **`5.81 ± 1.97`** (`Core8 = 4.57 / 8.0`, median `5.80`, `< 5.0` = `34.8%`, `< 6.0` = `50.9%`) in the **2020s ($n=273$; `5.79 ± 1.83` in `2021–2025`)**. Across the 35-year span, Composite score declined by **`-0.58` points/decade** ($r = -0.330, p = 1.2 \times 10^{-24}$), and the 8.0-point Scientific Core declined by **`-0.54` raw points/decade** (`-0.68` scaled pts/decade, $r = -0.356, p = 8.7 \times 10^{-29}$).
* **Publication Volume Explosion vs. Ecosystem Compositional Shift:** Annual core-domain PubMed volume expanded **11.2-fold** (`57,850`/yr in 1991 $\rightarrow$ `648,325`/yr in 2025) and Open-Access volume expanded **295-fold** (`3,124` $\rightarrow$ `921,565`). Within 30 recurring multi-year journals ($n = 549$ papers), within-journal drift was modest (`-0.23` pts/decade, $r = -0.094, p = 0.027$), whereas an Oaxaca–Blinder decomposition shows that **`54.1%–58.3%` (`0.98` pts)** of the drop between the 1990s and 2020s is explained by compositional shift as Open-Access Megajournals expanded from `0%` (`1990s`) to **`50.5%` (`2020s`)**, averaging **`5.80 ± 1.73`** ($n=422$, `< 5.0` = `33.9%`) vs. **`6.75 ± 1.79`** ($n=654$, `< 5.0` = `17.3%`, $p = 1.3 \times 10^{-17}$) at Selective/Society venues across the $N = 1,076$ pooled wild corpus.
* **Physical/Functional Outcome vs. Secondary Cohort/Database Re-Analysis ($N = 1,076$):** `Wet-Lab Primary Experimental` ($n = 408$, **`6.81 ± 1.68`**, `< 5.0` = `16.4%`), `Hybrid Computational + Wet-Lab Validation` ($n = 351$, **`6.56 ± 1.73`**, `< 5.0` = `19.9%`), and `Dry-Lab Theory / Methods / Simulation` ($n = 87$, **`6.33 ± 1.96`**, `< 5.0` = `24.1%`) substantially outperform `Dry-Lab Secondary Cohort / Database Re-Analysis Only` ($n = 230$, **`5.33 ± 1.78`**, `< 5.0` = **`42.6%`**, `< 6.0` = **`62.2%`**; $\Delta = -1.48$ pts vs. Wet-Lab, $p = 5.5 \times 10^{-23}$).
* **Technology Maturity & Epistemic Stage ($N = 1,076$):** `Mid-Stage High-Throughput` ($n = 348$, **`6.65 ± 1.65`**, `< 5.0` = `17.0%`) and `Mature / Classical` ($n = 616$, **`6.62 ± 1.71`**, `< 5.0` = `18.5%`) technologies far outperform `Commodity / Hype-Cycle Template` pipelines ($n = 112$, **`4.16 ± 1.42`**, `< 5.0` = **`74.1%`**, `< 6.0` = **`90.2%`**, $p = 2.0 \times 10^{-44}$). Similarly, `Basic / Mechanistic Discovery` ($n = 679$, **`6.89 ± 1.68`**, `< 5.0` = `15.3%`) outperforms `Translational / Biomarker` ($n = 215$, **`5.65 ± 1.80`**, `< 5.0` = `36.3%`) and `Clinical / Observational` ($n = 182$, **`5.33 ± 1.62`**, `< 5.0` = **`40.7%`**).

### Blinded Self-Audit: All Full-Text PubMed Central Papers by Sergei Kosakovsky Pond ([`SPOND_SELF_AUDIT.md`](SPOND_SELF_AUDIT.md))
To maintain complete transparency and self-critical symmetry, we ran all **$N = 164$ Open-Access full-text PubMed Central articles matching `kosakovsky pond[au] OR pond sl[au] OR pond sk[au]` (`2004–2026`)** through the de-identification preprocessor (`SP_ANON_001`–`SP_ANON_164`, scrubbing titles, author names, affiliations, journals, and identifiers):
* **Overall ($N = 164$):** Mean **`7.53 ± 1.38 / 10.0`** (`Median = 7.85`, `IQR = 6.70–8.53`, `Scientific Core = 5.98 / 8.0`), with **`4.9%` (`8/164`) scoring `< 5.0`**, **`14.0%` (`23/164`) `< 6.0`**, and **`47.0%` (`77/164`) `>= 8.0`**.
* **First/Senior Author ($n = 42$) vs. Middle Co-Author ($n = 122$):**
  * **First or Senior Author ($n = 42$: `10` First, `32` Senior):** Mean **`8.22 ± 1.11 / 10.0`** (`Median = 8.50`, `IQR = 8.12–9.00`; First Author `8.33 ± 1.25`, Senior Author `8.19 ± 1.08`), **`0.0%` (`0/42`) `< 5.0`**, **`7.1%` (`3/42`) `< 6.0`**, and **`76.2%` (`32/42`) `>= 8.0`**.
  * **Middle Co-Author ($n = 122$):** Mean **`7.29 ± 1.39 / 10.0`** (`Median = 7.70`, `IQR = 6.50–8.38`, `< 5.0` = `6.6%` [`8/122`], `< 6.0` = `16.4%` [`20/122`], `>= 8.0` = `36.9%` [`45/122`]).
  * **Role Gap:** First/Senior-author papers score **`+0.93` points higher** than middle co-author papers (Welch's $t = 4.40, p = 3.05 \times 10^{-5}$; Mann–Whitney $p = 6.69 \times 10^{-6}$).
* **Zero Secular Decline (`2004–2026`):** `2000s` Mean `7.70` (First/Senior `8.14`, Med `8.90`), `2010s` Mean `7.46` (First/Senior `8.30`, Med `8.50`), `2020s` Mean `7.54` (First/Senior `8.16`, Med `8.95`; overall $r = -0.021, p = 0.79$; First/Senior $r = +0.039, p = 0.81$).
* **Unsparing Blinded Calibration on Self-Authored & Co-Authored Flaws:** The blinded reviewer flagged 8 middle co-author papers below `5.0` (including `SP_ANON_103` *Amendola et al. 2022* at **`2.2`**, `SP_ANON_034` *de Oliveira et al. 2015* at **`3.8`**, `SP_ANON_135` *Canuti et al. 2022* at **`3.8`**, `SP_ANON_109` *Lorenzo-Redondo et al. 2016* at **`4.1`**, and `SP_ANON_003` *Kumar et al. 2021* at **`4.2`**) as well as 4 First/Senior-author papers below `6.5` (`SP_ANON_044` *AUTO-TUNE* 2024 at **`5.0`**, `SP_ANON_028` *PLoS Comput Biol* 2006 at **`5.2`**, `SP_ANON_162` *Mammalian Rem2* 2024 at **`5.4`**, and `SP_ANON_012` *RASCL* 2022 at **`6.4`**—whose Omicron BA.5 amplicon-dropout reversion artifact was subsequently investigated and refuted in `SP_ANON_007` *Martin et al. 2023*, which scored **`8.9 / 10.0`**).

### The Economics of Doing, Reviewing, and Publishing Science: From 4-Cent AI Audits to Billion-Dollar Failures ([`economics_ai_human_pubmed.json`](economics_ai_human_pubmed.json))
Across all **`1,480` unique scrubbed full-text manuscripts** and **`1,568` generated review dossiers**, linked to NIH RePORTER grant portfolios (`452` NIH-funded papers, `222` in the everyday wild corpus) and Open-Access Article Processing Charges (APCs):
* **Token & API Cost per Paper (`$0.041` Batch / `$0.087` On-Demand):** Scrubbed full-text manuscripts average **`44,023` characters (`6,958` words, `11,585` tokens)** plus **`3,807` cacheable rubric tokens** (`15,392` total input tokens/paper). Generated review dossiers average **`8,083` characters (`1,100` words, `2,127` visible tokens)** plus **`~4,600` internal reasoning tokens** (`6,727` output tokens; **`22,119` total tokens/review**). At standard frontier pricing (`$1.25/1M` input, `$10.00/1M` output), a single-pass blinded review costs **`$0.087` (`8.65 cents`) on-demand** or **`$0.041` (`4.14 cents`) using Batch API with context caching** (`$0.124` Batch / `$0.260` on-demand for a 3-run consensus ensemble; **`$65.41` Batch / `$136.67` on-demand** for our entire 1,580-review study).
* **Extrapolating to All of PubMed Central & PubMed:**
  * **2025 Annual Open-Access PMC Flow (`921,565` articles/yr, `20.4B` tokens):** **`$38,109/year` Batch** (`$79,727/year` on-demand; `$114,327/year` 3-run Batch ensemble).
  * **2025 Entire Annual PubMed Flow (`1,965,335` articles/yr, `43.5B` tokens):** **`$81,272/year` Batch** (`$170,025/year` on-demand; `$243,815/year` 3-run Batch ensemble)—roughly the APCs of **7 luxury flagship papers (`7 × $11,528`)**.
  * **All-Time PMC Full-Text Archive (`10.9 million` articles, `241B` tokens):** **`$450,743` Batch** (`$942,982` on-demand).
  * **All-Time Historical PubMed Stock (`39.4 million` papers since 1781, `872B` tokens):** **`$1.63 million` Batch** (`$3.41 million` on-demand)—roughly the cost of a single 5-year NIH R01 grant.
* **Human Peer-Review Labor (`15.05 hours` = `$1,505/paper`) vs. AI Pre-Screening:** Across our 100 open-review papers, human peer review required **`2.61` referees/paper** (`3,213` median referee words). At `5.0 hours/referee + 2.0 editorial hours` (`15.05 hours/paper`, or **`$1,505/paper`** at `$100/hr` loaded senior academic labor, totaling **`29.6M hours = $2.96 billion/year`** across annual PubMed volume per *Aczel et al. 2021*), a blinded AI pre-screen is **`17,400×` to `36,400×` cheaper than human referee labor** and **`33,300×` to `69,500×` cheaper than a `$2,879` megajournal APC**, while recalling `97.9%` of unresolved human critiques and catching `3.85` extra quantitative flaws per paper.
* **Funding Inflection Points, Society Journal Value & the Billion-Dollar Cost of Failures:** Quality peaks at focused 2–3 NIH grant support (`$0.6M–$1.5M/yr`, median `$949k/yr`, scoring **`7.63/10`**, median `8.00`) before plateauing in mega-consortia (`>$1.5M/yr`, **`7.46/10`**), while `$3,242` academic society journals outperform `$2,879` commercial megajournals by **`+0.72` points** (`6.48` vs. `5.76/10`, $p = 1.1 \times 10^{-8}$) and match `$11,528` luxury flagships on benchmark controls (`8.74` vs. `8.65/10`). Meanwhile, the 18 NIH-funded retracted/refuted papers in Cohort A sat atop **`$67.68 million/year` in active NIH grant portfolios** (including **`$31.85M/yr`** across four contaminated tumor/placental microbiome papers `A16–A18, A27` that also spawned the **`$17.5M`** venture-backed startup *Micronoma* before refutation and retraction), and methodologically failing (`< 5.0`) open-access papers consume **`~$0.9–$1.2 billion/year` in global APCs** alongside **`$28.2 billion/year`** in irreproducible US preclinical research (*Freedman et al. 2015*).

---

## Running Tab & Manuscript Leaderboard (1–10 Scale)

<!-- LEADERBOARD_START -->
### Interactive GitHub Pages Explorer (`1,778` Audited Manuscripts & Reviews)

> **[Launch Interactive Review Explorer & Graphical Dashboard (`veg.github.io/BARS`)](https://veg.github.io/BARS/)**
>
> Browse, search, and filter all **`1,560+` full-text scientific peer reviews** (and **`100+` paired verbatim human referee reports**) by **Cohort, Subfield, Venue Tier, Decade (`1991–2026`), Study Modality, Technology Maturity, Citation Impact, and Composite Score**, with interactive charts and clickable drill-down to every individual review dossier.

| Experiment / Cohort | Manuscripts ($N$) | Mean $\pm$ SD (/10) | Median | Strict Failure ($<5.0$) | Major Flaw ($<6.5$) | Documentation & Explorer |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Calibration: Cohort B (Validated Controls)** | `50` | **8.64** $\pm$ 0.84 | **8.85** | **0.0%** | **4.0%** | [`CALIBRATION.md`](CALIBRATION.md) · [Explore](https://veg.github.io/BARS/#experiment=Calibration%3A%20Cohort%20B%20(Validated%20Controls)) |
| **Calibration: Cohort A (Known Invalid)** | `50` | **4.42** $\pm$ 1.97 | **4.10** | **66.0%** | **80.0%** | [`CALIBRATION.md`](CALIBRATION.md) · [Explore](https://veg.github.io/BARS/#experiment=Calibration%3A%20Cohort%20A%20(Known%20Invalid)) |
| **Calibration: Cohort C (Wild 2024–2025)** | `101` | **5.48** $\pm$ 1.78 | **5.40** | **42.6%** | **70.3%** | [`CALIBRATION.md`](CALIBRATION.md) · [Explore](https://veg.github.io/BARS/#experiment=Calibration%3A%20Cohort%20C%20(Wild%202024%E2%80%932025)) |
| **Out-of-Domain Wild (N=60)** | `60` | **4.88** $\pm$ 1.88 | **4.80** | **55.0%** | **81.7%** | [`OOD_GENERALIZATION.md`](OOD_GENERALIZATION.md) · [Explore](https://veg.github.io/BARS/#experiment=Out-of-Domain%20Wild%20(N%3D60)) |
| **8-Field Everyday Expansion (N=160)** | `160` | **4.51** $\pm$ 1.94 | **4.30** | **60.6%** | **78.1%** | [`OOD_GENERALIZATION.md`](OOD_GENERALIZATION.md) · [Explore](https://veg.github.io/BARS/#experiment=8-Field%20Everyday%20Expansion%20(N%3D160)) |
| **Preprint vs. Published (N=100)** | `100` | **6.69** $\pm$ 1.43 | **6.80** | **11.0%** | **45.0%** | [`PEER_REVIEW_VALUE_ADDED.md`](PEER_REVIEW_VALUE_ADDED.md) · [Explore](https://veg.github.io/BARS/#experiment=Preprint%20vs.%20Published%20(N%3D100)) |
| **Open-Review Concordance (N=100)** | `100` | **6.25** $\pm$ 1.98 | **6.60** | **28.0%** | **45.0%** | [`PEER_REVIEW_VALUE_ADDED.md`](PEER_REVIEW_VALUE_ADDED.md) · [Explore](https://veg.github.io/BARS/#experiment=Open-Review%20Concordance%20(N%3D100)) |
| **35-Year Secular Trend (N=915)** | `915` | **6.57** $\pm$ 1.75 | **6.80** | **19.7%** | **41.5%** | [`SECULAR_TRENDS_AND_COVARIATES.md`](SECULAR_TRENDS_AND_COVARIATES.md) · [Explore](https://veg.github.io/BARS/#experiment=35-Year%20Secular%20Trend%20(N%3D915)) |
| **Career Self-Audit: S. Pond (N=164)** | `164` | **7.53** $\pm$ 1.38 | **7.85** | **4.9%** | **20.7%** | [`SPOND_SELF_AUDIT.md`](SPOND_SELF_AUDIT.md) · [Explore](https://veg.github.io/BARS/#experiment=Career%20Self-Audit%3A%20S.%20Pond%20(N%3D164)) |
| **Career Self-Audit: A. Nekrutenko (N=74)** | `74` | **7.68** $\pm$ 0.86 | **7.75** | **1.4%** | **8.1%** | [`ANTON_SELF_AUDIT.md`](ANTON_SELF_AUDIT.md) · [Explore](https://veg.github.io/BARS/#experiment=Career%20Self-Audit%3A%20A.%20Nekrutenko%20(N%3D74)) |
| **Community / Issue-Triggered Reviews** | `4` | **6.65** $\pm$ 1.17 | **6.65** | **0.0%** | **50.0%** | [`PROTOCOL.md`](PROTOCOL.md) · [Explore](https://veg.github.io/BARS/#experiment=Community%20%2F%20Issue-Triggered%20Reviews) |

*Complete machine-readable indices are committed in [`catalog.json`](catalog.json) (all cohorts) and [`index.json`](index.json) (calibration & issue ledger).*
<!-- LEADERBOARD_END -->

---

## Scoring Rubric Summary (1.0 – 10.0)

| Sub-Score | Weight | Pillars | Focus |
| :--- | :---: | :---: | :--- |
| **Methodological & Statistical Rigor** | **3.5 pts** | Pillars 3, 4, 5 | Model specification, internal consistency, calibration of $p$-values/Bayes factors/AIC, uncertainty propagation, and symmetric baseline/null controls |
| **Claim-to-Evidence Alignment** | **2.5 pts** | Pillars 1, 5 | Correspondence between title/abstract/discussion claims and what was formally tested; proportion of claims *Well Supported* vs. *Fragile/Overstated/Methodologically Flawed* |
| **Data Integrity & Biological Plausibility** | **2.0 pts** | Pillars 2, 6 | Data provenance, handling of ascertainment/sampling skew, absence of leakage or circular conditioning, contamination controls, and biophysical/epidemiological realism |
| **Reproducibility & Technical Execution** | **2.0 pts** | Pillar 7 | Public availability of raw data and executable code, mathematical accuracy of equations, numerical consistency across text/tables/supplements, and clean references |

| Score Range | Tier | Diagnostic Interpretation |
| :---: | :--- | :--- |
| **9.0 – 10.0** | **Exemplary** | Sound model specification, calibrated uncertainty, symmetric controls, open data/code, and claims strictly bounded by statistical support |
| **7.0 – 8.9** | **Strong / Sound** | Solid methodological and empirical contribution; minor modeling caveats, unpropagated intermediate uncertainty, or secondary framing overreach |
| **5.0 – 6.9** | **Mixed / Salvageable** | Useful dataset or core method, but undermined by 1–2 major pillar violations (e.g., circular conditioning, uncalibrated tests, or missing baselines) requiring re-analysis |
| **3.0 – 4.9** | **Flawed / Overstated** | Core conclusions rest on statistical artifacts, severe ascertainment/contamination bias, or biologically implausible assumptions |
| **1.0 – 2.9** | **Fundamentally Invalid** | Pervasive technical failures, unaddressed leakage/contamination, or claims directly contradicted by the manuscript's own tables |

---

## Repository Structure

```text
gemini-reviews/
├── README.md                        # Overview + Compact Cohort Summary Table
├── index.html                       # Interactive GitHub Pages Review Explorer & Dashboard
├── catalog.json                     # Unified machine-readable ledger of all 1,567 audited records
├── index.json                       # Machine-readable ledger of calibration & issue reviews
├── REVIEW_TEMPLATE.md               # 7-Pillar Audit, Anti-LLM Style Rules, 1-10 Rubric & 3-Section Template
├── CALIBRATION.md                   # N=200 calibration protocol & results
├── REPEATABILITY.md                 # Experiment 1: 3-wave test-retest repeatability
├── OOD_GENERALIZATION.md            # Experiment 3: out-of-domain generalization (3 new fields)
├── PEER_REVIEW_VALUE_ADDED.md       # Experiment 4: preprint-vs-published & N=100 open peer review audit
├── SECULAR_TRENDS_AND_COVARIATES.md # Experiment 5: 1991-2025 N=1,000 secular trends & N=1,161 decomposition
├── SPOND_SELF_AUDIT.md              # Blinded self-audit of all N=164 full-text Kosakovsky Pond PMC papers
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── review_request.yml       # Structured Issue form for submitting papers to review
│   └── workflows/
│       └── check-ledger.yml         # CI: index.json, catalog.json & README.md must regenerate cleanly
├── calibration/                     # N=200 calibration benchmark & blinded reviews
├── ood/                             # N=60 out-of-domain generalization benchmark & reviews
├── peer_review_exp/                 # N=20 preprint-to-published pairs (40 reviews) & human files
├── open_review_exp/                 # N=100 open-review concordance cohort (Stage 1 reviews, human reports, Stage 2 JSONs)
├── secular_trend_exp/               # N=1,000 35-year longitudinal secular cohort (TIME_ANON_0001..1000)
├── spond_self_audit/                # N=164 blinded career self-audit reviews (SP_ANON_001..164)
├── reviews/                         # Issue-triggered & calibration per-paper review directories
└── scripts/
    ├── watch_issues.py              # Polls GitHub Issues for pending review requests
    ├── update_leaderboard.py        # Rebuilds index.json, catalog.json, and README.md summary table
    └── lint_reviews.py              # Warning-only lint: banned phrases, headers, score consistency
```
