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
    if "Player" in df.columns:
        df = df[df["Player"] != "Player"]
        df = df[~df["Player"].isin(["Squad Total", "Opponent Total", "Players Used"])]
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


def _num(df, col):
    if df is None or col not in df.columns:
        return 0
    return pd.to_numeric(df[col], errors="coerce").fillna(0).sum()


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
    e.pases_clave = _num(passing, "KP")
    e.pases_progresivos = _num(passing, "PrgP")
    e.conducciones_progresivas = _num(possession, "PrgC")
    e.regates_exitosos = _num(possession, "Succ")
    e.entradas = _num(defense, "Tkl")
    e.entradas_ganadas = _num(defense, "TklW")
    e.intercepciones = _num(defense, "Int")
    e.despejes = _num(defense, "Clr")
    e.errores = _num(defense, "Err") or _num(misc, "Err")
    e.duelos_aereos_ganados = _num(misc, "Won")
    e.duelos_aereos_totales = e.duelos_aereos_ganados + _num(misc, "Lost")
    if passing is not None and "Cmp%" in passing.columns:
        e.precision_pases = pd.to_numeric(passing["Cmp%"], errors="coerce").mean()

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
    print("=" * 60)

    calidad_tiro = e.xg / e.tiros if e.tiros else 0
    finalizacion = e.goles - e.xg
    efectividad_entrada = e.entradas_ganadas / e.entradas if e.entradas else 0
    efectividad_aerea = e.duelos_aereos_ganados / e.duelos_aereos_totales if e.duelos_aereos_totales else 0

    print("\n⚔️  ATAQUE")
    print(f"   Goles: {e.goles:.0f}  |  xG: {e.xg:.1f}  |  Calidad de tiro: {calidad_tiro:.2f} xG/disparo")
    if finalizacion > 2:
        print("   ✅ Sobrerrendimiento de finalización — cuidado, esto suele normalizarse con el tiempo.")
    elif finalizacion < -2:
        print("   ⚠️  Desperdicia ocasiones claras frente al xG generado. Revisar finalización.")
    else:
        print("   ➖ Finalización acorde a lo esperado por xG.")

    print("\n🛡️  DEFENSA")
    print(f"   Entradas ganadas: {efectividad_entrada*100:.0f}%  |  Errores: {e.errores:.0f}  |  Duelos aéreos: {efectividad_aerea*100:.0f}%")
    if efectividad_entrada < 0.55:
        print("   ⚠️  Baja efectividad en el duelo — entra mucho pero gana poco. Revisar timing de la entrada.")
    if efectividad_aerea < 0.45:
        print("   ⚠️  Débil en el juego aéreo defensivo. Vigilar en jugadas a balón parado.")

    print("\n🎯 A MEJORAR")
    if calidad_tiro < 0.10:
        print("   - Buscar mejor posición antes de rematar (baja calidad de tiro).")
    if efectividad_entrada < 0.55:
        print("   - Trabajar anticipación defensiva en vez de solo volumen de entradas.")
    if e.errores > 5:
        print("   - Revisar en qué zona se concentran los errores defensivos.")
    print()


# ============================================================
# PASO 5: GRÁFICOS ELEGANTES
# ============================================================
def _normalizar(valor, minimo, maximo):
    if maximo == minimo:
        return 50
    return max(0, min(100, (valor - minimo) / (maximo - minimo) * 100))


def _graficar_perfil(e: EstadisticasEquipo):
    """Radar de perfil general del equipo."""
    categorias = ["Calidad\nde tiro", "Progresión", "Regate", "Efectividad\nentrada", "Juego\naéreo", "Precisión\npases"]

    calidad_tiro = e.xg / e.tiros if e.tiros else 0
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
