"""Módulo de parametrización económica, impositiva y laboral. Bienio 2025-2026.

Valores cuantitativos reflejan los decretos supremos vigentes en el Perú.
Fuentes: INEI (EPEN 2025), SUNAT (Código Tributario), MEF (UIT/RMV).
Ver marco teórico en informe_proyecto_gamarra.md.
"""

# Parámetros macroeconómicos y tributarios peruanos
UIT_2025 = 5350.0  # D.S. N° 260-2024-EF
UIT_2026 = 5500.0  # D.S. N° 301-2025-EF
RMV_2025 = 1130.0  # D.S. N° 006-2024-TR

# Selección temporal del simulador: año fiscal 2026
UIT_VIGENTE = UIT_2026
RMV_VIGENTE = RMV_2025
TASA_IGV = 0.18  # 18% (16% IGV + 2% IPM)

# Costos laborales bajo REMYPE microempresa (un trabajador)
COSTO_SIS_EMPLEADOR = 15.00  # SIS Microempresa, pago mensual fijo
VACACIONES_PROVISION = (RMV_VIGENTE / 30.0) * 15.0 / 12.0  # 15 días anuales prorrateados ≈ 47.08
COSTO_LABORAL_MENSUAL = RMV_VIGENTE + COSTO_SIS_EMPLEADOR + VACACIONES_PROVISION  # ≈ 1192.08

# Costo administrativo: contabilidad + trámites mensuales
COSTO_ADMINISTRATIVO_CONTABLE = 200.00

# Costo fijo total mensual de operar formal (promedio: unipersonal + REMYPE con 1 trabajador)
COSTO_FIJO_FORMALIDAD = 400.00  # contabilidad S/200 + NRUS/trámites S/100 + aportes promedio S/100

# Estructura de sanciones (Código Tributario Art. 174)
MULTA_NO_EMISION = 0.50 * UIT_VIGENTE  # S/ 2750 — no emitir comprobante
DESCUENTO_GRADUALIDAD = 0.90  # rebaja 90% por subsanación voluntaria
MULTA_EVASION_PCT = 0.30  # 30% de ingresos ocultos (sanción sobre evasión parcial)

# Comerciante
PRECIO_BASE = 30.0  # precio neto de una prenda (margen comercial Gamarra)
COSTO_UNITARIO = 12.0  # costo de adquisición de materia prima / prenda
CAPITAL_INICIAL = 4000.0  # colchón financiero típico (enanismo: sin escala)
ALPHA_EVASION = 0.60  # fracción de ventas no reportadas por evasor
DISTRIBUCION_INICIAL = ["formal", "evasor", "informal", "informal"]  # 25/25/50

# Consumidor
PRESUPUESTO_MEDIA = 200.0
PRESUPUESTO_DESV = 40.0
MORAL_MIN = 0.05
MORAL_MAX = 0.35  # moral tributaria baja y heterogénea (encuestas)

# Modelo
N_COMERCIANTES = 40
N_CONSUMIDORES = 800  # Gamarra recibe miles de compradores/día — volumen suficiente para viabilidad formal
AGRESIVIDAD_SUNAT = 0.55  # % de comercios auditados por ciclo
TASA_DISCRECIONALIDAD = 0.30  # prob. de acta preventiva vs multa (primera infracción)
SENSIBILIDAD_MERCADO = 3.0  # beta del Logit Multinomial (racionalidad limitada)
PESO_PRECIO = 0.80
PESO_MORAL = 0.20
WIDTH = 15
HEIGHT = 15
SEED = 42
