import streamlit as st
import itertools
import math

# ============================================================
# LÓGICA MATEMÁTICA (Idéntica)
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

TINKER_COLORS = [
    "#e74c3c", "#e67e22", "#f1c40f", "#27ae60", "#2ecc71", 
    "#a2d149", "#2980b9", "#3498db", "#5dade2"
]

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

.stApp {
    background-color: #f9f9f9 !important;
    font-family: 'Inter', sans-serif !important;
    color: #0f0f0f !important;
}
[data-testid="stHeader"] { background-color: transparent !important; }
[data-testid="stToolbar"] { right: 2rem; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stNumberInput > div > div > input {
    background-color: #f2f2f2 !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 10px !important;
    color: #0f0f0f !important;
    font-size: 16px !important;
    font-family: 'Inter', sans-serif !important;
    height: 45px !important;
}
.stNumberInput > div > div > input:focus {
    border-color: #ff0000 !important;
    box-shadow: 0 0 0 1px #ff0000 !important;
}
.stNumberInput label {
    color: #606060 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.stButton > button {
    background-color: #ff0000 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    height: 45px !important;
    width: 100%;
    transition: background-color 0.2s;
}
.stButton > button:hover { background-color: #cc0000 !important; color: white !important;}
.stButton > button:focus:not(:active) { color: white !important; border-color: transparent !important;}

/* ARREGLO: Aplicamos padding y border-radius juntos a las tarjetas de colores */
.card-gold, .card-silver, .card-bronze { 
    padding: 16px; 
    border-radius: 12px !important; 
    margin-bottom: 12px; 
    box-sizing: border-box;
    overflow: hidden;
}
.card-gold { background-color: #fdf0ba; border: 3px solid #f59e0b; }
.card-silver { background-color: #d4dfec; border: 2px solid #9ca3af; }
.card-bronze { background-color: #f0e8e0; border: 2px solid #b45309; }

.resistor-container { display: flex; align-items: center; margin: 8px 0; }
.resistor-lead { width: 15px; height: 3px; background-color: #9aa0a8; }
.resistor-body { width: 70px; height: 24px; background-color: #e8d4a8; border: 1px solid #8b7355; border-radius: 4px; display: flex; justify-content: space-evenly; align-items: center; }
.band { width: 5px; height: 100%; }

.val-eq { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: #0f0f0f; margin: 0; }
.err-chip { font-family: 'JetBrains Mono', monospace; display: inline-block; padding: 4px 10px; border-radius: 6px; color: white; font-weight: 700; font-size: 14px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

words = ["CALCULADORA", "DE", "RESISTENCIAS"]
color_idx = 0
title_html = '<div style="text-align: center; margin-bottom: 5px; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px;">'
for i, word in enumerate(words):
    title_html += '<div style="display: flex; gap: 2px;">'
    for char in word:
        bg = TINKER_COLORS[color_idx % len(TINKER_COLORS)]
        title_html += f'<div style="background-color: {bg}; color: white; font-family: Inter; font-weight: bold; font-size: 22px; width: 32px; height: 32px; display: flex; justify-content: center; align-items: center;">{char}</div>'
        color_idx += 1
    title_html += '</div>'
title_html += '</div>'
st.markdown(title_html, unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-bottom: 30px; display: flex; justify-content: center; align-items: center; gap: 8px;">
    <div style="width: 4px; height: 14px; background-color: #e74c3c; border-radius: 2px;"></div>
    <span style="color: #64748b; font-size: 14px;">Encuentra la combinación perfecta con resistencias comerciales :D</span>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([3, 3, 4])
with col1:
    objetivo = st.number_input("VALOR DESEADO (Ω)", min_value=0.1, value=500.0, step=10.0)
with col2:
    tolerancia = st.number_input("TOLERANCIA (%)", min_value=0.1, value=5.0, step=1.0)
with col3:
    st.write("")
    st.write("")
    buscar = st.button("🔍   Buscar combinaciones", use_container_width=True)

def render_resistor(valor, tol):
    bands = bandas_resistor(valor, tol)
    if not bands: return f"<div style='color: #000; font-family: monospace;'>{valor} Ω</div>"
    band_divs = "".join([f'<div class="band" style="background-color: {color};"></div>' for color in bands])
    return f"""<div style="display: flex; flex-direction: column; align-items: center; background: #ffffff; border-radius: 8px; padding: 8px 12px; border: 1px solid #e0e0e0; box-sizing: border-box;">
<div class="resistor-container">
<div class="resistor-lead"></div>
<div class="resistor-body">{band_divs}</div>
<div class="resistor-lead"></div>
</div>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 14px; color: #000000; font-weight: bold; margin-top: 4px;">{valor:g} Ω</span>
</div>"""

if buscar:
    with st.spinner("Calculando combinaciones..."):
        resistencias = obtener_lista_resistencias(tolerancia)
        etiqueta = "E12" if tolerancia >= 10 else "E24"
        resultados = encontrar_mejores_combinaciones(objetivo, resistencias, tolerancia)
        
    if not resultados:
        st.error("❌ Nada dentro de la tolerancia. Prueba a subir el %.")
    else:
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0; color: #1e8e3e; font-weight: bold;">
            ✅ Top {min(3, len(resultados))} de {len(resultados)} combinaciones · Serie {etiqueta}
        </div>
        """, unsafe_allow_html=True)
        
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

            html_card = f"""<div class="{clase_css}" style="display: flex; flex-direction: row; align-items: center; gap: 20px; width: 100%; box-sizing: border-box;">
<div style="background-color: {color_badge}; color: white; width: {44 - i*4}px; height: {44 - i*4}px; flex-shrink: 0; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 18px;">
#{i+1}
</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
        <span style="background-color: {color_badge}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;">{texto_badge if texto_badge else '&nbsp;'}</span>
        <strong style="color: #606060; font-size: 12px; letter-spacing: 0.5px;">{r['tipo'].upper()}</strong> 
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: bold; color: #000000;">{r['expresion']}</span>
    </div>
    <div style="display: flex; flex-direction: row; gap: 10px; flex-wrap: wrap;">"""
            
            for val in r['combinacion']:
                html_card += render_resistor(val, tolerancia)
                
            html_card += f"""</div>
</div>
<div style="text-align: right; min-width: 140px; display: flex; flex-direction: column; align-items: flex-end;">
    <p class="val-eq">{r['valor_eq']:.2f} Ω</p>
    <div class="err-chip" style="background-color: {err_bg};">Error: {err:.3f}%</div>
</div>
</div>"""
            
            st.markdown(html_card, unsafe_allow_html=True)
