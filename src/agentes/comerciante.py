"""P1 — Comerciante. 3 estrategias: formal / informal / evasor."""
import mesa
from src.entorno import IGV, PRECIO_BASE, DINERO_INICIAL_COMERCIANTE, COSTO_FORMALIDAD


class Comerciante(mesa.Agent):
    def __init__(self, model, tipo: str = "informal"):
        super().__init__(model)
        self.tipo = tipo  # formal / informal / evasor
        self.precio = PRECIO_BASE
        self.dinero = DINERO_INICIAL_COMERCIANTE

    def calcular_precio(self, igv: float = IGV) -> float:
        # ponytail: placeholder — P1 implementa costos reales según tipo
        markup = {"formal": 1.0 + igv, "informal": 1.0, "evasor": 1.0 + igv * 0.5}[self.tipo]
        self.precio = PRECIO_BASE * markup
        return self.precio

    def decidir_estrategia(self, rentabilidad: dict) -> None:
        # ponytail: placeholder — P1 implementa lógica de cambio de tipo
        # rentabilidad = {"formal": float, "informal": float, "evasor": float}
        if rentabilidad.get(self.tipo, 0) < 0:
            self.tipo = max(rentabilidad, key=rentabilidad.get)

    def step(self):
        # ponytail: placeholder
        self.calcular_precio()
        self.dinero -= COSTO_FORMALIDAD if self.tipo == "formal" else 0
