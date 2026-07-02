"""P1 — Comerciante. 3 estrategias: formal / informal / evasor.

Dinámica:
- Formal: cobra IGV (precio +18%), lo transfiere al estado, paga costo de formalidad.
- Informal: precio base, sin IGV ni costo. Riesgo: multa si lo fiscalizan.
- Evasor: cobra medio IGV (precio +9%), no lo paga. Riesgo: multa mayor.
"""
import mesa
from src.entorno import (
    IGV,
    PRECIO_BASE,
    DINERO_INICIAL_COMERCIANTE,
    COSTO_FORMALIDAD,
    P_CAMBIO_ESTRATEGIA,
    P_RELAJACION,
    UMBRAL_QUIEBRA,
)


class Comerciante(mesa.Agent):
    def __init__(self, model, tipo: str = "informal"):
        super().__init__(model)
        self.tipo = tipo
        self.precio = PRECIO_BASE
        self.dinero = DINERO_INICIAL_COMERCIANTE
        self.dinero_prev = DINERO_INICIAL_COMERCIANTE
        self.multado_recientemente = False

    def calcular_precio(self, igv: float = IGV) -> float:
        markup = {"formal": 1.0 + igv, "informal": 1.0, "evasor": 1.0 + igv * 0.5}[self.tipo]
        self.precio = PRECIO_BASE * markup
        return self.precio

    def decidir_estrategia(self) -> None:
        # ponytail: reglas deterministas basadas en desempeño, sin churn aleatorio
        if self.multado_recientemente and self.tipo in ("evasor", "informal"):
            if self.dinero > COSTO_FORMALIDAD * 3:
                self.tipo = "formal"  # aprendió la lección y puede pagar
            else:
                self.tipo = "informal"  # no le alcanza para formalizar
        elif self.tipo == "formal" and self.dinero < DINERO_INICIAL_COMERCIANTE * UMBRAL_QUIEBRA:
            self.tipo = "informal"  # no banca el costo de formalidad
        elif self.tipo == "formal" and self.random.random() < P_RELAJACION:
            self.tipo = "informal"  # se relaja: percibe bajo riesgo de fiscalización
        elif self.tipo == "informal" and self.dinero > DINERO_INICIAL_COMERCIANTE * 1.5:
            if self.random.random() < P_CAMBIO_ESTRATEGIA:
                self.tipo = "evasor"  # probando margen extra cuando va bien

    def step(self):
        self.dinero_prev = self.dinero
        self.calcular_precio()
        if self.tipo == "formal":
            self.dinero -= COSTO_FORMALIDAD
        self.decidir_estrategia()
        self.multado_recientemente = False  # reset al final: el flag de Sunat sobrevive hasta la decisión
