"""Dashboard interactivo con Solara para El Trilema de Gamarra.

Requiere: pip install solara altair
Ejecutar:  solara run src/visualizacion.py

Features:
- Grid visual: comerciantes cambian de color (verde=formal, naranja=evasor, rojo=informal)
- Sliders para todas las políticas fiscales y de mercado
- Checkboxes para activar/desactivar políticas nuevas
- Botones de preset para escenarios completos con un click
- Gráficas en vivo: % estrategias + recaudación
"""
import solara
from mesa.visualization import (
    Slider,
    SolaraViz,
    SpaceRenderer,
    make_plot_component,
)
from mesa.visualization.components import AgentPortrayalStyle
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
    PESO_PRECIO,
    PESO_MORAL,
    COSTO_FIJO_FORMALIDAD,
    TASA_IGV,
    MULTA_NO_EMISION,
    ALPHA_EVASION,
    MULTA_EVASION_PCT,
)


def agent_portrayal(agent):
    if agent is None:
        return
    portrayal = AgentPortrayalStyle(size=50, marker="o", zorder=2)
    if isinstance(agent, Comerciante):
        colores = {"formal": "green", "evasor": "orange", "informal": "red"}
        portrayal.update(
            ("color", colores.get(agent.estrategia, "gray")),
            ("size", 80),
            ("marker", "s"),
            ("zorder", 3),
        )
    elif isinstance(agent, Sunat):
        portrayal.update(("color", "black"), ("size", 120), ("marker", "X"), ("zorder", 4))
    elif isinstance(agent, Consumidor):
        portrayal.update(("color", "royalblue"), ("size", 15), ("marker", "."), ("zorder", 1), ("alpha", 0.3))
    return portrayal


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


model_params = {
    "n_comerciantes": Slider("N° Comerciantes", N_COMERCIANTES, 10, 80, 5),
    "n_consumidores": Slider("N° Consumidores", N_CONSUMIDORES, 200, 1500, 100),
    "agresividad_sunat": Slider("Agresividad SUNAT", AGRESIVIDAD_SUNAT, 0.05, 0.95, 0.05),
    "tasa_discrecionalidad": Slider("Discrecionalidad (gradualidad)", TASA_DISCRECIONALIDAD, 0.0, 1.0, 0.05),
    "costo_fijo_formalidad": Slider("Costo Fijo Formalidad (S/)", COSTO_FIJO_FORMALIDAD, 100, 1500, 50),
    "tasa_igv": Slider("Tasa IGV", TASA_IGV, 0.05, 0.25, 0.01),
    "multa_no_emision": Slider("Multa No Emisión (S/)", MULTA_NO_EMISION, 500, 5500, 250),
    "alpha_evasion": Slider("Fracción Evasión (alpha)", ALPHA_EVASION, 0.1, 0.9, 0.05),
    "multa_evasion_pct": Slider("Multa Evasión (%)", MULTA_EVASION_PCT, 0.1, 1.5, 0.1),
    "sensibilidad_mercado": Slider("Sensibilidad Mercado (beta)", SENSIBILIDAD_MERCADO, 0.5, 8.0, 0.5),
    "peso_precio": Slider("Peso Precio (consumidor)", PESO_PRECIO, 0.5, 0.95, 0.05),
    "peso_moral": Slider("Peso Moral (consumidor)", PESO_MORAL, 0.05, 0.50, 0.05),
    "beneficio_antiguedad": {
        "type": "Checkbox",
        "value": False,
        "label": "Beneficio por antigüedad formal",
    },
    "tasa_descuento_antiguedad": Slider("Descuento antigüedad/ciclo", 0.05, 0.01, 0.10, 0.01),
    "sorteo_comprobantes": {
        "type": "Checkbox",
        "value": False,
        "label": "Sorteo de comprobantes",
    },
    "prob_sorteo": Slider("Prob. sorteo", 0.01, 0.005, 0.05, 0.005),
    "premio_sorteo": Slider("Premio sorteo (S/)", 50, 10, 200, 10),
    "multa_progresiva": {
        "type": "Checkbox",
        "value": False,
        "label": "Multa progresiva por reincidencia",
    },
    "factor_reincidencia": Slider("Factor reincidencia", 2.0, 1.5, 4.0, 0.5),
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
}

grafica_estrategias = make_plot_component(
    {"pct_formal": "green", "pct_evasor": "orange", "pct_informal": "red"},
    post_process=post_process_lines,
)
grafica_recaudacion = make_plot_component("recaudacion")

model = solara.reactive(ModeloGamarra())

renderer = SpaceRenderer(model.value, backend="matplotlib").setup_agents(agent_portrayal)
renderer.post_process = post_process_space
renderer.draw_agents()


@solara.component
def Page():
    with solara.Sidebar():
        with solara.Card("Presets — escenarios con un click"):
            solara.Text("Aplica un escenario completo y reinicia:")
            for name in PRESETS:
                def apply_preset(_name=name):
                    model.value = ModeloGamarra(**PRESETS[_name])

                solara.Button(name, on_click=apply_preset, text=True, full_width=True)

    SolaraViz(
        model,
        renderer,
        components=[grafica_estrategias, grafica_recaudacion],
        model_params=model_params,
        name="El Trilema de Gamarra",
    )


Page
