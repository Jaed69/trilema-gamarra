"""Dashboard interactivo con Solara para El Trilema de Gamarra.

Requiere: pip install solara
Ejecutar:  solara run src/visualizacion.py
"""
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from src.modelo import ModeloGamarra
from src.agentes.comerciante import Comerciante
from src.agentes.sunat import Sunat
from src.agentes.consumidor import Consumidor


def agent_portrayal(agent):
    if isinstance(agent, Comerciante):
        colores = {"formal": "green", "evasor": "orange", "informal": "red"}
        return AgentPortrayalStyle(
            color=colores.get(agent.estrategia, "gray"),
            size=55,
            marker="s",  # cuadrados = puestos comerciales
        )
    elif isinstance(agent, Sunat):
        return AgentPortrayalStyle(color="black", size=75, marker="x")
    else:  # Consumidor
        return AgentPortrayalStyle(color="blue", size=25, marker="o")


model_params = {
    "n_comerciantes": {
        "type": "SliderInt",
        "value": 40,
        "label": "N° Comerciantes",
        "min": 10,
        "max": 80,
        "step": 5,
    },
    "n_consumidores": {
        "type": "SliderInt",
        "value": 800,
        "label": "N° Consumidores",
        "min": 200,
        "max": 1500,
        "step": 100,
    },
    "agresividad_sunat": {
        "type": "SliderFloat",
        "value": 0.55,
        "label": "Agresividad Fiscal (SUNAT)",
        "min": 0.05,
        "max": 0.95,
        "step": 0.05,
    },
    "tasa_discrecionalidad": {
        "type": "SliderFloat",
        "value": 0.30,
        "label": "Tolerancia Discrecional",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
}

grafica_fiscal = make_plot_component(
    ["pct_formal", "pct_evasor", "pct_informal"], page=1
)
grafica_recaudacion = make_plot_component("recaudacion", page=1)

page = SolaraViz(
    model_class=ModeloGamarra,
    portrayal_method=agent_portrayal,
    model_params=model_params,
    components=[grafica_fiscal, grafica_recaudacion],
    name="El Trilema de Gamarra",
)
