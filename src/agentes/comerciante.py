"""Comerciante. 3 estrategias: formal / evasor / informal.

Decisión por Logit Multinomial (racionalidad limitada): estima utilidad neta
esperada de cada estrategia y transiciona probabilísticamente.

- Formal: cobra IGV completo, lo declara, paga COSTO_FIJO_FORMALIDAD.
- Evasor: cobra precio formal (con IGV), por cada venta declara o esconde con
  prob alpha. Riesgo: multa proporcional a ingresos ocultos.
- Informal: sin IGV, sin RUC. Riesgo: multa + forzado a evasor si detectado.

B1: Si capital < UMBRAL_BANCARROTA, marca en_quiebra=True. No opera más.
B3: Precio dinámico según ventas del ciclo anterior. Se cachea en step() una vez.
B4: Si agresividad_efectiva > 0.80, costo de cumplimiento del formal sube 2% revenue.

Políticas activables:
- beneficio_antiguedad: descuento incremental en costo_fijo por ciclos formal consecutivo.
- multa_progresiva: el contador de infracciones escala la multa (gestionado por Sunat).
"""
import math
import mesa
from src.entorno import (COSTO_UNITARIO, PRECIO_BASE, CAPITAL_INICIAL, ESCALA_LOGIT,
                          UMBRAL_BANCARROTA, UMBRAL_CRECIMIENTO,
                          VENTAS_NORMALES, VENTAS_RANGO, MAX_VARIACION_PRECIO)


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
        # B1: marca de bancarrota
        self.en_quiebra = False
        # B3: precio dinámico (se calcula una vez en step() y se cachea)
        self.precio_actual = PRECIO_BASE

    def _costo_fijo_efectivo(self) -> float:
        """Costo fijo con descuento por antigüedad si la política está activa."""
        costo = self.model.costo_fijo_formalidad
        if self.model.beneficio_antiguedad and self.estrategia == "formal":
            descuento = min(0.50, self.model.tasa_descuento_antiguedad * self.ciclos_formal_consecutivos)
            costo *= (1.0 - descuento)
        return costo

    def _costo_unitario_efectivo(self) -> float:
        """B2: Economías de escala. Si capital > UMBRAL_CRECIMIENTO y formal,
        baja costo unitario hasta 50% (capital muy alto)."""
        if self.capital > UMBRAL_CRECIMIENTO and self.estrategia == "formal":
            reduccion = min(0.50, (self.capital - UMBRAL_CRECIMIENTO) / 100000.0)
            return COSTO_UNITARIO * (1.0 - reduccion)
        return COSTO_UNITARIO

    def _calcular_factor_demanda(self) -> float:
        """B3: factor de demanda según ventas del ciclo anterior.
        Ventas altas → +precio; ventas bajas → -precio. Tope ±MAX_VARIACION_PRECIO.
        """
        delta = (self.ventas_ciclo - VENTAS_NORMALES) / VENTAS_RANGO
        return 1.0 + max(-MAX_VARIACION_PRECIO, min(MAX_VARIACION_PRECIO, delta))

    def calcular_precio(self) -> float:
        """Precio dinámico (B3). precio_actual se cachea en step() una vez por ciclo.

        BUG 18+19 fix: antes recalculaba factor en cada llamada → precio cambiaba
        durante el ciclo y difería entre realizar_compra y ejecutar_transaccion.
        Ahora precio_actual incluye el factor de demanda, calculado una sola vez.
        """
        igv = self.model.tasa_igv
        if self.estrategia in ("formal", "evasor"):
            return self.precio_actual * (1.0 + igv)
        else:  # informal
            return self.precio_actual

    def estimar_utilidad_futura(self, est: str) -> float:
        """Utilidad neta esperada por estrategia (racionalidad limitada).

        Usa revenue real por estrategia (BUG 3 fix) y sin doble descuento de
        IGV (BUG 1 fix). Modelo binario para evasor (BUG 2 fix).
        B4: si agresividad_efectiva > 0.80, costo compliance formal = 2% revenue.
        """
        volumen = max(1, self.ventas_ciclo)
        igv = self.model.tasa_igv
        alpha = self.model.alpha_evasion
        costo_fijo = self.model.costo_fijo_formalidad
        p_inspeccion = self.model.prob_inspeccion_percibida
        disc = self.model.tasa_discrecionalidad
        costos_produccion = self._costo_unitario_efectivo() * volumen  # B2: economías escala

        if est == "formal":
            # Ingreso neto = PRECIO_BASE * volumen (sin IGV, que se paga a SUNAT)
            ingreso_neto = PRECIO_BASE * volumen
            util_antes_imp = ingreso_neto - costos_produccion
            # BUG 11 fix: RMT real 1% primer tramo (no 10%)
            imp_renta = max(0.0, util_antes_imp * 0.01)
            costo_fijo_est = costo_fijo
            if self.model.beneficio_antiguedad:
                descuento = min(0.50, self.model.tasa_descuento_antiguedad * (self.ciclos_formal_consecutivos + 1))
                costo_fijo_est = costo_fijo * (1.0 - descuento)
            # B4: si SUNAT muy agresiva, costo de cumplimiento sube (auditorías, paperwork)
            # proporcional al revenue, no plano — antes era -1000 fijo (bug: siempre negativo)
            compliance_cost = 0.0
            if self.model.agresividad_efectiva > 0.80:
                compliance_cost = ingreso_neto * 0.02  # 2% revenue por audits/paperwork
            return (util_antes_imp - imp_renta) - costo_fijo_est - compliance_cost

        elif est == "informal":
            ingresos_brutos = PRECIO_BASE * volumen  # sin IGV
            # BUG 15 fix: multa solo fija (multa_no_emision), sin 0.50*ingresos
            penalidad = p_inspeccion * self.model.multa_no_emision * (1.0 - disc)
            return ingresos_brutos - costos_produccion - penalidad

        elif est == "evasor":
            # Binario: cobra precio formal, declara (1-alpha) de ventas, esconde alpha
            precio_neto = PRECIO_BASE
            precio_con_igv = PRECIO_BASE * (1.0 + igv)
            # Parte declarada: neto sin IGV
            ing_declarado_neto = (1.0 - alpha) * precio_neto * volumen
            # Parte oculta: precio completo (con IGV cobrado y no remitido)
            ing_oculto_bruto = alpha * precio_con_igv * volumen
            util_declarada = ing_declarado_neto - (costos_produccion * (1.0 - alpha))
            # BUG 11 fix: RMT 1% (no 10%)
            imp_renta = max(0.0, util_declarada * 0.01)
            # BUG 12 fix: alineado con multa real de sunat.py (con factor (1-disc))
            multa_evasion = p_inspeccion * (self.model.multa_evasion_pct * ing_oculto_bruto) * (1.0 - disc)
            util_oculta = ing_oculto_bruto - (costos_produccion * alpha) - multa_evasion
            return (util_declarada - imp_renta - costo_fijo * 0.40) + util_oculta
        return 0.0

    def ajustar_cumplimiento(self) -> None:
        """Transición probabilística vía Logit Multinomial."""
        beta = self.model.sensibilidad_mercado
        escala = self.model.escala_logit
        utilidades = {est: self.estimar_utilidad_futura(est) for est in
                      ("formal", "evasor", "informal")}
        expos = {}
        for est, u in utilidades.items():
            try:
                expos[est] = math.exp(min(500.0, beta * u / escala))
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
        # B1: bancarrota. Si capital bajo umbral, marca en_quiebra. No opera más.
        if self.en_quiebra:
            return
        if self.capital < UMBRAL_BANCARROTA:
            self.en_quiebra = True
            return
        # B3: setear precio_actual al inicio del ciclo, basado en ventas del ciclo anterior
        # BUG 18 fix: calcular una sola vez (no en cada calcular_precio)
        factor = self._calcular_factor_demanda()
        self.precio_actual = PRECIO_BASE * factor
        self.ajustar_cumplimiento()
        self.ventas_ciclo = 0
        self.ingresos_declarados = 0.0
        self.ingresos_ocultos = 0.0
        if self.estrategia == "formal":
            self.ciclos_formal_consecutivos += 1
            self.capital -= self._costo_fijo_efectivo()
        elif self.estrategia == "evasor":
            self.capital -= self.model.costo_fijo_formalidad * 0.40
