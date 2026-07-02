"""Modelo MAS principal. Orquesta step() + DataCollector.

Punto de entrada: python -m src.modelo
"""
import mesa
from src.entorno import (
    N_COMERCIANTES,
    N_CONSUMIDORES,
    AGRESIVIDAD_SUNAT,
    WIDTH,
    HEIGHT,
    DISTRIBUCION_INICIAL,
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
        width: int = WIDTH,
        height: int = HEIGHT,
    ):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.agresividad_sunat = agresividad_sunat

        tipos = list(DISTRIBUCION_INICIAL.keys())
        pesos = list(DISTRIBUCION_INICIAL.values())
        for _ in range(n_comerciantes):
            tipo = self.random.choices(tipos, weights=pesos)[0]
            c = Comerciante(self, tipo=tipo)
            self.grid.place_agent(
                c, (self.random.randrange(width), self.random.randrange(height))
            )

        for _ in range(n_consumidores):
            con = Consumidor(self)
            self.grid.place_agent(
                con, (self.random.randrange(width), self.random.randrange(height))
            )

        self.sunat = Sunat(self)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "pct_formal": lambda m: m._pct("formal"),
                "pct_informal": lambda m: m._pct("informal"),
                "pct_evasor": lambda m: m._pct("evasor"),
                "fondo_publico": lambda m: m.sunat.presupuesto_fiscalizacion,
                "recaudacion": lambda m: getattr(m, "_recaudacion_ciclo", 0),
            }
        )
        self._recaudacion_ciclo = 0

    def _pct(self, tipo: str) -> float:
        comerciantes = self.agents.select(agent_type=Comerciante)
        n = len(comerciantes)
        return 100.0 * sum(1 for c in comerciantes if c.tipo == tipo) / n if n else 0.0

    def step(self):
        self._recaudacion_ciclo = 0
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


if __name__ == "__main__":
    modelo = ModeloGamarra()
    N_CICLOS = 100
    for _ in range(N_CICLOS):
        modelo.step()

    df = modelo.datacollector.get_model_vars_dataframe()
    print(df.tail(5))
    print("\n--- Resumen final ---")
    print(f"Formal:       {df['pct_formal'].iloc[-1]:.1f}%")
    print(f"Informal:     {df['pct_informal'].iloc[-1]:.1f}%")
    print(f"Evasor:       {df['pct_evasor'].iloc[-1]:.1f}%")
    print(f"Fondo público: S/. {df['fondo_publico'].iloc[-1]:.1f}")

    # ponytail: self-check mínimo
    for col in ["pct_formal", "pct_informal", "pct_evasor"]:
        assert 0 <= df[col].iloc[-1] <= 100, f"{col} fuera de rango"
    assert len(df) == N_CICLOS, f"Esperaba {N_CICLOS} filas, hay {len(df)}"
    print("\n✓ Esqueleto dividido funciona end-to-end")
