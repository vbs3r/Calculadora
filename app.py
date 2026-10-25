import streamlit as st
import itertools
import math

# ============================================================
# LÓGICA MATEMÁTICA
# ============================================================
E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

COLOR_CODE = {
    0: "#000000", 1: "#8B4513", 2: "#FF0000", 3: "#FF8C00",
    4: "#FFD700", 5: "#00FF00", 6: "#0000FF", 7: "#8A2BE2",
    8: "#808080", 9: "#FFFFFF",
}
MULT_COLORS = {-1: "#FFD700", -2: "#C0C0C0"}

def generar_valores_comerciales(serie, max_decadas=6):
    valores = []
    for decada in range(max_decadas):
        for v in serie:
            valores.append(round(v * (10 ** decada), 2))
    return sorted(valores)

def obtener_lista_resistencias(tolerancia):
    return generar_valores_comerciales(E12 if tolerancia >= 10 else E24)

def _topologias_3r(a, b, c):
    opciones = {}
    for sola, p1, p2 in [(a, b, c), (b, a, c), (c, a, b)]:
        den = p1 + p2 + sola
        if den > 0:
            v = (p1 + p2) * sola / den
            opciones[f"({p1:g}+{p2:g})||{sola:g}"] = ('Serie-Paralelo', v)
        if p1 + p2 > 0:
            v = p1 * p2 / (p1 + p2) + sola
            opciones[f"({p1:g}||{p2:g})+{sola:g}"] = ('Paralelo-Serie', v)
    return [(t, v, e) for e, (t, v) in opciones.items()]

def encontrar_mejores_combinaciones(target, resistencias, tolerancia_pct):
    resultados = []
    for r in range(1, 4):
        for combo in itertools.combinations_with_replacement(resistencias, r):
            v = sum(combo)
            err = abs(v - target) / target * 100
            if err <= tolerancia_pct:
                resultados.append({'tipo': 'Serie',
                    'expresion': ' + '.join(f"{x:g}" for x in combo),
                    'combinacion': combo, 'valor_eq': round(v, 2),
                    'error': round(err, 3), 'n': r})
            if r > 1:
                v = 1 / sum(1/x for x in combo)
                err = abs(v - target) / target * 100
                if err <= tolerancia_pct:
                    resultados.append({'tipo': 'Paralelo',
                        'expresion': ' || '.join(f"{x:g}" for x in combo),
                        'combinacion': combo, 'valor_eq': round(v, 2),
                        'error': round(err, 3), 'n': r})
            if r == 3:
                for tipo, v, expr in _topologias_3r(*combo):
                    err = abs(v - target) / target * 100
                    if err <= tolerancia_pct:
                        resultados.append({'tipo': tipo, 'expresion': expr,
                            'combinacion': combo, 'valor_eq': round(v, 2),
                            'error': round(err, 3), 'n': r})
    vistos, unicos = set(), []
    for r in resultados:
        k = (r['expresion'], r['valor_eq'])
        if k not in vistos:
            vistos.add(k); unicos.append(r)
    return sorted(unicos, key=lambda x: (x['error'], x['n']))

def bandas_resistor(valor, tolerancia_pct=5.0):
    if valor <= 0: return None
    try:
        exp = int(math.floor(math.log10(valor)))
        scaled = round(valor / (10 ** exp) * 10)
        if scaled >= 100:
            scaled //= 10
            exp += 1
        if scaled < 10: return None
        d1, d2 = divmod(scaled, 10)
        idx = exp - 1
        band3 = COLOR_CODE.get(idx) if idx >= 0 else MULT_COLORS.get(idx, "#888888")

        if tolerancia_pct <= 1.0: band4 = "#8B4513"
        elif tolerancia_pct <= 2.0: band4 = "#FF0000"
        elif tolerancia_pct <= 5.0: band4 = "#FFD700"
        else: band4 = "#C0C0C0"

        return [COLOR_CODE.get(d1, "#888888"), COLOR_CODE.get(d2, "#888888"), band3, band4]
    except (ValueError, OverflowError):
        return None

# ============================================================
# INTERFAZ GRÁFICA (STREAMLIT)
# ============================================================
st.set_page_config(page_title="Calculadora de Resistencias", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.card { padding: 20px; border-radius: 12px; margin-bottom: 20px; }
.card-gold { background-color: #fdf0ba; border: 3px solid #f59e0b; }
.card-silver { background-color: #d4dfec; border: 2px solid #9ca3af; }
.card-bronze { background-color: #f0e8e0; border: 2px solid #b45309; }
.resistor-container { display: flex; align-items: center; margin: 10px 0; }
.resistor-lead { width: 15px; height: 3px; background-color: #9aa0a8; }
.resistor-body { width: 70px; height: 24px; background-color: #e8d4a8; border: 1px solid #8b7355; border-radius: 4px; display: flex; justify-content: space-evenly; align-items: center; }
.band { width: 5px; height: 100%; }
.val-eq { font-size: 24px; font-weight: bold; color: #0f0f0f; margin: 0; }
.err-chip { display: inline-block; padding: 4px 8px; border-radius: 6px; color: white; font-weight: bold; font-size: 14px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Calculadora de Resistencias")
st.markdown("Encuentra la combinación perfecta con resistencias comerciales :D")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    objetivo = st.number_input("VALOR DESEADO (Ω)", min_value=0.1, value=500.0, step=10.0)
with col2:
    tolerancia = st.number_input("TOLERANCIA (%)", min_value=0.1, value=5.0, step=1.0)
with col3:
    st.write("")
    st.write("")
    buscar = st.button("🔍 Buscar combinaciones", use_container_width=True, type="primary")

def render_resistor(valor, tol):
    bands = bandas_resistor(valor, tol)
    if not bands: return f"<div style='color: #000000;'>{valor} Ω</div>"
    band_divs = "".join([f'<div class="band" style="background-color: {color};"></div>' for color in bands])
    # Añadimos 'color: #000000;' al span para forzar el color negro
    return f"""<div style="display: flex; flex-direction: column; align-items: center;">
<div class="resistor-container">
<div class="resistor-lead"></div>
<div class="resistor-body">{band_divs}</div>
<div class="resistor-lead"></div>
</div>
<span style="font-family: monospace; font-size: 14px; color: #000000; font-weight: bold;">{valor:g} Ω</span>
</div>"""

if buscar:
    with st.spinner("Calculando combinaciones..."):
        resistencias = obtener_lista_resistencias(tolerancia)
        etiqueta = "E12" if tolerancia >= 10 else "E24"
        resultados = encontrar_mejores_combinaciones(objetivo, resistencias, tolerancia)
        
    if not resultados:
        st.error("❌ Nada dentro de la tolerancia. Prueba a subir el %.")
    else:
        st.success(f"✅ Top {min(3, len(resultados))} de {len(resultados)} combinaciones · Serie {etiqueta}")
        
        top = resultados[:3]
        estilos = [
            ("card-gold", "#ca8a04", "MEJOR OPCIÓN"),
            ("card-silver", "#6b7280", ""),
            ("card-bronze", "#92400e", "")
        ]
        
        for i, r in enumerate(top):
            clase_css, color_badge, texto_badge = estilos[i]
            err = r['error']
            if err < 1.0: err_bg = "#1e8e3e"
            elif err < 3.0: err_bg = "#5e9c1a"
            elif err < 7.0: err_bg = "#e67e00"
            else: err_bg = "#d32f2f"

            # CONSTRUCCIÓN DEL HTML SIN ESPACIOS AL PRINCIPIO
            html_card = f"""<div class="card {clase_css}" style="display: flex; align-items: center; gap: 20px;">
<div style="background-color: {color_badge}; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 20px;">
#{i+1}
</div>
<div style="flex-grow: 1;">
<div style="margin-bottom: 5px;">
<span style="background-color: {color_badge}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 10px;">{texto_badge}</span>
<strong style="color: #606060;">{r['tipo'].upper()}</strong> &nbsp;|&nbsp; 
<span style="font-family: monospace; font-size: 16px; font-weight: bold;">{r['expresion']}</span>
</div>
<div style="display: flex; gap: 15px; flex-wrap: wrap; background: white; padding: 10px; border-radius: 8px; width: fit-content;">"""
            
            for val in r['combinacion']:
                html_card += render_resistor(val, tolerancia)
                
            html_card += f"""</div>
</div>
<div style="text-align: right; min-width: 120px;">
<p class="val-eq">{r['valor_eq']:.2f} Ω</p>
<div class="err-chip" style="background-color: {err_bg};">Error: {err:.3f}%</div>
</div>
</div>"""
            
            st.markdown(html_card, unsafe_allow_html=True)
