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
        width: int = WIDTH,
        height: int = HEIGHT,
        seed: int = SEED,
    ):
        super().__init__(rng=seed)
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
        # Fase 1: mercado — comerciantes ajustan precios, consumidores compran
        self.agents.select(agent_type=Comerciante).shuffle_do("step")
        self.agents.select(agent_type=Consumidor).shuffle_do("step")
        # Fase 2: fiscalización — Sunat lee recaudación acumulada este ciclo
        self.sunat.step()
        self.datacollector.collect(self)


if __name__ == "__main__":
    modelo = ModeloGamarra()
    N_CICLOS = 1000
    for _ in range(N_CICLOS):
        modelo.step()

    df = modelo.datacollector.get_model_vars_dataframe()
    print("--- Trayectoria ---")
    print(f"Ciclo 0:   formal {df['pct_formal'].iloc[0]:5.1f}%  informal {df['pct_informal'].iloc[0]:5.1f}%  evasor {df['pct_evasor'].iloc[0]:5.1f}%  fondo {df['fondo_publico'].iloc[0]:8.1f}")
    print(f"Ciclo 100: formal {df['pct_formal'].iloc[100]:5.1f}%  informal {df['pct_informal'].iloc[100]:5.1f}%  evasor {df['pct_evasor'].iloc[100]:5.1f}%  fondo {df['fondo_publico'].iloc[100]:8.1f}")
    print(f"Ciclo 500: formal {df['pct_formal'].iloc[500]:5.1f}%  informal {df['pct_informal'].iloc[500]:5.1f}%  evasor {df['pct_evasor'].iloc[500]:5.1f}%  fondo {df['fondo_publico'].iloc[500]:8.1f}")
    print(f"Ciclo 999: formal {df['pct_formal'].iloc[-1]:5.1f}%  informal {df['pct_informal'].iloc[-1]:5.1f}%  evasor {df['pct_evasor'].iloc[-1]:5.1f}%  fondo {df['fondo_publico'].iloc[-1]:8.1f}")

    print("\n--- Promedios últimos 100 ciclos ---")
    tail = df.tail(100)
    print(f"Formal:       {tail['pct_formal'].mean():.1f}%")
    print(f"Informal:     {tail['pct_informal'].mean():.1f}%")
    print(f"Evasor:       {tail['pct_evasor'].mean():.1f}%")
    print(f"Fondo público: S/. {tail['fondo_publico'].mean():.1f}")
    print(f"Recaudación:   S/. {tail['recaudacion'].mean():.1f}")

    # ponytail: self-check — valida equilibrio no degenerado (no 0% ni 100%)
    assert len(df) == N_CICLOS, f"Esperaba {N_CICLOS} filas, hay {len(df)}"
    for col in ["pct_formal", "pct_informal", "pct_evasor"]:
        assert 0 <= df[col].iloc[-1] <= 100, f"{col} fuera de rango"
    # la informalidad no debe colapsar a 0 ni saturar al 100% — el trilema existe
    inf_final = tail["pct_informal"].mean() + tail["pct_evasor"].mean()
    assert 1 < inf_final < 99, f"Informalidad total {inf_final:.1f}% fuera de rango esperado"
    assert df["fondo_publico"].iloc[-1] > -1e6, "Fondo colapsado sin control"
    print(f"\nInformalidad total (equilibrio): {inf_final:.1f}%  (target INEI: ~70%)")
    print("✓ Dinámica viva: el trilema produce equilibrio no trivial")
