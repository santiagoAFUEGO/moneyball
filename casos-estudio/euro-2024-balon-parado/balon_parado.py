"""
Análisis de Balón Parado - StatsBomb Open Data
Métricas propias: ISA, xGxBP, TRSJ
"""
from statsbombpy import sb
import pandas as pd

def extraer_tiros_balon_parado(match_id):
    """
    Extrae tiros de córner y falta directa de un partido,
    calculando superioridad numérica en el área usando freeze frames.
    """
    events = sb.events(match_id=match_id)
    shots = events[events['type'] == 'Shot'].copy()
    passes = events[events['type'] == 'Pass'][['id', 'pass_type']].rename(
        columns={'id': 'pass_id', 'pass_type': 'tipo_pase_asistencia'}
    )

    # Cruzar cada tiro con el pase que lo asistió (para detectar corners)
    # Nota: 'shots' ya trae su propia columna 'pass_type' heredada del esquema
    # general de eventos (vacía para tiros) -> por eso renombramos la del merge
    # para evitar colisión pass_type_x/pass_type_y, igual que el problema de
    # cabeceras duplicadas de FBref.
    shots = shots.merge(
        passes, left_on='shot_key_pass_id', right_on='pass_id', how='left'
    )

    # Clasificar origen: Free Kick directo O asistido por córner
    shots['origen_bp'] = None
    shots.loc[shots['shot_type'] == 'Free Kick', 'origen_bp'] = 'Falta directa'
    shots.loc[shots['tipo_pase_asistencia'] == 'Corner', 'origen_bp'] = 'Corner'

    bp = shots[shots['origen_bp'].notna()].copy()
    if bp.empty:
        return pd.DataFrame()

    # Calcular superioridad numérica LOCAL: jugadores propios vs rivales dentro
    # de un radio de 8m alrededor del punto de remate (la zona real de disputa).
    # Nota: medir superioridad sobre el área completa da 0.0 en el 100% de los
    # casos -> el equipo defensor casi siempre iguala o supera en jugadores
    # totales dentro del área durante un balón parado (arquero + línea completa).
    # Lo que de verdad diferencia una buena jugada es el desequilibrio LOCAL
    # justo donde cae el balón, no el conteo global.
    RADIO_LOCAL = 8.0

    def contar_superioridad_local(row):
        freeze_frame = row['shot_freeze_frame']
        loc_tiro = row['location']
        if not isinstance(freeze_frame, list) or not isinstance(loc_tiro, list):
            return None
        x0, y0 = loc_tiro
        propios = rivales = 0
        for j in freeze_frame:
            jx, jy = j['location']
            dist = ((jx - x0) ** 2 + (jy - y0) ** 2) ** 0.5
            if dist <= RADIO_LOCAL:
                if j.get('teammate') is True:
                    propios += 1
                elif j.get('teammate') is False:
                    rivales += 1
        return propios - rivales  # >0 = superioridad local atacante

    bp['superioridad'] = bp.apply(contar_superioridad_local, axis=1)
    bp['es_gol'] = bp['shot_outcome'] == 'Goal'
    bp['a_puerta'] = bp['shot_outcome'].isin(['Goal', 'Saved'])
    bp['match_id'] = match_id

    return bp[['match_id', 'team', 'origen_bp', 'shot_statsbomb_xg',
                'es_gol', 'a_puerta', 'superioridad']]


def calcular_metricas(df_bp):
    """
    Calcula ISA, xGxBP por equipo a partir de todos los tiros de balón parado.
    """
    resumen = df_bp.groupby('team').agg(
        total_jugadas_bp=('origen_bp', 'count'),
        goles_bp=('es_gol', 'sum'),
        xg_bp=('shot_statsbomb_xg', 'sum'),
        remates_puerta_bp=('a_puerta', 'sum'),
        jugadas_con_superioridad=('superioridad', lambda x: (x > 0).sum()),
        jugadas_con_freeze_frame=('superioridad', lambda x: x.notna().sum())
    ).reset_index()

    resumen['xGxBP'] = (resumen['xg_bp'] / resumen['total_jugadas_bp']).round(3)
    resumen['pct_a_puerta'] = (resumen['remates_puerta_bp'] / resumen['total_jugadas_bp']).round(3)
    resumen['ISA'] = (resumen['jugadas_con_superioridad'] / resumen['jugadas_con_freeze_frame']).round(3)

    return resumen.sort_values('xGxBP', ascending=False)


if __name__ == '__main__':
    matches = sb.matches(competition_id=55, season_id=282)  # Euro 2024
    match_ids = matches['match_id'].tolist()

    print(f"Procesando {len(match_ids)} partidos de Euro 2024...")
    todas = []
    for i, mid in enumerate(match_ids):
        try:
            bp = extraer_tiros_balon_parado(mid)
            if not bp.empty:
                todas.append(bp)
        except Exception as e:
            print(f"  Error en partido {mid}: {e}")
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(match_ids)} partidos procesados")

    df_total = pd.concat(todas, ignore_index=True)
    df_total.to_csv('/home/claude/tiros_balon_parado_raw.csv', index=False)

    resumen = calcular_metricas(df_total)
    resumen.to_csv('/home/claude/resumen_metricas_bp.csv', index=False)

    print(f"\nTotal jugadas de balón parado analizadas: {len(df_total)}")
    print("\nTop 10 equipos por xGxBP:")
    print(resumen[['team', 'total_jugadas_bp', 'goles_bp', 'xGxBP', 'ISA', 'pct_a_puerta']].head(10).to_string(index=False))
