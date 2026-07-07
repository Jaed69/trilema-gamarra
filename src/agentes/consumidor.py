"""Consumidor. Móvil, presupuesto variable, moral tributaria baja.

Elige tienda en vecindario Moore por utilidad precio + moral (comprobante).
La compra enruta el IGV según estrategia del vendedor (F declara, E parcial, I oculto).

Modelo binario para evasor: cobra precio formal, por cada venta decide declarar
(con prob 1-alpha, paga IGV, entra sorteo) o esconder (con prob alpha, oculta).

Política activable:
- sorteo_comprobantes: el consumidor que compra formal (o evasor declarado) tiene
  chance de premio, sumando valor esperado a la utilidad de elegir formal.
"""
import mesa
from src.entorno import PRECIO_BASE
from src.entorno import PRESUPUESTO_MEDIA, PRESUPUESTO_DESV, MORAL_MIN, MORAL_MAX
from src.agentes.comerciante import Comerciante


class Consumidor(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.moral_tributaria = self.random.uniform(MORAL_MIN, MORAL_MAX)
        self.presupuesto = self.random.gauss(PRESUPUESTO_MEDIA, PRESUPUESTO_DESV)

    def _valor_esperado_sorteo(self) -> float:
        """Valor esperado del premio si el modelo tiene sorteo activo."""
        if self.model.sorteo_comprobantes:
            return self.model.prob_sorteo * self.model.premio_sorteo
        return 0.0

    def _prob_comprobante(self, estrategia: str) -> float:
        """Probabilidad esperada de recibir comprobante según estrategia."""
        if estrategia == "formal":
            return 1.0
        elif estrategia == "evasor":
            # BUG 5 fix: evasor solo da comprobante cuando declara (1-alpha)
            return 1.0 - self.model.alpha_evasion
        return 0.0

    def realizar_compra(self) -> None:
        # BUG 9 fix: mantener condición original (permite comprar informal)
        # pero agregar tope anti-loop infinito
        max_movimientos = 20  # ponytail: tope anti-loop infinito
        movimientos = 0
        while self.presupuesto > PRECIO_BASE and movimientos < max_movimientos:
            vecinos = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
            comerciantes = [v for v in vecinos if isinstance(v, Comerciante) and not getattr(v, "en_quiebra", False)]
            if not comerciantes:
                self.mover()
                movimientos += 1
                vecinos = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
                comerciantes = [v for v in vecinos if isinstance(v, Comerciante) and not getattr(v, "en_quiebra", False)]
                if not comerciantes:
                    return

            mejor = None
            max_util = -float("inf")
            sorteo_ev = self._valor_esperado_sorteo()
            for c in comerciantes:
                precio = c.calcular_precio()
                if precio > self.presupuesto:
                    continue
                # BUG 5 fix: comprobante probabilístico por estrategia
                prob_comp = self._prob_comprobante(c.estrategia)
                # Sorteo: solo si hay probabilidad de comprobante
                bonus_sorteo = sorteo_ev * prob_comp if c.estrategia != "informal" else 0.0
                util = (
                    -(self.model.peso_precio * precio)
                    + (self.model.peso_moral * self.moral_tributaria * prob_comp)
                    + bonus_sorteo
                )
                if util > max_util:
                    max_util = util
                    mejor = c

            if mejor is not None:
                self.ejecutar_transaccion(mejor)
            else:
                self.mover()
                movimientos += 1

    def ejecutar_transaccion(self, comerciante: Comerciante) -> None:
        precio = comerciante.calcular_precio()
        self.presupuesto -= precio
        comerciante.ventas_ciclo += 1
        # BUG 8 fix: comerciante recibe neto (precio - IGV), SUNAT recibe IGV
        igv = self.model.tasa_igv
        alpha = self.model.alpha_evasion

        if comerciante.estrategia == "formal":
            monto_igv = precio * (igv / (1.0 + igv))
            comerciante.capital += precio - monto_igv  # comerciante retiene neto
            comerciante.ingresos_declarados += precio
            self.model.recaudacion_ciclo += monto_igv  # SUNAT recibe IGV
            if self.model.sorteo_comprobantes and self.random.random() < self.model.prob_sorteo:
                # BUG 13 fix: premio sale de recaudación, no de la nada
                self.presupuesto += self.model.premio_sorteo
                self.model.recaudacion_ciclo -= self.model.premio_sorteo
        elif comerciante.estrategia == "evasor":
            # BUG 2 fix: modelo binario — declara o esconde por venta
            if self.random.random() > alpha:
                # Declara esta venta: paga IGV, entra sorteo (BUG 7 fix)
                monto_igv = precio * (igv / (1.0 + igv))
                comerciante.capital += precio - monto_igv  # BUG 8 fix: retiene neto
                comerciante.ingresos_declarados += precio
                self.model.recaudacion_ciclo += monto_igv
                if self.model.sorteo_comprobantes and self.random.random() < self.model.prob_sorteo:
                    # BUG 13 fix: premio sale de recaudación
                    self.presupuesto += self.model.premio_sorteo
                    self.model.recaudacion_ciclo -= self.model.premio_sorteo
            else:
                # Esconde esta venta: no paga IGV, no entra sorteo
                comerciante.capital += precio  # evasor retiene todo (incluido IGV cobrado)
                comerciante.ingresos_ocultos += precio
        else:  # informal
            comerciante.capital += precio
            comerciante.ingresos_ocultos += precio

    def mover(self) -> None:
        pasos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        nueva = self.random.choice(pasos)
        self.model.grid.move_agent(self, nueva)

    def step(self):
        self.presupuesto = self.random.gauss(PRESUPUESTO_MEDIA, PRESUPUESTO_DESV)
        self.realizar_compra()
