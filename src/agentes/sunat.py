"""Sunat. Fiscalización con gradualidad y discrecionalidad.

Cobertura = agresividad_sunat (% de comercios auditados/ciclo), leída en vivo
del modelo (BUG 4 fix: antes se capturaba en init y no se actualizaba).

- Informal detectado: multa con gradualidad, forzado a evasor.
- Evasor auditado: multa proporcional a ingresos ocultos, o acta preventiva.

B5: SUNAT reactiva. Si evasión > 60% sostenido 20 ciclos, endurece
(agresividad_efectiva += 0.02). Si formal > 50% sostenido, relaja
(agresividad_efectiva -= 0.01). Modifica model.agresividad_efectiva, no el
slider base (agresividad_sunat).

Contadores per-ciclo (multas_ciclo, actas_ciclo) y acumulados para visualización.

Política activable:
- multa_progresiva: la multa escala según el contador de infracciones del comerciante
  (1ra = acta, 2da = multa base, 3ra+ = multa * factor_reincidencia).
"""
import mesa
from src.agentes.comerciante import Comerciante
from src.entorno import (
    EVASION_ALTA, EVASION_BAJA, SOSTENIMIENTO_FEEDBACK,
    AJUSTE_AGRESIVIDAD_UP, AJUSTE_AGRESIVIDAD_DOWN,
)


class Sunat(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        # Contadores per-ciclo (reset en cada step)
        self.multas_ciclo = 0
        self.actas_ciclo = 0
        self.n_auditorias_ciclo = 0
        # Contadores acumulados (para informe final)
        self.multas_acumuladas = 0
        self.actas_acumuladas = 0
        self.cierres_ejecutados = 0
        # B5: historial de % evasión para feedback adaptativo
        self.historia_evasion = []

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
        # Reset contadores per-ciclo
        self.multas_ciclo = 0
        self.actas_ciclo = 0
        self.n_auditorias_ciclo = 0

        comerciantes = [c for c in self.model.agents.select(agent_type=Comerciante)
                        if not getattr(c, "en_quiebra", False)]
        if not comerciantes:
            return
        # BUG 20 fix: usar agresividad_efectiva (B5), no agresividad_sunat (base)
        tasa = self.model.agresividad_efectiva
        n_auditorias = int(len(comerciantes) * tasa)
        muestra = self.random.sample(comerciantes, min(n_auditorias, len(comerciantes)))
        self.n_auditorias_ciclo = len(muestra)

        for c in muestra:
            if c.estrategia == "informal":
                factor = self._factor_reincidencia(c)
                if factor == 0.0 or self.random.random() < self.model.tasa_discrecionalidad:
                    self.actas_ciclo += 1
                    self.actas_acumuladas += 1
                    # BUG 14 fix: acta preventiva no cuenta como infracción
                else:
                    # BUG 15 fix: multa solo fija (multa_no_emision), sin 0.50*ingresos
                    multa = self.model.multa_no_emision * factor
                    # BUG 10 fix: no cobrar si capital negativo
                    cobrado = max(0.0, min(multa, c.capital))
                    c.capital -= cobrado
                    c.multas_pagadas += cobrado
                    self.model.recaudacion_ciclo += cobrado
                    self.multas_ciclo += 1
                    self.multas_acumuladas += 1
                    c.infracciones += 1  # solo multa cuenta como infracción
                c.estrategia = "evasor"

            elif c.estrategia == "evasor":
                factor = self._factor_reincidencia(c)
                if factor == 0.0 or self.random.random() < self.model.tasa_discrecionalidad:
                    self.actas_ciclo += 1
                    self.actas_acumuladas += 1
                    # BUG 14 fix: acta preventiva no cuenta como infracción
                else:
                    # BUG 12 fix: alinear con estimación — aplicar (1-disc) a multa real
                    multa = (c.ingresos_ocultos * self.model.multa_evasion_pct) * factor * (1.0 - self.model.tasa_discrecionalidad)
                    # BUG 10 fix: no cobrar si capital negativo
                    cobrado = max(0.0, min(multa, c.capital))
                    c.capital -= cobrado
                    c.multas_pagadas += cobrado
                    self.model.recaudacion_ciclo += cobrado
                    self.multas_ciclo += 1
                    self.multas_acumuladas += 1
                    c.infracciones += 1  # solo multa cuenta como infracción

        # B5: feedback adaptativo. Lee % evasión actual, actualiza agresividad_efectiva
        self._aplicar_feedback_evasion(comerciantes)

    def _aplicar_feedback_evasion(self, comerciantes: list) -> None:
        """Si evasión alta sostenida → endurece; si formal alto → relaja."""
        from src.entorno import MAX_AGRESIVIDAD, MIN_AGRESIVIDAD
        if not comerciantes:
            return
        pct_evasion = 100.0 * sum(1 for c in comerciantes
                                   if c.estrategia in ("evasor", "informal")) / len(comerciantes)
        self.historia_evasion.append(pct_evasion)
        if len(self.historia_evasion) > SOSTENIMIENTO_FEEDBACK:
            self.historia_evasion.pop(0)
        if len(self.historia_evasion) < SOSTENIMIENTO_FEEDBACK:
            return
        if all(e > EVASION_ALTA for e in self.historia_evasion):
            self.model.agresividad_efectiva = min(
                MAX_AGRESIVIDAD,
                self.model.agresividad_efectiva + AJUSTE_AGRESIVIDAD_UP
            )
        elif all(e < EVASION_BAJA for e in self.historia_evasion):
            self.model.agresividad_efectiva = max(
                MIN_AGRESIVIDAD,
                self.model.agresividad_efectiva - AJUSTE_AGRESIVIDAD_DOWN
            )

    def step(self):
        self.fiscalizar_mercado()
