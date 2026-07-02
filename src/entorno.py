"""Parámetros centralizados del modelo. Editar aquí, no dentro de los agentes."""

# Tributación (Perú, julio 2026)
IGV = 0.18  # 18% vigente

# Comerciante
COSTO_FORMALIDAD = 22.0           # costo por ciclo de operar formal (IGV + laboral + contable)
PRECIO_BASE = 10.0
DINERO_INICIAL_COMERCIANTE = 200.0
DISTRIBUCION_INICIAL = {"formal": 0.2, "informal": 0.6, "evasor": 0.2}  # ~70% informal (INEI)
P_CAMBIO_ESTRATEGIA = 0.05        # probabilidad base de reevaluar tipo por ciclo
UMBRAL_QUIEBRA = 0.3              # fracción de DINERO_INICIAL bajo la cual se reconsidera

# Consumidor
PRESUPUESTO_INICIAL = 50.0
INGRESO_CONSUMIDOR = 11.0       # ingreso recurrente por ciclo (sueldo) — sostiene el mercado
W_PRECIO = 0.7                    # peso del precio en elegir_tienda (consumidor busca barato)
W_MORAL = 0.1                     # peso de moral tributaria (preferir formal)
W_DIST = 0.2                      # peso de distancia al puesto

# Sunat / fiscalización
PRESUPUESTO_FISCALIZACION = 1000.0
APROPIACION_SUNAT = 20.0         # financiamiento estatal fijo por ciclo (rompe death spiral)
MULTA_EVASOR = 100.0
MULTA_INFORMAL = 40.0
COSTO_FISCALIZACION = 10.0        # costo al Fondo por cada objetivo fiscalizado (calibrado)
SHARE_IGV_A_SUNAT = 0.2           # fracción del IGV recaudado que alimenta el Fondo
N_FISCALIZACIONES_POR_CICLO = 5

# Modelo
N_COMERCIANTES = 30
N_CONSUMIDORES = 50
AGRESIVIDAD_SUNAT = 0.3
WIDTH = 15
HEIGHT = 15
SEED = 42                         # semilla para reproducibilidad
