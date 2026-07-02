"""Consumidor. Móvil, presupuesto variable, moral tributaria baja.

Elige tienda en vecindario Moore por utilidad precio + moral (comprobante).
La compra enruta el IGV según estrategia del vendedor (F declara, E parcial, I oculto).

Política activable:
- sorteo_comprobantes: el consumidor que compra formal tiene chance de premio,
  sumando valor esperado a la utilidad de elegir formal.
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

    def realizar_compra(self) -> None:
        while self.presupuesto > PRECIO_BASE:
            vecinos = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
            comerciantes = [v for v in vecinos if isinstance(v, Comerciante)]
            if not comerciantes:
                self.mover()
                vecinos = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
                comerciantes = [v for v in vecinos if isinstance(v, Comerciante)]
                if not comerciantes:
                    return

            mejor = None
            max_util = -float("inf")
            sorteo_ev = self._valor_esperado_sorteo()
            for c in comerciantes:
                precio = c.calcular_precio()
                if precio > self.presupuesto:
                    continue
                comprobante = 1.0 if c.estrategia in ("formal", "evasor") else 0.0
                bonus_sorteo = sorteo_ev if c.estrategia == "formal" else 0.0
                util = (
                    -(self.model.peso_precio * precio)
                    + (self.model.peso_moral * self.moral_tributaria * comprobante)
                    + bonus_sorteo
                )
                if util > max_util:
                    max_util = util
                    mejor = c

            if mejor is not None:
                self.ejecutar_transaccion(mejor)
            else:
                self.mover()

    def ejecutar_transaccion(self, comerciante: Comerciante) -> None:
        precio = comerciante.calcular_precio()
        self.presupuesto -= precio
        comerciante.ventas_ciclo += 1
        comerciante.capital += precio

        igv = self.model.tasa_igv
        alpha = self.model.alpha_evasion

        if comerciante.estrategia == "formal":
            comerciante.ingresos_declarados += precio
            monto_igv = precio * (igv / (1.0 + igv))
            self.model.recaudacion_ciclo += monto_igv
            if self.model.sorteo_comprobantes and self.random.random() < self.model.prob_sorteo:
                self.presupuesto += self.model.premio_sorteo
        elif comerciante.estrategia == "evasor":
            if self.random.random() > alpha:
                comerciante.ingresos_declarados += precio
                monto_igv = precio * (igv / (1.0 + igv))
                self.model.recaudacion_ciclo += monto_igv
            else:
                comerciante.ingresos_ocultos += precio
        else:  # informal
            comerciante.ingresos_ocultos += precio

    def mover(self) -> None:
        pasos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        nueva = self.random.choice(pasos)
        self.model.grid.move_agent(self, nueva)

    def step(self):
        self.presupuesto = self.random.gauss(PRESUPUESTO_MEDIA, PRESUPUESTO_DESV)
        self.realizar_compra()
