# El Trilema de la Gamarra

Simulación Multiagente (MAS) de informalidad y evasión tributaria en el Perú, con
[framework Mesa](https://github.com/projectmesa/mesa). Tres tipos de agentes
(`Comerciante`, `Consumidor`, `Sunat`) interactúan en ciclos discretos sobre un
grid tipo mercado.

## Stack

- Python 3.11+
- Mesa 3.5 (ABM: `Agent`, `Model`, `MultiGrid`, `DataCollector`)
- pandas / matplotlib (análisis y gráficas)

## Cómo correr

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.modelo          # corre 100 ciclos + self-check
```

## Estructura

```
src/
├── agentes/
│   ├── comerciante.py   # P1 — 3 estrategias, calcular_precio, decidir_estrategia
│   ├── consumidor.py    # P2 — presupuesto, moral tributaria, elegir_tienda, comprar
│   └── sunat.py         # P3 — fiscalización, aplicar_multa, Fondo Público
├── entorno.py           # parámetros centralizados (IGV, costos, presets) — dueño: P3
└── modelo.py            # P4 — ModeloGamarra: step(), DataCollector, entry point
```

## Parámetros

Todos en `src/entorno.py`. No hardcodear dentro de los agentes.

| Parámetro | Valor | Fuente |
|---|---|---|
| IGV | 0.18 | vigente Perú |
| Distribución inicial | 20% formal / 60% informal / 20% evasor | calibrado a ~70% informal (INEI 2025) |
| Costo formalidad/ciclo | 20.0 | supuesto del modelo |
| Presupuesto fiscalización | 1000.0 | supuesto |
| Multa evasor | 200.0 | supuesto |

---

## Contrato de Interfaces (firmas firmes)

Cada persona implementa su agente respetando estas firmas. El `step()` del modelo
llama `agents.shuffle_do("step")`, así que toda la lógica por ciclo vive en el
`step()` de cada agente.

### `Comerciante` — P1 (`src/agentes/comerciante.py`)

```python
class Comerciante(mesa.Agent):
    def __init__(self, model, tipo: str = "informal"): ...
        # atributos: self.tipo, self.precio, self.dinero

    def calcular_precio(self, igv: float = IGV) -> float: ...
        # devuelve precio final según tipo. Formal: suma IGV. Informal: no. Evasor: medio IGV.

    def decidir_estrategia(self, rentabilidad: dict) -> None: ...
        # rentabilidad = {"formal": float, "informal": float, "evasor": float}
        # si la actual da negativo, cambia al tipo de mayor rentabilidad.

    def step(self): ...
        # orquesta calcular_precio + descuenta costo de formalidad + (decidir_estrategia si toca)
```

### `Consumidor` — P2 (`src/agentes/consumidor.py`)

```python
class Consumidor(mesa.Agent):
    def __init__(self, model): ...
        # atributos: self.presupuesto, self.moral_tributaria (0..1)

    def elegir_tienda(self, comerciantes: list) -> Comerciante | None: ...
        # filtra por presupuesto asequible + pondera por precio, moral tributaria, distancia.
        # devuelve None si ninguna tienda es viable.

    def comprar(self, tienda: Comerciante | None) -> None: ...
        # resta precio del presupuesto, suma al dinero del comerciante.
        # no-op si tienda is None.

    def step(self): ...
        # obtiene comerciantes del modelo, elige tienda, compra.
```

### `Sunat` — P3 (`src/agentes/sunat.py`)

```python
class Sunat(mesa.Agent):
    def __init__(self, model): ...
        # atributos: self.presupuesto_fiscalizacion (Fondo Público)

    def seleccionar_objetivos(self, comerciantes: list, n: int = 3) -> list: ...
        # prioriza evasores según self.model.agresividad_sunat (0..1).
        # devuelve lista de objetivos a fiscalizar este ciclo.

    def aplicar_multa(self, objetivo: Comerciante) -> float: ...
        # si objetivo es evasor: suma MULTA al Fondo, descuenta del comerciante.
        # devuelve monto recaudado (0 si no aplica).

    def step(self): ...
        # selecciona objetivos entre los comerciantes, aplica multa a cada uno.
```

### `ModeloGamarra` — P4 (`src/modelo.py`)

```python
class ModeloGamarra(mesa.Model):
    def __init__(self, n_comerciantes=30, n_consumidores=50, agresividad_sunat=0.3, width=15, height=15): ...
    def step(self): ...
        # 1. agents.shuffle_do("step")  — orden aleatorio cada ciclo
        # 2. datacollector.collect(self)
    # métricas: pct_formal, pct_informal, pct_evasor, fondo_publico, recaudacion
```

---

## Orden del `step()` (referencia)

1. `Comerciante.step()` — calcula precio, descuenta costo de formalidad, decide estrategia
2. `Consumidor.step()` — elige tienda y compra
3. `Sunat.step()` — fiscaliza objetivos y aplica multas

El orden real es aleatorio (`shuffle_do`), pero cada agente solo lee estado que
el modelo le pasa, no estado de otros agentes en el mismo ciclo — esto evita bugs
de orden.

## Reglas de oro para el handoff

1. Los parámetros viven en `src/entorno.py`, no hardcodeados en agentes.
2. La lógica de negocio en `.py`, los notebooks solo para correr y graficar.
3. `agent_type=` en `agents.select()` es la forma de filtrar agentes por clase.
4. `self.random` (stdlib `Random`) para todo RNG — no usar el módulo `random` global.
