"""Comerciante. 3 estrategias: formal / evasor / informal.

Decisión por Logit Multinomial (racionalidad limitada): estima utilidad neta
esperada de cada estrategia y transiciona probabilísticamente.

- Formal: cobra IGV completo, lo declara, paga COSTO_FIJO_FORMALIDAD.
- Evasor: cobra IGV solo sobre (1-alpha) de ventas, subdeclara alpha. Riesgo: multa.
- Informal: sin IGV, sin RUC. Riesgo: multa + forzado a evasor si detectado.
"""
import math
import mesa
from src.entorno import (
    TASA_IGV,
    COSTO_FIJO_FORMALIDAD,
    COSTO_UNITARIO,
    PRECIO_BASE,
    CAPITAL_INICIAL,
    ALPHA_EVASION,
    MULTA_NO_EMISION,
    DESCUENTO_GRADUALIDAD,
    MULTA_EVASION_PCT,
    SENSIBILIDAD_MERCADO,
)


class Comerciante(mesa.Agent):
    def __init__(self, model, estrategia: str = "informal", capital: float = CAPITAL_INICIAL):
        super().__init__(model)
        self.estrategia = estrategia
        self.capital = capital
        self.ventas_ciclo = 0
        self.ingresos_declarados = 0.0
        self.ingresos_ocultos = 0.0
        self.multas_pagadas = 0.0

    def calcular_precio(self) -> float:
        """Precio de venta final al público con carga impositiva según estrategia."""
        if self.estrategia == "formal":
            return PRECIO_BASE * (1.0 + TASA_IGV)
        elif self.estrategia == "evasor":
            # IGV solo sobre la fracción declarada (1-alpha)
            parte_formal = (PRECIO_BASE * (1.0 - ALPHA_EVASION)) * (1.0 + TASA_IGV)
            parte_informal = PRECIO_BASE * ALPHA_EVASION
            return parte_formal + parte_informal
        else:  # informal
            return PRECIO_BASE

    def estimar_utilidad_futura(self, est: str) -> float:
        """Utilidad neta esperada por estrategia (racionalidad limitada)."""
        volumen = max(1, self.ventas_ciclo)
        ingresos_brutos = PRECIO_BASE * volumen
        costos_produccion = COSTO_UNITARIO * volumen
        p_inspeccion = self.model.prob_inspeccion_percibida

        if est == "formal":
            util_antes_imp = (ingresos_brutos / (1.0 + TASA_IGV)) - costos_produccion
            imp_renta = max(0.0, util_antes_imp * 0.10)  # RMT 10% primer tramo
            return (util_antes_imp - imp_renta) - COSTO_FIJO_FORMALIDAD

        elif est == "informal":
            # Multa: fija + proporcional a ingresos (comiso) — escala con volumen
            penalidad = p_inspeccion * (MULTA_NO_EMISION + 0.50 * ingresos_brutos) * (1.0 - self.model.tasa_discrecionalidad)
            return ingresos_brutos - costos_produccion - penalidad

        elif est == "evasor":
            ing_declarado_neto = (ingresos_brutos * (1.0 - ALPHA_EVASION)) / (1.0 + TASA_IGV)
            ing_oculto_neto = ingresos_brutos * ALPHA_EVASION
            util_declarada = ing_declarado_neto - (costos_produccion * (1.0 - ALPHA_EVASION))
            imp_renta = max(0.0, util_declarada * 0.10)
            igv_omitido = (ingresos_brutos * ALPHA_EVASION) * (TASA_IGV / (1.0 + TASA_IGV))
            # Multa proporcional a ingresos ocultos (no solo IGV omitido) — más disuasiva
            multa_evasion = p_inspeccion * (MULTA_EVASION_PCT * ingresos_brutos * ALPHA_EVASION) * (1.0 - self.model.tasa_discrecionalidad)
            util_neta = (util_declarada - imp_renta - COSTO_FIJO_FORMALIDAD * 0.40)
            util_oculta = ing_oculto_neto - (costos_produccion * ALPHA_EVASION) - multa_evasion
            return util_neta + util_oculta
        return 0.0

    def ajustar_cumplimiento(self) -> None:
        """Transición probabilística vía Logit Multinomial."""
        beta = SENSIBILIDAD_MERCADO
        utilidades = {est: self.estimar_utilidad_futura(est) for est in
                      ("formal", "evasor", "informal")}
        # ponytail: guard overflow en exp — normalización por 10000 (utilidades ~miles)
        expos = {}
        for est, u in utilidades.items():
            try:
                expos[est] = math.exp(min(500.0, beta * u / 10000.0))
            except OverflowError:
                expos[est] = math.exp(500.0)
        total = sum(expos.values())
        probs = {est: e / total for est, e in expos.items()}

        r = self.random.random()
        acum = 0.0
        for est, p in probs.items():
            acum += p
            if r <= acum:
                self.estrategia = est
                return

    def step(self):
        # ponytail: decide con ventas del ciclo anterior (ya registradas), luego resetea
        self.ajustar_cumplimiento()
        self.ventas_ciclo = 0
        self.ingresos_declarados = 0.0
        self.ingresos_ocultos = 0.0
        if self.estrategia == "formal":
            self.capital -= COSTO_FIJO_FORMALIDAD
        elif self.estrategia == "evasor":
            self.capital -= COSTO_FIJO_FORMALIDAD * 0.40  # costo mitigado de evasión
