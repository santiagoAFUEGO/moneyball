# ScoutAI Pro

*[🇪🇸 Versión en español](README.md)*

Data-driven football analysis built for clubs with limited budgets who want to compete with the same intelligence as bigger, richer teams — no invented formulas, no uncalibrated indexes. Every number in these reports is traceable back to its original public source.

## The 5 Pillars of Competitiveness

1. **Efficiency over volume** — goals per shot, shot-on-target %, tackle success rate. Not how much you do, how well you do it.
2. **Situational context** — home vs. away performance, a team's real tactical identity.
3. **Set pieces** — what share of a team's attacking threat comes from dead-ball situations.
4. **Squad management** — minutes concentration, fatigue/injury risk in short squads.
5. **Opponent-specific preparation** — head-to-head comparison ahead of a specific match.

## Repository structure

```
src/                           Reusable source code
  scoutai_simple.py            Full-season analysis (5 pillars)
  fbref_match_analyzer.py      Head-to-head comparison for a specific match

casos-estudio/                 Tactical case studies
  mundial-2026-australia-turquia/

reportes/                      Full season reports, ready to share
  beerschot-wilrijk/
```

## How it works

All analysis runs in Google Colab from public FBref.com HTML — no paid APIs or aggressive scraping required. The pipeline automatically detects what data exists for each league (some leagues have xG and advanced stats, others only basic ones) and adapts instead of inventing numbers that don't exist.

```python
from scoutai_simple import analizar_equipo, generar_reporte_portafolio

stats = analizar_equipo(html=html, nombre_equipo="Team Name")
generar_reporte_portafolio(stats, archivo_salida="report.pdf")
```

## Data source

[FBref.com](https://fbref.com) — public football statistics.

## Author

Santiago — football data analyst and aspiring head coach, building ScoutAI Pro as a portfolio to work with professional clubs.
