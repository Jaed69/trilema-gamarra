"""P3 — Sunat. Fiscalización + Fondo Público."""
import mesa
from src.entorno import (
    PRESUPUESTO_FISCALIZACION,
    MULTA_EVASOR,
    N_FISCALIZACIONES_POR_CICLO,
)
from src.agentes.comerciante import Comerciante


class Sunat(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.presupuesto_fiscalizacion = PRESUPUESTO_FISCALIZACION

    def seleccionar_objetivos(
        self, comerciantes: list, n: int = N_FISCALIZACIONES_POR_CICLO
    ) -> list:
        # ponytail: placeholder — P3 implementa (priorizar evasores según agresividad)
        return self.random.sample(comerciantes, min(n, len(comerciantes)))

    def aplicar_multa(self, objetivo: Comerciante) -> float:
        # ponytail: placeholder — P3 implementa
        if objetivo.tipo == "evasor":
            self.presupuesto_fiscalizacion += MULTA_EVASOR
            objetivo.dinero -= MULTA_EVASOR
            return MULTA_EVASOR
        return 0.0

    def step(self):
        comerciantes = list(self.model.agents.select(agent_type=Comerciante))
        for obj in self.seleccionar_objetivos(comerciantes):
            self.aplicar_multa(obj)
