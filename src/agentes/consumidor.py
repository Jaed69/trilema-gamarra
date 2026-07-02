"""P2 — Consumidor. Presupuesto + moral tributaria."""
import mesa
from src.entorno import PRESUPUESTO_INICIAL
from src.agentes.comerciante import Comerciante


class Consumidor(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.presupuesto = PRESUPUESTO_INICIAL
        self.moral_tributaria = self.random.random()

    def elegir_tienda(self, comerciantes: list) -> Comerciante | None:
        # ponytail: placeholder — P2 implementa (precio + moral + distancia)
        visible = [c for c in comerciantes if c.precio <= self.presupuesto]
        if not visible:
            return None
        return self.random.choice(visible)

    def comprar(self, tienda: Comerciante | None) -> None:
        # ponytail: placeholder
        if tienda is None:
            return
        self.presupuesto -= tienda.precio
        tienda.dinero += tienda.precio

    def step(self):
        comerciantes = list(self.model.agents.select(agent_type=Comerciante))
        self.comprar(self.elegir_tienda(comerciantes))
