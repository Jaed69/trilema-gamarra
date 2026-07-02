"""Sunat. Fiscalización con gradualidad y discrecionalidad.

Cobertura = agresividad_sunat (% de comercios auditados/ciclo).
- Informal detectado: multa con gradualidad (90% rebaja), forzado a evasor.
- Evasor auditado: multa = 50% del IGV omitido, o acta preventiva (discrecionalidad).
"""
import mesa
from src.entorno import (
    TASA_IGV,
    MULTA_NO_EMISION,
    DESCUENTO_GRADUALIDAD,
    MULTA_EVASION_PCT,
    AGRESIVIDAD_SUNAT,
)
from src.agentes.comerciante import Comerciante


class Sunat(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.tasa_cobertura = AGRESIVIDAD_SUNAT
        self.multas_emitidas = 0
        self.cierres_ejecutados = 0
        self.actas_preventivas = 0

    def fiscalizar_mercado(self) -> None:
        comerciantes = list(self.model.agents.select(agent_type=Comerciante))
        if not comerciantes:
            return
        n_auditorias = int(len(comerciantes) * self.tasa_cobertura)
        muestra = self.random.sample(comerciantes, min(n_auditorias, len(comerciantes)))

        for c in muestra:
            if c.estrategia == "informal":
                # Multa: fija + proporcional a ingresos (comiso) — escala con volumen
                if self.random.random() < self.model.tasa_discrecionalidad:
                    self.actas_preventivas += 1
                else:
                    multa = MULTA_NO_EMISION + 0.50 * (c.ingresos_ocultos + c.ingresos_declarados)
                    cobrado = min(multa, c.capital)
                    c.capital -= cobrado
                    c.multas_pagadas += cobrado
                    self.model.recaudacion_ciclo += cobrado
                    self.multas_emitidas += 1
                c.estrategia = "evasor"  # forzado a registro aparente

            elif c.estrategia == "evasor":
                # Multa proporcional a ingresos ocultos (más disuasiva que solo IGV omitido)
                multa = c.ingresos_ocultos * MULTA_EVASION_PCT
                if self.random.random() < self.model.tasa_discrecionalidad:
                    self.actas_preventivas += 1  # acta preventiva, sin multa
                else:
                    cobrado = min(multa, c.capital)
                    c.capital -= cobrado
                    c.multas_pagadas += cobrado
                    self.model.recaudacion_ciclo += cobrado
                    self.multas_emitidas += 1

    def step(self):
        self.fiscalizar_mercado()
