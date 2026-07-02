"""Consumidor. Móvil, presupuesto variable, moral tributaria baja.

Elige tienda en vecindario Moore por utilidad precio + moral (comprobante).
La compra enruta el IGV según estrategia del vendedor (F declara, E parcial, I oculto).
"""
import mesa
from src.entorno import TASA_IGV, ALPHA_EVASION, PESO_PRECIO, PESO_MORAL, PRECIO_BASE
from src.entorno import PRESUPUESTO_MEDIA, PRESUPUESTO_DESV, MORAL_MIN, MORAL_MAX
from src.agentes.comerciante import Comerciante


class Consumidor(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.moral_tributaria = self.random.uniform(MORAL_MIN, MORAL_MAX)
        self.presupuesto = self.random.gauss(PRESUPUESTO_MEDIA, PRESUPUESTO_DESV)

    def realizar_compra(self) -> None:
        # ponytail: loop de compras hasta agotar presupuesto o vecinos asequibles
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
            for c in comerciantes:
                precio = c.calcular_precio()
                if precio > self.presupuesto:
                    continue
                comprobante = 1.0 if c.estrategia in ("formal", "evasor") else 0.0
                util = -(PESO_PRECIO * precio) + (PESO_MORAL * self.moral_tributaria * comprobante)
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

        if comerciante.estrategia == "formal":
            comerciante.ingresos_declarados += precio
            igv = precio * (TASA_IGV / (1.0 + TASA_IGV))
            self.model.recaudacion_ciclo += igv
        elif comerciante.estrategia == "evasor":
            if self.random.random() > ALPHA_EVASION:
                comerciante.ingresos_declarados += precio
                igv = precio * (TASA_IGV / (1.0 + TASA_IGV))
                self.model.recaudacion_ciclo += igv
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
