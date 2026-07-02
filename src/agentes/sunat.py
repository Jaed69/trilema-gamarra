"""Sunat. Fiscalización con gradualidad y discrecionalidad.

Cobertura = agresividad_sunat (% de comercios auditados/ciclo).
- Informal detectado: multa con gradualidad, forzado a evasor.
- Evasor auditado: multa proporcional a ingresos ocultos, o acta preventiva.

Política activable:
- multa_progresiva: la multa escala según el contador de infracciones del comerciante
  (1ra = acta, 2da = multa base, 3ra+ = multa * factor_reincidencia).
"""
import mesa
from src.agentes.comerciante import Comerciante


class Sunat(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.tasa_cobertura = model.agresividad_sunat
        self.multas_emitidas = 0
        self.cierres_ejecutados = 0
        self.actas_preventivas = 0

    def _factor_reincidencia(self, comerciante: Comerciante) -> float:
        """Factor multiplicador de multa según historial de infracciones."""
        if not self.model.multa_progresiva:
            return 1.0
        if comerciante.infracciones == 0:
            return 0.0  # primera infracción: acta preventiva
        elif comerciante.infracciones == 1:
            return 1.0  # segunda infracción: multa base
        else:
            return self.model.factor_reincidencia ** (comerciante.infracciones - 1)

    def fiscalizar_mercado(self) -> None:
        comerciantes = list(self.model.agents.select(agent_type=Comerciante))
        if not comerciantes:
            return
        n_auditorias = int(len(comerciantes) * self.tasa_cobertura)
        muestra = self.random.sample(comerciantes, min(n_auditorias, len(comerciantes)))

        for c in muestra:
            if c.estrategia == "informal":
                factor = self._factor_reincidencia(c)
                if factor == 0.0 or self.random.random() < self.model.tasa_discrecionalidad:
                    self.actas_preventivas += 1
                else:
                    multa = (self.model.multa_no_emision + 0.50 * (c.ingresos_ocultos + c.ingresos_declarados)) * factor
                    cobrado = min(multa, c.capital)
                    c.capital -= cobrado
                    c.multas_pagadas += cobrado
                    self.model.recaudacion_ciclo += cobrado
                    self.multas_emitidas += 1
                c.infracciones += 1
                c.estrategia = "evasor"

            elif c.estrategia == "evasor":
                factor = self._factor_reincidencia(c)
                if factor == 0.0 or self.random.random() < self.model.tasa_discrecionalidad:
                    self.actas_preventivas += 1
                else:
                    multa = (c.ingresos_ocultos * self.model.multa_evasion_pct) * factor
                    cobrado = min(multa, c.capital)
                    c.capital -= cobrado
                    c.multas_pagadas += cobrado
                    self.model.recaudacion_ciclo += cobrado
                    self.multas_emitidas += 1
                c.infracciones += 1

    def step(self):
        self.fiscalizar_mercado()
