# El Trilema de la Gamarra

Simulación Multiagente (MAS) de informalidad y evasión tributaria en el Perú, con
[framework Mesa 3.5](https://github.com/projectmesa/mesa). Tres tipos de agentes
(`Comerciante`, `Consumidor`, `Sunat`) interactúan en ciclos discretos sobre un
grid tipo mercado, con valores reales en soles (UIT, RMV, IGV, multas del Código
Tributario) y decisión por Logit Multinomial.

## Resultados

| Métrica | Modelo | INEI (EPEN 2025) | Gap |
|---|---|---|---|
| Informalidad total | **65.5%** | 70.2% | −4.7 pp |
| Formal | 34.5% | ~29.8% | — |
| Evasor | 53.4% | — | — |
| Informal puro | 12.1% | — | — |

## Stack

- Python 3.14
- Mesa 3.5.1 (`Agent`, `Model`, `MultiGrid`, `DataCollector`)
- pandas / matplotlib (análisis y gráficas)
- Solara 1.57 + altair (dashboard interactivo, opcional)

## Cómo correr

### Opción 1: Notebook (Google Colab o Jupyter)

```bash
# En Colab: abrir trilema_gamarra.ipynb y ejecutar todo
# La primera celda instala dependencias automáticamente
```

### Opción 2: Scripts .py

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m src.modelo                    # 1000 ciclos + self-check
PYTHONPATH=. solara run src/visualizacion.py   # dashboard interactivo
```

## Estructura

```
trilema-gamarra/
├── trilema_gamarra.ipynb   # notebook auto-contenido (Colab/Jupyter)
├── informe_proyecto_gamarra.md
├── requirements.txt
├── src/
│   ├── agentes/
│   │   ├── comerciante.py   # Logit Multinomial, 3 estrategias, beneficio antigüedad
│   │   ├── consumidor.py    # Moore, multi-compra, sorteo comprobantes
│   │   └── sunat.py         # fiscalización, discrecionalidad, multa progresiva
│   ├── modelo.py            # ModeloGamarra: step bifásico, DataCollector
│   ├── entorno.py           # UIT, RMV, IGV, multas — parámetros centralizados
│   └── visualizacion.py     # dashboard Solara: 19 sliders, 6 presets, grid visual
└── .venv/
```

## Parámetros principales

Todos en `src/entorno.py`. Los agentes leen de `self.model.<param>`.

| Parámetro | Valor | Descripción |
|---|---|---|
| `UIT_VIGENTE` | S/ 5,500 | UIT 2026 (D.S. N° 301-2025-EF) |
| `RMV_VIGENTE` | S/ 1,130 | RMV 2025 (D.S. N° 006-2024-TR) |
| `TASA_IGV` | 0.18 | 18% (16% IGV + 2% IPM) |
| `COSTO_FIJO_FORMALIDAD` | S/ 400 | contabilidad + trámites + aportes |
| `MULTA_NO_EMISION` | S/ 2,750 | 50% UIT (Código Tributario Art. 174) |
| `ALPHA_EVASION` | 0.60 | fracción de ventas no reportadas |
| `N_COMERCIANTES` | 40 | puestos en el grid |
| `N_CONSUMIDORES` | 800 | compradores por ciclo |
| `AGRESIVIDAD_SUNAT` | 0.55 | % de comercios auditados/ciclo |
| `TASA_DISCRECIONALIDAD` | 0.30 | prob. de acta preventiva vs multa |
| `SENSIBILIDAD_MERCADO` | 3.0 | beta del Logit Multinomial |

## Políticas activables

Tres políticas se activan vía parámetros del modelo o checkboxes en el dashboard:

| Política | Parámetro | Mecanismo |
|---|---|---|
| Beneficio por antigüedad | `beneficio_antiguedad=True` | Descuento incremental en costo fijo por ciclo formal consecutivo (tope 50%) |
| Sorteo de comprobantes | `sorteo_comprobantes=True` | Consumidor que compra formal tiene chance de premio (aumenta utilidad de formal) |
| Multa progresiva | `multa_progresiva=True` | 1ra=acta, 2da=multa base, 3ra+=multa × factor_reincidencia |

## Dashboard interactivo

```bash
PYTHONPATH=. solara run src/visualizacion.py
```

- **Grid visual**: comerciantes cambian de color (verde/naranja/rojo) en tiempo real
- **19 sliders**: fiscalización, costos, IGV, multas, mercado, consumidores
- **3 checkboxes**: activar políticas nuevas
- **6 presets**: Línea base, Más enforcement, Subsidio formalidad, Cultura tributaria, Reducción tributaria, Combo reforma
- **2 gráficas en vivo**: % estrategias + recaudación

## Interfaces

### `Comerciante` (`src/agentes/comerciante.py`)

```python
class Comerciante(mesa.Agent):
    def __init__(self, model, estrategia="informal", capital=4000.0): ...
        # atributos: estrategia, capital, ventas_ciclo, ingresos_declarados,
        #            ingresos_ocultos, multas_pagadas, ciclos_formal_consecutivos, infracciones

    def calcular_precio(self) -> float: ...
        # formal: PRECIO_BASE * (1 + IGV)
        # evasor: parte formal + parte informal (alpha)
        # informal: PRECIO_BASE (sin IGV)

    def estimar_utilidad_futura(self, est: str) -> float: ...
        # utilidad neta esperada por estrategia (formal/evasor/informal)

    def ajustar_cumplimiento(self) -> None: ...
        # transición probabilística vía Logit Multinomial

    def step(self): ...
        # ajusta cumplimiento → resetea ventas → descuenta costo fijo
```

### `Consumidor` (`src/agentes/consumidor.py`)

```python
class Consumidor(mesa.Agent):
    def __init__(self, model): ...
        # atributos: moral_tributaria, presupuesto

    def realizar_compra(self) -> None: ...
        # loop: busca comerciantes en Moore, elige por utilidad, compra, mueve

    def ejecutar_transaccion(self, comerciante) -> None: ...
        # enruta IGV según estrategia del vendedor (F declara, E parcial, I oculto)

    def step(self): ...
        # resetea presupuesto → realiza compra
```

### `Sunat` (`src/agentes/sunat.py`)

```python
class Sunat(mesa.Agent):
    def __init__(self, model): ...
        # atributos: tasa_cobertura, multas_emitidas, actas_preventivas

    def fiscalizar_mercado(self) -> None: ...
        # audita muestra de comerciantes → multa o acta preventiva
        # informal detectado → forzado a evasor

    def step(self): ...
        # fiscaliza mercado
```

### `ModeloGamarra` (`src/modelo.py`)

```python
class ModeloGamarra(mesa.Model):
    def __init__(self, n_comerciantes=40, n_consumidores=800,
                 agresividad_sunat=0.55, tasa_discrecionalidad=0.30, ...): ...
    def step(self): ...
        # 1. Comerciante.shuffle_do("step")  — ajustan estrategia y resetean
        # 2. Consumidor.shuffle_do("step")   — compran
        # 3. Sunat.step()                    — fiscaliza
        # 4. datacollector.collect(self)
    # métricas: pct_formal, pct_evasor, pct_informal, recaudacion, multas, actas_preventivas
```

## Orden del `step()`

1. **Comerciantes** — deciden estrategia vía Logit, resetean ventas, descuentan costo fijo
2. **Consumidores** — se mueven (Moore), eligen tienda por utilidad, compran
3. **Sunat** — fiscaliza muestra, aplica multas/actas, fuerza informales a evasor

## Convenciones

1. Parámetros en `src/entorno.py` → modelo los recibe en `__init__` → agentes leen de `self.model.<param>`
2. `self.random` (Mesa RNG) para todo RNG — no usar el módulo `random` global
3. `agents.select(agent_type=Clase)` para filtrar agentes por tipo
4. Nomenclatura: `'formal'` / `'evasor'` / `'informal'` (strings, no abreviaturas)
5. Mesa 3.5 API: `Agent(model)` sin `unique_id`, `shuffle_do("step")`, `super().__init__(rng=seed)`
