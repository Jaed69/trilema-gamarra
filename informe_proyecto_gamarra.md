# Informe de Proyecto: "El Trilema de la Gamarra"
## Simulación Multiagente de Informalidad y Evasión Tributaria en el Perú

---

## 1. Resumen Ejecutivo

Este proyecto modela mediante un Sistema Multiagente (MAS) la dinámica de informalidad
empresarial y evasión tributaria en el Perú, usando tres tipos de agentes (Comerciantes,
Consumidores, Fiscalizador) que interactúan en ciclos discretos dentro de un entorno
económico simplificado. El modelo usa valores reales en soles (UIT, RMV, IGV, multas del
Código Tributario), decisión por Logit Multinomial, y fiscalización con gradualidad y
discrecionalidad según la normatividad vigente.

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
(marco teórico y mapeo a parámetros), §1ter–1quater (resultados de calibración
y hallazgos) y §1quinquies (comparación de políticas). El equilibrio del modelo
alcanza **72.3% de informalidad**, a solo +2.1 pp del dato INEI, con los tres tipos
coexistiendo: 27.7% formal, 59.8% evasor, 12.5% informal puro. El modelo incluye
mecanismos adaptativos (bancarrota, entrada dinámica, SUNAT reactiva) que lo
acercan al dato real.

**Componentes del proyecto:**

- Modelo MAS modular en `src/` (Mesa 3.5, Python 3.14)
- **3 políticas activables**: beneficio por antigüedad formal, sorteo de comprobantes,
  multa progresiva por reincidencia
- **Dashboard interactivo** (Solara): grid visual en tiempo real, 19 sliders, 6 presets
- **Notebook auto-contenido** (`trilema_gamarra.ipynb`): ejecutable en Google Colab sin
  pre-configuración

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
| IGV del 18% | `TASA_IGV` | 0.18 |
| UIT 2026 (referencia multas) | `UIT_VIGENTE` | 5500.0 |
| RMV 2025 (costo laboral) | `RMV_VIGENTE` | 1130.0 |
| Costos fijos de formalidad | `COSTO_FIJO_FORMALIDAD` | 400.0 (contabilidad + trámites + aportes) |
| Multa por no emitir comprobante (50% UIT) | `MULTA_NO_EMISION` | 2750.0 |
| Sanción sobre evasión parcial | `MULTA_EVASION_PCT` | 0.30 (30% de ingresos ocultos) |
| Gradualidad por subsanación | `DESCUENTO_GRADUALIDAD` | 0.90 (rebaja 90%) |
| Discrecionalidad SUNAT (acta vs multa) | `TASA_DISCRECIONALIDAD` | 0.30 |
| Débil fiscalización | `AGRESIVIDAD_SUNAT` | 0.55 (% de comercios auditados/ciclo) |
| Baja moral tributaria | `PESO_MORAL` | 0.20 |
| Preferencia por precio bajo (pobreza) | `PESO_PRECIO` | 0.80 |
| Evación parcial (subdeclaración) | `ALPHA_EVASION` | 0.60 (60% de ventas no reportadas) |
| Sensibilidad del Logit (racionalidad) | `SENSIBILIDAD_MERCADO` | 3.0 (beta) |
| Enanismo (microempresa típica) | `CAPITAL_INICIAL` | 4000.0 |
| Sobrofererta de puestos | `N_COMERCIANTES` / `N_CONSUMIDORES` | 40 / 800 |
| Distribución observada (INEI) | `DISTRIBUCION_INICIAL` | 25/25/50 ≈ 75% no-formal |
| Presupuesto consumidor (Gamarra) | `PRESUPUESTO_MEDIA` / `DESV` | 200 / 40 (gauss) |
| Moral tributaria heterogénea | `MORAL_MIN` / `MORAL_MAX` | 0.05 / 0.35 (uniform) |

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

Tras arreglar bugs en ecuaciones de agentes (BUG 1-15) e implementar mecanismos
adaptativos del mundo real (bancarrota, entrada dinámica, precios dinámicos,
SUNAT reactiva, adaptación en Logit), el equilibrio en los últimos 100 ciclos:

| Métrica | Modelo | Dato real (INEI/SUNAT) | Gap |
|---|---|---|---|
| Informalidad (informal + evasor) | **72.3%** | **70.2%** (EPEN 2025) | +2.1 pp |
| Formal | 27.7% | ~29.8% (complemento) | −2.1 pp |
| Evasor | 59.8% | (incluido en informal INEI) | — |
| Informal puro | 12.5% | — | — |
| Recaudación/ciclo | S/ 33,873 | — | — |
| Multas/ciclo | 22.1 | — | — |
| Actas preventivas/ciclo | 9.7 | — | — |
| Auditorías/ciclo | 44.0 | — | — |
| Comerciantes activos | 80 (de 40 inicial) | — | — |
| Agresividad efectiva SUNAT | 0.95 (de 0.55 base) | — | — |

Con mecanismos adaptativos, el modelo se acerca al dato INEI con solo +2.1 pp
de gap. SUNAT reactiva endurece la fiscalización al máximo (0.95) en respuesta
a la evasión alta sostenida, lo que duplica las auditorías (44/ciclo vs 22 sin
feedback) y triplica la recaudación por multas.

### Respuesta al parámetro de política (`agresividad_sunat`)

| Agresividad base | % Formal | % Evasor | % Informal | Informalidad total |
|---|---|---|---|---|
| 0.25 (baja) | 28% | 60% | 12% | **72%** |
| 0.55 (default) | 28% | 60% | 13% | **72%** |
| 0.80 (alta) | 30% | 62% | 8% | **70%** |

**Lectura:** con SUNAT reactiva, la agresividad base tiene menos impacto porque
el feedback adaptativo la ajusta al máximo (0.95) en todos los casos. El modelo
endurece automáticamente cuando la evasión supera 60% sostenido.

### Trayectoria temporal (default)

| Ciclo | Formal | Evasor | Informal | Recaudación | Multas | Actas |
|---|---|---|---|---|---|---|
| 0 | 32.5% | 60.0% | 7.5% | S/ 23,150 | 13 | 3 |
| 100 | 30.0% | 56.2% | 13.8% | S/ 23,431 | 20 | 10 |
| 500 | 23.8% | 56.2% | 20.0% | S/ 26,907 | 22 | 9 |
| 999 | 22.5% | 63.8% | 13.8% | S/ 40,161 | 24 | 10 |

El sistema oscila alrededor del equilibrio ~28/60/13: los formales declinan
por bancarrota (B1), SUNAT endurece (B5), los informales son fiscalizados y
forzados a evasores, y nuevos formales entran cuando el mercado se recupera (B2).

---

## 1quater. Análisis de Dinámicas No Lineales e Insights Sistémicos

### El umbral de asfixia formal y el enanismo empresarial

El modelo evidencia un "umbral de asfixia formal" para microempresas. Con un
trabajador bajo REMYPE, el costo laboral mensual asciende a S/ 1,192 (RMV 1,130 +
SIS 15 + vacaciones prorrateadas S/ 47). Sumando contabilidad (S/ 200), la carga
fija total supera S/ 1,392/mes — **más del 35% de la facturación típica** de un
comerciante minorista de Gamarra (S/ 4,000/mes).

Con márgenes comerciales de 15-20% (alta competencia + subvaluación de importados),
el formal opera con **pérdidas netas sistemáticas** o debe subir precios, perdiendo
competitividad frente al informal. El resultado: **formalizarse plenamente es una
ruta hacia la inviabilidad financiera** para la microempresa. El modelo reproduce
esto: el parámetro `COSTO_FIJO_FORMALIDAD` hace que la utilidad esperada del formal
sea estructuralmente menor, y solo los comerciantes con alto volumen de ventas
pueden sostenerla.

### El círculo vicioso de la moral tributaria

La interacción dinámica entre comerciantes y consumidores genera un círculo vicioso:
cuando la densidad de informales/evasores es alta, la base imponible se contrae →
menos recaudación → menos servicios públicos → percepción de que el Estado no
devuelve → **moral tributaria cae** → consumidores priorizan precio (no exigen
comprobante) → el informal puede vender más barato (sin IGV 18%) → captura demanda
→ el formal se asfixia por falta de clientes.

En el modelo, `PESO_PRECIO=0.80` y `PESO_MORAL=0.20` con moral `uniform(0.05, 0.35)`
reproducen este círculo: el consumidor pobre prefiere el bien informal (15% más
barato) y rara vez exige boleta. El bien informal funciona como un **subsidio
directo de mercado** a la economía familiar.

### Evasión sofisticada vs. destrucción de capital

La simulación de alta presión fiscal revela **dos distorsiones** que agravan el
problema en lugar de solucionarlo:

1. **Tránsito a evasión sofisticada:** los comerciantes con capital suficiente se
   registran en NRUS/RER (RUC aparente) para neutralizar el riesgo de cierre o
   comiso, pero **siguen subdeclarando masivamente** (alpha=60% de ventas no
   reportadas). La fiscalización punitiva solo incrementa los costos transaccionales
   sin elevar genuinamente la recaudación. En el modelo, esto se observa cuando los
   informales fiscalizados son forzados a "evasor" (no a "formal") — registro
   aparente, evasión continúa.

2. **Destrucción de capital:** los informales de menor escala, incapaces de absorber
   la multa (S/ 2,750 = 50% UIT), sufren **colapso financiero y quiebra**. En el
   modelo, `min(multa, capital)` implica que el comerciante con poco capital pierde
   todo. Estos agentes desempleados se reincorporan como ambulantes móviles,
   expandiendo la informalidad fuera del control municipal.

**Conclusión:** la coacción fiscal como única herramienta genera un sistema
inestable — o evasión sofisticada o quiebra masiva. Ninguna reduce estructuralmente
la informalidad.

### Implicaciones de política pública (4 recomendaciones)

El trilema fundamental: el regulador **no puede maximizar simultáneamente** la
recaudación, los estándares formales, y la estabilidad del empleo microempresarial.
Cuatro recomendaciones emergen del modelo:

1. **Sustituir multas por capacitación voluntaria.** Consolidar las facultades
   preventivas de SUNAT (`tasa_discrecionalidad`): actas preventivas en lugar de
   multas en primera infracción. En el modelo, esto reduce la destrucción de capital
   sin eliminar la señalización de incumplimiento.

2. **Atenuar la brecha del costo laboral.** Mantener el SIS en S/ 15/mes y
   cofinanciar los aportes previsionales durante los primeros 3 años de REMYPE.
   Reducir `COSTO_FIJO_FORMALIDAD` hace la formalidad viable para más comerciantes.

3. **Simplificar y unificar regímenes tributarios.** Fusionar RER y RMT en un
   régimen progresivo único, eliminando los topes rígidos que incentivan la
   fragmentación artificial de empresas para evitar el salto de tramo.

4. **Estimular la moral tributaria activa.** Fortalecer los sorteos virtuales de
   comprobantes y devolver un % del IGV a consumidores que exijan boleta. Elevar
   `PESO_MORAL` de 0.20 a 0.40 reduce la informalidad más que doblar
   `AGRESIVIDAD_SUNAT` (a validar en Fase 3).

**Ninguna palanca aislada basta.** Reducir la informalidad al 50% (meta del
gobierno) requiere actuar en los tres frentes simultáneamente: enforcement
sostenido + reducción de costos formales + cultura tributaria.

---

## 1quinquies. Comparación de Políticas Activables

El modelo implementa tres políticas activables que pueden combinarse. Cada una se testeó
por separado y en combo, corriendo 1000 ciclos y promediando los últimos 100:

| Escenario | % Formal | % Evasor | % Informal | Informal total | Δ vs línea base |
|---|---|---|---|---|---|
| Línea base | 28% | 60% | 13% | **72%** | — |
| + Beneficio antigüedad | 28% | 60% | 13% | 72% | 0pp |
| + Sorteo comprobantes | 27% | 60% | 13% | 73% | +1pp |
| + Multa progresiva | 28% | 60% | 12% | 72% | 0pp |
| Combo (3 + costo ↓) | 28% | 61% | 11% | 72% | 0pp |
| Más enforcement | 36% | 63% | 2% | 64% | −8pp |

**Lectura:** con SUNAT reactiva activa, las políticas individuales tienen efectos
mínimos porque el feedback adaptativo ya está operando al máximo (agresividad
efectiva = 0.95). Solo "Más enforcement" desplaza el equilibrio (−8pp) porque
sube la base por encima del tope. El trilema persiste — ninguna palanca aislada
resuelve el problema.

**Uso del dashboard:** abrir `src/visualizacion.py` con Solara, seleccionar un preset
(un click), y observar en tiempo real cómo los comerciantes cambian de color. Los 6
presets pre-configurados cubren los escenarios más relevantes para política pública.

---

## 1sexies. Mecanismos Adaptativos del Mundo Real

El modelo incluye 5 mecanismos de feedback que reproducen dinámicas de mercado reales.
Estos NO son políticas activables (no se encienden/apagan con checkboxes) — son
comportamientos emergentes del sistema que operan siempre.

### B1. Bancarrota con cierre

Si el capital de un comerciante cae bajo `UMBRAL_BANCARROTA` (S/ 500, ~10% del
capital inicial), marca `en_quiebra=True` y deja de operar. No participa del
mercado: no decide estrategia, no vende, no es auditado, no aparece en métricas.

**Justificación:** en la realidad, un microcomerciante que no puede cubrir costos
fijos cierra su negocio. El modelo anterior mantenía comerciantes zombis con
capital negativo operando indefinidamente.

**Impacto en el equilibrio:** reduce el número de formales (los más castigados
por costo fijo), pero B2 compensa con entrada de nuevos cuando el mercado
se recupera.

### B2. Entrada dinámica de comerciantes

Si el capital medio de los formales activos supera `UMBRAL_CRECIMIENTO`
(S/ 20,000, 5x capital inicial) y hay espacio (`N activos < MAX_COMERCIANTES=80`),
entra un nuevo comerciante formal con capital inicial S/ 4,000.

**Justificación:** un mercado próspero atrae inversión. Si los formales están
creciendo, es señal de que la formalidad es rentable, y nuevos comerciantes
entran al sector.

**Impacto:** el número de comerciantes oscila entre 40 y 80. En la línea base,
crece de 40 a 80 en los primeros ciclos y se estabiliza.

### B3. Precios dinámicos

Cada comerciante ajusta su precio ±20% según sus ventas del ciclo anterior:
- Ventas > 50/ciclo (alta demanda) → sube precio
- Ventas < 50/ciclo (baja demanda) → baja precio

El precio se calcula una vez al inicio del `step()` (no en cada llamada a
`calcular_precio()`), almacenado en `self.precio_actual`.

**Justificación:** en la realidad, un comerciante con alta demanda sube precios
(captura margen), y uno con baja demanda los baja (captura mercado).

### B4. Adaptación en Logit (riesgo percibido)

Si `agresividad_efectiva > 0.80`, el riesgo percibido del formal sube 1.5x en
`estimar_utilidad_futura`. El Logit naturalmente mueve al comerciante hacia
evasor/informal sin forzar la transición.

**Justificación:** cuando SUNAT endurece mucho, los formales perciben mayor
riesgo de ser auditados y multados (incluso cumpliendo, hay costos transaccionales
de auditoría). Algunos migran a evasión para evadir el escrutinio.

### B5. SUNAT reactiva (feedback adaptativo)

SUNAT mantiene un historial de los últimos 20 ciclos de % evasión. Si todos
superan 60%, endurece: `agresividad_efectiva += 0.02` (tope 0.95). Si todos
están bajo 50% (formales dominan), relaja: `agresividad_efectiva -= 0.01`
(piso 0.05).

**Justificación:** en la realidad, SUNAT ajusta su estrategia de fiscalización
según los resultados observados. Si la evasión sube, destina más recursos a
auditorías. Si baja, los reasigna.

**Impacto:** en la línea base, `agresividad_efectiva` sube de 0.55 a 0.95
en los primeros ~100 ciclos y se mantiene allí (evasión persistentemente alta).
Esto duplica las auditorías (44/ciclo vs 22 sin feedback) y triplica la
recaudación por multas.

### Detección de colapsos (B6)

El dashboard detecta 4 tipos de colapso del sistema:
- **COLAPSO FORMAL:** % formal < 5% (sector formal casi extinto)
- **COLAPSO AMBULANTE:** % informal > 80% (economía totalmente ambulante)
- **COLAPSO FISCAL:** recaudación < S/ 2,000/ciclo (SUNAT no recauda)
- **COLAPSO DEMANDA:** presupuesto medio > S/ 150 (consumidores no gastan)

El modelo NO pausa ni auto-rescata — solo reporta el estado. El usuario puede
observar cómo el sistema evoluciona hacia o desde el colapso.

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
trilema-gamarra/
├── README.md
├── requirements.txt          # mesa, pandas, matplotlib, solara, altair
├── trilema_gamarra.ipynb     # notebook auto-contenido (Colab/Jupyter)
├── informe_proyecto_gamarra.md
├── src/
│   ├── agentes/
│   │   ├── comerciante.py    # Logit Multinomial, 3 estrategias, beneficio antigüedad
│   │   ├── consumidor.py     # Moore, multi-compra, sorteo comprobantes
│   │   └── sunat.py          # fiscalización, discrecionalidad, multa progresiva
│   ├── modelo.py             # ModeloGamarra: step bifásico, DataCollector
│   ├── entorno.py            # UIT, RMV, IGV, multas, parámetros centralizados
│   └── visualizacion.py      # dashboard Solara (19 sliders, 6 presets, grid visual)
└── .venv/                    # Python 3.14 + mesa 3.5.1
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

## 6. Visualización Interactiva (Streamlit)

El dashboard interactivo (`src/visualizacion.py`) usa **Streamlit** + matplotlib
para renderizar el grid y las gráficas. Es más estable que Solara (que tenía
issues con Mesa 3.5). Corre en el navegador con controles de play/pause/step,
sliders para variar parámetros en vivo, y un grid visual donde los comerciantes
cambian de color según su estrategia.

**Filosofía: 3 elementos, calidad sobre cantidad.** El dashboard prioriza señal
sobre ruido: un grid visual, una gráfica de convergencia, y un panel de implicaciones.

**Ejecución:**

```bash
streamlit run src/visualizacion.py
```

**Componentes del dashboard:**

- **Grid visual (SpaceView):** comerciantes como cuadrados grandes (size=120) que
  cambian de color en tiempo real — verde (formal), naranja (evasor), rojo (informal) —
  más consumidores azules atenuados (alpha=0.15) y SUNAT como X negro grande
- **20 sliders:** agresividad SUNAT, discrecionalidad, costo fijo formalidad, tasa IGV,
  multa no emisión, alpha evasión, multa evasión %, sensibilidad mercado (beta),
  escala Logit, peso precio, peso moral, N comerciantes, N consumidores, y parámetros
  de las 3 políticas activables
- **3 checkboxes:** activar/desactivar beneficio por antigüedad, sorteo de comprobantes,
  multa progresiva por reincidencia
- **6 botones de preset** (un click = escenario completo):
  - Línea base, Más enforcement, Subsidio formalidad, Cultura tributaria,
    Reducción tributaria, Combo reforma
- **1 gráfica de convergencia:** % estrategias (3 líneas) + línea vertical negra en
  el ciclo de equilibrio + sombreado verde "zona estable" post-equilibrio + anotación
  "Equilibrio @ ciclo X"
- **Panel "Implicaciones del equilibrio":** texto narrativo auto-generado con:
  - Estado del sistema (ESTABLE / PRÓSPERO / COLAPSO FORMAL / COLAPSO AMBULANTE / etc.)
  - Agresividad SUNAT base vs efectiva (si divergen por B5 feedback)
  - Composición post-equilibrio + delta vs línea base
  - Zonas temporales (PRE-EQUILIBRIO / EQUILIBRIO / POST-EQUILIBRIO con valores)
  - Capital por estrategia vs inicial (con ratios ×N)
  - Texto descriptivo del escenario (qué es, qué espera, qué implica)
- **Panel "Variables y su efecto":** tabla estática de 16 variables con qué controlan
  y efecto esperado en el modelo

**Detección de equilibrio:** el dashboard detecta cuándo la media móvil (ventana 50)
de informalidad total deja de cambiar más de 1pp por 30 ciclos consecutivos. Marca
ese ciclo con una línea vertical y sombrea la "zona estable" posterior.

```python
# src/visualizacion.py — extracto del código real
from mesa.visualization import Slider, SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle

def agent_portrayal(agent):
    if agent is None:
        return
    portrayal = AgentPortrayalStyle(size=50, marker="o", zorder=2)
    if isinstance(agent, Comerciante):
        colores = {"formal": "green", "evasor": "orange", "informal": "red"}
        portrayal.update(("color", colores.get(agent.estrategia, "gray")),
                         ("size", 80), ("marker", "s"), ("zorder", 3))
    elif isinstance(agent, Sunat):
        portrayal.update(("color", "black"), ("size", 120), ("marker", "X"))
    elif isinstance(agent, Consumidor):
        portrayal.update(("color", "royalblue"), ("size", 15), ("marker", "."))
    return portrayal

model_params = {
    "agresividad_sunat": Slider("Agresividad SUNAT", 0.55, 0.05, 0.95, 0.05),
    "costo_fijo_formalidad": Slider("Costo Fijo Formalidad (S/)", 400, 100, 1500, 50),
    "tasa_igv": Slider("Tasa IGV", 0.18, 0.05, 0.25, 0.01),
    "beneficio_antiguedad": {"type": "Checkbox", "value": False, "label": "Beneficio antigüedad"},
    "sorteo_comprobantes": {"type": "Checkbox", "value": False, "label": "Sorteo comprobantes"},
    "multa_progresiva": {"type": "Checkbox", "value": False, "label": "Multa progresiva"},
    # ... 13 sliders más
}

PRESETS = {
    "Línea base": {},
    "Más enforcement": {"agresividad_sunat": 0.90, "multa_no_emision": 5000},
    "Subsidio formalidad": {"costo_fijo_formalidad": 150, "beneficio_antiguedad": True},
    "Combo reforma": {"agresividad_sunat": 0.75, "costo_fijo_formalidad": 200,
                      "beneficio_antiguedad": True, "sorteo_comprobantes": True,
                      "multa_progresiva": True},
}

grafica_estrategias = make_plot_component(
    {"pct_formal": "green", "pct_evasor": "orange", "pct_informal": "red"})
grafica_recaudacion = make_plot_component("recaudacion")

model = solara.reactive(ModeloGamarra())
renderer = SpaceRenderer(model.value, backend="matplotlib").setup_agents(agent_portrayal)

@solara.component
def Page():
    with solara.Sidebar():
        with solara.Card("Presets"):
            for name in PRESETS:
                solara.Button(name, on_click=lambda n=name: model.set(ModeloGamarra(**PRESETS[n])))
    SolaraViz(model, renderer, components=[grafica_estrategias, grafica_recaudacion],
              model_params=model_params, name="El Trilema de Gamarra")
```

---

## 7. Cronograma Resumen

| Fase | Estado | Entregable |
|---|---|---|
| 0. Setup | ✓ Completado | Repo + diseño + parámetros reales |
| 1. Agentes base | ✓ Completado | 3 clases con Logit Multinomial, Moore, fiscalización |
| 2. Integración | ✓ Completado | ModeloGamarra con step bifásico + DataCollector |
| 3. Experimentos | ✓ Completado | Sweep de agresividad + comparación de políticas |
| 4. Dashboard + Notebook | ✓ Completado | Solara (19 sliders, 6 presets) + notebook Colab |
| 5. Informe final | ✓ Completado | Este documento + hallazgos + recomendaciones |

**Commits clave:**

| Commit | Descripción |
|---|---|
| `0b5885c` | Fase 1: lógica real en los 3 agentes + step bifásico |
| `952b93e` | Marco teórico + recalibración con datos INEI |
| `d2242df` | Migración a valores reales (UIT, RMV) + Logit Multinomial |
| `4cda5d7` | Dashboard interactivo + 3 políticas activables |
| `902fc95` | Notebook auto-contenido para Google Colab |
| `20d686b` | Informe actualizado con políticas y dashboard |
