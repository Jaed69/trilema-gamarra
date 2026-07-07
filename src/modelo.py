"""Modelo MAS principal. Orquesta grilla, step bifásico y DataCollector.

Punto de entrada: python -m src.modelo
"""
import mesa
from src.entorno import (
    N_COMERCIANTES,
    N_CONSUMIDORES,
    AGRESIVIDAD_SUNAT,
    TASA_DISCRECIONALIDAD,
    SENSIBILIDAD_MERCADO,
    ESCALA_LOGIT,
    PESO_PRECIO,
    PESO_MORAL,
    WIDTH,
    HEIGHT,
    CAPITAL_INICIAL,
    DISTRIBUCION_INICIAL,
    SEED,
    COSTO_FIJO_FORMALIDAD,
    TASA_IGV,
    MULTA_NO_EMISION,
    ALPHA_EVASION,
    MULTA_EVASION_PCT,
)
from src.agentes.comerciante import Comerciante
from src.agentes.consumidor import Consumidor
from src.agentes.sunat import Sunat


class ModeloGamarra(mesa.Model):
    def __init__(
        self,
        n_comerciantes: int = N_COMERCIANTES,
        n_consumidores: int = N_CONSUMIDORES,
        agresividad_sunat: float = AGRESIVIDAD_SUNAT,
        tasa_discrecionalidad: float = TASA_DISCRECIONALIDAD,
        peso_precio: float = PESO_PRECIO,
        peso_moral: float = PESO_MORAL,
        sensibilidad_mercado: float = SENSIBILIDAD_MERCADO,
        escala_logit: float = ESCALA_LOGIT,
        costo_fijo_formalidad: float = COSTO_FIJO_FORMALIDAD,
        tasa_igv: float = TASA_IGV,
        multa_no_emision: float = MULTA_NO_EMISION,
        alpha_evasion: float = ALPHA_EVASION,
        multa_evasion_pct: float = MULTA_EVASION_PCT,
        beneficio_antiguedad: bool = False,
        tasa_descuento_antiguedad: float = 0.05,
        sorteo_comprobantes: bool = False,
        prob_sorteo: float = 0.01,
        premio_sorteo: float = 50.0,
        multa_progresiva: bool = False,
        factor_reincidencia: float = 2.0,
        width: int = WIDTH,
        height: int = HEIGHT,
        seed: int = SEED,
    ):
        super().__init__(rng=seed)
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.agresividad_sunat = agresividad_sunat
        # B5: agresividad_efectiva es la que Sunat usa realmente; puede divergir del slider
        # base si el feedback adaptativo la ajusta (evasión alta → endurece, formal alto → relaja)
        self.agresividad_efectiva = agresividad_sunat
        self.tasa_discrecionalidad = tasa_discrecionalidad
        self.sensibilidad_mercado = sensibilidad_mercado
        self.escala_logit = escala_logit
        self.peso_precio = peso_precio
        self.peso_moral = peso_moral
        self.costo_fijo_formalidad = costo_fijo_formalidad
        self.tasa_igv = tasa_igv
        self.multa_no_emision = multa_no_emision
        self.alpha_evasion = alpha_evasion
        self.multa_evasion_pct = multa_evasion_pct
        self.beneficio_antiguedad = beneficio_antiguedad
        self.tasa_descuento_antiguedad = tasa_descuento_antiguedad
        self.sorteo_comprobantes = sorteo_comprobantes
        self.prob_sorteo = prob_sorteo
        self.premio_sorteo = premio_sorteo
        self.multa_progresiva = multa_progresiva
        self.factor_reincidencia = factor_reincidencia
        self.recaudacion_ciclo = 0.0

        # Comerciantes con distribución sesgada a no-formalidad
        for _ in range(n_comerciantes):
            est = self.random.choice(DISTRIBUCION_INICIAL)
            c = Comerciante(self, estrategia=est, capital=CAPITAL_INICIAL)
            self.grid.place_agent(
                c, (self.random.randrange(width), self.random.randrange(height))
            )

        # Consumidores con moral baja heterogénea
        for _ in range(n_consumidores):
            con = Consumidor(self)
            self.grid.place_agent(
                con, (self.random.randrange(width), self.random.randrange(height))
            )

        # Sunat fuera del grid (agente regulador, no espacial)
        self.sunat = Sunat(self)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                # Estrategias (%)
                "pct_formal": lambda m: m._pct("formal"),
                "pct_evasor": lambda m: m._pct("evasor"),
                "pct_informal": lambda m: m._pct("informal"),
                # Recaudación y fiscalización (per-ciclo)
                "recaudacion": lambda m: m.recaudacion_ciclo,
                "multas": lambda m: m.sunat.multas_ciclo,
                "actas_preventivas": lambda m: m.sunat.actas_ciclo,
                "n_auditorias": lambda m: m.sunat.n_auditorias_ciclo,
                # Capital medio por estrategia
                "capital_formal": lambda m: m._capital_medio("formal"),
                "capital_evasor": lambda m: m._capital_medio("evasor"),
                "capital_informal": lambda m: m._capital_medio("informal"),
                # Ventas medias por estrategia
                "ventas_formal": lambda m: m._ventas_medio("formal"),
                "ventas_evasor": lambda m: m._ventas_medio("evasor"),
                "ventas_informal": lambda m: m._ventas_medio("informal"),
                # Ingresos agregados (per-ciclo)
                "ingresos_declarados": lambda m: m._sum_attr_comerciante("ingresos_declarados"),
                "ingresos_ocultos": lambda m: m._sum_attr_comerciante("ingresos_ocultos"),
                # Estado consumidor
                "presupuesto_medio": lambda m: m._consumidor_media("presupuesto"),
                "moral_media": lambda m: m._consumidor_media("moral_tributaria"),
            }
        )

    @property
    def prob_inspeccion_percibida(self) -> float:
        """Los comerciantes estiman el riesgo de inspección del ciclo.

        B5: usa agresividad_efectiva (puede divergir del slider base si SUNAT
        es reactiva).
        """
        return self.agresividad_efectiva

    def _pct(self, estrategia: str) -> float:
        comerciantes = self._comerciantes_activos()
        n = len(comerciantes)
        if not n:
            return 0.0
        return 100.0 * sum(1 for c in comerciantes if c.estrategia == estrategia) / n

    def _capital_medio(self, estrategia: str) -> float:
        comerciantes = [c for c in self._comerciantes_activos()
                        if c.estrategia == estrategia]
        if not comerciantes:
            return 0.0
        return sum(c.capital for c in comerciantes) / len(comerciantes)

    def _ventas_medio(self, estrategia: str) -> float:
        comerciantes = [c for c in self._comerciantes_activos()
                        if c.estrategia == estrategia]
        if not comerciantes:
            return 0.0
        return sum(c.ventas_ciclo for c in comerciantes) / len(comerciantes)

    def _sum_attr_comerciante(self, attr: str) -> float:
        return sum(getattr(c, attr) for c in self._comerciantes_activos())

    def _consumidor_media(self, attr: str) -> float:
        consumidores = self.agents.select(agent_type=Consumidor)
        n = len(consumidores)
        if not n:
            return 0.0
        return sum(getattr(c, attr) for c in consumidores) / n

    def _comerciantes_activos(self):
        """B1: filtra comerciantes en bancarrota."""
        return [c for c in self.agents.select(agent_type=Comerciante)
                if not getattr(c, "en_quiebra", False)]

    def step(self):
        self.recaudacion_ciclo = 0.0
        # Fase 1: mercado (comerciantes ajustan estrategia, consumidores compran)
        self.agents.select(agent_type=Comerciante).shuffle_do("step")
        self.agents.select(agent_type=Consumidor).shuffle_do("step")
        # Fase 2: fiscalización (Sunat lee recaudación y fiscaliza)
        self.sunat.step()
        # B2: entrada de nuevos comerciantes si mercado próspero
        self._entrada_nuevos_comerciantes()
        self.datacollector.collect(self)

    def _entrada_nuevos_comerciantes(self) -> None:
        """B2: si capital medio formal > UMBRAL_CRECIMIENTO y hay espacio, entra nuevo formal."""
        from src.entorno import UMBRAL_CRECIMIENTO, MAX_COMERCIANTES, CAPITAL_INICIAL
        activos = self._comerciantes_activos()
        if len(activos) >= MAX_COMERCIANTES:
            return
        formales = [c for c in activos if c.estrategia == "formal"]
        if not formales:
            return
        capital_medio = sum(c.capital for c in formales) / len(formales)
        if capital_medio > UMBRAL_CRECIMIENTO:
            nuevo = Comerciante(self, estrategia="formal", capital=CAPITAL_INICIAL)
            x, y = self.random.randrange(self.grid.width), self.random.randrange(self.grid.height)
            self.grid.place_agent(nuevo, (x, y))


if __name__ == "__main__":
    modelo = ModeloGamarra()
    N_CICLOS = 1000
    for _ in range(N_CICLOS):
        modelo.step()

    df = modelo.datacollector.get_model_vars_dataframe()
    print("--- Trayectoria ---")
    for i in [0, 100, 500, 999]:
        row = df.iloc[i]
        inf = row["pct_informal"] + row["pct_evasor"]
        print(f"Ciclo {i:4d}: formal {row['pct_formal']:5.1f}%  informal {row['pct_informal']:5.1f}%  "
              f"evasor {row['pct_evasor']:5.1f}%  recaud S/.{row['recaudacion']:7.1f}  "
              f"multas {int(row['multas']):3d}  actas {int(row['actas_preventivas']):3d}")

    tail = df.tail(100)
    inf_final = tail["pct_informal"].mean() + tail["pct_evasor"].mean()
    print("\n--- Promedios últimos 100 ciclos ---")
    print(f"Formal:              {tail['pct_formal'].mean():5.1f}%")
    print(f"Informal:            {tail['pct_informal'].mean():5.1f}%")
    print(f"Evasor:              {tail['pct_evasor'].mean():5.1f}%")
    print(f"Recaudación/ciclo:   S/. {tail['recaudacion'].mean():.1f}")
    print(f"Multas/ciclo:        {tail['multas'].mean():.1f}")
    print(f"Actas prev./ciclo:   {tail['actas_preventivas'].mean():.1f}")
    print(f"Auditorías/ciclo:    {tail['n_auditorias'].mean():.1f}")
    print(f"Capital formal:      S/. {tail['capital_formal'].mean():.1f}")
    print(f"Capital evasor:      S/. {tail['capital_evasor'].mean():.1f}")
    print(f"Capital informal:    S/. {tail['capital_informal'].mean():.1f}")
    print(f"Ingresos declar.:    S/. {tail['ingresos_declarados'].mean():.1f}/ciclo")
    print(f"Ingresos ocultos:    S/. {tail['ingresos_ocultos'].mean():.1f}/ciclo")

    # ponytail: self-check — equilibrio no degenerado
    assert len(df) == N_CICLOS, f"Esperaba {N_CICLOS} filas, hay {len(df)}"
    for col in ["pct_formal", "pct_informal", "pct_evasor"]:
        assert 0 <= df[col].iloc[-1] <= 100, f"{col} fuera de rango"
    assert 1 < inf_final < 99, f"Informalidad {inf_final:.1f}% fuera de rango"
    print(f"\nInformalidad total (equilibrio): {inf_final:.1f}%  (target INEI: ~70%)")
    print(f"Gap vs INEI: {inf_final - 70.2:+.1f} pp")
    print("✓ Dinámica viva: el trilema produce equilibrio no trivial")
