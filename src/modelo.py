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
    PESO_PRECIO,
    PESO_MORAL,
    WIDTH,
    HEIGHT,
    CAPITAL_INICIAL,
    DISTRIBUCION_INICIAL,
    SEED,
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
        width: int = WIDTH,
        height: int = HEIGHT,
        seed: int = SEED,
    ):
        super().__init__(rng=seed)
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.agresividad_sunat = agresividad_sunat
        self.tasa_discrecionalidad = tasa_discrecionalidad
        self.sensibilidad_mercado = sensibilidad_mercado
        self.peso_precio = peso_precio
        self.peso_moral = peso_moral
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
                "pct_formal": lambda m: m._pct("formal"),
                "pct_evasor": lambda m: m._pct("evasor"),
                "pct_informal": lambda m: m._pct("informal"),
                "recaudacion": lambda m: m.recaudacion_ciclo,
                "multas": lambda m: m.sunat.multas_emitidas,
                "actas_preventivas": lambda m: m.sunat.actas_preventivas,
            }
        )

    @property
    def prob_inspeccion_percibida(self) -> float:
        """Los comerciantes estiman el riesgo de inspección del ciclo."""
        return self.agresividad_sunat

    def _pct(self, estrategia: str) -> float:
        comerciantes = self.agents.select(agent_type=Comerciante)
        n = len(comerciantes)
        if not n:
            return 0.0
        return 100.0 * sum(1 for c in comerciantes if c.estrategia == estrategia) / n

    def step(self):
        self.recaudacion_ciclo = 0.0
        # Fase 1: mercado (comerciantes ajustan estrategia, consumidores compran)
        self.agents.select(agent_type=Comerciante).shuffle_do("step")
        self.agents.select(agent_type=Consumidor).shuffle_do("step")
        # Fase 2: fiscalización (Sunat lee recaudación y fiscaliza)
        self.sunat.step()
        self.datacollector.collect(self)


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
              f"evasor {row['pct_evasor']:5.1f}%  recaud S/.{row['recaudacion']:7.1f}")

    tail = df.tail(100)
    inf_final = tail["pct_informal"].mean() + tail["pct_evasor"].mean()
    print("\n--- Promedios últimos 100 ciclos ---")
    print(f"Formal:       {tail['pct_formal'].mean():5.1f}%")
    print(f"Informal:     {tail['pct_informal'].mean():5.1f}%")
    print(f"Evasor:       {tail['pct_evasor'].mean():5.1f}%")
    print(f"Recaudación:  S/. {tail['recaudacion'].mean():.1f}/ciclo")
    print(f"Multas:       {tail['multas'].mean():.1f}/ciclo")
    print(f"Actas prev.:  {tail['actas_preventivas'].mean():.1f}/ciclo")

    # ponytail: self-check — equilibrio no degenerado
    assert len(df) == N_CICLOS, f"Esperaba {N_CICLOS} filas, hay {len(df)}"
    for col in ["pct_formal", "pct_informal", "pct_evasor"]:
        assert 0 <= df[col].iloc[-1] <= 100, f"{col} fuera de rango"
    assert 1 < inf_final < 99, f"Informalidad {inf_final:.1f}% fuera de rango"
    print(f"\nInformalidad total (equilibrio): {inf_final:.1f}%  (target INEI: ~70%)")
    print("✓ Dinámica viva: el trilema produce equilibrio no trivial")
