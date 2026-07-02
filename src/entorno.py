"""Parámetros centralizados del modelo. Calibrados contra datos reales del Perú.

Fuentes: INEI (EPEN 2025), SUNAT (Tabla de Infracciones), MEF (UIT 2025).
Ver marco teórico en informe_proyecto_gamarra.md §1bis.
"""

# Tributación (Perú, 2025-2026)
IGV = 0.18  # 18% vigente (16% IGV + 2% IPM)
UIT = 5350.0  # S/ 5,350 en 2025 (D.S. N° 380-2024-EF) — referencia para multas

# Comerciante — calibrado a microempresa típica de Gamarra
PRECIO_BASE = 10.0
DINERO_INICIAL_COMERCIANTE = 80.0  # enanismo: colchón bajo, sin escala
COSTO_FORMALIDAD = 6.0            # ~30% de ingresos/ciclo (NRUS + Essalud + contabilidad)
DISTRIBUCION_INICIAL = {"formal": 0.2, "informal": 0.6, "evasor": 0.2}  # ~80% no-formal (INEI)
P_CAMBIO_ESTRATEGIA = 0.05        # prob. de probar evasión cuando va bien
P_RELAJACION = 0.06              # prob. de que un formal no auditado se relaje a informal
UMBRAL_QUIEBRA = 0.3              # fracción de DINERO_INICIAL bajo la cual abandona formalidad

# Consumidor — calibrado a baja moral tributaria y preferencia por precio (pobreza)
PRESUPUESTO_INICIAL = 30.0
INGRESO_CONSUMIDOR = 11.0         # marginal: alcanza informal (10) pero formal (11.8) apreta
W_PRECIO = 0.85                   # peso del precio (consumidor pobre busca barato, camina el mercado)
W_MORAL = 0.1                     # peso de moral tributaria (baja cultura tributaria)
W_DIST = 0.05                     # peso de distancia (Gamarra: se camina comparando)

# Sunat / fiscalización — calibrado a débil capacidad de fiscalización
PRESUPUESTO_FISCALIZACION = 200.0  # presupuesto inicial bajo
FONDO_MAX = 500.0                 # cap: el exceso se redistribuye a otras partidas del Estado
APROPIACION_SUNAT = 10.0          # financiamiento estatal fijo por ciclo (limitado)
MULTA_EVASOR = 60.0               # ~3 ciclos de ingresos (50% UIT escalado al modelo)
MULTA_INFORMAL = 30.0             # ~1.5 ciclos de ingresos
COSTO_FISCALIZACION = 12.0        # costo operativo por objetivo fiscalizado
SHARE_IGV_A_SUNAT = 0.3           # fracción del IGV que recicla al Fondo
N_FISCALIZACIONES_POR_CICLO = 3   # capacidad limitada (SUNAT no llega a todos)

# Modelo
N_COMERCIANTES = 60               # sobrofererta: muchos puestos compitiendo (Gamarra real)
N_CONSUMIDORES = 40
AGRESIVIDAD_SUNAT = 0.1           # baja: SUNAT apenas llega a microcomerciantes (realidad peruana)
WIDTH = 15
HEIGHT = 15
SEED = 42                         # semilla para reproducibilidad
