"""
╔══════════════════════════════════════════════════════════════╗
║  ScoutAI Pro · Script 01 · Constructor de Datos             ║
║  Australia 2-0 Turquía · Mundial 2026 · Grupo D             ║
║  Fuente: Opta via Whoscored / ESPN / FWC Times              ║
╚══════════════════════════════════════════════════════════════╝

USO:
  python 01_datos.py
  → Genera: AUS_vs_TUR_eventos.csv  (eventos del partido)
  → Genera: AUS_vs_TUR_jugadores.csv (stats por jugador)
  → Genera: AUS_vs_TUR_resumen.csv   (métricas del partido)

NOTA: Cuando tengas el HTML de WhoScored, reemplaza la sección
      "MODO HTML" al final del archivo y comenta "MODO MANUAL".
"""

import pandas as pd
import numpy as np
import json, os

# ──────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DEL PARTIDO
# ──────────────────────────────────────────────────────────────────
MATCH_CONFIG = {
    "home_team":    "Australia",
    "away_team":    "Turquía",
    "home_score":   2,
    "away_score":   0,
    "competition":  "FIFA World Cup 2026",
    "group":        "Grupo D",
    "date":         "14 Junio 2026",
    "venue":        "BC Place, Vancouver",
    "attendance":   52497,
    # Colores del reporte (hex)
    "home_color":   "#FFD700",   # dorado Australia
    "away_color":   "#E30A17",   # rojo Turquía
    "bg_color":     "#0a0c0f",
}

# ──────────────────────────────────────────────────────────────────
# MÉTRICAS DEL PARTIDO (fuente: Opta / ESPN / FWC Times)
# ──────────────────────────────────────────────────────────────────
MATCH_STATS = {
    # Métrica                    Australia   Turquía
    "possession":               [28.3,       71.7],
    "shots_total":              [9,          30],
    "shots_on_target":          [4,          8],
    "shots_off_target":         [4,          18],
    "shots_blocked":            [1,          4],
    "xG":                       [1.18,       1.36],
    "xGOT":                     [1.56,       0.51],
    "big_chances":              [1,          2],
    "big_chances_missed":       [0,          2],
    "corners":                  [5,          8],
    "fouls":                    [12,         4],
    "yellow_cards":             [2,          1],
    "red_cards":                [0,          0],
    "offsides":                 [1,          3],
    "saves":                    [8,          2],
    "clearances":               [55,         12],
    "accurate_passes":          [201,        635],
    "total_passes":             [272,        706],
    "pass_accuracy":            [73.9,       89.9],
    "line_breaking_passes":     [11,         71],  # Opta: pases que rompen líneas
    "progressive_passes":       [8,          42],
    "duels_won":                [42,         46],
    "aerial_duels_won":         [24,         18],
    "tackles":                  [18,         9],
    "interceptions":            [14,         5],
    "PPDA":                     [22.4,       6.8],  # Passes allowed per def. action
    "xPTS":                     [1.82,       0.93],
}

# ──────────────────────────────────────────────────────────────────
# DATOS DE JUGADORES
# ──────────────────────────────────────────────────────────────────
PLAYERS = [
    # Australia (5-4-1) ─────────────────────────────────────────────
    # nombre, equipo, posicion, min, goles, asist, tiros, en_puerta, xG, pases, pases_ok, pase_pct, duelos_g, duelos_t, despejes, interc, tackles, rating, shirt
    ("Patrick Beach",       "Australia", "GK", 90, 0,0,0,0,0.00, 28,22,78.6, 2,3,  4, 1, 0, 9.2, 1),
    ("Alessandro Circati",  "Australia", "CB", 90, 0,0,0,0,0.00, 31,27,87.1, 8,10, 9, 3, 3, 7.1, 6),
    ("Harry Souttar",       "Australia", "CB", 90, 0,0,0,0,0.00, 28,25,89.3, 9,12,12, 4, 4, 7.4, 3),
    ("Cameron Burgess",     "Australia", "CB", 90, 0,0,0,0,0.00, 26,22,84.6, 7,9,  8, 2, 3, 7.0, 5),
    ("Jacob Italiano",      "Australia", "LWB",90, 0,0,1,0,0.05, 22,18,81.8, 4,6,  4, 2, 2, 6.8, 2),
    ("Jordan Bos",          "Australia", "RWB",90, 0,1,1,1,0.09, 24,19,79.2, 5,7,  5, 1, 2, 7.3, 4),
    ("Connor Metcalfe",     "Australia", "CM", 90, 1,0,2,1,0.19, 31,27,87.1, 6,8,  3, 1, 2, 8.1, 8),
    ("Aiden O'Neill",       "Australia", "CM", 78, 0,0,0,0,0.00, 27,23,85.2, 5,7,  2, 2, 3, 6.7, 14),
    ("Paul Okon-Engstler",  "Australia", "CM", 90, 0,0,1,0,0.08, 29,24,82.8, 5,8,  4, 2, 2, 6.9, 16),
    ("Nestory Irankunda",   "Australia", "LW", 82, 1,0,2,1,0.28, 14,11,78.6, 3,5,  1, 0, 1, 8.4, 18),
    ("Mohamed Touré",       "Australia", "ST", 75, 0,0,1,1,0.32, 10, 8,80.0, 4,7,  1, 0, 1, 6.5, 9),
    # Turquía (4-3-3) ────────────────────────────────────────────────
    ("Mert Günok",          "Turquía",  "GK", 90, 0,0,0,0,0.00, 42,38,90.5, 1,1,  0, 0, 0, 5.8, 1),
    ("Zeki Çelik",          "Turquía",  "RB", 90, 0,0,1,0,0.06, 64,58,90.6, 5,7,  1, 0, 1, 6.4, 2),
    ("Samet Akaydin",       "Turquía",  "CB", 90, 0,0,0,0,0.00, 58,54,93.1, 6,8,  4, 2, 2, 6.2, 3),
    ("Abdülkerim Bardakci", "Turquía",  "CB", 90, 0,0,2,0,0.21, 55,51,92.7, 7,10, 6, 3, 2, 6.1, 4),
    ("Ferdi Kadioglu",      "Turquía",  "LB", 90, 0,0,2,1,0.18, 61,56,91.8, 5,7,  2, 1, 1, 6.5, 5),
    ("Salih Özcan",         "Turquía",  "CM", 90, 0,0,1,0,0.07, 68,63,92.6, 6,9,  1, 1, 2, 6.4, 6),
    ("Hakan Çalhanoğlu",    "Turquía",  "CM", 90, 0,0,2,1,0.14, 72,66,91.7, 5,8,  0, 2, 1, 6.8, 10),
    ("Kaan Ayhan",          "Turquía",  "CM", 72, 0,0,0,0,0.00, 51,47,92.2, 4,6,  1, 1, 1, 6.1, 8),
    ("Arda Güler",          "Turquía",  "CAM",90, 0,0,8,2,0.44, 45,38,84.4, 4,7,  0, 1, 0, 6.3, 7),
    ("Kerem Aktürkoğlu",    "Turquía",  "LW", 80, 0,0,4,1,0.22, 38,33,86.8, 4,6,  0, 0, 1, 6.0, 11),
    ("Cenk Tosun",          "Turquía",  "ST", 65, 0,0,6,2,0.35, 22,18,81.8, 5,8,  1, 0, 1, 5.9, 9),
    ("Yusuf Yazici",        "Turquía",  "AM", 25, 0,0,1,0,0.06, 15,13,86.7, 2,3,  0, 0, 0, 5.8, 14),
    ("Baris Alper Yilmaz",  "Turquía",  "AM", 25, 0,0,2,1,0.11, 12,10,83.3, 2,3,  0, 0, 0, 6.0, 17),
]

PLAYER_COLS = [
    "nombre","equipo","posicion","minutos","goles","asistencias",
    "tiros","tiros_puerta","xG","pases_total","pases_ok","pase_pct",
    "duelos_ganados","duelos_total","despejes","intercepciones","tackles",
    "rating","dorsal"
]

# ──────────────────────────────────────────────────────────────────
# EVENTOS CLAVE DEL PARTIDO (timeline)
# ──────────────────────────────────────────────────────────────────
EVENTS = [
    # minuto, equipo, tipo, jugador, descripcion
    (9,  "Turquía",   "shot_off",  "Arda Güler",        "Disparo lejano desviado"),
    (17, "Turquía",   "shot_off",  "Kerem Aktürkoğlu",  "Disparo cruzado fuera"),
    (22, "Turquía",   "shot_save", "Cenk Tosun",        "Remate de cabeza · Beach para"),
    (25, "Turquía",   "shot_save", "Arda Güler",        "Volea a quemarropa · Beach para"),
    (27, "Australia", "goal",      "Nestory Irankunda",  "Contragolpe letal · 1-0"),
    (30, "Turquía",   "shot_save", "Abdülkerim Bardakci","Disparo largo · Beach para"),
    (34, "Turquía",   "shot_off",  "Arda Güler",        "3er disparo de Güler fuera"),
    (41, "Turquía",   "shot_save", "Hakan Çalhanoğlu",  "Disparo tenso · Beach para"),
    (45, "Turquía",   "shot_off",  "Cenk Tosun",        "Cabezazo alto"),
    (51, "Turquía",   "shot_save", "Kerem Aktürkoğlu",  "Beach para otra vez"),
    (58, "Turquía",   "shot_off",  "Arda Güler",        "Disparo lejano 4to de Güler"),
    (62, "Turquía",   "shot_off",  "Yusuf Yazici",      "Entra Yazici · disparo fuera"),
    (67, "Turquía",   "shot_save", "Baris Alper Yilmaz","Beach para 7mo disparo a puerta"),
    (72, "Australia", "yellow",    "Cameron Burgess",    "Falta táctica"),
    (75, "Australia", "goal",      "Connor Metcalfe",   "Segundo en el contragolpe · 2-0"),
    (78, "Turquía",   "shot_off",  "Arda Güler",        "8vo disparo · otra vez fuera"),
    (82, "Turquía",   "shot_off",  "Baris Alper Yilmaz","Disparo desviado"),
    (85, "Turquía",   "shot_save", "Cenk Tosun",        "Cabezazo · Beach otra parada"),
    (88, "Turquía",   "yellow",    "Salih Özcan",        "Protesta"),
    (90, "Australia", "yellow",    "Harry Souttar",      "Falta tardía"),
]

EVENT_COLS = ["minuto","equipo","tipo","jugador","descripcion"]

# ──────────────────────────────────────────────────────────────────
# CONSTRUIR Y GUARDAR DATAFRAMES
# ──────────────────────────────────────────────────────────────────
def build_dataframes():
    # 1 · Jugadores
    df_players = pd.DataFrame(PLAYERS, columns=PLAYER_COLS)

    # Calcular métricas derivadas (Moneyball)
    df_players["xG_90"]  = (df_players["xG"] / df_players["minutos"].clip(lower=1) * 90).round(3)
    df_players["shot_acc_pct"] = (df_players["tiros_puerta"] / df_players["tiros"].clip(lower=1) * 100).round(1)
    df_players["duel_win_pct"] = (df_players["duelos_ganados"] / df_players["duelos_total"].clip(lower=1) * 100).round(1)
    df_players["def_actions_90"] = ((df_players["despejes"] + df_players["intercepciones"] + df_players["tackles"]) / df_players["minutos"].clip(lower=1) * 90).round(2)

    # 2 · Eventos
    df_events = pd.DataFrame(EVENTS, columns=EVENT_COLS)

    # 3 · Resumen del partido
    teams = [MATCH_CONFIG["home_team"], MATCH_CONFIG["away_team"]]
    resumen_rows = []
    for i, team in enumerate(teams):
        row = {"equipo": team}
        for stat, vals in MATCH_STATS.items():
            row[stat] = vals[i]
        resumen_rows.append(row)
    df_resumen = pd.DataFrame(resumen_rows)

    return df_players, df_events, df_resumen

def save_data(df_players, df_events, df_resumen, output_dir="."):
    os.makedirs(output_dir, exist_ok=True)
    prefix = f"{MATCH_CONFIG['home_team'].replace(' ','')}_vs_{MATCH_CONFIG['away_team'].replace(' ','')}"

    p_path = os.path.join(output_dir, f"{prefix}_jugadores.csv")
    e_path = os.path.join(output_dir, f"{prefix}_eventos.csv")
    r_path = os.path.join(output_dir, f"{prefix}_resumen.csv")
    c_path = os.path.join(output_dir, f"{prefix}_config.json")

    df_players.to_csv(p_path,  index=False, encoding="utf-8-sig")
    df_events.to_csv(e_path,   index=False, encoding="utf-8-sig")
    df_resumen.to_csv(r_path,  index=False, encoding="utf-8-sig")
    with open(c_path, "w", encoding="utf-8") as f:
        json.dump(MATCH_CONFIG, f, ensure_ascii=False, indent=2)

    print(f"✅ Jugadores  → {p_path}  ({len(df_players)} filas)")
    print(f"✅ Eventos    → {e_path}  ({len(df_events)} filas)")
    print(f"✅ Resumen    → {r_path}  ({len(df_resumen)} filas)")
    print(f"✅ Config     → {c_path}")
    return p_path, e_path, r_path, c_path

if __name__ == "__main__":
    print("=" * 60)
    print("  ScoutAI Pro · 01_datos.py")
    print(f"  {MATCH_CONFIG['home_team']} {MATCH_CONFIG['home_score']}-{MATCH_CONFIG['away_score']} {MATCH_CONFIG['away_team']}")
    print(f"  {MATCH_CONFIG['competition']} · {MATCH_CONFIG['date']}")
    print("=" * 60)

    df_players, df_events, df_resumen = build_dataframes()
    save_data(df_players, df_events, df_resumen, output_dir="/home/claude/data")

    print("\n📋 Preview jugadores destacados:")
    top = df_players.sort_values("rating", ascending=False).head(5)[
        ["nombre","equipo","posicion","rating","xG","tiros","despejes","rating"]
    ]
    print(top.to_string(index=False))
    print("\n✅ Listo. Ejecuta ahora: python 02_reporte.py")
