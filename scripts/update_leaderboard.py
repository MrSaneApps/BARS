#!/usr/bin/env python3
"""
Rebuild `index.json` (from `reviews/**/metadata.json`), build the unified
multi-cohort `catalog.json` (all 1,567+ audited manuscripts across Calibration,
Repeatability, Out-of-Domain, Preprint-to-Published, Open-Review Concordance,
35-Year Longitudinal Secular Trend, and Career Self-Audit), and update the
compact Cohort Summary & Interactive Explorer section in `README.md`.
"""

import html
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWS_DIR = ROOT / "reviews"
INDEX_FILE = ROOT / "index.json"
CATALOG_FILE = ROOT / "catalog.json"
README_FILE = ROOT / "README.md"

START_MARKER = "<!-- LEADERBOARD_START -->"
END_MARKER = "<!-- LEADERBOARD_END -->"

TIERS = [
    (9.0, "Exemplary"),
    (7.0, "Strong / Sound"),
    (5.0, "Mixed / Salvageable"),
    (3.0, "Flawed / Overstated"),
    (0.0, "Fundamentally Invalid"),
]
SUB_RANGES = {"rigor": 3.5, "claims": 2.5, "biology": 2.0, "reproducibility": 2.0}
KNOWN_EXCEPTIONS: set[str] = set()


def tier_for(score: float) -> str:
    s = round(float(score), 1)
    for threshold, name in TIERS:
        if s >= threshold:
            return name
    return TIERS[-1][1]


def validate(data: dict, meta_path: Path) -> None:
    scores = data.get("scores", {})
    errors = []
    for key, hi in SUB_RANGES.items():
        v = float(scores.get(key, 0.0))
        if not 0.0 <= v <= hi:
            errors.append(f"{key}={v} outside [0, {hi}]")
    overall = float(scores.get("overall", 0.0))
    total = round(sum(float(scores.get(k, 0.0)) for k in SUB_RANGES), 2)
    if abs(total - overall) > 0.05:
        errors.append(f"sub-score sum {total} != overall {overall}")
    expected = tier_for(overall)
    if data.get("tier") != expected:
        errors.append(f"tier {data.get('tier')!r} != {expected!r} for {overall}")
    if errors:
        rel = meta_path.relative_to(ROOT)
        msg = f"{rel}: " + "; ".join(errors)
        if str(rel) in KNOWN_EXCEPTIONS:
            print(f"WARNING: {msg}", file=sys.stderr)
        else:
            raise ValueError(msg)


def collect_reviews() -> list[dict]:
    entries = []
    if REVIEWS_DIR.exists():
        for meta_path in sorted(REVIEWS_DIR.glob("**/metadata.json")):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validate(data, meta_path)
            rel_review = meta_path.parent.relative_to(ROOT) / "review.md"
            data["review_path"] = str(rel_review)
            entries.append(data)
    entries.sort(
        key=lambda x: (
            float(x.get("scores", {}).get("overall", 0.0)),
            x.get("reviewed_at", ""),
        ),
        reverse=True,
    )
    return entries


def normalize_authors_short(authors: str) -> str:
    if not authors:
        return "Anonymous"
    parts = [p.strip() for p in re.split(r"[,;]", str(authors)) if p.strip()]
    if not parts:
        return str(authors)[:40]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} & {parts[1]}"
    return f"{parts[0]} et al. ({parts[-1]})"


def infer_decade(year) -> str:
    try:
        y = int(year)
    except Exception:
        return "2020s"
    if y < 2000:
        return "1990s"
    if y < 2010:
        return "2000s"
    if y < 2020:
        return "2010s"
    return "2020s"


def build_unified_catalog(index_entries: list[dict]) -> dict:
    records = []

    # Lookup map from index_entries by cohort_id or id
    idx_by_cid = {}
    for item in index_entries:
        cid = item.get("cohort_id") or item.get("id")
        if cid:
            idx_by_cid[cid] = item

    # 1. Calibration Cohort (N=200) + extra issue reviews in `reviews/`
    cal_file = ROOT / "calibration" / "results_200.json"
    cal_cites = {}
    if cal_file.exists():
        cal_data = json.loads(cal_file.read_text(encoding="utf-8"))
        for grp_key in ["cohort_a", "cohort_b", "cohort_c"]:
            for r in cal_data.get(grp_key, []):
                cal_cites[r.get("cohort_id")] = r

    for item in index_entries:
        cid = item.get("cohort_id") or item.get("id")
        cal_meta = cal_cites.get(cid, {})
        scores = item.get("scores", {})
        overall = float(scores.get("overall", 0.0))
        rigor = float(scores.get("rigor", 0.0))
        claims = float(scores.get("claims", 0.0))
        biology = float(scores.get("biology", 0.0))
        repro = float(scores.get("reproducibility", 0.0))
        cohort_raw = str(item.get("cohort") or "").strip()
        if cohort_raw in ("A", "Cohort A") or str(cid).startswith("A"):
            exp_group = "Calibration: Cohort A (Known Invalid)"
            is_wild = False
        elif cohort_raw in ("B", "Cohort B") or str(cid).startswith("B"):
            exp_group = "Calibration: Cohort B (Validated Controls)"
            is_wild = False
        elif cohort_raw in ("C", "Cohort C") or (str(cid).startswith("C") and str(cid)[1:].isdigit() and int(str(cid)[1:]) <= 100):
            exp_group = "Calibration: Cohort C (Wild 2024–2025)"
            is_wild = True
        else:
            exp_group = "Community / Issue-Triggered Reviews"
            is_wild = True

        venue_raw = item.get("venue", "")
        venue_clean = re.sub(r"\s*\(\d{4}\)\s*$", "", venue_raw).strip()
        year_val = int(item.get("year") or 2024)
        pmcid = item.get("id", "") if str(item.get("id", "")).startswith("PMC") else cal_meta.get("pmcid", "")
        cites = int(cal_meta.get("citedByCount", 0) or 0)

        is_mega = any(
            m in venue_clean.lower()
            for m in [
                "plos one",
                "scientific reports",
                "sci rep",
                "nature communications",
                "nat commun",
                "peerj",
                "frontiers in",
                "front ",
                "mdpi",
                "int j mol sci",
                "cancers",
                "cells",
                "genes",
                "viruses",
                "antibiotics",
                "nutrients",
                "diagnostics",
                "j clin med",
                "helion",
                "heliyon",
                "medicine",
                "bmj open",
                "ieee access",
                "bmc ",
                "journal of translational medicine",
                "j transl med",
            ]
        )

        records.append(
            {
                "uid": f"CAL_{cid}",
                "code": cid,
                "anon_id": item.get("anon_id", cid),
                "experiment": exp_group,
                "is_wild": is_wild,
                "pmcid": pmcid,
                "pmid": str(item.get("pmid") or ""),
                "doi": str(item.get("doi") or ""),
                "url": item.get("url") or (f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else ""),
                "title": item.get("title", "Untitled"),
                "authors": item.get("authors", ""),
                "authors_short": item.get("authors_short") or normalize_authors_short(item.get("authors", "")),
                "journal": venue_clean or cal_meta.get("journal", ""),
                "year": year_val,
                "decade": infer_decade(year_val),
                "subfield": item.get("domain", "Quantitative Biology"),
                "venue_tier": "Megajournal" if is_mega else "Selective / Established",
                "citedByCount": cites,
                "overall": round(overall, 2),
                "rigor": round(rigor, 2),
                "claims": round(claims, 2),
                "biology": round(biology, 2),
                "reproducibility": round(repro, 2),
                "sci_core_8": round(rigor + claims + biology, 2),
                "tier": item.get("tier") or tier_for(overall),
                "study_modality": "Not Annotated (Calibration)",
                "tech_maturity": "Not Annotated (Calibration)",
                "epistemic_stage": "Not Annotated (Calibration)",
                "bias_category": "",
                "verdict": "",
                "review_path": item.get("review_path", ""),
                "human_review_path": "",
                "has_human_review": False,
            }
        )

    # 2. Out-of-Domain Generalization (N=60)
    ood_file = ROOT / "ood" / "ood_results_60.json"
    if ood_file.exists():
        for r in json.loads(ood_file.read_text(encoding="utf-8")):
            cid = r["cohort_id"]
            aid = r["anon_id"]
            year_val = int(r.get("year") or 2024)
            j_name = r.get("journal", "")
            is_mega = any(
                m in j_name.lower()
                for m in ["plos one", "scientific reports", "sci rep", "nat commun", "peerj", "front", "bmc ", "heliyon", "mdpi", "int j mol sci"]
            )
            records.append(
                {
                    "uid": f"OOD_{cid}",
                    "code": cid,
                    "anon_id": aid,
                    "experiment": "Out-of-Domain Wild (N=60)",
                    "is_wild": True,
                    "pmcid": r.get("pmcid", ""),
                    "pmid": str(r.get("pmid") or ""),
                    "doi": str(r.get("doi") or ""),
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{r.get('pmcid')}/" if r.get("pmcid") else "",
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "authors_short": normalize_authors_short(r.get("authors", "")),
                    "journal": j_name,
                    "year": year_val,
                    "decade": infer_decade(year_val),
                    "subfield": r.get("domain", ""),
                    "venue_tier": "Megajournal" if is_mega else "Selective / Established",
                    "citedByCount": int(r.get("citedByCount") or 0),
                    "overall": round(float(r["overall"]), 2),
                    "rigor": round(float(r["rigor"]), 2),
                    "claims": round(float(r["claims"]), 2),
                    "biology": round(float(r["biology"]), 2),
                    "reproducibility": round(float(r["reproducibility"]), 2),
                    "sci_core_8": round(float(r["rigor"]) + float(r["claims"]) + float(r["biology"]), 2),
                    "tier": r.get("tier") or tier_for(float(r["overall"])),
                    "study_modality": "Not Annotated",
                    "tech_maturity": "Not Annotated",
                    "epistemic_stage": "Not Annotated",
                    "bias_category": "",
                    "verdict": "",
                    "review_path": f"ood/reviews_stage1/{aid}.md",
                    "human_review_path": "",
                    "has_human_review": False,
                }
            )

    # 2b. 8-Field Expansion Cohort (N=160, expanding all 8 fields to n=40 each)
    fexp_file = ROOT / "field_expansion_160" / "fexp_results_160.json"
    if fexp_file.exists():
        for r in json.loads(fexp_file.read_text(encoding="utf-8")):
            aid = r["anon_id"]
            year_val = int(r.get("year") or 2024)
            j_name = r.get("journal", "")
            is_mega = any(
                m in j_name.lower()
                for m in ["plos one", "scientific reports", "sci rep", "peerj", "front", "bmc ", "heliyon", "mdpi", "int j mol sci", "cancers", "genes", "viruses", "microorganisms", "cells", "biomolecules"]
            )
            records.append(
                {
                    "uid": f"FEXP_{aid}",
                    "code": aid,
                    "anon_id": aid,
                    "experiment": "8-Field Everyday Expansion (N=160)",
                    "is_wild": True,
                    "pmcid": r.get("pmcid", ""),
                    "pmid": str(r.get("pmid") or ""),
                    "doi": str(r.get("doi") or ""),
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{r.get('pmcid')}/" if r.get("pmcid") else "",
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "authors_short": normalize_authors_short(r.get("authors", "")),
                    "journal": j_name,
                    "year": year_val,
                    "decade": infer_decade(year_val),
                    "subfield": r.get("domain", ""),
                    "venue_tier": "Megajournal" if is_mega else "Selective / Established",
                    "citedByCount": int(r.get("citedByCount") or 0),
                    "overall": round(float(r["overall"]), 2),
                    "rigor": round(float(r["rigor"]), 2),
                    "claims": round(float(r["claims"]), 2),
                    "biology": round(float(r["biology"]), 2),
                    "reproducibility": round(float(r["reproducibility"]), 2),
                    "sci_core_8": round(float(r["rigor"]) + float(r["claims"]) + float(r["biology"]), 2),
                    "tier": r.get("tier") or tier_for(float(r["overall"])),
                    "study_modality": "Not Annotated",
                    "tech_maturity": "Not Annotated",
                    "epistemic_stage": "Not Annotated",
                    "bias_category": r.get("bias_category", ""),
                    "verdict": r.get("verdict", ""),
                    "review_path": f"field_expansion_160/reviews/{aid}.md",
                    "human_review_path": "",
                    "has_human_review": False,
                }
            )

    # 3. Preprint-to-Published Pairs (N=50 pairs = 100 full-text reviews)
    pr_file = ROOT / "peer_review_exp" / "peer_review_results.json"
    if pr_file.exists():
        pr_data = json.loads(pr_file.read_text(encoding="utf-8"))
        for pair in pr_data.get("pairs", []):
            pid = pair["pair_id"]
            vt = "Selective / Established" if "Tier 1" in pair.get("venue_tier", "") else "Megajournal"
            hum_files = list((ROOT / "peer_review_exp" / "human_reviews").glob(f"{pid}_*"))
            hum_path = f"peer_review_exp/human_reviews/{hum_files[0].name}" if hum_files else ""

            for stage_label, scores_key, aid_key, wave_key in [
                ("Preprint (v1)", "preprint_scores", "preprint_anon_id", "preprint_wave"),
                ("Published (vFinal)", "published_scores", "published_anon_id", "published_wave"),
            ]:
                sc = pair[scores_key]
                ov_val = float(sc.get("overall", sc.get("total_10", 0.0)))
                delta_val = float(pair["deltas"].get("overall", pair["deltas"].get("total_10", 0.0)))
                aid = pair[aid_key]
                wdir = "wave1_reviews" if str(pair.get(wave_key)) in ("1", "wave1") or aid.startswith("PR_W1_") else "wave2_reviews"
                yr = int(pair.get("ppr_year" if "Preprint" in stage_label else "year") or 2024)
                records.append(
                    {
                        "uid": f"PR_{pid}_{'PPR' if 'Preprint' in stage_label else 'PUB'}",
                        "code": f"{pid} ({stage_label})",
                        "anon_id": aid,
                        "experiment": "Preprint vs. Published (N=100)",
                        "is_wild": False,
                        "pmcid": pair.get("pmcid", ""),
                        "pmid": str(pair.get("pmid") or ""),
                        "doi": str(pair.get("ppr_doi" if "Preprint" in stage_label else "doi") or ""),
                        "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pair.get('pmcid')}/" if pair.get("pmcid") else "",
                        "title": f"[{stage_label}] {pair.get('title', '')}",
                        "authors": pair.get("authors", ""),
                        "authors_short": normalize_authors_short(pair.get("authors", "")),
                        "journal": f"{pair.get('journal', '')} ({stage_label})",
                        "year": yr,
                        "decade": infer_decade(yr),
                        "subfield": f"Peer-Review Value-Added ({pair.get('sub_tier', '')})",
                        "venue_tier": "Preprint" if "Preprint" in stage_label else vt,
                        "citedByCount": int(pair.get("citedByCount") or 0),
                        "overall": round(ov_val, 2),
                        "rigor": round(float(sc["rigor"]), 2),
                        "claims": round(float(sc["claims"]), 2),
                        "biology": round(float(sc["biology"]), 2),
                        "reproducibility": round(float(sc["reproducibility"]), 2),
                        "sci_core_8": round(float(sc["rigor"]) + float(sc["claims"]) + float(sc["biology"]), 2),
                        "tier": tier_for(ov_val),
                        "study_modality": f"ΔS = {delta_val:+.1f} pts (Pub - Preprint)",
                        "tech_maturity": pair.get("preprint_timing_class", ""),
                        "epistemic_stage": stage_label,
                        "bias_category": "",
                        "verdict": "",
                        "review_path": f"peer_review_exp/{wdir}/{aid}.md",
                        "human_review_path": hum_path,
                        "has_human_review": bool(hum_path),
                    }
                )

    # 4. Open-Review Concordance Cohort (N=100)
    open_file = ROOT / "open_review_exp" / "open_review_results_100.json"
    if open_file.exists():
        for r in json.loads(open_file.read_text(encoding="utf-8")):
            aid = r["anon_id"]
            yr = int(r.get("year") or 2024)
            vt = "Selective / Established" if "Selective" in r.get("venue_tier", "") else "Megajournal"
            records.append(
                {
                    "uid": f"OPEN_{aid}",
                    "code": r.get("cohort_id", aid),
                    "anon_id": aid,
                    "experiment": "Open-Review Concordance (N=100)",
                    "is_wild": True,
                    "pmcid": r.get("pmcid", ""),
                    "pmid": str(r.get("pmid") or ""),
                    "doi": str(r.get("doi") or ""),
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{r.get('pmcid')}/" if r.get("pmcid") else "",
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "authors_short": normalize_authors_short(r.get("authors", "")),
                    "journal": r.get("journal", ""),
                    "year": yr,
                    "decade": infer_decade(yr),
                    "subfield": r.get("subfield", ""),
                    "venue_tier": vt,
                    "citedByCount": int(r.get("citedByCount") or 0),
                    "overall": round(float(r["overall"]), 2),
                    "rigor": round(float(r["rigor"]), 2),
                    "claims": round(float(r["claims"]), 2),
                    "biology": round(float(r["biology"]), 2),
                    "reproducibility": round(float(r["reproducibility"]), 2),
                    "sci_core_8": round(float(r.get("sci_core_8") or (float(r["rigor"]) + float(r["claims"]) + float(r["biology"]))), 2),
                    "tier": tier_for(float(r["overall"])),
                    "study_modality": r.get("study_modality", ""),
                    "tech_maturity": r.get("tech_maturity", ""),
                    "epistemic_stage": r.get("epistemic_stage", ""),
                    "bias_category": r.get("bias_category", ""),
                    "verdict": r.get("verdict", ""),
                    "review_path": r.get("review_path", f"open_review_exp/reviews/{aid}.md"),
                    "human_review_path": r.get("human_review_path", ""),
                    "has_human_review": True,
                    "human_referee_words": r.get("human_referee_words_clean", 0),
                    "num_human_reviewers": r.get("num_human_reviewers", 2),
                    "decision_rounds": r.get("decision_rounds", 1),
                    "human_coercive_citation_flag": bool(r.get("human_coercive_citation_flag")),
                    "ai_critique_count": r.get("ai_critique_count", 0),
                    "concordance": r.get("concordance"),
                }
            )

    # 5. 35-Year Longitudinal Secular Cohort (N=1,000)
    sec_file = ROOT / "secular_trend_exp" / "secular_results_1000.json"
    if sec_file.exists():
        for r in json.loads(sec_file.read_text(encoding="utf-8")):
            aid = r["anon_id"]
            yr = int(r.get("year") or 2020)
            vt = "Megajournal" if r.get("is_megajournal") else "Selective / Established"
            records.append(
                {
                    "uid": f"SEC_{aid}",
                    "code": r.get("sec_id", aid),
                    "anon_id": aid,
                    "experiment": "35-Year Secular Trend (N=915)",
                    "is_wild": True,
                    "pmcid": r.get("pmcid", ""),
                    "pmid": str(r.get("pmid") or ""),
                    "doi": str(r.get("doi") or ""),
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{r.get('pmcid')}/" if r.get("pmcid") else "",
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "authors_short": normalize_authors_short(r.get("authors", "")),
                    "journal": r.get("journal", ""),
                    "year": yr,
                    "decade": r.get("true_decade_short") or infer_decade(yr),
                    "window_label": r.get("window_label", ""),
                    "subfield": r.get("track", ""),
                    "venue_tier": vt,
                    "citedByCount": int(r.get("citedByCount") or 0),
                    "author_count": int(r.get("author_count") or 1),
                    "overall": round(float(r["overall"]), 2),
                    "rigor": round(float(r["rigor"]), 2),
                    "claims": round(float(r["claims"]), 2),
                    "biology": round(float(r["biology"]), 2),
                    "reproducibility": round(float(r["reproducibility"]), 2),
                    "sci_core_8": round(float(r.get("sci_core_8") or (float(r["rigor"]) + float(r["claims"]) + float(r["biology"]))), 2),
                    "tier": tier_for(float(r["overall"])),
                    "study_modality": r.get("study_modality", ""),
                    "tech_maturity": r.get("tech_maturity", ""),
                    "epistemic_stage": r.get("epistemic_stage", ""),
                    "bias_category": r.get("bias_category", ""),
                    "verdict": r.get("verdict", ""),
                    "review_path": f"secular_trend_exp/reviews/{aid}.md",
                    "human_review_path": "",
                    "has_human_review": False,
                }
            )

    # 6. Blinded Career Self-Audit (N=164)
    sp_file = ROOT / "spond_self_audit" / "spond_results_164.json"
    if sp_file.exists():
        for r in json.loads(sp_file.read_text(encoding="utf-8")):
            aid = r["anon_id"]
            yr = int(r.get("year") or 2020)
            j_name = r.get("journal", "")
            is_mega = any(
                m in j_name.lower()
                for m in ["plos one", "scientific reports", "sci rep", "nat commun", "peerj", "front", "bmc ", "heliyon", "mdpi"]
            )
            records.append(
                {
                    "uid": f"SP_{aid}",
                    "code": r.get("sp_id", aid),
                    "anon_id": aid,
                    "experiment": "Career Self-Audit: S. Pond (N=164)",
                    "is_wild": False,
                    "pmcid": r.get("pmcid", ""),
                    "pmid": str(r.get("pmid") or ""),
                    "doi": str(r.get("doi") or ""),
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{r.get('pmcid')}/" if r.get("pmcid") else "",
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "authors_short": normalize_authors_short(r.get("authors", "")),
                    "journal": j_name,
                    "year": yr,
                    "decade": r.get("decade") or infer_decade(yr),
                    "subfield": f"Self-Audit ({r.get('authorship_role', 'Co-Author')})",
                    "venue_tier": "Megajournal" if is_mega else "Selective / Established",
                    "citedByCount": int(r.get("citedByCount") or 0),
                    "author_count": int(r.get("author_count") or 1),
                    "overall": round(float(r["overall"]), 2),
                    "rigor": round(float(r["rigor"]), 2),
                    "claims": round(float(r["claims"]), 2),
                    "biology": round(float(r["biology"]), 2),
                    "reproducibility": round(float(r["reproducibility"]), 2),
                    "sci_core_8": round(float(r.get("sci_core_8") or (float(r["rigor"]) + float(r["claims"]) + float(r["biology"]))), 2),
                    "tier": tier_for(float(r["overall"])),
                    "study_modality": r.get("study_modality", ""),
                    "tech_maturity": r.get("tech_maturity", ""),
                    "epistemic_stage": r.get("epistemic_stage", ""),
                    "bias_category": r.get("bias_category", ""),
                    "verdict": r.get("verdict", ""),
                    "review_path": f"spond_self_audit/reviews/{aid}.md",
                    "human_review_path": "",
                    "has_human_review": False,
                }
            )

    # 6b. Blinded Career Self-Audit: A. Nekrutenko (N=74)
    an_file = ROOT / "anton_self_audit" / "anton_results_74.json"
    if an_file.exists():
        for r in json.loads(an_file.read_text(encoding="utf-8")):
            aid = r["anon_id"]
            yr = int(r.get("year") or 2020)
            j_name = r.get("journal", "")
            is_mega = any(
                m in j_name.lower()
                for m in ["plos one", "scientific reports", "sci rep", "nat commun", "peerj", "front", "bmc ", "heliyon", "mdpi"]
            )
            records.append(
                {
                    "uid": f"AN_{aid}",
                    "code": r.get("an_id", aid),
                    "anon_id": aid,
                    "experiment": "Career Self-Audit: A. Nekrutenko (N=74)",
                    "is_wild": False,
                    "pmcid": r.get("pmcid", ""),
                    "pmid": str(r.get("pmid") or ""),
                    "doi": str(r.get("doi") or ""),
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{r.get('pmcid')}/" if r.get("pmcid") else "",
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "authors_short": normalize_authors_short(r.get("authors", "")),
                    "journal": j_name,
                    "year": yr,
                    "decade": r.get("decade") or infer_decade(yr),
                    "subfield": f"Self-Audit ({r.get('authorship_role', 'Co-Author')})",
                    "venue_tier": "Megajournal" if is_mega else "Selective / Established",
                    "citedByCount": int(r.get("citedByCount") or 0),
                    "author_count": int(r.get("author_count") or 1),
                    "overall": round(float(r["overall"]), 2),
                    "rigor": round(float(r["rigor"]), 2),
                    "claims": round(float(r["claims"]), 2),
                    "biology": round(float(r["biology"]), 2),
                    "reproducibility": round(float(r["reproducibility"]), 2),
                    "sci_core_8": round(float(r.get("sci_core_8") or (float(r["rigor"]) + float(r["claims"]) + float(r["biology"]))), 2),
                    "tier": tier_for(float(r["overall"])),
                    "study_modality": r.get("study_modality", "Not Annotated"),
                    "tech_maturity": r.get("tech_maturity", "Not Annotated"),
                    "epistemic_stage": r.get("epistemic_stage", "Not Annotated"),
                    "bias_category": r.get("bias_category", ""),
                    "verdict": r.get("verdict", ""),
                    "review_path": f"anton_self_audit/reviews/{aid}_review.md",
                    "human_review_path": "",
                    "has_human_review": False,
                }
            )

    # Omit author names from public UI catalog.json for randomly sampled cohorts
    # (retaining author names only for Career Self-Audits, Calibration Controls A/B, and Community Reviews)
    named_cohorts = {
        "Calibration: Cohort A (Known Invalid)",
        "Calibration: Cohort B (Validated Controls)",
        "Career Self-Audit: S. Pond (N=164)",
        "Career Self-Audit: A. Nekrutenko (N=74)",
        "Community / Issue-Triggered Reviews",
    }
    for r in records:
        if r.get("experiment") not in named_cohorts:
            r["authors"] = ""
            r["authors_short"] = ""

    # Sort descending by overall score, then citations
    records.sort(key=lambda x: (x["overall"], x.get("citedByCount", 0)), reverse=True)

    # Compute cohort summary statistics
    cohort_order = [
        "Calibration: Cohort B (Validated Controls)",
        "Calibration: Cohort A (Known Invalid)",
        "Calibration: Cohort C (Wild 2024–2025)",
        "Out-of-Domain Wild (N=60)",
        "8-Field Everyday Expansion (N=160)",
        "Preprint vs. Published (N=100)",
        "Open-Review Concordance (N=100)",
        "35-Year Secular Trend (N=915)",
        "Career Self-Audit: S. Pond (N=164)",
        "Career Self-Audit: A. Nekrutenko (N=74)",
        "Community / Issue-Triggered Reviews",
    ]
    # Validate all review_path and uid uniqueness before returning
    seen_uids = set()
    missing_paths = []
    for r in records:
        uid = r["uid"]
        if uid in seen_uids:
            raise ValueError(f"Duplicate UID in catalog: {uid}")
        seen_uids.add(uid)
        rp = r.get("review_path", "")
        if rp and not (ROOT / rp).exists():
            missing_paths.append((uid, rp))
        hp = r.get("human_review_path", "")
        if hp and not (ROOT / hp).exists():
            missing_paths.append((uid, hp))
    if missing_paths:
        raise FileNotFoundError(f"Missing review_path/human_review_path files ({len(missing_paths)}): {missing_paths[:5]}")
    cohort_summaries = []
    for c_name in cohort_order:
        grp = [r for r in records if r["experiment"] == c_name]
        if not grp:
            continue
        scores = [r["overall"] for r in grp]
        n = len(scores)
        cohort_summaries.append(
            {
                "experiment": c_name,
                "n": n,
                "mean": round(statistics.mean(scores), 2),
                "sd": round(statistics.stdev(scores), 2) if n > 1 else 0.0,
                "median": round(statistics.median(scores), 2),
                "fail_50_pct": round(sum(1 for s in scores if s < 5.0) / n * 100, 1),
                "flaw_65_pct": round(sum(1 for s in scores if s < 6.5) / n * 100, 1),
            }
        )

    return {
        "total_records": len(records),
        "cohort_summaries": cohort_summaries,
        "records": records,
    }


def format_compact_readme_section(catalog: dict) -> str:
    total_n = catalog["total_records"]
    lines = [
        f"### Interactive GitHub Pages Explorer (`{total_n:,}` Audited Manuscripts & Reviews)",
        "",
        "> **[Launch Interactive Review Explorer & Graphical Dashboard (`spond.github.io/gemini-reviews`)](https://spond.github.io/gemini-reviews/)**",
        ">",
        "> Browse, search, and filter all **`1,560+` full-text scientific peer reviews** (and **`100+` paired verbatim human referee reports**) by **Cohort, Subfield, Venue Tier, Decade (`1991–2026`), Study Modality, Technology Maturity, Citation Impact, and Composite Score**, with interactive charts and clickable drill-down to every individual review dossier.",
        "",
        "| Experiment / Cohort | Manuscripts ($N$) | Mean $\\pm$ SD (/10) | Median | Strict Failure ($<5.0$) | Major Flaw ($<6.5$) | Documentation & Explorer |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    doc_links = {
        "Calibration: Cohort B (Validated Controls)": "[`CALIBRATION.md`](CALIBRATION.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Calibration%3A%20Cohort%20B%20(Validated%20Controls))",
        "Calibration: Cohort A (Known Invalid)": "[`CALIBRATION.md`](CALIBRATION.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Calibration%3A%20Cohort%20A%20(Known%20Invalid))",
        "Calibration: Cohort C (Wild 2024–2025)": "[`CALIBRATION.md`](CALIBRATION.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Calibration%3A%20Cohort%20C%20(Wild%202024%E2%80%932025))",
        "Out-of-Domain Wild (N=60)": "[`OOD_GENERALIZATION.md`](OOD_GENERALIZATION.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Out-of-Domain%20Wild%20(N%3D60))",
        "8-Field Everyday Expansion (N=160)": "[`OOD_GENERALIZATION.md`](OOD_GENERALIZATION.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=8-Field%20Everyday%20Expansion%20(N%3D160))",
        "Preprint vs. Published (N=100)": "[`PEER_REVIEW_VALUE_ADDED.md`](PEER_REVIEW_VALUE_ADDED.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Preprint%20vs.%20Published%20(N%3D100))",
        "Open-Review Concordance (N=100)": "[`PEER_REVIEW_VALUE_ADDED.md`](PEER_REVIEW_VALUE_ADDED.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Open-Review%20Concordance%20(N%3D100))",
        "35-Year Secular Trend (N=915)": "[`SECULAR_TRENDS_AND_COVARIATES.md`](SECULAR_TRENDS_AND_COVARIATES.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=35-Year%20Secular%20Trend%20(N%3D915))",
        "Career Self-Audit: S. Pond (N=164)": "[`SPOND_SELF_AUDIT.md`](SPOND_SELF_AUDIT.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Career%20Self-Audit%3A%20S.%20Pond%20(N%3D164))",
        "Career Self-Audit: A. Nekrutenko (N=74)": "[`ANTON_SELF_AUDIT.md`](ANTON_SELF_AUDIT.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Career%20Self-Audit%3A%20A.%20Nekrutenko%20(N%3D74))",
        "Community / Issue-Triggered Reviews": "[`PROTOCOL.md`](PROTOCOL.md) · [Explore](https://spond.github.io/gemini-reviews/#experiment=Community%20%2F%20Issue-Triggered%20Reviews)",
    }

    for cs in catalog["cohort_summaries"]:
        exp = cs["experiment"]
        lines.append(
            f"| **{exp}** | `{cs['n']:,}` | **{cs['mean']:.2f}** $\\pm$ {cs['sd']:.2f} | **{cs['median']:.2f}** | **{cs['fail_50_pct']:.1f}%** | **{cs['flaw_65_pct']:.1f}%** | {doc_links.get(exp, '[Explore](https://spond.github.io/gemini-reviews/)')} |"
        )

    lines.extend(
        [
            "",
            "*Complete machine-readable indices are committed in [`catalog.json`](catalog.json) (all cohorts) and [`index.json`](index.json) (calibration & issue ledger).*",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    entries = collect_reviews()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
        f.write("\n")

    catalog = build_unified_catalog(entries)
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write("\n")

    summary_md = format_compact_readme_section(catalog)
    if README_FILE.exists():
        content = README_FILE.read_text(encoding="utf-8")
        if START_MARKER in content and END_MARKER in content:
            before, rest = content.split(START_MARKER, 1)
            _, after = rest.split(END_MARKER, 1)
            updated = f"{before}{START_MARKER}\n{summary_md}\n{END_MARKER}{after}"
            README_FILE.write_text(updated, encoding="utf-8")
            print(
                f"Updated {README_FILE.name}, {INDEX_FILE.name} ({len(entries)} entries), and {CATALOG_FILE.name} ({catalog['total_records']} total audited records)."
            )
            return
    print(f"Wrote {INDEX_FILE.name} and {CATALOG_FILE.name} ({catalog['total_records']} records).")


if __name__ == "__main__":
    main()
