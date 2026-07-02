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

Estos datos deben citarse en el marco teórico del informe final con sus fuentes (INEI/EPEN).

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
- Graficar evolución temporal de % formal/informal/evasor
- Graficar comportamiento del Fondo Público (mostrar el círculo vicioso si aparece)
- Comparar el equilibrio de la simulación contra el dato real (~70% informalidad INEI)
  y discutir similitudes/diferencias
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
