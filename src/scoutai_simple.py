"""
SCOUTAI PRO - VERSION SIMPLE
============================================================
UNA sola función que necesitas usar: analizar_equipo()

Uso en Colab (esto es TODO lo que necesitas escribir):

    from scoutai_simple import analizar_equipo
    stats = analizar_equipo(
        url="https://fbref.com/en/squads/c16e44ce/Beerschot-Wilrijk-Stats",
        nombre_equipo="Beerschot Wilrijk"
    )

Eso trae el HTML, lo analiza, imprime el reporte Y te muestra los gráficos.
Nada más que memorizar.
============================================================
"""

import time
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup, Comment
from io import StringIO
from dataclasses import dataclass

# ============================================================
# ESTÉTICA — paleta y estilo de todos los gráficos (edítalo aquí una sola vez)
# ============================================================
COLOR_FONDO = "#0e1117"
COLOR_TEXTO = "#e6e6e6"
COLOR_ACENTO_1 = "#00d4aa"   # verde-agua (ataque)
COLOR_ACENTO_2 = "#f4a300"   # dorado (defensa)
COLOR_GRID = "#2a2e39"

plt.rcParams.update({
    "figure.facecolor": COLOR_FONDO,
    "axes.facecolor": COLOR_FONDO,
    "axes.edgecolor": COLOR_GRID,
    "axes.labelcolor": COLOR_TEXTO,
    "text.color": COLOR_TEXTO,
    "xtick.color": COLOR_TEXTO,
    "ytick.color": COLOR_TEXTO,
    "font.size": 11,
    "font.family": "sans-serif",
})


# ============================================================
# PASO 1: TRAER EL HTML DE FORMA SEGURA
# ============================================================
_ULTIMO_REQUEST = [0.0]
_SESION = requests.Session()

def _fetch_html(url: str, espera_minima=4.0) -> str:
    transcurrido = time.time() - _ULTIMO_REQUEST[0]
    if transcurrido < espera_minima:
        time.sleep(espera_minima - transcurrido)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Referer": "https://fbref.com/",
        "Connection": "keep-alive",
    }
    resp = _SESION.get(url, headers=headers, timeout=15)
    _ULTIMO_REQUEST[0] = time.time()

    if resp.status_code == 403:
        raise RuntimeError(
            "Error 403: FBref está bloqueando la IP de este entorno (típico en Colab/nube, "
            "no es un error de tu código). Usa el método manual: abre la URL en tu navegador, "
            "Ctrl+S, y súbelo con el helper leer_html_local() de este mismo archivo."
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Error {resp.status_code} trayendo {url}. Revisa la URL o espera unos minutos.")
    return resp.text


def leer_html_local(ruta_archivo: str) -> str:
    """
    Plan B cuando FBref bloquea la IP de Colab (pasa seguido, no es un bug).
    1. Abre la URL en TU navegador (tu computador, no Colab).
    2. Ctrl+S -> guardar como 'Página web, solo HTML'.
    3. Sube ese archivo a Colab con files.upload().
    4. Usa esta función en vez de la URL directa:
         html = leer_html_local("Beerschot-Wilrijk-Stats.html")
    """
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# PASO 2: EXTRAER TABLAS (incluye las escondidas en comentarios HTML de FBref)
# ============================================================
def _flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        leaves = [c[-1] for c in df.columns]
        counts = {}
        for leaf in leaves:
            counts[leaf] = counts.get(leaf, 0) + 1
        seen, new_cols = {}, []
        for c in df.columns:
            top, leaf = c[0], c[-1]
            if counts[leaf] > 1:
                n = seen.get(leaf, 0)
                seen[leaf] = n + 1
                new_cols.append(leaf if n == 0 else f"{top}_{leaf}")
            else:
                new_cols.append(leaf)
        df.columns = new_cols
    # Quitamos filas de resumen (Squad Total / Opponent Total) usando la PRIMERA
    # columna por posición, no por nombre — así funciona igual si la página vino
    # en inglés ('Player') o traducida por el navegador ('Jugador', 'Joueur', etc.)
    if len(df.columns) > 0:
        primera_col = df.columns[0]
        etiquetas_resumen = {"Player", "Jugador", "Joueur", "Squad Total", "Opponent Total", "Players Used"}
        df = df[~df[primera_col].astype(str).isin(etiquetas_resumen)]
    return df.reset_index(drop=True)


def _extraer_tablas(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    tablas = {}

    for tabla in soup.find_all("table"):
        tid = tabla.get("id")
        if tid:
            try:
                df = pd.read_html(StringIO(str(tabla)))[0]
                tablas[tid] = _flatten_columns(df)
            except ValueError:
                continue

    comentarios = soup.find_all(string=lambda t: isinstance(t, Comment))
    for comentario in comentarios:
        if "<table" not in comentario:
            continue
        sub = BeautifulSoup(comentario, "html.parser")
        for tabla in sub.find_all("table"):
            tid = tabla.get("id")
            if tid and tid not in tablas:
                try:
                    df = pd.read_html(StringIO(str(tabla)))[0]
                    tablas[tid] = _flatten_columns(df)
                except ValueError:
                    continue
    return tablas


def _buscar_tabla(tablas, palabras_clave):
    for tid, df in tablas.items():
        if any(k in tid.lower() for k in palabras_clave):
            return df
    return None


# ============================================================
# PASO 3: CONSTRUIR LAS ESTADÍSTICAS DEL EQUIPO
# ============================================================
@dataclass
class EstadisticasEquipo:
    nombre: str
    goles: float = 0
    tiros: float = 0
    tiros_al_arco: float = 0
    xg: float = 0
    pases_clave: float = 0
    pases_progresivos: float = 0
    conducciones_progresivas: float = 0
    regates_exitosos: float = 0
    entradas: float = 0
    entradas_ganadas: float = 0
    intercepciones: float = 0
    despejes: float = 0
    errores: float = 0
    duelos_aereos_ganados: float = 0
    duelos_aereos_totales: float = 0
    precision_pases: float = 0
    # Proxy de calidad de tiro sin xG
    goles_por_tiro: float = 0
    pct_tiros_al_arco: float = 0
    tiene_xg: bool = False
    # Pilar 2 — contexto situacional (local vs visitante), viene de matchlogs_for
    local_partidos: int = 0
    local_victorias: int = 0
    local_gf_promedio: float = 0
    local_gc_promedio: float = 0
    visitante_partidos: int = 0
    visitante_victorias: int = 0
    visitante_gf_promedio: float = 0
    visitante_gc_promedio: float = 0
    # Pilar 3 — balón parado (solo si la liga tiene datos avanzados)
    tiene_datos_balon_parado: bool = False
    pct_peligro_balon_parado: float = 0
    # Pilar 4 — gestión de plantilla
    concentracion_minutos_top5: float = 0
    # Banderas de disponibilidad real de datos (evitan mostrar 0% engañoso)
    tiene_entradas_totales: bool = False
    tiene_datos_avanzados: bool = False
    partidos_equipo: float = 0  # partidos reales jugados por el EQUIPO (no suma de 90s de jugadores)


def _num(df, col):
    if df is None or col not in df.columns:
        return 0
    return pd.to_numeric(df[col], errors="coerce").fillna(0).sum()


def _analizar_situacional(tablas: dict) -> dict:
    """
    Pilar 2: separa el rendimiento en local vs visitante usando matchlogs_for.
    Esta tabla SIEMPRE está disponible (es el calendario de resultados), incluso
    en ligas sin datos avanzados — por eso este pilar nunca queda vacío.
    """
    matchlogs = _buscar_tabla(tablas, ["matchlogs_for"])
    resultado = {}
    if matchlogs is None or "Venue" not in matchlogs.columns:
        return resultado

    df = matchlogs.copy()
    df = df[df["Venue"].isin(["Home", "Away"])]  # descarta filas de encabezado repetido u otros valores raros
    df["GF"] = pd.to_numeric(df.get("GF"), errors="coerce")
    df["GA"] = pd.to_numeric(df.get("GA"), errors="coerce")
    df = df.dropna(subset=["GF", "GA"])

    for venue, prefijo in [("Home", "local"), ("Away", "visitante")]:
        sub = df[df["Venue"] == venue]
        if len(sub) == 0:
            continue
        victorias = (sub["GF"] > sub["GA"]).sum() if "Result" not in sub.columns else (sub["Result"] == "W").sum()
        resultado[f"{prefijo}_partidos"] = len(sub)
        resultado[f"{prefijo}_victorias"] = int(victorias)
        resultado[f"{prefijo}_gf_promedio"] = sub["GF"].mean()
        resultado[f"{prefijo}_gc_promedio"] = sub["GA"].mean()
    return resultado


def _analizar_concentracion_minutos(standard) -> float:
    """
    Pilar 4: qué % de los minutos totales de la temporada se concentran
    en los 5 jugadores más usados. Alto = riesgo de fatiga/lesión en el tramo
    final, típico problema de plantillas cortas con presupuesto limitado.
    """
    if standard is None or "Min" not in standard.columns:
        return 0
    minutos = pd.to_numeric(standard["Min"], errors="coerce").fillna(0)
    total = minutos.sum()
    if total == 0:
        return 0
    top5 = minutos.nlargest(5).sum()
    return (top5 / total) * 100


def analizar_equipo(url: str = None, nombre_equipo: str = "", mostrar_graficos=True, html: str = None):
    """
    LA función que necesitas.

    Opción A (normal): le das la URL de FBref.
        analizar_equipo(url="https://fbref.com/...", nombre_equipo="Beerschot Wilrijk")

    Opción B (si FBref bloquea la IP de Colab con error 403):
        html = leer_html_local("Beerschot-Wilrijk-Stats.html")
        analizar_equipo(html=html, nombre_equipo="Beerschot Wilrijk")
    """
    print(f"🔎 Analizando {nombre_equipo}...")
    if html is None:
        html = _fetch_html(url)
    tablas = _extraer_tablas(html)

    if not tablas:
        print("⚠️  No se encontró ninguna tabla. Verifica la URL o que la página haya cargado bien.")
        return None

    standard = _buscar_tabla(tablas, ["standard"])
    shooting = _buscar_tabla(tablas, ["shooting"])
    passing = _buscar_tabla(tablas, ["passing", "pass"])
    defense = _buscar_tabla(tablas, ["defense", "defensive"])
    possession = _buscar_tabla(tablas, ["possession"])
    misc = _buscar_tabla(tablas, ["misc"])

    e = EstadisticasEquipo(nombre=nombre_equipo)
    e.goles = _num(standard, "Gls") or _num(shooting, "Gls")
    e.tiros = _num(shooting, "Sh")
    e.tiros_al_arco = _num(shooting, "SoT")
    e.xg = _num(shooting, "xG") or _num(standard, "xG")
    e.tiene_xg = e.xg > 0
    e.pases_clave = _num(passing, "KP")
    e.pases_progresivos = _num(passing, "PrgP")
    e.conducciones_progresivas = _num(possession, "PrgC")
    e.regates_exitosos = _num(possession, "Succ")

    # Defensa: preferimos la tabla 'Defense' avanzada si existe (Big 5 ligas).
    # Si no existe (ligas sin cobertura avanzada, ej. 2ª división), usamos Misc como respaldo,
    # que casi siempre trae Int/TklW/Recov aunque no venga el desglose completo por tercio de cancha.
    e.entradas = _num(defense, "Tkl")
    e.tiene_entradas_totales = e.entradas > 0  # 'Tkl' (intentos) no siempre existe, 'TklW' sí
    e.entradas_ganadas = _num(defense, "TklW") or _num(misc, "TklW")
    e.intercepciones = _num(defense, "Int") or _num(misc, "Int")
    e.despejes = _num(defense, "Clr")
    e.errores = _num(defense, "Err") or _num(misc, "Err")
    e.duelos_aereos_ganados = _num(misc, "Won")
    e.duelos_aereos_totales = e.duelos_aereos_ganados + _num(misc, "Lost")
    e.tiene_datos_avanzados = passing is not None or possession is not None
    if passing is not None and "Cmp" in passing.columns and "Att" in passing.columns:
        pases_completados = _num(passing, "Cmp")
        pases_intentados = _num(passing, "Att")
        e.precision_pases = (pases_completados / pases_intentados * 100) if pases_intentados else 0

    # Proxy de calidad de tiro cuando NO hay xG. IMPORTANTE: usamos el TOTAL del
    # equipo (goles totales / tiros totales), no el promedio de G/Sh por jugador
    # — promediar tasas individuales sesga el número (un suplente con 1 tiro y
    # 0 goles pesaría igual que el goleador titular con 80 tiros).
    e.goles_por_tiro = (e.goles / e.tiros) if e.tiros else 0
    e.pct_tiros_al_arco = (e.tiros_al_arco / e.tiros * 100) if e.tiros else 0

    if not e.tiene_xg:
        print("ℹ️  Esta liga no publica xG en FBref (normal en 2ª/3ª división). "
              "El reporte usa G/Sh y SoT% como proxies reales de calidad de tiro.")

    # Pilar 2 — contexto situacional (local/visitante)
    situacional = _analizar_situacional(tablas)
    for k, v in situacional.items():
        setattr(e, k, v)

    # Pilar 3 — balón parado (solo si la liga tiene datos avanzados de GCA Types)
    gca_types = _buscar_tabla(tablas, ["gca"])
    if gca_types is not None and "PassDead" in gca_types.columns:
        e.tiene_datos_balon_parado = True
        vivo = _num(gca_types, "PassLive")
        muerto = _num(gca_types, "PassDead")
        total = vivo + muerto + _num(gca_types, "TO") + _num(gca_types, "Def")
        e.pct_peligro_balon_parado = (muerto / total * 100) if total else 0

    # Pilar 4 — gestión de plantilla (concentración de minutos)
    e.concentracion_minutos_top5 = _analizar_concentracion_minutos(standard)

    # Partidos reales del equipo (denominador correcto para tasas por partido, NO suma de 90s de jugadores)
    matchlogs_tmp = _buscar_tabla(tablas, ["matchlogs_for"])
    if matchlogs_tmp is not None:
        e.partidos_equipo = len(matchlogs_tmp)
    elif standard is not None and "MP" in standard.columns:
        e.partidos_equipo = pd.to_numeric(standard["MP"], errors="coerce").max()

    print("✅ Datos listos.\n")
    _imprimir_reporte(e)
    if mostrar_graficos:
        _graficar_perfil(e)
        _graficar_ataque_defensa(e)

    return e


# ============================================================
# PASO 4: REPORTE DE TEXTO (fortalezas, debilidades, mejoras)
# ============================================================
def _imprimir_reporte(e: EstadisticasEquipo):
    print("=" * 60)
    print(f"REPORTE — {e.nombre}")
    print("   Estructura: 5 Pilares de Competitividad")
    print("=" * 60)

    efectividad_entrada = e.entradas_ganadas / e.entradas if e.entradas else 0
    efectividad_aerea = e.duelos_aereos_ganados / e.duelos_aereos_totales if e.duelos_aereos_totales else 0

    # ---------- PILAR 1: EFICIENCIA SOBRE VOLUMEN ----------
    print("\n🎯 PILAR 1 — EFICIENCIA SOBRE VOLUMEN")
    if e.tiene_xg:
        calidad_tiro = e.xg / e.tiros if e.tiros else 0
        finalizacion = e.goles - e.xg
        print(f"   Ataque: {e.goles:.0f} goles | xG {e.xg:.1f} | {calidad_tiro:.2f} xG/disparo")
        if finalizacion > 2:
            print("   ✅ Sobrerrendimiento de finalización — vigilar, suele normalizarse.")
        elif finalizacion < -2:
            print("   ⚠️  Desperdicia ocasiones claras frente al xG generado.")
    else:
        print(f"   Ataque: {e.goles:.0f} goles | {e.goles_por_tiro:.2f} goles/tiro | {e.pct_tiros_al_arco:.0f}% tiros al arco")
        if e.goles_por_tiro < 0.08:
            print("   ⚠️  Baja eficiencia de finalización — muchos tiros, pocos goles.")
    print(f"   Defensa: {e.entradas_ganadas:.0f} entradas ganadas | {e.intercepciones:.0f} intercepciones | {e.errores:.0f} errores")
    if e.tiene_entradas_totales:
        print(f"      Efectividad de entrada: {efectividad_entrada*100:.0f}%")
        if efectividad_entrada < 0.55:
            print("   ⚠️  Entra mucho, gana poco — revisar timing de la entrada, no volumen.")
    else:
        print("      (Esta liga no publica el total de entradas intentadas, solo las ganadas — no se puede calcular %)")
    if e.duelos_aereos_totales > 0:
        print(f"      Duelos aéreos ganados: {efectividad_aerea*100:.0f}%")
    else:
        print("      (Sin datos de duelos aéreos disponibles en esta liga)")

    # ---------- PILAR 2: CONTEXTO SITUACIONAL ----------
    print("\n🏟️  PILAR 2 — CONTEXTO SITUACIONAL (LOCAL VS VISITANTE)")
    if e.local_partidos or e.visitante_partidos:
        if e.local_partidos:
            print(f"   Local:      {e.local_victorias}/{e.local_partidos} victorias | {e.local_gf_promedio:.1f} GF/partido | {e.local_gc_promedio:.1f} GC/partido")
        if e.visitante_partidos:
            print(f"   Visitante:  {e.visitante_victorias}/{e.visitante_partidos} victorias | {e.visitante_gf_promedio:.1f} GF/partido | {e.visitante_gc_promedio:.1f} GC/partido")
        if e.local_partidos and e.visitante_partidos:
            diff_gf = e.local_gf_promedio - e.visitante_gf_promedio
            diff_gc = e.local_gc_promedio - e.visitante_gc_promedio
            if abs(diff_gf) > 0.4:
                lugar = "en casa" if diff_gf > 0 else "de visitante"
                print(f"   ⚠️  Identidad marcada: rinde notablemente mejor {lugar}. Vale la pena investigar por qué.")
            elif abs(diff_gf) < 0.05 and abs(diff_gc) < 0.05:
                print("   📌 Rendimiento prácticamente idéntico en casa y fuera — consistencia táctica")
                print("      poco común. Vale la pena destacarlo como fortaleza de identidad de equipo.")
    else:
        print("   ℹ️  No se encontró tabla de partidos (matchlogs) en este HTML.")

    # ---------- PILAR 3: BALÓN PARADO ----------
    print("\n⚽ PILAR 3 — BALÓN PARADO")
    if e.tiene_datos_balon_parado:
        print(f"   {e.pct_peligro_balon_parado:.0f}% del peligro ofensivo creado viene de balón parado.")
        if e.pct_peligro_balon_parado > 30:
            print("   ✅ Fuerte dependencia de estrategia — el entrenamiento específico ya rinde, sostenerlo.")
    else:
        print("   ℹ️  FBref no publica desglose de balón parado para esta liga.")
        print("      Alternativa de bajo costo: llevar una planilla manual (Excel/Sheets) marcando")
        print("      cada córner/tiro libre y si terminó en remate — 10 min por partido, dato propio.")

    # ---------- PILAR 4: GESTIÓN DE PLANTILLA ----------
    print("\n👥 PILAR 4 — GESTIÓN DE PLANTILLA")
    if e.concentracion_minutos_top5:
        print(f"   Los 5 jugadores más usados acumulan el {e.concentracion_minutos_top5:.0f}% de los minutos totales.")
        if e.concentracion_minutos_top5 > 45:
            print("   ⚠️  Alta concentración — riesgo de fatiga/lesión en el tramo final. Plantilla corta.")
        else:
            print("   ✅ Buena distribución de minutos — menor riesgo de desgaste en titulares clave.")

    # ---------- PILAR 5: PREPARACIÓN POR RIVAL ----------
    print("\n🔍 PILAR 5 — PREPARACIÓN POR RIVAL")
    print("   Este pilar se trabaja con fbref_match_analyzer.py comparando este equipo")
    print("   contra un rival específico antes de cada partido (no aplica a nivel de temporada).")
    print()


# ============================================================
# PASO 5: GRÁFICOS ELEGANTES
# ============================================================
def _normalizar(valor, minimo, maximo):
    if maximo == minimo:
        return 50
    return max(0, min(100, (valor - minimo) / (maximo - minimo) * 100))


def _graficar_perfil(e: EstadisticasEquipo):
    """
    Radar de perfil general. Se adapta automáticamente según qué datos
    existen de verdad para la liga del equipo — nunca fuerza ejes en 0
    por falta de dato (eso mentiría sobre el rendimiento real).
    """
    if e.tiene_datos_avanzados:
        categorias = ["Calidad\nde tiro", "Progresión", "Regate", "Efectividad\nentrada", "Juego\naéreo", "Precisión\npases"]
        calidad_tiro = (e.xg / e.tiros if e.tiros else 0) if e.tiene_xg else e.goles_por_tiro
        efectividad_entrada = e.entradas_ganadas / e.entradas if e.entradas else 0
        efectividad_aerea = e.duelos_aereos_ganados / e.duelos_aereos_totales if e.duelos_aereos_totales else 0
        valores = [
            _normalizar(calidad_tiro, 0, 0.25),
            _normalizar(e.pases_progresivos + e.conducciones_progresivas, 0, 800),
            _normalizar(e.regates_exitosos, 0, 150),
            _normalizar(efectividad_entrada, 0.3, 0.75),
            _normalizar(efectividad_aerea, 0.3, 0.7),
            _normalizar(e.precision_pases, 65, 90),
        ]
    else:
        # Versión básica: solo ejes que SÍ existen en ligas sin Passing/Possession
        # (ej. segundas/terceras divisiones). Usamos tasas por 90' en vez de %
        # cuando el denominador total no está disponible.
        partidos = e.partidos_equipo if e.partidos_equipo else 20  # respaldo razonable si no hay dato
        categorias = ["Eficiencia\nde gol", "Tiros\nal arco", "Entradas\nganadas/90", "Intercep.\n/90", "Disciplina\n(errores)", "Distribución\nde minutos"]
        valores = [
            _normalizar(e.goles_por_tiro, 0, 0.20),
            _normalizar(e.pct_tiros_al_arco, 20, 50),
            _normalizar(e.entradas_ganadas / partidos, 5, 20),
            _normalizar(e.intercepciones / partidos, 2, 12),
            _normalizar(10 - e.errores, 0, 10),  # menos errores = mejor
            _normalizar(100 - e.concentracion_minutos_top5, 40, 70),  # más repartido = mejor
        ]

    N = len(categorias)
    angulos = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    valores += valores[:1]
    angulos += angulos[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angulos, valores, color=COLOR_ACENTO_1, linewidth=2.5)
    ax.fill(angulos, valores, color=COLOR_ACENTO_1, alpha=0.25)
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, fontsize=10, fontweight="bold")
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color=COLOR_GRID)
    ax.spines["polar"].set_color(COLOR_GRID)
    ax.grid(color=COLOR_GRID, alpha=0.5)
    plt.title(f"Perfil de Rendimiento — {e.nombre}", fontsize=14, fontweight="bold", color=COLOR_TEXTO, pad=20)
    plt.tight_layout()
    plt.show()


def _graficar_ataque_defensa(e: EstadisticasEquipo):
    """Barras horizontales: números clave de un vistazo."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    ataque_labels = ["Goles", "xG", "Tiros al arco", "Pases clave"]
    ataque_vals = [e.goles, e.xg, e.tiros_al_arco, e.pases_clave]
    axes[0].barh(ataque_labels, ataque_vals, color=COLOR_ACENTO_1)
    axes[0].set_title("Ataque — Temporada", fontsize=12, fontweight="bold")
    axes[0].invert_yaxis()
    for i, v in enumerate(ataque_vals):
        axes[0].text(v, i, f" {v:.1f}", va="center", fontsize=9)

    defensa_labels = ["Entradas\nganadas", "Intercepciones", "Despejes", "Errores"]
    defensa_vals = [e.entradas_ganadas, e.intercepciones, e.despejes, e.errores]
    axes[1].barh(defensa_labels, defensa_vals, color=COLOR_ACENTO_2)
    axes[1].set_title("Defensa — Temporada", fontsize=12, fontweight="bold")
    axes[1].invert_yaxis()
    for i, v in enumerate(defensa_vals):
        axes[1].text(v, i, f" {v:.0f}", va="center", fontsize=9)

    for ax in axes:
        ax.grid(axis="x", color=COLOR_GRID, alpha=0.4)
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.suptitle(f"{e.nombre} — Números Clave", fontsize=13, fontweight="bold", color=COLOR_TEXTO)
    plt.tight_layout()
    plt.show()
