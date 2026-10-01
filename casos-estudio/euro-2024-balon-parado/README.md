# Euro 2024 - Set-Piece Effectiveness Analysis

*[Versión en español más abajo / Spanish version below]*

## The problem

Set pieces (corners and direct free kicks) are one of the few phases of play a coaching staff 
can fully script and rehearse. But rehearsing a routine doesn't guarantee an advantage on matchday. 
This project answers a concrete question: **do teams that generate numerical superiority in the box 
actually convert that advantage into higher-quality shots?**

## Data source

- **StatsBomb Open Data** — event data from all 51 matches of UEFA Euro 2024, including shot freeze 
  frames (player positions at the moment of the shot)
- Extracted via `statsbombpy` in Python
- Total sample: 127 set-piece shots (corners and direct free kicks)

## Custom metrics

| Metric | What it measures | Formula |
|---|---|---|
| **xGxSP** (xG per Set Piece) | Average shot quality per set-piece play, normalized for volume | Total xG from set pieces / total set-piece shots |
| **LSI** (Local Superiority Index) | *Local* numerical superiority — teammates vs. opponents within an 8m radius of the shot location (not the whole penalty box) | Shots with local superiority / shots with available freeze frame |
| **SBRR** (Second-Ball Recovery Rate) | Control of the second ball after a clearance | Second balls recovered / set pieces defended by the opponent |

## Key finding (and why reporting it honestly matters)

The correlation between LSI and xGxSP, among teams with a reliable sample (≥3 shots, n=16), was 
**-0.28** — weak. This suggests local numerical superiority alone doesn't guarantee better shot 
quality: delivery execution and finisher timing likely matter more than headcount.

With only 127 total shots, this is a directional signal, not a definitive conclusion — a larger 
sample (pooled across competitions) would be needed to validate LSI with confidence before trusting 
it as a standalone indicator.

## Methodological note

The first definition of LSI (superiority across the entire box) returned 0.0 for 100% of shots: the 
defending team almost always matches or outnumbers attackers in total headcount during a set piece. 
The metric was redefined to measure *local* superiority (8m radius around the shot location), which 
showed real variation across teams.

## Files

- `balon_parado.py` — full extraction and metric-calculation pipeline
- `tiros_balon_parado_raw.csv` — shot-level raw data
- `resumen_metricas_bp.csv` — team-level aggregated metrics
- Power BI dashboard screenshots

## Credits

Data: [StatsBomb Open Data](https://github.com/statsbomb/open-data), under their open data license.

---

# Eurocopa 2024 - Análisis de la efectividad de las jugadas a balón parado

## El problema

Las jugadas a balón parado (córners y faltas directas) son una de las pocas fases del juego 
que un cuerpo técnico puede diseñar y ensayar por completo. Pero ensayar una jugada no garantiza 
una ventaja real el día del partido. Este proyecto responde una pregunta concreta: **¿los equipos 
que generan superioridad numérica en el área realmente convierten esa ventaja en remates de calidad?**

## Fuente de datos

- **StatsBomb Open Data** — eventos de los 51 partidos de la Eurocopa 2024, incluyendo freeze frames 
  (posición de jugadores en el momento del remate)
- Extracción vía `statsbombpy` en Python
- Muestra total: 127 jugadas de balón parado (córners y faltas directas) con tiro

## Métricas propias

| Métrica | Qué mide | Fórmula |
|---|---|---|
| **xGxSP** (xG per Set Piece) | Calidad promedio de remate por jugada, normalizada por volumen | xG total en balón parado / total de jugadas |
| **LSI** (Local Superiority Index) | Superioridad numérica *local* — jugadores propios vs. rivales en un radio de 8m alrededor del punto de remate (no en toda el área) | jugadas con superioridad local / jugadas con freeze frame disponible |
| **SBRR** (Second-Ball Recovery Rate) | Control del segundo balón tras un despeje | segundas jugadas recuperadas / jugadas defendidas por el rival |

## Hallazgo principal (y por qué importa ser honesto con los datos)

La correlación entre LSI y xGxSP en los equipos con muestra confiable (≥3 jugadas, n=16) fue de 
**-0.28** — débil. Esto sugiere que la superioridad numérica local, por sí sola, no garantiza 
remates de mejor calidad: la ejecución del envío y el timing del rematador probablemente pesan más 
que la cantidad de jugadores.

Con 127 jugadas totales, esta es una señal direccional, no una conclusión definitiva — se necesitaría 
una muestra más grande (varias competiciones) para validar el índice LSI con más confianza antes de 
usarlo como indicador aislado.

## Nota metodológica

La primera definición de LSI (superioridad en toda el área) resultó en 0.0 para
