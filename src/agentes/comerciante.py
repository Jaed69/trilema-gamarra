"""Comerciante. 3 estrategias: formal / evasor / informal.

Decisión por Logit Multinomial (racionalidad limitada): estima utilidad neta
esperada de cada estrategia y transiciona probabilísticamente.

- Formal: cobra IGV completo, lo declara, paga COSTO_FIJO_FORMALIDAD.
- Evasor: cobra IGV solo sobre (1-alpha) de ventas, subdeclara alpha. Riesgo: multa.
- Informal: sin IGV, sin RUC. Riesgo: multa + forzado a evasor si detectado.

Políticas activables:
- beneficio_antiguedad: descuento incremental en costo_fijo por ciclos formal consecutivo.
- multa_progresiva: el contador de infracciones escala la multa (gestionado por Sunat).
"""
import math
import mesa
from src.entorno import COSTO_UNITARIO, PRECIO_BASE, CAPITAL_INICIAL


class Comerciante(mesa.Agent):
    def __init__(self, model, estrategia: str = "informal", capital: float = CAPITAL_INICIAL):
        super().__init__(model)
        self.estrategia = estrategia
        self.capital = capital
        self.ventas_ciclo = 0
        self.ingresos_declarados = 0.0
        self.ingresos_ocultos = 0.0
        self.multas_pagadas = 0.0
        self.ciclos_formal_consecutivos = 0
        self.infracciones = 0

    def _costo_fijo_efectivo(self) -> float:
        """Costo fijo con descuento por antigüedad si la política está activa."""
        costo = self.model.costo_fijo_formalidad
        if self.model.beneficio_antiguedad and self.estrategia == "formal":
            descuento = min(0.50, self.model.tasa_descuento_antiguedad * self.ciclos_formal_consecutivos)
            costo *= (1.0 - descuento)
        return costo

    def calcular_precio(self) -> float:
        """Precio de venta final al público con carga impositiva según estrategia."""
        igv = self.model.tasa_igv
        alpha = self.model.alpha_evasion
        if self.estrategia == "formal":
            return PRECIO_BASE * (1.0 + igv)
        elif self.estrategia == "evasor":
            parte_formal = (PRECIO_BASE * (1.0 - alpha)) * (1.0 + igv)
            parte_informal = PRECIO_BASE * alpha
            return parte_formal + parte_informal
        else:  # informal
            return PRECIO_BASE

    def estimar_utilidad_futura(self, est: str) -> float:
        """Utilidad neta esperada por estrategia (racionalidad limitada)."""
        volumen = max(1, self.ventas_ciclo)
        ingresos_brutos = PRECIO_BASE * volumen
        costos_produccion = COSTO_UNITARIO * volumen
        p_inspeccion = self.model.prob_inspeccion_percibida
        igv = self.model.tasa_igv
        alpha = self.model.alpha_evasion
        costo_fijo = self.model.costo_fijo_formalidad
        disc = self.model.tasa_discrecionalidad

        if est == "formal":
            util_antes_imp = (ingresos_brutos / (1.0 + igv)) - costos_produccion
            imp_renta = max(0.0, util_antes_imp * 0.10)  # RMT 10% primer tramo
            costo_fijo_est = costo_fijo
            if self.model.beneficio_antiguedad:
                descuento = min(0.50, self.model.tasa_descuento_antiguedad * (self.ciclos_formal_consecutivos + 1))
                costo_fijo_est = costo_fijo * (1.0 - descuento)
            return (util_antes_imp - imp_renta) - costo_fijo_est

        elif est == "informal":
            multa_base = self.model.multa_no_emision + 0.50 * ingresos_brutos
            penalidad = p_inspeccion * multa_base * (1.0 - disc)
            return ingresos_brutos - costos_produccion - penalidad

        elif est == "evasor":
            ing_declarado_neto = (ingresos_brutos * (1.0 - alpha)) / (1.0 + igv)
            ing_oculto_neto = ingresos_brutos * alpha
            util_declarada = ing_declarado_neto - (costos_produccion * (1.0 - alpha))
            imp_renta = max(0.0, util_declarada * 0.10)
            multa_evasion = p_inspeccion * (self.model.multa_evasion_pct * ingresos_brutos * alpha) * (1.0 - disc)
            util_neta = (util_declarada - imp_renta - costo_fijo * 0.40)
            util_oculta = ing_oculto_neto - (costos_produccion * alpha) - multa_evasion
            return util_neta + util_oculta
        return 0.0

    def ajustar_cumplimiento(self) -> None:
        """Transición probabilística vía Logit Multinomial."""
        beta = self.model.sensibilidad_mercado
        utilidades = {est: self.estimar_utilidad_futura(est) for est in
                      ("formal", "evasor", "informal")}
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
                if est != self.estrategia:
                    if self.estrategia == "formal":
                        self.ciclos_formal_consecutivos = 0
                self.estrategia = est
                return

    def step(self):
        self.ajustar_cumplimiento()
        self.ventas_ciclo = 0
        self.ingresos_declarados = 0.0
        self.ingresos_ocultos = 0.0
        if self.estrategia == "formal":
            self.ciclos_formal_consecutivos += 1
            self.capital -= self._costo_fijo_efectivo()
        elif self.estrategia == "evasor":
            self.capital -= self.model.costo_fijo_formalidad * 0.40
