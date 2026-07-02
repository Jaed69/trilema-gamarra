"""P3 — Sunat. Fiscalización + Fondo Público.

Fondo Público se alimenta del IGV recaudado (SHARE_IGV_A_SUNAT) + multas,
y se consume por cada fiscalización (COSTO_FISCALIZACION).
Prioriza evasores; la agresividad abre el blanco a informales.
"""
import mesa
from src.entorno import (
    PRESUPUESTO_FISCALIZACION,
    APROPIACION_SUNAT,
    MULTA_EVASOR,
    MULTA_INFORMAL,
    COSTO_FISCALIZACION,
    SHARE_IGV_A_SUNAT,
    N_FISCALIZACIONES_POR_CICLO,
)
from src.agentes.comerciante import Comerciante


class Sunat(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.presupuesto_fiscalizacion = PRESUPUESTO_FISCALIZACION

    def seleccionar_objetivos(self, comerciantes: list) -> list:
        if self.presupuesto_fiscalizacion < COSTO_FISCALIZACION:
            return []  # ponytail: Fondo colapsado = círculo vicioso
        n_max = min(
            N_FISCALIZACIONES_POR_CICLO,
            int(self.presupuesto_fiscalizacion / COSTO_FISCALIZACION),
            len(comerciantes),
        )
        evasores = [c for c in comerciantes if c.tipo == "evasor"]
        informales = [c for c in comerciantes if c.tipo == "informal"]
        objetivos = list(evasores[:n_max])  # prioridad absoluta: evasores
        # slots restantes: cada uno fiscaliza un informal con prob = agresividad
        remaining = n_max - len(objetivos)
        pool = list(informales)
        for _ in range(remaining):
            if not pool:
                break
            if self.random.random() < self.model.agresividad_sunat:
                obj = self.random.choice(pool)
                objetivos.append(obj)
                pool.remove(obj)
        return objetivos

    def aplicar_multa(self, objetivo: Comerciante) -> float:
        if objetivo.tipo == "evasor":
            multa = MULTA_EVASOR
        elif objetivo.tipo == "informal":
            multa = MULTA_INFORMAL
        else:
            return 0.0
        cobrado = min(multa, objetivo.dinero)
        objetivo.dinero -= cobrado
        objetivo.multado_recientemente = True
        self.presupuesto_fiscalizacion += cobrado
        return cobrado

    def step(self):
        # Fondo se alimenta de: apropiación estatal + IGV recaudado + multas - costo fiscalización
        self.presupuesto_fiscalizacion += APROPIACION_SUNAT
        self.presupuesto_fiscalizacion += self.model._recaudacion_ciclo * SHARE_IGV_A_SUNAT
        comerciantes = list(self.model.agents.select(agent_type=Comerciante))
        objetivos = self.seleccionar_objetivos(comerciantes)
        self.presupuesto_fiscalizacion -= len(objetivos) * COSTO_FISCALIZACION
        for obj in objetivos:
            self.aplicar_multa(obj)
