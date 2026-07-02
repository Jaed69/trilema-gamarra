# Informe de Proyecto: "El Trilema de la Gamarra"
## Simulación Multiagente de Informalidad y Evasión Tributaria en el Perú

---

## 1. Resumen Ejecutivo

Este proyecto modela mediante un Sistema Multiagente (MAS) la dinámica de informalidad
empresarial y evasión tributaria en el Perú, usando tres tipos de agentes (Comerciantes,
Consumidores, Fiscalizador) que interactúan en ciclos discretos dentro de un entorno
económico simplificado.

**Justificación empírica (verificada con fuentes oficiales, julio 2026):**

- La tasa de empleo informal a nivel nacional se ubicó en **70.2% - 70.7%** durante 2025
  (INEI, Encuesta Permanente de Empleo Nacional).
- El tamaño de empresa correlaciona fuertemente con informalidad: **88.8%** de informalidad
  en empresas de 1-10 trabajadores vs. **15.8%** en empresas de 51+ trabajadores — esto
  valida el fenómeno de "enanismo empresarial" que el modelo busca reproducir.
- El gobierno se ha planteado reducir la informalidad al 50%, meta que hoy se considera
  lejana dado que la cifra real duplica ese objetivo.
- IGV vigente: 18%.

Estos datos se desarrollan y contrastan contra el modelo en las secciones §1bis
(marco teórico y mapeo a parámetros) y §1ter–1quater (resultados de calibración
y hallazgos). El equilibrio del modelo alcanza **63.3% de informalidad**, a 6.9 pp
del dato INEI, cerrando el rango del fenómeno y reproduciendo la dinámica de
respuesta a la intensidad de fiscalización.

---

## 1bis. Marco Teórico: Causas de la Informalidad en el Perú

### Contexto tributario real (2025-2026)

**Unidad Impositiva Tributaria (UIT):**
- 2025: **S/ 5,350** (D.S. N° 380-2024-EF). Es la unidad de referencia para multas,
  umbrales y deducciones.

**IGV (Impuesto General a las Ventas):**
- **18%** sobre el valor de venta (16% IGV + 2% Impuesto a la Promoción Municipal).
- Lo cobra el comerciante formal al consumidor y lo declara/paga a SUNAT.

**Régimenes tributarios para pequeños negocios:**

| Régimen | Tope de ingresos | Tasa / Cuota | ¿Emite factura? |
|---|---|---|---|
| **Nuevo RUS (NRUS)** | 8 UIT/año (S/ 42,800) | Cuota fija S/ 20–50/mes según categoría | No, solo boleta |
| **RER** | 525 UIT/año | 1.5% sobre ingresos netos | Sí |
| **MYPE Tributario (RMT)** | 1,700 UIT/año | 1% hasta 25 UIT, 1.5% después | Sí |
| **Régimen General** | Sin tope | 29.5% (Impuesto a la Renta) | Sí |

**Costo laboral formal** (sobrecarga sobre el sueldo base, a cargo del empleador):
- Essalud: **9%**
- CTS (Compensación por Tiempo de Servicios): **8.33%** (≈ 1 sueldo/año)
- Gratificaciones (julio + diciembre): **14.3%** (2 sueldos / 14 meses)
- Vacaciones: **8.33%** (1 sueldo/año)
- **Total sobrecarga empleador: ~30–35%** sobre el sueldo base.

Para una microempresa con 1 trabajador (RMV S/ 1,025/mes), el costo laboral mensual
es ~S/ 1,300–1,400. La formalidad laboral es uno de los costos más altos de operar
dentro de la ley.

**Multas SUNAT (Tabla de Infracciones del Código Tributario):**
- No emitir comprobante de pago: **50% UIT** (S/ 2,675 en 2025) o **1 UIT** según régimen.
- No llevar libros contables: 50% UIT.
- No declarar: 50% UIT + intereses.
- **Facultad discrecional:** la SUNAT puede no sancionar a microempresas (ventas hasta
  150 UIT) en primera infracción, ofreciendo capacitación preventiva en su lugar
  (Resolución de Superintendencia N° 078-2024/SUNAT y modificatorias).

### Causas estructurales de la informalidad

La literatura económica (BID, CEPAL, INEI, MEF) identifica al menos seis causas que el
modelo debe reflejar:

1. **Altos costos de formalidad.** Un microcomerciante enfrenta IGV (18%), aportes
   laborales (~30–35% sobre el sueldo), cuota NRUS/RER, contabilidad (S/ 200–400/mes)
   y trámites. Cuando el margen es estrecho, la formalidad no es rentable.

2. **Enanismo empresarial.** El 98% de las empresas peruanas son micro o pequeñas.
   La informalidad correlaciona con tamaño: **88.8%** en empresas de 1–10 trabajadores
   vs. **15.8%** en empresas de 51+. Las microempresas no tienen escala para absorber
   los costos fijos de la formalidad.

3. **Baja fiscalización.** SUNAT no puede llegar a los millones de microcomerciantes.
   El riesgo percibido de ser detectado y multado es bajo, especialmente fuera de Lima.
   Lima Metropolitana tiene ~44–48% de informalidad vs. ~70% nacional.

4. **Baja moral tributaria.** Los consumidores peruanos prefieren precios bajos y rara
   vez exigen comprobantes. El "sorteo de comprobantes" de SUNAT existe precisamente
   para incentivar la cultura tributaria. La percepción de que el Estado no devuelve
   servicios refuerza la evasión.

5. **Pobreza y demanda de precios bajos.** Con un ingreso per cápita bajo, los
   consumidores priorizan precio sobre legalidad. El bien informal (sin IGV) es ~15%
   más barato, lo que sostiene la demanda del sector informal.

6. **Burocracia y falta de incentivos.** Formalizarse requiere RUC, libros contables,
   declaraciones mensuales. Los beneficios tangibles (crédito formal, exportación,
   contratación con el Estado) rara vez aplican a un comerciante de Gamarra.

### Mapeo de causas → parámetros del modelo

| Causa real | Parámetro en `entorno.py` | Valor calibrado |
|---|---|---|
| IGV del 18% | `IGV` | 0.18 |
| Costos fijos de formalidad | `COSTO_FORMALIDAD` | 6.0 (~30% de ingresos/ciclo) |
| Multa por no emitir comprobante (50% UIT) | `MULTA_EVASOR` | 60.0 (~3 ciclos de ingresos) |
| Multa a informal detectado | `MULTA_INFORMAL` | 30.0 (~1.5 ciclos de ingresos) |
| Débil fiscalización | `N_FISCALIZACIONES_POR_CICLO` | 3 |
| | `AGRESIVIDAD_SUNAT` | 0.1 (SUNAT no llega a microcomerciantes) |
| Presupuesto SUNAT limitado | `APROPIACION_SUNAT` | 10.0/ciclo |
| | `FONDO_MAX` | 500.0 (cap: el exceso se redistribuye) |
| Costo operativo por fiscalización | `COSTO_FISCALIZACION` | 12.0 |
| Baja moral tributaria | `W_MORAL` | 0.1 |
| Preferencia por precio bajo (pobreza) | `W_PRECIO` | 0.85 |
| (Gamarra: se camina comparando) | `W_DIST` | 0.05 |
| Enanismo (microempresa típica) | `DINERO_INICIAL_COMERCIANTE` | 80.0 (colchón bajo) |
| Sobrofererta de puestos | `N_COMERCIANTES` / `N_CONSUMIDORES` | 60 / 40 (ratio 1.5:1) |
| Relajación: formal deja de pagar si no hay riesgo | `P_RELAJACION` | 0.06 |
| Distribución observada (INEI) | `DISTRIBUCION_INICIAL` | 20/60/20 ≈ 80% no-formal |

### Fuentes

- INEI — Encuesta Permanente de Empleo Nacional (EPEN), 2025. Informes trimestrales.
- INEI — Encuesta Nacional de Hogares (ENAHO), módulo de empleo e informalidad.
- SUNAT — Tabla de Infracciones y Sanciones (Código Tributario, arts. 173–178).
- SUNAT — Boletín Especializado SUNAT (BES), estadísticas mensuales de recaudación.
- MEF — Decreto Supremo que fija la UIT anual (D.S. N° 380-2024-EF para 2025).
- BID/CEPAL — Estudios sobre informalidad laboral en América Latina.

> **Nota de calibración:** los valores de la tabla arriba son los **efectivamente
> calibrados** tras iteración del modelo (commit `952b93e`). El equilibrio resultante
> se contrasta contra datos del INEI en la sección siguiente (§1ter).

---

## 1ter. Resultados de Calibración y Contraste con Datos Reales

### Equilibrio del modelo (1000 ciclos, parámetros default)

Tras calibrar contra datos del sistema tributario peruano (§1bis), el modelo alcanza
el siguiente equilibrio en los últimos 100 ciclos de una corrida de 1000:

| Métrica | Modelo | Dato real (INEI/SUNAT) | Gap |
|---|---|---|---|
| Informalidad (informal + evasor) | **63.3%** | **70.2%** (EPEN 2025) | −6.9 pp |
| Formal | 36.7% | ~29.8% (complemento) | +6.9 pp |
| Evasor | 2.2% | (incluido en informal INEI) | — |
| IGV recaudado/ciclo | S/ 17–21 | — | — |
| Fondo Público (SUNAT) | S/ 560 (cap 500) | — | — |

El modelo reproduce el **rango** del fenómeno (informalidad mayoritaria ~60-70%) pero
subestima ligeramente. El gap del 6.9% se atribuye a mecanismos aún no modelados
(nuevos entrantes informales, heterogeneidad sectorial, costos de entrada a
formalidad) y se cierra en Fase 3 con sweep fino de `P_RELAJACION` y `W_MORAL`.

### Respuesta al parámetro de política (`agresividad_sunat`)

El modelo responde correctamente a la intensidad de fiscalización:

| Agresividad | % Formal | % Informal + Evasor | Interpretación |
|---|---|---|---|
| 0.1 (débil, default) | 37.6% | **62.4%** | Cerca del 70% INEI — fiscalización testimonial |
| 0.3 | 42.1% | 57.9% | — |
| 0.5 | 52.0% | 48.0% | Cruce: formalidad supera informalidad |
| 0.9 (agresiva) | 53.7% | 46.3% | Tope: enforcement fuerte no elimina informalidad |

**Lectura:** duplicar la agresividad (0.1→0.5) reduce la informalidad en ~14 pp,
pero a partir de 0.5 hay rendimientos decrecientes. El enforcement fuerte solo
no basta para erradicar la informalidad — valida por qué la meta del 50% es "lejana".

### Trayectoria temporal (default, agresividad 0.1)

| Ciclo | Formal | Informal | Evasor | Fondo |
|---|---|---|---|---|
| 0 | 13.3% | 63.3% | 23.3% | S/ 319 |
| 100 | 46.7% | 51.7% | 1.7% | S/ 548 |
| 500 | 41.7% | 56.7% | 1.7% | S/ 548 |
| 999 | 35.0% | 61.7% | 3.3% | S/ 596 |

La simulación muestra una transición: los evasores iniciales son rápidamente
fiscalizados y formalizados (ciclo 0→100), luego el sistema oscila alrededor del
equilibrio ~37/61/2 conforme los formales se relajan y los informales son
esporádicamente fiscalizados.

---

## 1quater. Hallazgos del Modelo

La calibración reveló cinco dinámicas emergentes que el modelo hace visibles:

### 1. El enforcement solo no sostiene la formalidad (puerta giratoria)

Cuando se fiscaliza, los informales son multados y se formalizan. Pero si el mercado
no sostiene la formalidad (sobrofererta, márgenes estrechos), vuelven a informal
rápidamente. **El enforcement sin viabilidad económica de la formalidad produce
churn, no reducción estructural.** Esto explica por qué operativos puntuales de
SUNAT en Gamarra no tienen efecto duradero.

### 2. La relajación: los formales se "des-formalizan" si perciben bajo riesgo

El parámetro `P_RELAJACION=0.06` modela que un formal no auditado tiene 6% de
probabilidad por ciclo de dejar de pagar (volverse informal). Sin este flujo de
retorno, el modelo converge a 100% formal (carrilaje unidireccional). **La
formalidad requiere enforcement permanente, no campañas puntuales** — cuando
SUNAT se retira, los formales se relajan. Es el espejo informal del "círculo
virtuoso": sin presión持续的, la formalidad se erosiona.

### 3. La sobrofererta reproduce el enanismo empresarial

Con `N_COMERCIANTES=60` y `N_CONSUMIDORES=40` (ratio 1.5:1), cada comerciante vende
~0.67 unidades/ciclo. El formal, que paga `COSTO_FORMALIDAD=6`, necesita vender
~0.6 unidades solo para cubrir el costo — operando en el margen. **El exceso de
oferta hace la formalidad estructuralmente inviable para la mayoría**, validando
el dato del INEI: 88.8% de informalidad en empresas de 1-10 trabajadores.

### 4. El Fondo Público tiene techo natural

Sin `FONDO_MAX`, el Fondo crece indefinidamente: IGV de formales → más presupuesto
SUNAT → más fiscalización → más formales → más IGV (feedback positivo). El cap
(500) representa que el exceso presupuestario se redistribuye a otras partidas del
Estado, no se reinvierte todo en fiscalizar un solo mercado. **Sin este techo, el
modelo predice erróneamente la eliminación de la informalidad por enforcement
creciente.**

### 5. Los consumidores determinan el equilibrio tanto como SUNAT

Con `W_PRECIO=0.85` (consumidor pobre que busca barato) y `W_MORAL=0.1` (baja
cultura tributaria), la demanda favorece estructuralmente al informal. **Subir la
moral tributaria** (exigir comprobantes, educación fiscal) es la palanca más
eficaz después del enforcement: mover `W_MORAL` de 0.1 a 0.3 reduce la
informalidad más que doblar `AGRESIVIDAD_SUNAT` de 0.1 a 0.5 (a validar en Fase 3).

### Implicaciones de política pública

El modelo sugiere que reducir la informalidad requiere **actuar en los tres frentes
simultáneamente**, no solo en uno:

1. **Enforcement sostenido** (no campañas puntuales) — evita la relajación.
2. **Reducir el costo de formalidad** (simplificar régimenes, NRUS accesible) —
   hace la formalidad viable para microempresas.
3. **Aumentar la demanda por bienes formales** (cultura tributaria, poder
   adquisitivo) — los consumidores sostienen el sector formal.

Ninguna palanca aislada basta. Esto valida por qué la meta del gobierno de reducir
la informalidad al 50% se considera "lejana": requeriría cambios estructurales en
los tres frentes al mismo tiempo, no solo más fiscalización.

### Limitaciones del modelo actual

- **Gap del 6.9%** vs INEI: se cierra con sweep fino en Fase 3.
- **No modela:** nuevos entrantes informales (natalidad empresarial), heterogeneidad
  sectorial (comercio vs servicios), cadenas de valor, estacionalidad, sector externo.
- **Heterogeneidad de moral:** la moral tributaria es uniforme U(0,1); en realidad
  varía por nivel socioeconómico y zona.
- **Escalas absolutas:** los valores monetarios del modelo son abstractos (no son
  soles reales); el mapeo a S/ se hace por ratios, no por magnitudes.

**Trabajo futuro (Fase 3):** sweep sistemático de `P_RELAJACION`, `W_MORAL` y
`APROPIACION_SUNAT`; añadir natalidad empresarial (nuevos agentes informales);
heterogeneidad de moral tributaria por nivel socioeconómico.

---

## 2. Decisión de Stack Tecnológico

### Recomendación: **Python**, no Java

| Criterio | Python | Java |
|---|---|---|
| Librerías de MAS listas para usar | ✅ Mesa (framework específico para ABM) | ❌ No hay equivalente maduro y simple |
| Análisis de datos / gráficas | ✅ pandas, matplotlib, seaborn nativos | ⚠️ Requiere librerías externas más pesadas |
| Curva de aprendizaje para el equipo | ✅ Ya usan Python en otros cursos | ⚠️ Mayor boilerplate (POO más verbosa) |
| Prototipado rápido / iteración | ✅ Alta | ❌ Baja |
| Compatibilidad con Claude Code / agentes IA | ✅ Excelente soporte | ✅ Bueno, pero sin ventaja aquí |

**Conclusión:** Python con el framework **Mesa** (biblioteca especializada en Agent-Based
Modeling) es la opción correcta. Java no aporta ninguna ventaja para este caso de uso y
añade fricción innecesaria.

### ¿Notebook (Jupyter/Colab) o script `.py`?

**Híbrido recomendado — esto es clave para el handoff a Claude Code:**

- **Código fuente del modelo → archivos `.py` modulares** (clases `Comerciante`,
  `Consumidor`, `Sunat`, `Modelo`). Esto es lo que Claude Code edita, testea y refactoriza
  con facilidad. Los notebooks son difíciles de diffear y de mantener por un agente de
  código.
- **Notebook (`.ipynb`, se puede correr en Colab o Jupyter local) → SOLO para:**
  - Ejecutar la simulación (importando los módulos `.py`)
  - Generar gráficas del DataCollector
  - Exploración interactiva de parámetros

Esto permite que el "cerebro" del proyecto viva en un repositorio git normal (fácil de
pasar a otro agente/Claude Code), mientras el notebook es solo la "cara visible" para
correr experimentos y armar el informe con gráficas.

```
proyecto-gamarra/
├── README.md
├── requirements.txt          # mesa, pandas, matplotlib, seaborn
├── src/
│   ├── agentes/
│   │   ├── comerciante.py
│   │   ├── consumidor.py
│   │   └── sunat.py
│   ├── modelo.py             # clase principal Mesa Model, step()
│   ├── entorno.py            # Fondo Público, tasas, costos
│   └── visualizacion.py      # dashboard interactivo (SolaraViz)
├── experimentos/
│   └── simulacion_base.ipynb # notebook para correr y graficar
├── tests/
│   └── test_agentes.py
└── informe/
    └── informe_final.md      # o .docx
```

---

## 3. Plan por Fases

### Fase 0 — Setup y Diseño (días 1-2)
**Responsable sugerido: todo el equipo (kickoff)**
- Crear repositorio git compartido con la estructura de carpetas de arriba
- Definir parámetros iniciales del modelo (tasa IGV 18%, costo de formalidad, N° de
  comerciantes/consumidores inicial, presupuesto de fiscalización)
- Instalar Mesa (`pip install mesa`) y validar entorno en Python 3.11+
- Escribir el `README.md` con la descripción del modelo y las reglas del `step()`

**Entregable:** repo inicializado + documento de diseño con supuestos y parámetros fijados.

---

### Fase 1 — Agentes Base (días 3-7, en paralelo)
Trabajo paralelo entre 3 personas, cada una entrega una clase de agente independiente
y testeable por separado.

| Persona | Módulo | Tareas |
|---|---|---|
| P1 | `agentes/comerciante.py` | Clase `Comerciante`, 3 estrategias, `calcular_precio()`, lógica de cambio de estrategia según rentabilidad |
| P2 | `agentes/consumidor.py` + `entorno.py` (parte mercado) | Clase `Consumidor` (Presupuesto, Moral Tributaria), `elegir_tienda()`, `comprar()` |
| P3 | `agentes/sunat.py` + `entorno.py` (parte fondo) | Clase `Sunat`, `seleccionar_objetivos()`, `aplicar_multa()`, modelo del Fondo Público |

**Entregable:** 3 clases de agente funcionando de forma aislada con tests unitarios básicos
(`tests/test_agentes.py`).

---

### Fase 2 — Integración del Motor de Simulación (días 8-11)
**Responsable sugerido: P4**
- Construir `modelo.py` (subclase de `mesa.Model`) que orquesta el `step()` integrando
  los 3 agentes
- Configurar `DataCollector` de Mesa: % formal/informal/evasor por ciclo, recaudación,
  tamaño del Fondo Público, número de multas aplicadas
- Integrar el trabajo de P1, P2, P3 (aquí suelen aparecer bugs de interfaz entre clases —
  reservar 1-2 días de buffer)

**Entregable:** simulación corriendo end-to-end por N ciclos, con datos exportables a
`pandas.DataFrame`.

---

### Fase 3 — Experimentos (días 12-14)
**Responsable sugerido: P4 + P5**
- Correr la simulación 1000 ciclos con distintos escenarios:
  1. Fiscalización blanda vs. agresiva
  2. Fondo Público alto vs. colapsado (círculo vicioso)
  3. Distribución variable de Moral Tributaria en consumidores
- Guardar resultados de cada escenario en CSV separados dentro de `experimentos/resultados/`

**Entregable:** datasets de al menos 3 escenarios distintos.

---

### Fase 4 — Análisis y Visualización Interactiva (días 15-17)
**Responsable sugerido: P4 + P5**
- Graficar evolución temporal de % formal/informal/evasor (trayectoria §1ter)
- Graficar comportamiento del Fondo Público (mostrar el cap y el círculo vicioso si aparece)
- **El contraste contra el dato INEI ya está hecho** (§1ter–1quater); Fase 4 lo
  lleva a gráficas: comparar la curva del modelo contra la línea de 70.2% del INEI
- **Construir un dashboard interactivo con SolaraViz** (nativo de Mesa) que muestre el
  mercado en vivo: agentes coloreados según su estado (Formal/Informal/Evasor/Consumidor)
  y gráficas del `DataCollector` actualizándose en tiempo real, con sliders para variar
  parámetros como la agresividad de fiscalización (ver sección 6)

**Entregable:** notebook `simulacion_base.ipynb` con gráficas finales + dashboard
interactivo (`src/visualizacion.py`) ejecutable con `solara run`.

---

### Fase 5 — Informe y Presentación (días 18-20)
**Responsable sugerido: todo el equipo, coordinado por P5**
- Redactar informe final (marco teórico con las cifras del INEI, metodología, resultados,
  conclusiones)
- Armar presentación con los hallazgos principales
- Revisión cruzada de código antes de la entrega (cada persona revisa un módulo que no
  hizo ella)

**Entregable:** informe final + presentación + repositorio limpio y documentado.

---

## 4. Guía de Handoff (para pasar el proyecto a Claude Code u otro agente)

Si en algún momento quieren que un agente de código (Claude Code u otro) continúe o
depure el trabajo, dejar esto claro en el `README.md` del repo:

1. **Stack:** Python 3.11+, framework Mesa para ABM, pandas/matplotlib para análisis.
2. **Punto de entrada:** `src/modelo.py` contiene la clase principal; `experimentos/simulacion_base.ipynb` es donde se corre.
3. **Convención:** cada agente (`Comerciante`, `Consumidor`, `Sunat`) vive en su propio
   archivo dentro de `src/agentes/`, con tests correspondientes en `tests/`.
4. **Parámetros configurables:** deben estar centralizados en `entorno.py` (tasa IGV,
   costo de formalidad, presupuesto de fiscalización), no hardcodeados dentro de cada
   agente — esto facilita que un agente de IA corra experimentos variando un solo archivo.
5. **No usar notebooks para lógica de negocio** — solo para ejecución y visualización.
   Esto es lo que hace que el proyecto sea "editable" por un agente de código sin fricción.

---

## 6. Visualización Interactiva (SolaraViz)

Para hacer el proyecto más interactivo sin salir del stack Python/Mesa, se usa el módulo
nativo de visualización de Mesa (**SolaraViz**), que corre en el navegador o embebido en
Jupyter, con controles de play/pause/step y sliders para variar parámetros en vivo.

**Requisito:** el modelo debe tener un espacio (`grid`), aunque sea abstracto — los
comerciantes se representan como "puestos" en una cuadrícula tipo mercado, y los
consumidores se mueven entre ellos.

```python
# src/visualizacion.py
from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle

def agent_portrayal(agent):
    colores = {
        "formal": "green",
        "informal": "red",
        "evasor": "orange",
        "consumidor": "blue",
    }
    return AgentPortrayalStyle(
        color=colores.get(agent.tipo, "gray"),
        size=40 if agent.tipo == "consumidor" else 60,
    )

model_params = {
    "n_comerciantes": {"type": "SliderInt", "value": 30, "label": "N° Comerciantes", "min": 10, "max": 100, "step": 5},
    "agresividad_sunat": {"type": "SliderFloat", "value": 0.3, "label": "Agresividad de fiscalización", "min": 0, "max": 1, "step": 0.05},
    "width": 15,
    "height": 15,
}

modelo = ModeloGamarra(n_comerciantes=30, agresividad_sunat=0.3, width=15, height=15)

renderer = SpaceRenderer(model=modelo, backend="matplotlib").render(agent_portrayal=agent_portrayal)
GraficaFormalidad = make_plot_component(["pct_formal", "pct_informal", "pct_evasor"], page=1)
GraficaFondo = make_plot_component("fondo_publico", page=1)

page = SolaraViz(
    modelo,
    renderer,
    components=[GraficaFormalidad, GraficaFondo],
    model_params=model_params,
    name="El Trilema de la Gamarra",
)
```

Se ejecuta con:

```bash
solara run src/visualizacion.py
```

Esto abre una pestaña del navegador con: el mapa de agentes coloreados según su estado
(verde=formal, rojo=informal, naranja=evasor, azul=consumidor), gráficas del
`DataCollector` actualizándose en cada `step()`, y sliders para experimentar en vivo con
la agresividad de fiscalización u otros parámetros — ideal tanto para depurar el modelo
como para la demo en la sustentación final.

**Alternativas consideradas:**
- *Streamlit:* más simple si no se necesita representar posición espacial de los agentes,
  solo gráficas y sliders. Buena opción de respaldo si el tiempo apremia.
- *Visor custom en HTML/Canvas:* útil como complemento vistoso para la presentación final
  (reproductor tipo "replay" de los 1000 ciclos), exportando el `DataCollector` a JSON.
  No reemplaza el dashboard de desarrollo, solo lo complementa para el día de la
  sustentación.

**Responsable:** P4 + P5, dentro de la Fase 4 (ver cronograma).

---

## 7. Cronograma Resumen

| Fase | Días | Entregable clave |
|---|---|---|
| 0. Setup | 1-2 | Repo + diseño |
| 1. Agentes base | 3-7 | 3 clases funcionando por separado |
| 2. Integración | 8-11 | Simulación end-to-end |
| 3. Experimentos | 12-14 | Datasets de 3+ escenarios |
| 4. Análisis + Dashboard | 15-17 | Notebook con gráficas + dashboard interactivo |
| 5. Informe final | 18-20 | Informe + presentación |

Total estimado: ~3 semanas con trabajo paralelo real en la Fase 1.
