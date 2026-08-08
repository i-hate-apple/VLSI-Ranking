# VLSI-Ranking — A CSRankings-style Research & Grad-School Navigator for VLSI, EDA, Architecture & Hardware Security

**Creator:** i-hate-apple
**Inspired by:** CSRankings.org
**Domain:** VLSI / EDA / Computer Architecture / Hardware Security

---

## 1. Project Description

VLSI-Ranking is an open-source, metrics-driven ranking and discovery platform for hardware research — VLSI, EDA, Computer Architecture, and Hardware Security. It applies CSRankings' core philosophy (rank by publication *count* in top venues, not citations or subjective reputation, to resist gaming) to the hardware research world, which is currently underserved — CSRankings itself barely covers ISSCC, DAC, ICCAD, or hardware security venues.

The original VLSIRankings spec was a solid ranking engine. The gap: **a ranking table alone doesn't help a student decide where to apply, who to email, or whether they'd actually get in.** VLSI-Ranking keeps the serverless, zero-cost architecture but reframes the whole product around one job-to-be-done:

> "I'm a student who wants to do a PhD/MS in VLSI/hardware. Help me find the right faculty, the right lab, and the right program — and understand my odds."

---

## 2. Target Users

- **Undergrads/dual-degree students** (like most visitors to this kind of tool) shortlisting PhD/MS advisors 1–2 years out.
- **Final-year applicants** actively building a shortlist + cold-emailing professors.
- **Current MS/PhD students** scouting postdoc labs or lateral moves.
- **Faculty/departments** who want visibility for recruiting.

---

## 3. What's New vs. the Original Spec (and vs. CSRankings)

| Original VLSIRankings | VLSI-Ranking |
|---|---|
| Institution + faculty rank table | Same, **plus** advisor-fit discovery layer |
| Static count-based score | Adds **trend view** (is this lab's output rising/falling by sub-area?) |
| Faculty external links (Homepage, Scholar, IEEE) | Adds **funding model** (publicly listed, e.g. "guaranteed RA/TA") + co-authorship graph, sourced from public department pages |
| Region filter | Adds **program-level basics**: funding model, program homepage — kept to what's publicly published, not hand-researched per program |
| No comparison tool | **Shortlist + Compare** view (bookmark faculty, side-by-side compare like a spreadsheet) |
| No community layer | **"Who works with whom" co-authorship graph** to spot active collaborations/joint labs |

---

## 4. Core Feature Set

### A. Ranking Engine (kept from original, refined)
- Adjusted fractional counting (1/N per paper for N authors).
- Geometric mean aggregation across selected sub-areas — same formula as CSRankings, applied to hardware venues.
- Sub-areas: **Circuits & VLSI Design** (ISSCC, JSSC, VLSI Symp), **EDA** (DAC, ICCAD, DATE), **Computer Architecture** (ISCA, MICRO, ASPLOS, HPCA), **Hardware Security** (HOST, CHES).
- Configurable date range, per-venue toggling, geographic filter.

### B. Grad-School Discovery Layer (new, scoped to what's realistically obtainable)
- **Advisor Fit Panel**: for each faculty member — sub-area breakdown, recent papers (last 3 yrs weighted higher). No "recruiting" flag — this data isn't reliably self-reported or verifiable at scale, so it's dropped rather than shipped as unreliable info.
- **Trend Sparkline**: per-faculty and per-institution publication trend over time, so students can spot rising labs vs. coasting ones. This is computable directly from the same data the ranking engine already pulls — no extra sourcing needed.
- **Co-authorship Graph**: force-directed graph showing collaboration clusters — useful for spotting joint advising / interdisciplinary labs. Also derived from existing publication data, so no new data-collection risk.
- **Program Cards (lightweight)**: funding model and program homepage link only, pulled from department pages that already publish this info. Deliberately excludes things like average time-to-degree or cohort size — those aren't consistently published anywhere and would require manual per-program research to keep accurate, which doesn't scale with a weekly automated pipeline.

**Dropped entirely**: anonymized/crowdsourced admissions outcome data ("I got in with X pubs"). This was the highest-risk feature — self-reported outcome data is noisy, hard to moderate, sets false expectations, and carries real privacy/liability exposure. CSRankings deliberately avoids anything like it, and VLSI-Ranking follows that precedent.

### C. Comparison & Planning Tools
- **Shortlist Builder**: bookmark faculty/institutions, tag with notes ("email sent," "reply received," "fit: high").
- **Side-by-side Compare View**: up to 5 faculty/institutions compared on pub count, sub-area mix, trend, funding, location.
- **Export**: CSV export of the current filtered view *and* of your personal shortlist.

### D. Standard CSRankings-parity Features
- Real-time text search/filter.
- Dual-thumb year-range slider.
- Region/country dropdown.
- Expandable institution → faculty drill-down.
- Per-faculty venue-breakdown pie chart.
- Permalink/shareable URL state (filters encoded in query string, like CSRankings).

---

## 5. Tech Stack (unchanged philosophy: zero hosting cost, static + serverless)

- **Frontend**: Vanilla JS or lightweight React SPA, consuming a pre-compiled `data.json`. D3.js added for the co-authorship graph and trend sparklines; Chart.js retained for pie charts.
- **Data pipeline**: Python, hitting IEEE Xplore + Semantic Scholar APIs (Semantic Scholar is the better free source for architecture/security venues that IEEE doesn't fully index, e.g. some ASPLOS/USENIX Security overlap papers).
- **Automation**: GitHub Actions, weekly cron, regenerates `data.json`, commits, deploys to GitHub Pages.
- **Crowdsourcing**: CSV + PR-based, same as CSRankings — no backend DB needed, GitHub *is* the database.
- **Admissions data points**: kept in a separate, moderated `admissions.csv` with a PR template that strips identifying info before merge (privacy-by-process, not automated PII scrubbing — flag this as a manual review step in the CONTRIBUTING.md).

---

## 6. Data Schema

```
faculty.csv
  id, name, affiliation, homepage, scholarid, ieeeid, subareas[], recruiting_status(optional)

aliases.csv
  alias_name, faculty_id        # for name-variant resolution

venues.csv
  venue_code, full_name, subarea, tier

programs.csv   (NEW, scoped to publicly published info only)
  institution, degree_type(PhD/MS), funding_model, program_homepage

data.json (compiled output)
  {
    institutions: [{
      name, country, faculty: [{
        id, name, subareas: {area: adjustedCount},
        trend: [{year, count}], coauthors: [facultyId...],
        links: {homepage, scholar, ieee}
      }]
    }],
    programs: {...}
  }
```

---

## 7. Scoring Logic (JS, same core formula as CSRankings/original spec)

```js
// Adjusted count: 1/N credit per paper with N matched authors
adjustedCount += 1 / numAuthorsMatched;

// Geometric mean across M active sub-areas
averageCount = Math.pow(
  activeSubareas.reduce((prod, area) => prod * (adjustedCount[area] + 1), 1),
  1 / activeSubareas.length
);

// NEW: trend weight — optional toggle to weight recent years higher
// e.g. linear decay: weight = 1 - (currentYear - pubYear) * 0.05, floor 0.3
```

---

## 8. UI/UX Outline

1. **Landing / Rankings View** (default) — CSRankings-style table, sidebar filters (sub-area checkboxes → venue expansion, year slider, region dropdown, "recruiting only" toggle).
2. **Faculty Drill-down** — expand row → pie chart, trend sparkline, links, co-author mini-graph, "Add to shortlist" button.
3. **Program Explorer** — separate tab: institution cards with funding/timeline/admissions metadata.
4. **Compare View** — table of shortlisted faculty/programs, side-by-side.
5. **Graph View** — full-screen co-authorship force graph, filterable by sub-area/institution.
6. **Contribute** — instructions + PR templates for faculty.csv, programs.csv, admissions.csv.

---

## 9. Branding

- **Name**: VLSI-Ranking
- **Creator credit**: i-hate-apple
- **Tagline suggestion**: *"Rankings for the chips that actually ship."* (or similar — happy to brainstorm more if you want options)
- **Footer**: "Built by [i-hate-apple](https://github.com/i-hate-apple). Inspired by CSRankings."

---

## 10. Suggested Roadmap

| Phase | Scope |
|---|---|
| **Phase 1** | Port original ranking engine + schemas, get `data.json` pipeline working weekly on GitHub Actions |
| **Phase 2** | Ship lightweight Program Explorer + programs.csv (funding model + homepage only — highest value-to-effort for grad applicants) |
| **Phase 3** | Trend sparklines (derived from existing pub data, no new sourcing) |
| **Phase 4** | Co-authorship graph (D3 force layout, also derived from existing pub data) |
| **Phase 5** | Shortlist/Compare tool |

This phasing lets you ship something usable (and CV-worthy) after Phase 1–2 without needing the graph complexity up front, and every phase after that only uses data the pipeline already collects — no manual research or crowdsourced self-reports required.

---

## 11. Updated Mega-Prompt for AI Coding Assistants

```
System Context:
You are an expert full-stack developer and system architect. We are building
"VLSI-Ranking" (created by i-hate-apple), a metrics-based ranking and grad-school
discovery platform for VLSI, EDA, Computer Architecture, and Hardware Security
research, modeled on CSRankings.org but extended with grad-applicant-focused
features: program metadata, advisor trend/recruiting signals, a co-authorship
graph, and a shortlist/compare tool.

Architecture Constraints:
- Serverless static SPA (HTML/CSS/vanilla JS or lightweight React), no backend,
  consumes a pre-compiled data.json.
- Python data pipeline pulling from IEEE Xplore + Semantic Scholar APIs, parsing
  faculty.csv, aliases.csv, venues.csv, programs.csv into data.json with zero
  double-counting (entity resolution via aliases.csv).
- programs.csv is scoped to publicly published info only (funding_model,
  program_homepage) — do not design for manually-researched or self-reported
  fields like time-to-degree, cohort size, or admissions outcomes.
- GitHub Actions weekly cron regenerates data.json and deploys to GitHub Pages.

Scoring:
- Adjusted fractional counting (1/N per paper).
- Geometric mean across active sub-areas: 
  averageCount = (Π(adjustedCount_i + 1))^(1/M)
- Optional recency-weighted trend score.

Features to build, in order:
1. Core ranking table + drill-down (institution → faculty → pie chart of venues).
2. Program Explorer tab reading programs.csv (funding, timeline, cohort size).
3. Trend sparkline per faculty (publications per year, last ~8 years).
4. Co-authorship graph (D3 force-directed) filterable by sub-area.
5. Shortlist + Compare view (localStorage/session-based, no login required).

Step 1: Define schemas for faculty.csv, aliases.csv, venues.csv, programs.csv,
admissions.csv, and the compiled data.json — output the structures.
Step 2: Write the Python data pipeline (API calls, entity resolution, JSON gen).
Step 3: Write the GitHub Actions YAML for weekly automation + Pages deploy.
Step 4: Generate core frontend files (index.html, styles.css, app.js) — focus
first on ranking table + drill-down, then Program Explorer.

Begin with Step 1.
```

---

## 12. Open Questions for You

- `programs.csv` is now scoped to only funding model + homepage link. If you later want richer program info (time-to-degree, cohort size), the sustainable path is linking out to each program's own admissions page rather than hosting hand-curated data that will go stale.
- Given your own two-track CV strategy (SDE + VLSI), this project itself is a strong VLSI-adjacent portfolio piece — worth noting in your CV as "built a full-stack research analytics platform," which also nicely bridges your systems background with your hardware interest.
