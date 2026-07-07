# El Trilema de la Gamarra

Simulación Multiagente (MAS) de informalidad y evasión tributaria en el Perú, con
[framework Mesa 3.5](https://github.com/projectmesa/mesa). Tres tipos de agentes
(`Comerciante`, `Consumidor`, `Sunat`) interactúan en ciclos discretos sobre un
grid tipo mercado, con valores reales en soles (UIT, RMV, IGV, multas del Código
Tributario) y decisión por Logit Multinomial.

El modelo incluye **mecanismos adaptativos del mundo real**: bancarrota de negocios
no rentables, entrada de nuevos comerciantes si el mercado es próspero, precios
dinámicos según demanda local, y SUNAT reactiva que endurece fiscalización si la
evasión sube.

## Resultados

| Métrica | Modelo | INEI (EPEN 2025) | Gap |
|---|---|---|---|
| Informalidad total | **72.3%** | 70.2% | +2.1 pp |
| Formal | 27.7% | ~29.8% | — |
| Evasor | 59.8% | — | — |
| Informal puro | 12.5% | — | — |

Con mecanismos adaptativos (bancarrota + entrada dinámica + SUNAT reactiva), el
modelo se acerca al dato INEI con solo +2.1 pp de gap.

## Stack

- Python 3.14
- Mesa 3.5.1 (`Agent`, `Model`, `MultiGrid`, `DataCollector`)
- pandas / matplotlib (análisis y gráficas)
- Solara 1.57 + altair (dashboard interactivo, opcional)
- Streamlit 1.45 (dashboard interactivo, más estable que Solara)

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
streamlit run src/visualizacion.py      # dashboard interactivo (Streamlit)
```

## Estructura

```
trilema-gamarra/
├── trilema_gamarra.ipynb   # notebook auto-contenido (Colab/Jupyter)
├── informe_proyecto_gamarra.md
├── requirements.txt
├── src/
│   ├── agentes/
│   │   ├── comerciante.py   # Logit Multinomial, 3 estrategias, precios dinámicos, bancarrota
│   │   ├── consumidor.py    # Moore, multi-compra, sorteo comprobantes, modelo binario evasión
│   │   └── sunat.py         # fiscalización, discrecionalidad, multa progresiva, SUNAT reactiva
│   ├── modelo.py            # ModeloGamarra: step bifásico, DataCollector, entrada dinámica
│   ├── entorno.py           # UIT, RMV, IGV, multas, umbrales adaptativos — parámetros centralizados
│   └── visualizacion.py     # dashboard Solara: 20 sliders, 6 presets, panel implicaciones
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
| `N_COMERCIANTES` | 40 | puestos iniciales en el grid |
| `N_CONSUMIDORES` | 800 | compradores por ciclo |
| `AGRESIVIDAD_SUNAT` | 0.55 | % de comercios auditados/ciclo (base) |
| `TASA_DISCRECIONALIDAD` | 0.30 | prob. de acta preventiva vs multa |
| `SENSIBILIDAD_MERCADO` | 3.0 | beta del Logit Multinomial |
| `ESCALA_LOGIT` | 10000.0 | normalización de utilidades en exp() |

## Mecanismos adaptativos del mundo real

Además de las políticas activables, el modelo incluye 5 mecanismos de feedback
que reproducen dinámicas de mercado reales:

| Mecanismo | Parámetro | Comportamiento |
|---|---|---|
| Bancarrota | `UMBRAL_BANCARROTA=500` | Comerciante con capital < S/ 500 cierra (marca `en_quiebra`) |
| Entrada dinámica | `UMBRAL_CRECIMIENTO=20000` | Si capital medio formal > S/ 20,000, entra nuevo comerciante formal |
| Precios dinámicos | `VENTAS_NORMALES=50` | Precio sube/baja ±20% según ventas del ciclo anterior |
| SUNAT reactiva | `EVASION_ALTA=60` | Si evasión > 60% sostenido 20 ciclos, `agresividad_efectiva += 0.02` |
| Adaptación Logit | (automático) | Si `agresividad_efectiva > 0.80`, riesgo percibido del formal sube 1.5x |

La `agresividad_efectiva` puede divergir del slider base (`agresividad_sunat`)
porque SUNAT la ajusta dinámicamente según el nivel de evasión observado.

## Políticas activables

Tres políticas se activan vía parámetros del modelo o checkboxes en el dashboard:

| Política | Parámetro | Mecanismo |
|---|---|---|
| Beneficio por antigüedad | `beneficio_antiguedad=True` | Descuento incremental en costo fijo por ciclo formal consecutivo (tope 50%) |
| Sorteo de comprobantes | `sorteo_comprobantes=True` | Consumidor que compra formal (o evasor declarado) tiene chance de premio |
| Multa progresiva | `multa_progresiva=True` | 1ra=acta, 2da=multa base, 3ra+=multa × factor_reincidencia |

## Dashboard interactivo

```bash
streamlit run src/visualizacion.py
```

- **Grid visual**: comerciantes cambian de color (verde/naranja/rojo) en tiempo real
- **20 sliders**: fiscalización, costos, IGV, multas, mercado, consumidores, escala Logit
- **3 checkboxes**: activar políticas nuevas
- **6 presets**: Línea base, Más enforcement, Subsidio formalidad, Cultura tributaria, Reducción tributaria, Combo reforma
- **1 gráfica de convergencia**: % estrategias + línea vertical de equilibrio + zona estable sombreada
- **Panel "Implicaciones del equilibrio"**: estado del sistema, agresividad base vs efectiva, zonas temporales (pre/durante/post), capital por estrategia vs inicial, texto descriptivo por escenario, implicación de política
- **Panel "Variables y su efecto"**: tabla estática de 16 variables con efecto esperado
- **Detección de colapsos**: COLAPSO FORMAL / COLAPSO AMBULANTE / COLAPSO FISCAL / COLAPSO DEMANDA

## Interfaces

### `Comerciante` (`src/agentes/comerciante.py`)

```python
class Comerciante(mesa.Agent):
    def __init__(self, model, estrategia="informal", capital=4000.0): ...
        # atributos: estrategia, capital, ventas_ciclo, ingresos_declarados,
        #            ingresos_ocultos, multas_pagadas, ciclos_formal_consecutivos,
        #            infracciones, en_quiebra, precio_actual

    def calcular_precio(self) -> float: ...
        # precio dinámico (B3): PRECIO_BASE * factor_demanda * carga_estrategia
        # formal/evasor: *(1+IGV), informal: sin IGV

    def estimar_utilidad_futura(self, est: str) -> float: ...
        # utilidad neta esperada por estrategia
        # B4: si agresividad_efectiva > 0.80, riesgo percibido del formal sube 1.5x

    def ajustar_cumplimiento(self) -> None: ...
        # transición probabilística vía Logit Multinomial

    def step(self): ...
        # B1: si capital < UMBRAL_BANCARROTA → en_quiebra=True (cierra)
        # ajusta cumplimiento → resetea ventas → descuenta costo fijo
```

### `Consumidor` (`src/agentes/consumidor.py`)

```python
class Consumidor(mesa.Agent):
    def __init__(self, model): ...
        # atributos: moral_tributaria, presupuesto

    def realizar_compra(self) -> None: ...
        # loop: busca comerciantes activos en Moore, elige por utilidad, compra
        # anti-loop infinito (max 20 movimientos)

    def ejecutar_transaccion(self, comerciante) -> None: ...
        # modelo binario: evasor declara o esconde por venta (prob alpha)
        # BUG 8 fix: comerciante retiene neto (precio - IGV), SUNAT recibe IGV
```

### `Sunat` (`src/agentes/sunat.py`)

```python
class Sunat(mesa.Agent):
    def __init__(self, model): ...
        # atributos: multas_ciclo, actas_ciclo, n_auditorias_ciclo,
        #            multas_acumuladas, actas_acumuladas, historia_evasion

    def fiscalizar_mercado(self) -> None: ...
        # audita muestra de comerciantes activos → multa o acta preventiva
        # B5: feedback adaptativo en agresividad_efectiva

    def _aplicar_feedback_evasion(self, comerciantes) -> None: ...
        # si evasión > 60% sostenido 20 ciclos → endurece (+0.02)
        # si formal > 50% sostenido → relaja (-0.01)
```

### `ModeloGamarra` (`src/modelo.py`)

```python
class ModeloGamarra(mesa.Model):
    def __init__(self, n_comerciantes=40, n_consumidores=800,
                 agresividad_sunat=0.55, tasa_discrecionalidad=0.30, ...): ...
        # agresividad_efectiva: la que Sunat usa (puede divergir del slider base)
    def step(self): ...
        # 1. Comerciante.shuffle_do("step")  — ajustan estrategia, B1 bancarrota
        # 2. Consumidor.shuffle_do("step")   — compran
        # 3. Sunat.step()                    — fiscaliza + B5 feedback adaptativo
        # 4. _entrada_nuevos_comerciantes()  — B2 entrada si mercado próspero
        # 5. datacollector.collect(self)
    # métricas: pct_formal, pct_evasor, pct_informal, recaudacion, multas,
    #           actas_preventivas, n_auditorias, capital_*, ventas_*,
    #           ingresos_declarados, ingresos_ocultos, presupuesto_medio, moral_media
```

## Orden del `step()`

1. **Comerciantes** — B1: check bancarrota → ajustan estrategia vía Logit → resetean ventas → descuentan costo fijo
2. **Consumidores** — se mueven (Moore), eligen tienda activa por utilidad, compran (modelo binario evasión)
3. **Sunat** — fiscaliza muestra de activos, aplica multas/actas, B5: feedback adaptativo en agresividad_efectiva
4. **Entrada dinámica** — B2: si capital medio formal > umbral y hay espacio, entra nuevo comerciante formal
5. **DataCollector** — recolecta métricas del ciclo

## Convenciones

1. Parámetros en `src/entorno.py` → modelo los recibe en `__init__` → agentes leen de `self.model.<param>`
2. `self.random` (Mesa RNG) para todo RNG — no usar el módulo `random` global
3. `agents.select(agent_type=Clase)` para filtrar agentes por tipo
4. Nomenclatura: `'formal'` / `'evasor'` / `'informal'` (strings, no abreviaturas)
5. Mesa 3.5 API: `Agent(model)` sin `unique_id`, `shuffle_do("step")`, `super().__init__(rng=seed)`
6. Comerciantes en quiebra (`en_quiebra=True`) se filtran en todas las operaciones (no participan del mercado)
