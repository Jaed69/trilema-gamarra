"""Dashboard interactivo con Streamlit para El Trilema de Gamarra.

Requiere: pip install streamlit
Ejecutar:  streamlit run src/visualizacion.py

Filosofía: 3 elementos, calidad sobre cantidad.
1. Grid visual (interacción agentes en vivo)
2. Gráfica de convergencia al equilibrio (con línea vertical + zona estable)
3. Panel de implicaciones (texto interpretativo auto-generado)

Más estable que Solara. Streamlit maneja todo: sliders, botones, métricas,
gráficas, banners de estado. No depende de internals de Mesa.
"""
import sys
import os
# ponytail: añadir project root a sys.path para que `from src.xxx` funcione
# sin importar desde dónde se ejecute streamlit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st
import pandas as pd
import numpy as np
from src.modelo import ModeloGamarra
from src.agentes.comerciante import Comerciante
from src.agentes.consumidor import Consumidor
from src.agentes.sunat import Sunat
from src.entorno import (
    N_COMERCIANTES,
    N_CONSUMIDORES,
    AGRESIVIDAD_SUNAT,
    TASA_DISCRECIONALIDAD,
    SENSIBILIDAD_MERCADO,
    ESCALA_LOGIT,
    PESO_PRECIO,
    PESO_MORAL,
    COSTO_FIJO_FORMALIDAD,
    TASA_IGV,
    MULTA_NO_EMISION,
    ALPHA_EVASION,
    MULTA_EVASION_PCT,
    CAPITAL_INICIAL,
)

# ponytail: línea base hardcodeada — valor de referencia, no meta.
# Corrida default (1000 ciclos) con mecanismos adaptativos B1-B5 + bug fixes 16-20.
LINEA_BASE = {
    "pct_formal": 36.1,
    "pct_evasor": 57.5,
    "pct_informal": 6.5,
    "informalidad_total": 63.9,
    "recaudacion": 40112.0,
}

EXPECTATIVAS_PRESETS = {
    "Línea base": {
        "descripcion": "Modelo sin políticas activas. Params default (agresividad=0.55, IGV=18%, costo=S/400, alpha=0.60). Mecanismos B1-B5 activos: bancarrota, entrada dinámica, precios dinámicos, SUNAT reactiva, adaptación Logit.",
        "expectativa": "Evasor domina (~60%). Formal estancado (~28%). Informal residual (~13%). SUNAT reactiva endurece al máximo (0.95). Recrea trilema estructural peruano.",
        "implicacion": "Punto de partida. El modelo SIN intervención reproduce el 72% de informalidad del Perú (INEI 70.2%). Ninguna palanca aislada resuelve el trilema.",
    },
    "Más enforcement": {
        "descripcion": "Subir agresividad Sunat 0.55→0.90, multa no emisión S/2750→S/5000, multa evasión 30%→100%, discrecionalidad 0.30→0.10. Política punitiva pura.",
        "expectativa": "Reduce informal puro a ~2% (fiscalización alcanza ambulatorio). Pero evasor persiste (~63%) — registro aparente sin cumplimiento. Recaudación triplica. Rendimientos decrecientes.",
        "implicacion": "Enforcement punitivo solo no resuelve estructural. Genera evasión sofisticada (subdeclaración) o quiebra microempresa. Necesita reformas de costos para impacto real.",
    },
    "Subsidio formalidad": {
        "descripcion": "Bajar costo fijo S/400→S/150 + beneficio antigüedad (descuento 8%/ciclo formal consecutivo, tope 50%). Reduce barreras de entrada a formalidad.",
        "expectativa": "Más formales (reducen barreras entrada). Pero evasores no migran — evasión sigue siendo más rentable que formalidad. Formal sube marginalmente.",
        "implicacion": "Reduce barreras pero no cambia incentivo de evadir. Suficiente si combinas con enforcement y cultura tributaria.",
    },
    "Cultura tributaria": {
        "descripcion": "Subir peso moral 0.20→0.40 + sorteo comprobantes (prob 3%, premio S/100). Actúa sobre demanda: consumidores exigen comprobante.",
        "expectativa": "Consumidores exigen más comprobante. Formal captura demanda por moral. Pero oferta no cambia — comerciantes siguen evadiendo.",
        "implicacion": "Actúa sobre demanda, no oferta. Cambia patrones de compra pero no decisión de evadir del comerciante. Suficiente si combinas con reducción de costos.",
    },
    "Reducción tributaria": {
        "descripcion": "Bajar IGV 18%→10% + alpha 0.60→0.30 (menos fracción evadida). Reduce brecha precio formal/informal y atractivo de evadir.",
        "expectativa": "Brecha precio formal/informal se reduce. Menor incentivo evadir (alpha bajo = menos ganancia oculta). Recaudación cae por menor tasa pero base crece.",
        "implicacion": "Reduce atractivo económico de evasión. Trade-off: recaudación por unidad cae pero base imponible crece. Efecto neto depende de elasticidad.",
    },
    "Combo reforma": {
        "descripcion": "Enforcement 0.75 + costo S/200 + moral 0.35 + 3 políticas activas (antigüedad, sorteo, multa progresiva). Reforma integral moderada.",
        "expectativa": "Único escenario que desplaza equilibrio significativamente. Sinergia: costos bajos + enforcement moderado + cultura tributaria + multa progresiva.",
        "implicacion": "Trilema se resuelve solo actuando en múltiples frentes simultáneamente. Ninguna palanca aislada basta — el combo sí mueve la aguja.",
    },
    # ── ESCENARIOS EXTREMOS POSITIVOS ──
    "Paraíso formal": {
        "descripcion": "Caso ideal pro-formal: costo S/100, IGV 5%, moral 0.50, alpha 0.10, beneficio antigüedad + sorteo activos. Todo a favor de formalidad.",
        "expectativa": "Formalidad debería prosperar. Pero SUNAT reactiva (B5) sigue endureciendo porque evasión inicial > 60%. Resultado: evasor persiste a pesar de incentivos pro-formal.",
        "implicacion": "Incluso con todo a favor, el trilema persiste por inercia del sistema. La transición a formalidad requiere tiempo + persistencia política, no solo buenos incentivos.",
    },
    "Reforma gradual": {
        "descripcion": "Subsidio S/200 + enforcement moderado 0.65 + moral 0.30 + multa progresiva. Reforma gradual sin shocks.",
        "expectativa": "Mejora marginal vs línea base. Combinación moderada no desplaza equilibrio drásticamente pero reduce informalidad 3-5pp.",
        "implicacion": "Reformas graduales son más sostenibles políticas pero de impacto limitado. Necesaria persistencia multigobierno para efecto acumulativo.",
    },
    # ── ESCENARIOS EXTREMOS NEGATIVOS (colapsos) ──
    "Mercado libre": {
        "descripcion": "SUNAT mínima (0.05), multas bajas (S/500, 10%), sin discrecionalidad. Estado ausente del mercado.",
        "expectativa": "Informal explota a ~35%. Evasor baja (menos necesitan registro aparente). SUNAT reactiva (B5) compensa subiendo agresividad al máximo, pero tarda.",
        "implicacion": "Sin Estado, informal domina. Pero el feedback adaptativo (B5) eventualmente endurece — el sistema se autocorrige, pero con rezago temporal donde informalidad es alta.",
    },
    "Represión extrema": {
        "descripcion": "Agresividad 0.95, multa S/5500, sin discrecionalidad (0%), multa evasión 150%. Estado punitivo máximo.",
        "expectativa": "Formal sube a ~42% (más alto). Informal casi eliminado (~1%). PERO: quiebras masivas (~90 comerciantes). Mercado se destruye por exceso de enforcement.",
        "implicacion": "Over-enforcement destruye mercado. Reducir informalidad por represión genera bancarrotas, desempleo, contracción económica. No es solución — es destrucción.",
    },
    "Crisis de demanda": {
        "descripcion": "Pocos consumidores (200 vs 800), costo fijo alto S/800. Mercado contraído + costos altos.",
        "expectativa": "Bancarrotas masivas (~270 quiebras). Mercado se contrae. Formales y evasores quiebran por falta de ventas. B2 entrada no compensa.",
        "implicacion": "Sin demanda suficiente, el mercado colapsa independientemente de la política tributaria. La demanda es condición necesaria — sin compradores, no hay sector que formalizar.",
    },
    "Evasión incentivada": {
        "descripcion": "Alpha 0.90 (90% ventas ocultas), multa evasión 10%, SUNAT mínima 0.10. Evadir es muy rentable y sin riesgo.",
        "expectativa": "Informal sube a ~25%. Evasor baja (al alpha tan alto, más rentable ser informal puro). SUNAT reactiva compensa pero lentamente.",
        "implicacion": "Cuando evadir es muy rentable y sin riesgo, el sistema se va al informal puro. La clave es que el riesgo percibido (P multa × valor multa) supere la ganancia de evadir.",
    },
}

PRESETS = {
    "Línea base": {},
    "Más enforcement": {
        "agresividad_sunat": 0.90,
        "tasa_discrecionalidad": 0.10,
        "multa_no_emision": 5000,
        "multa_evasion_pct": 1.0,
    },
    "Subsidio formalidad": {
        "costo_fijo_formalidad": 150,
        "beneficio_antiguedad": True,
        "tasa_descuento_antiguedad": 0.08,
    },
    "Cultura tributaria": {
        "peso_moral": 0.40,
        "sorteo_comprobantes": True,
        "prob_sorteo": 0.03,
        "premio_sorteo": 100,
    },
    "Reducción tributaria": {
        "tasa_igv": 0.10,
        "alpha_evasion": 0.30,
    },
    "Combo reforma": {
        "agresividad_sunat": 0.75,
        "costo_fijo_formalidad": 200,
        "peso_moral": 0.35,
        "beneficio_antiguedad": True,
        "sorteo_comprobantes": True,
        "multa_progresiva": True,
    },
    # ── ESCENARIOS EXTREMOS POSITIVOS ──
    "Paraíso formal": {
        "costo_fijo_formalidad": 100,
        "tasa_igv": 0.05,
        "peso_moral": 0.50,
        "alpha_evasion": 0.10,
        "beneficio_antiguedad": True,
        "sorteo_comprobantes": True,
    },
    "Reforma gradual": {
        "costo_fijo_formalidad": 200,
        "agresividad_sunat": 0.65,
        "peso_moral": 0.30,
        "multa_progresiva": True,
    },
    # ── ESCENARIOS EXTREMOS NEGATIVOS (colapsos) ──
    "Mercado libre": {
        "agresividad_sunat": 0.05,
        "multa_no_emision": 500,
        "multa_evasion_pct": 0.1,
    },
    "Represión extrema": {
        "agresividad_sunat": 0.95,
        "multa_no_emision": 5500,
        "tasa_discrecionalidad": 0.0,
        "multa_evasion_pct": 1.5,
    },
    "Crisis de demanda": {
        "n_consumidores": 200,
        "costo_fijo_formalidad": 800,
    },
    "Evasión incentivada": {
        "alpha_evasion": 0.90,
        "multa_evasion_pct": 0.1,
        "agresividad_sunat": 0.10,
    },
}

VARIABLES_EFECTO = """| Variable | Qué controla | Efecto esperado |
|---|---|---|
| `agresividad_sunat` | % comercios auditados/ciclo | ↑→menos informal, +formal (rendimientos decrec.) |
| `tasa_discrecionalidad` | prob. acta preventiva vs multa | ↑→menos destrucción capital, -deterrente |
| `costo_fijo_formalidad` | costo operar formal (S/ mes) | ↑→-formal, +evasor/informal (asfixia) |
| `tasa_igv` | IGV cobrado (18%) | ↑→+brecha precio, +incentivo evadir |
| `multa_no_emision` | multa fija no emitir (50% UIT) | ↑→+deterrente informal |
| `alpha_evasion` | fracción ventas ocultas evasor | ↑→+evasión, -recaudación |
| `multa_evasion_pct` | % ingresos ocultos como multa | ↑→+riesgo evasión |
| `sensibilidad_mercado` | beta Logit (racionalidad) | ↑→decisiones más racionales |
| `escala_logit` | normalización utilidades en exp() | ↑→probs más uniformes |
| `peso_precio` | peso precio en compra | ↑→+demanda informal |
| `peso_moral` | peso moral en compra | ↑→+demanda formal |
| `beneficio_antiguedad` | descuento costo fijo por ciclos formal | ON→+formal sostenible |
| `sorteo_comprobantes` | premio por exigir comprobante | ON→+demanda formal |
| `multa_progresiva` | multa escala por reincidencia | ON→+costo reincidente |"""


def _detectar_equilibrio(df, ventana=50, umbral_delta=1.0, sostenimiento=30):
    """Primer ciclo donde la media móvil de informalidad se estabiliza."""
    if len(df) < ventana + sostenimiento:
        return None
    inf_total = df["pct_informal"] + df["pct_evasor"]
    rolling_mean = inf_total.rolling(window=ventana).mean()
    delta = rolling_mean.diff().abs()
    bajo = (delta < umbral_delta).astype(int)
    streak = 0
    for idx in range(ventana + 1, len(df)):
        if bajo.iloc[idx]:
            streak += 1
            if streak >= sostenimiento:
                return int(idx - sostenimiento + 1)
        else:
            streak = 0
    return None


def _detectar_preset(m) -> str:
    """Detecta qué preset coincide con los params del modelo."""
    from src.entorno import (AGRESIVIDAD_SUNAT, TASA_DISCRECIONALIDAD, COSTO_FIJO_FORMALIDAD,
                             TASA_IGV, MULTA_NO_EMISION, ALPHA_EVASION, MULTA_EVASION_PCT,
                             PESO_MORAL, SENSIBILIDAD_MERCADO)
    defaults = {
        "agresividad_sunat": AGRESIVIDAD_SUNAT,
        "tasa_discrecionalidad": TASA_DISCRECIONALIDAD,
        "costo_fijo_formalidad": COSTO_FIJO_FORMALIDAD,
        "tasa_igv": TASA_IGV,
        "multa_no_emision": MULTA_NO_EMISION,
        "alpha_evasion": ALPHA_EVASION,
        "multa_evasion_pct": MULTA_EVASION_PCT,
        "peso_moral": PESO_MORAL,
        "sensibilidad_mercado": SENSIBILIDAD_MERCADO,
        "beneficio_antiguedad": False,
        "sorteo_comprobantes": False,
        "multa_progresiva": False,
    }
    for nombre, overrides in PRESETS.items():
        params = {**defaults, **overrides}
        match = True
        for k, v in params.items():
            mv = getattr(m, k, None)
            if mv is None:
                match = False
                break
            if isinstance(v, float):
                if abs(mv - v) > 0.01:
                    match = False
                    break
            elif mv != v:
                match = False
                break
        if match:
            return nombre
    return "Custom"


def _estado_sistema(m) -> str:
    """Detecta estado del sistema."""
    if m is None:
        return "INICIANDO"
    df = m.datacollector.get_model_vars_dataframe()
    if len(df) < 20:
        return "INICIANDO"
    tail = df.tail(20)
    pct_formal = tail["pct_formal"].mean()
    pct_informal = tail["pct_informal"].mean()
    recaud = tail["recaudacion"].mean()
    presupuesto = tail["presupuesto_medio"].mean()
    if pct_formal < 5:
        return "COLAPSO FORMAL"
    if pct_informal > 80:
        return "COLAPSO AMBULANTE"
    if recaud < 2000:
        return "COLAPSO FISCAL"
    if presupuesto > 150:
        return "COLAPSO DEMANDA"
    if pct_formal > 50:
        return "PRÓSPERO"
    return "ESTABLE"


def _generar_implicaciones(m) -> str:
    """Texto interpretativo auto-generado al detectar equilibrio."""
    if m is None:
        return "Iniciando simulación..."
    df = m.datacollector.get_model_vars_dataframe()
    if len(df) < 60:
        return f"Corriendo... {len(df)} ciclos. Mínimo 60 para detectar equilibrio."

    ciclo_eq = _detectar_equilibrio(df)
    if ciclo_eq is None:
        return (f"Simulación en progreso ({len(df)} ciclos).\n"
                f"No se ha detectado equilibrio aún (media móvil no estabilizada).\n"
                f"El modelo oscila — esperar estabilización en banda.")

    posteriores = df.iloc[ciclo_eq:]
    f = posteriores["pct_formal"].mean()
    e = posteriores["pct_evasor"].mean()
    i = posteriores["pct_informal"].mean()
    inf_total = i + e
    recaud = posteriores["recaudacion"].mean()

    preset_nombre = _detectar_preset(m)
    expectativa = EXPECTATIVAS_PRESETS.get(preset_nombre, {
        "descripcion": "Configuración personalizada — params modificados manualmente.",
        "expectativa": "Resultados dependen de combinación específica de params.",
        "implicacion": "Comparar vs línea base para evaluar efecto de la configuración.",
    })

    lecturas = []
    if e > 50:
        lecturas.append(f"• Evasor domina ({e:.0f}%) — registro aparente sin cumplimiento real.")
    if f < 35:
        lecturas.append(f"• Formalidad sub-sostenible ({f:.0f}%) — microempresa no absorbe costos fijos.")
    if i > 15:
        lecturas.append(f"• Ambulatorio persistente ({i:.0f}%) — fiscalización no alcanza comercio móvil.")
    elif i < 10:
        lecturas.append(f"• Informal residual bajo ({i:.0f}%) — fiscalización efectiva.")

    politicas = []
    if m.beneficio_antiguedad:
        politicas.append("antigüedad")
    if m.sorteo_comprobantes:
        politicas.append("sorteo")
    if m.multa_progresiva:
        politicas.append("multa progresiva")

    if preset_nombre == "Línea base":
        gap_inei = inf_total - 70.2
        comparacion = (f"Informalidad total: {inf_total:.0f}%  (INEI 2025: 70.2%, gap {gap_inei:+.0f} pp)\n"
                       f"Recaudación media: S/. {recaud:.0f}/ciclo\n")
    else:
        delta_inf = inf_total - LINEA_BASE["informalidad_total"]
        delta_formal = f - LINEA_BASE["pct_formal"]
        delta_recaud = recaud - LINEA_BASE["recaudacion"]
        comparacion = (f"Informalidad total: {inf_total:.0f}%  (Δ {delta_inf:+.1f}pp vs línea base)\n"
                       f"Formal: {f:.0f}%  (Δ {delta_formal:+.1f}pp vs línea base)\n"
                       f"Recaudación: S/. {recaud:.0f}/ciclo  (Δ {delta_recaud:+.0f} vs línea base)\n")

    politicas_str = f"Políticas activas: {', '.join(politicas)}\n" if politicas else ""

    # Zonas del equilibrio
    fin = len(df)
    mitad = ciclo_eq + max(1, (fin - ciclo_eq) // 2)
    zona_pre = df.iloc[:ciclo_eq]
    zona_durante = df.iloc[ciclo_eq:mitad]
    zona_post = df.iloc[mitad:]

    def _resumen_zona(z, nombre):
        if len(z) == 0:
            return ""
        return (f"{nombre} (ciclos {z.index[0]}-{z.index[-1]}): "
                f"{z['pct_formal'].mean():.0f}% F · {z['pct_evasor'].mean():.0f}% E · "
                f"{z['pct_informal'].mean():.0f}% I · Recaud S/. {z['recaudacion'].mean():.0f}\n")

    zonas = (_resumen_zona(zona_pre, "PRE-EQ") +
             _resumen_zona(zona_durante, "EQUILIBRIO") +
             _resumen_zona(zona_post, "POST-EQ"))

    # Capital por estrategia
    cap_str = ""
    if "capital_formal" in posteriores.columns:
        cf = posteriores["capital_formal"].mean()
        ce = posteriores["capital_evasor"].mean()
        ci = posteriores["capital_informal"].mean()
        cap_str = (f"\nCapital post-equilibrio (vs inicial S/. {CAPITAL_INICIAL:.0f}):\n"
                   f"  🟢 Formal:   S/. {cf:>10.0f}  (×{cf/CAPITAL_INICIAL:.1f})\n"
                   f"  🟠 Evasor:   S/. {ce:>10.0f}  (×{ce/CAPITAL_INICIAL:.1f})\n"
                   f"  🔴 Informal: S/. {ci:>10.0f}  (×{ci/CAPITAL_INICIAL:.1f})\n")

    estado = _estado_sistema(m)
    agres_str = f"Agresividad SUNAT: base={m.agresividad_sunat:.2f} · efectiva={m.agresividad_efectiva:.2f}\n"

    return (
        f"═══════════════════════════════════════════\n"
        f"  EQUILIBRIO @ ciclo {ciclo_eq}  [{preset_nombre}]\n"
        f"  Estado: {estado}\n"
        f"═══════════════════════════════════════════\n\n"
        f"Composición: {f:.0f}% formal · {e:.0f}% evasor · {i:.0f}% informal\n"
        f"{comparacion}"
        f"{politicas_str}"
        f"{agres_str}"
        f"\n── Zonas del equilibrio ──\n{zonas}"
        f"{cap_str}"
        f"\n── Escenario ──\n{expectativa['descripcion']}\n\n"
        f"── Expectativa ──\n{expectativa['expectativa']}\n\n"
        f"── Lectura ──\n" + "\n".join(lecturas) + "\n\n"
        f"── Implicación ──\n{expectativa['implicacion']}\n"
    )


def _dibujar_grid(m, fig, ax):
    """Dibuja el grid con todos los agentes en sus posiciones."""
    if m is None:
        return
    ax.clear()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.5, m.grid.width - 0.5)
    ax.set_ylim(-0.5, m.grid.height - 0.5)
    ax.set_facecolor("#f5f5f5")
    ax.set_title("Grid del mercado — Gamarra", fontsize=12, fontweight="bold")

    colores = {"formal": "green", "evasor": "orange", "informal": "red"}
    for agent in m.agents:
        if not hasattr(agent, "pos") or agent.pos is None:
            continue
        x, y = agent.pos
        if isinstance(agent, Comerciante):
            if getattr(agent, "en_quiebra", False):
                ax.scatter(x, y, c="gray", s=60, marker="x", zorder=0, alpha=0.3)
            else:
                c = colores.get(agent.estrategia, "gray")
                ax.scatter(x, y, c=c, s=120, marker="s", zorder=3, edgecolors="black", linewidths=0.5)
        elif isinstance(agent, Sunat):
            ax.scatter(x, y, c="black", s=150, marker="X", zorder=4)
        elif isinstance(agent, Consumidor):
            ax.scatter(x, y, c="royalblue", s=10, marker=".", zorder=1, alpha=0.15)

    # Leyenda
    handles = [
        mpatches.Patch(color="green", label="Formal"),
        mpatches.Patch(color="orange", label="Evasor"),
        mpatches.Patch(color="red", label="Informal"),
        mpatches.Patch(color="gray", label="En quiebra"),
        plt.Line2D([0], [0], marker="X", color="w", markerfacecolor="black", markersize=10, label="SUNAT"),
        plt.Line2D([0], [0], marker=".", color="w", markerfacecolor="royalblue", markersize=5, label="Consumidor"),
    ]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)


def _dibujar_convergencia(m, fig, ax):
    """Dibuja la gráfica de convergencia con línea de equilibrio."""
    if m is None:
        return
    df = m.datacollector.get_model_vars_dataframe()
    if len(df) == 0:
        return
    ax.clear()
    ax.plot(df.index, df["pct_formal"], color="green", label="Formal", linewidth=1.5)
    ax.plot(df.index, df["pct_evasor"], color="orange", label="Evasor", linewidth=1.5)
    ax.plot(df.index, df["pct_informal"], color="red", label="Informal", linewidth=1.5)
    ax.set_xlabel("Ciclo")
    ax.set_ylabel("%")
    ax.set_title("Convergencia al equilibrio", fontsize=12, fontweight="bold")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.grid(True, alpha=0.3)

    # Línea de equilibrio
    ciclo_eq = _detectar_equilibrio(df)
    if ciclo_eq is not None:
        ax.axvline(x=ciclo_eq, color="black", linestyle="--", linewidth=2, alpha=0.8)
        ax.axvspan(ciclo_eq, len(df), alpha=0.1, color="green")
        ax.annotate(f"Equilibrio @ ciclo {ciclo_eq}",
                    xy=(ciclo_eq, ax.get_ylim()[1] * 0.95),
                    xytext=(ciclo_eq + max(5, len(df) * 0.02), ax.get_ylim()[1] * 0.95),
                    fontsize=9, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color="black"))


# ─────────────────────────────────────────────
# Configuración de la página
# ─────────────────────────────────────────────
st.set_page_config(page_title="El Trilema de Gamarra", page_icon="🏪", layout="wide")

# Inicializar modelo en session_state
if "modelo" not in st.session_state:
    st.session_state.modelo = ModeloGamarra()
    st.session_state.params_actuales = {}

# ─────────────────────────────────────────────
# Sidebar — controles
# ─────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Controles")

# Presets
st.sidebar.markdown("### Presets — escenarios con un click")
for name in PRESETS:
    if st.sidebar.button(name, key=f"preset_{name}", use_container_width=True):
        st.session_state.modelo = ModeloGamarra(**PRESETS[name])
        st.session_state.params_actuales = PRESETS[name].copy()

st.sidebar.divider()

# Sliders de parámetros
st.sidebar.markdown("### Parámetros del modelo")
with st.sidebar.expander("Fiscalización", expanded=False):
    agres = st.slider("Agresividad SUNAT", 0.05, 0.95, AGRESIVIDAD_SUNAT, 0.05)
    disc = st.slider("Discrecionalidad", 0.0, 1.0, TASA_DISCRECIONALIDAD, 0.05)
    multa_no = st.slider("Multa No Emisión (S/)", 500, 5500, int(MULTA_NO_EMISION), 250)
    multa_ev = st.slider("Multa Evasión (%)", 0.1, 1.5, MULTA_EVASION_PCT, 0.1)

with st.sidebar.expander("Costos y tributos", expanded=False):
    costo_fijo = st.slider("Costo Fijo Formalidad (S/)", 100, 1500, int(COSTO_FIJO_FORMALIDAD), 50)
    igv = st.slider("Tasa IGV", 0.05, 0.25, TASA_IGV, 0.01)
    alpha = st.slider("Alpha Evasión", 0.1, 0.9, ALPHA_EVASION, 0.05)

with st.sidebar.expander("Mercado", expanded=False):
    n_com = st.slider("N° Comerciantes", 10, 80, N_COMERCIANTES, 5)
    n_con = st.slider("N° Consumidores", 200, 1500, N_CONSUMIDORES, 100)
    beta = st.slider("Sensibilidad Mercado (beta)", 0.5, 8.0, SENSIBILIDAD_MERCADO, 0.5)
    escala = st.slider("Escala Logit", 1000.0, 50000.0, ESCALA_LOGIT, 1000.0)
    p_precio = st.slider("Peso Precio", 0.5, 0.95, PESO_PRECIO, 0.05)
    p_moral = st.slider("Peso Moral", 0.05, 0.50, PESO_MORAL, 0.05)

with st.sidebar.expander("Políticas activables", expanded=False):
    ben_ant = st.checkbox("Beneficio por antigüedad", False)
    tasa_desc = st.slider("Descuento antigüedad/ciclo", 0.01, 0.10, 0.05, 0.01)
    sorteo = st.checkbox("Sorteo de comprobantes", False)
    prob_sort = st.slider("Prob. sorteo", 0.005, 0.05, 0.01, 0.005)
    premio = st.slider("Premio sorteo (S/)", 10, 200, 50, 10)
    multa_prog = st.checkbox("Multa progresiva", False)
    factor_reinc = st.slider("Factor reincidencia", 1.5, 4.0, 2.0, 0.5)

# Botón: aplicar params
if st.sidebar.button("🔄 Aplicar parámetros y reiniciar", use_container_width=True, type="primary"):
    nuevos_params = dict(
        n_comerciantes=n_com, n_consumidores=n_con,
        agresividad_sunat=agres, tasa_discrecionalidad=disc,
        costo_fijo_formalidad=costo_fijo, tasa_igv=igv,
        multa_no_emision=multa_no, alpha_evasion=alpha,
        multa_evasion_pct=multa_ev, sensibilidad_mercado=beta,
        escala_logit=escala, peso_precio=p_precio, peso_moral=p_moral,
        beneficio_antiguedad=ben_ant, tasa_descuento_antiguedad=tasa_desc,
        sorteo_comprobantes=sorteo, prob_sorteo=prob_sort, premio_sorteo=premio,
        multa_progresiva=multa_prog, factor_reincidencia=factor_reinc,
    )
    st.session_state.modelo = ModeloGamarra(**nuevos_params)
    st.session_state.params_actuales = nuevos_params

st.sidebar.divider()

# Controles de ejecución
st.sidebar.markdown("### ▶️ Ejecutar simulación")
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("▶ 1", use_container_width=True):
    st.session_state.modelo.step()
if col2.button("▶▶ 50", use_container_width=True):
    for _ in range(50):
        st.session_state.modelo.step()
if col3.button("⏩ 500", use_container_width=True):
    for _ in range(500):
        st.session_state.modelo.step()

# ─────────────────────────────────────────────
# Contenido principal
# ─────────────────────────────────────────────
st.title("🏪 El Trilema de la Gamarra")
st.markdown("Simulación Multiagente de informalidad y evasión tributaria en el Perú")

m = st.session_state.modelo
df = m.datacollector.get_model_vars_dataframe()

# Banner de estado
estado = _estado_sistema(m)
if "COLAPSO" in estado:
    st.error(f"🚨 {estado} — el sistema ha colapsado")
elif estado == "PRÓSPERO":
    st.success(f"🌟 {estado} — el mercado formal prospera")
elif estado == "ESTABLE":
    st.info(f"📊 {estado} — el sistema opera en equilibrio")
else:
    st.warning(f"⏳ {estado}")

# Métricas grandes en tiempo real
if len(df) > 0:
    row = df.iloc[-1]
    ciclo = len(df) - 1
    n_activos = len([c for c in m.agents.select(agent_type=Comerciante)
                     if not getattr(c, "en_quiebra", False)])
    n_quiebra = len([c for c in m.agents.select(agent_type=Comerciante)
                     if getattr(c, "en_quiebra", False)])
    agres_efect = m.agresividad_efectiva
    delta_agres = agres_efect - m.agresividad_sunat

    st.markdown(f"### Ciclo {ciclo}")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🟢 Formal", f"{row['pct_formal']:.1f}%")
    col2.metric("🟠 Evasor", f"{row['pct_evasor']:.1f}%")
    col3.metric("🔴 Informal", f"{row['pct_informal']:.1f}%")
    col4.metric("💰 Recaudación", f"S/. {row['recaudacion']:.0f}")
    col5.metric("🏪 Activos", f"{n_activos}", delta=f"{n_quiebra} en quiebra")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Agres. base", f"{m.agresividad_sunat:.2f}")
    col2.metric("⚡ Agres. efectiva", f"{agres_efect:.2f}",
                delta=f"{delta_agres:+.2f}" if delta_agres != 0 else None)
    col3.metric("⚖️ Multas/ciclo", f"{int(row['multas'])}")
    col4.metric("📋 Actas/ciclo", f"{int(row['actas_preventivas'])}")

# Grid + gráfica de convergencia
col_grid, col_plot = st.columns([1, 2])

with col_grid:
    st.markdown("### Grid del mercado")
    fig_grid, ax_grid = plt.subplots(figsize=(5, 5))
    _dibujar_grid(m, fig_grid, ax_grid)
    st.pyplot(fig_grid)
    plt.close(fig_grid)

with col_plot:
    st.markdown("### Convergencia al equilibrio")
    fig_conv, ax_conv = plt.subplots(figsize=(10, 5))
    _dibujar_convergencia(m, fig_conv, ax_conv)
    st.pyplot(fig_conv)
    plt.close(fig_conv)

# Panel de implicaciones
st.markdown("---")
st.markdown("### 📊 Implicaciones del equilibrio")
implicaciones = _generar_implicaciones(m)
st.text(implicaciones)

# Panel de variables
with st.expander("📋 Variables y su efecto en el modelo", expanded=False):
    st.markdown(VARIABLES_EFECTO)

# Leyenda del grid
st.markdown("---")
st.markdown("**Leyenda del grid:** 🟩 Formal · 🟧 Evasor · 🟥 Informal · ❌ En quiebra · ⚫ SUNAT · 🔵 Consumidor")
