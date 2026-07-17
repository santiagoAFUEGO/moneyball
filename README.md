# ScoutAI Pro

Análisis de fútbol basado en datos reales, construido para equipos con presupuesto limitado que quieren competir con la misma inteligencia que los grandes — sin fórmulas inventadas, sin índices sin calibrar. Cada número en estos reportes es trazable hasta la fuente pública original.

## Los 5 Pilares de Competitividad

1. **Eficiencia sobre volumen** — goles por tiro, % de tiros al arco, efectividad de entrada. No cuánto haces, qué tan bien lo haces.
2. **Contexto situacional** — rendimiento local vs. visitante, identidad táctica real del equipo.
3. **Balón parado** — % del peligro ofensivo que depende de jugadas a balón parado.
4. **Gestión de plantilla** — concentración de minutos, riesgo de fatiga en plantillas cortas.
5. **Preparación por rival** — comparación cabeza a cabeza antes de cada partido específico.

## Estructura del repositorio

```
src/                           Código fuente reutilizable
  scoutai_simple.py            Análisis de temporada completa (5 pilares)
  fbref_match_analyzer.py      Comparación cabeza a cabeza para un partido específico

casos-estudio/                 Análisis tácticos puntuales
  mundial-2026-australia-turquia/

reportes/                      Reportes de temporada completos, listos para compartir
  beerschot-wilrijk/
```

## Cómo funciona

Todo el análisis corre en Google Colab a partir de HTML público de FBref.com — sin necesidad de APIs de pago ni scraping agresivo. El pipeline detecta automáticamente qué datos existen para cada liga (algunas ligas tienen xG y estadísticas avanzadas, otras solo estadísticas básicas) y se adapta en vez de inventar números que no existen.

```python
from scoutai_simple import analizar_equipo, generar_reporte_portafolio

stats = analizar_equipo(html=html, nombre_equipo="Nombre del Equipo")
generar_reporte_portafolio(stats, archivo_salida="reporte.pdf")
```

## Fuente de datos

[FBref.com](https://fbref.com) — estadísticas públicas de fútbol.

## Autor

Santiago — analista de datos de fútbol y aspirante a cuerpo técnico, construyendo ScoutAI Pro como portafolio para trabajar en clubes profesionales.
