"""P2 — Consumidor. Presupuesto + moral tributaria.

Elige tienda ponderando precio, moral tributaria (preferir formal) y distancia.
La compra enruta el IGV al Fondo Público si el comerciante es formal.
"""
import mesa
from src.entorno import (
    PRESUPUESTO_INICIAL,
    INGRESO_CONSUMIDOR,
    IGV,
    W_PRECIO,
    W_MORAL,
    W_DIST,
)
from src.agentes.comerciante import Comerciante


class Consumidor(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.presupuesto = PRESUPUESTO_INICIAL
        self.moral_tributaria = self.random.random()

    def _distancia_toroide(self, otra_pos) -> float:
        x1, y1 = self.pos
        x2, y2 = otra_pos
        w, h = self.model.grid.width, self.model.grid.height
        dx = min(abs(x1 - x2), w - abs(x1 - x2))
        dy = min(abs(y1 - y2), h - abs(y1 - y2))
        return dx + dy

    def elegir_tienda(self, comerciantes: list) -> Comerciante | None:
        asequibles = [c for c in comerciantes if c.precio <= self.presupuesto]
        if not asequibles:
            return None

        precios = [c.precio for c in asequibles] or [1]
        precio_max = max(precios) if precios else 1
        dist_max = max((self._distancia_toroide(c.pos) for c in asequibles), default=1) or 1

        def score(c):
            s_precio = W_PRECIO * (1 - c.precio / precio_max) if precio_max else 0
            s_moral = W_MORAL * self.moral_tributaria * (1.0 if c.tipo == "formal" else 0.0)
            s_dist = W_DIST * (1 - self._distancia_toroide(c.pos) / dist_max) if dist_max else 0
            return s_precio + s_moral + s_dist

        return max(asequibles, key=score)

    def comprar(self, tienda: Comerciante | None) -> None:
        if tienda is None:
            return
        self.presupuesto -= tienda.precio
        tienda.dinero += tienda.precio
        if tienda.tipo == "formal":
            igv = tienda.precio * IGV / (1 + IGV)
            tienda.dinero -= igv  # el formal remite el IGV al estado
            self.model._recaudacion_ciclo += igv  # ponytail: acceso directo al modelo

    def step(self):
        self.presupuesto += INGRESO_CONSUMIDOR  # sueldo del ciclo
        comerciantes = list(self.model.agents.select(agent_type=Comerciante))
        self.comprar(self.elegir_tienda(comerciantes))
