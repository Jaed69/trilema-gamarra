"""Parámetros centralizados del modelo. Editar aquí, no dentro de los agentes."""

# Tributación (Perú, julio 2026)
IGV = 0.18  # 18% vigente

# Comerciante
COSTO_FORMALIDAD = 20.0           # costo por ciclo de operar formal
PRECIO_BASE = 10.0
DINERO_INICIAL_COMERCIANTE = 100.0
DISTRIBUCION_INICIAL = {"formal": 0.2, "informal": 0.6, "evasor": 0.2}  # ~70% informal (INEI)

# Consumidor
PRESUPUESTO_INICIAL = 100.0

# Sunat / fiscalización
PRESUPUESTO_FISCALIZACION = 1000.0
MULTA_EVASOR = 200.0
N_FISCALIZACIONES_POR_CICLO = 3

# Modelo
N_COMERCIANTES = 30
N_CONSUMIDORES = 50
AGRESIVIDAD_SUNAT = 0.3
WIDTH = 15
HEIGHT = 15
