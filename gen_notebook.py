#!/usr/bin/env python3
"""Genera trilema_gamarra.ipynb auto-contenido desde src/ para Google Colab."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent

def read_src(rel_path):
    """Lee archivo de src/ y strip imports de src.* (no existen en Colab)."""
    lines = (ROOT / rel_path).read_text().splitlines(True)
    result = []
    skip_paren = False
    for line in lines:
        if skip_paren:
            # Estamos dentro de import multi-línea, buscar cierre
            if ')' in line:
                skip_paren = False
            continue
        if line.strip().startswith('from src.'):
            # Import de src — chequear si es multi-línea (sin cierre en esta línea)
            if '(' in line and ')' not in line:
                skip_paren = True
            continue
        if line.strip().startswith('import src.'):
            continue
        result.append(line)
    return ''.join(result)

def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True) if isinstance(source, str) else source,
    }

def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(True) if isinstance(source, str) else source,
    }

cells = []

# Cell 0: pip install
cells.append(code_cell("!pip install mesa pandas matplotlib\n"))

# Cell 1: title
cells.append(md_cell("""# El Trilema de la Gamarra
## Simulación Multiagente de Informalidad y Evasión Tributaria en el Perú

Modelo MAS con framework **Mesa 3.5** que simula el trilema entre formalidad, evasión 
fiscal y supervivencia microempresarial en Gamarra. Incluye **mecanismos adaptativos 
del mundo real**: bancarrota, entrada dinámica de comerciantes, precios dinámicos, 
SUNAT reactiva y adaptación en Logit.

**Resultados línea base:** 36% formal · 58% evasor · 7% informal (64% informalidad, 
INEI 70.2%, gap −6pp)

**Mecanismos adaptativos:**
- **B1 Bancarrota:** capital < S/500 → cierra
- **B2 Entrada dinámica:** capital formal > S/20,000 → entra nuevo
- **B3 Precios dinámicos:** ±20% según demanda
- **B4 Compliance cost:** si agresividad > 0.80, formal paga 2% extra
- **B5 SUNAT reactiva:** evasión > 60% sostenido → endurece
"""))

# Cell 2: marco teórico breve
cells.append(md_cell("""## Marco Teórico

| Régimen | Tope ingresos | Tasa |
|---|---|---|
| NRUS | 8 UIT/año (S/ 42,800) | Cuota fija S/ 20–50/mes |
| RER | 525 UIT/año | 1.5% sobre ingresos netos |
| RMT | 1,700 UIT/año | 1% hasta 25 UIT, 1.5% después |
| General | Sin tope | 29.5% (Imp. Renta) |

**Causas estructurales de informalidad:**
1. Altos costos de formalidad (IGV 18% + aportes laborales 30% + contabilidad)
2. Enanismo empresarial (98% son microempresas)
3. Baja fiscalización (SUNAT no alcanza millones de microcomerciantes)
4. Baja moral tributaria (consumidores prefieren precios bajos)
5. Pobreza (demanda de bienes baratos)
6. Burocracia y falta de incentivos tangibles
"""))

# Cell 3: entorno.py
cells.append(code_cell(read_src("src/entorno.py")))

# Cell 4: comerciante.py
cells.append(code_cell(read_src("src/agentes/comerciante.py")))

# Cell 5: consumidor.py
cells.append(code_cell(read_src("src/agentes/consumidor.py")))

# Cell 6: sunat.py
cells.append(code_cell(read_src("src/agentes/sunat.py")))

# Cell 7: modelo.py (sin __main__)
modelo_code = read_src("src/modelo.py")
# Quitar bloque __main__
modelo_code = re.sub(r'\nif __name__ == "__main__":.*$', '', modelo_code, flags=re.DOTALL)
cells.append(code_cell(modelo_code))

# Cell 8: run simulation
cells.append(code_cell("""import pandas as pd

modelo = ModeloGamarra()
N_CICLOS = 1000
for _ in range(N_CICLOS):
    modelo.step()

df = modelo.datacollector.get_model_vars_dataframe()
print("--- Trayectoria ---")
for i in [0, 100, 500, 999]:
    row = df.iloc[i]
    inf = row["pct_informal"] + row["pct_evasor"]
    print(f"Ciclo {i:4d}: formal {row['pct_formal']:5.1f}%  informal {row['pct_informal']:5.1f}%  "
          f"evasor {row['pct_evasor']:5.1f}%  recaud S/.{row['recaudacion']:7.1f}  "
          f"multas {int(row['multas']):3d}  actas {int(row['actas_preventivas']):3d}")

tail = df.tail(100)
inf_final = tail["pct_informal"].mean() + tail["pct_evasor"].mean()
print("\\n--- Promedios últimos 100 ciclos ---")
print(f"Formal:              {tail['pct_formal'].mean():5.1f}%")
print(f"Informal:            {tail['pct_informal'].mean():5.1f}%")
print(f"Evasor:              {tail['pct_evasor'].mean():5.1f}%")
print(f"Recaudación/ciclo:   S/. {tail['recaudacion'].mean():.1f}")
print(f"Multas/ciclo:        {tail['multas'].mean():.1f}")
print(f"Actas prev./ciclo:   {tail['actas_preventivas'].mean():.1f}")
print(f"Auditorías/ciclo:    {tail['n_auditorias'].mean():.1f}")
print(f"Agresividad efectiva: {modelo.agresividad_efectiva:.2f} (base: {modelo.agresividad_sunat})")
print(f"\\nInformalidad total (equilibrio): {inf_final:.1f}%  (INEI: ~70%)")
print(f"Gap vs INEI: {inf_final - 70.2:+.1f} pp")
"""))

# Cell 9: plots
cells.append(code_cell("""import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Estrategias
ax = axes[0, 0]
ax.plot(df.index, df["pct_formal"], color="green", label="Formal")
ax.plot(df.index, df["pct_evasor"], color="orange", label="Evasor")
ax.plot(df.index, df["pct_informal"], color="red", label="Informal")
ax.set_title("Estrategias de comerciantes (%)")
ax.set_xlabel("Ciclo")
ax.legend()
ax.grid(True, alpha=0.3)

# Recaudación
ax = axes[0, 1]
ax.plot(df.index, df["recaudacion"], color="steelblue")
ax.set_title("Recaudación por ciclo (S/.)")
ax.set_xlabel("Ciclo")
ax.grid(True, alpha=0.3)

# Multas y actas
ax = axes[1, 0]
ax.plot(df.index, df["multas"], color="firebrick", label="Multas")
ax.plot(df.index, df["actas_preventivas"], color="navy", label="Actas")
ax.set_title("Multas y actas preventivas por ciclo")
ax.set_xlabel("Ciclo")
ax.legend()
ax.grid(True, alpha=0.3)

# Agresividad efectiva
ax = axes[1, 1]
ax.plot(df.index, df["n_auditorias"], color="purple")
ax.set_title("Auditorías por ciclo")
ax.set_xlabel("Ciclo")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
"""))

# Cell 10: sweep agresividad
cells.append(code_cell("""valores = [0.05, 0.25, 0.55, 0.80, 0.95]
resultados = []

for a in valores:
    m = ModeloGamarra(agresividad_sunat=a)
    for _ in range(1000):
        m.step()
    df_sweep = m.datacollector.get_model_vars_dataframe()
    tail = df_sweep.tail(100)
    resultados.append({
        "agresividad": a,
        "formal": tail["pct_formal"].mean(),
        "evasor": tail["pct_evasor"].mean(),
        "informal": tail["pct_informal"].mean(),
        "recaudacion": tail["recaudacion"].mean(),
        "agres_efectiva": m.agresividad_efectiva,
    })

sweep_df = pd.DataFrame(resultados)
print(sweep_df.to_string(index=False))
"""))

# Cell 11: comparación escenarios
cells.append(code_cell("""escenarios = {
    "Línea base": {},
    "Más enforcement": {"agresividad_sunat": 0.90, "tasa_discrecionalidad": 0.10, "multa_no_emision": 5000, "multa_evasion_pct": 1.0},
    "Subsidio formalidad": {"costo_fijo_formalidad": 150, "beneficio_antiguedad": True, "tasa_descuento_antiguedad": 0.08},
    "Cultura tributaria": {"peso_moral": 0.40, "sorteo_comprobantes": True, "prob_sorteo": 0.03, "premio_sorteo": 100},
    "Reducción tributaria": {"tasa_igv": 0.10, "alpha_evasion": 0.30},
    "Combo reforma": {"agresividad_sunat": 0.75, "costo_fijo_formalidad": 200, "peso_moral": 0.35, "beneficio_antiguedad": True, "sorteo_comprobantes": True, "multa_progresiva": True},
    "Paraíso formal": {"costo_fijo_formalidad": 100, "tasa_igv": 0.05, "peso_moral": 0.50, "alpha_evasion": 0.10, "beneficio_antiguedad": True, "sorteo_comprobantes": True},
    "Mercado libre": {"agresividad_sunat": 0.05, "multa_no_emision": 500, "multa_evasion_pct": 0.1},
    "Represión extrema": {"agresividad_sunat": 0.95, "multa_no_emision": 5500, "tasa_discrecionalidad": 0.0, "multa_evasion_pct": 1.5},
    "Crisis de demanda": {"n_consumidores": 200, "costo_fijo_formalidad": 800},
    "Evasión incentivada": {"alpha_evasion": 0.90, "multa_evasion_pct": 0.1, "agresividad_sunat": 0.10},
}

resultados_esc = []
for nombre, params in escenarios.items():
    m = ModeloGamarra(**params)
    for _ in range(1000):
        m.step()
    tail = m.datacollector.get_model_vars_dataframe().tail(100)
    f = tail["pct_formal"].mean()
    e = tail["pct_evasor"].mean()
    i = tail["pct_informal"].mean()
    resultados_esc.append({
        "escenario": nombre,
        "formal": f"{f:.0f}%",
        "evasor": f"{e:.0f}%",
        "informal": f"{i:.0f}%",
        "informal_total": f"{e+i:.0f}%",
        "recaudacion": f"S/. {tail['recaudacion'].mean():.0f}",
        "agres_efectiva": f"{m.agresividad_efectiva:.2f}",
    })

esc_df = pd.DataFrame(resultados_esc)
print(esc_df.to_string(index=False))
"""))

# Cell 12: hallazgos
cells.append(md_cell("""## Hallazgos

### El trilema estructural
El regulador **no puede maximizar simultáneamente** recaudación, estándares formales 
y estabilidad del empleo microempresarial. El modelo reproduce esto: incluso con 
reformas, el evasor persiste como estrategia racional dominante.

### SUNAT reactiva (B5) es poderosa
La agresividad efectiva sube automáticamente cuando la evasión supera 60% sostenido. 
En la línea base, SUNAT endurece de 0.55 a 0.77. Esto duplica las auditorías y 
triplica la recaudación por multas.

### Bancarrota y entrada dinámica
Los comerciantes formales con capital < S/500 quiebran (B1), pero si el mercado 
es próspero, entran nuevos (B2). El número de comerciantes oscila entre 40 y 80.

### Precios dinámicos
Los comerciantes ajustan precios ±20% según demanda. Ventas altas → suben precio; 
ventas bajas → bajan para captar mercado.

### Represión extrema: formal pero destruido
Con enforcement máximo, formal llega a 51% PERO con 9 quiebras. El mercado se 
destruye por exceso de fiscalización — no es solución, es demolición.
"""))

# Cell 13: recomendaciones
cells.append(md_cell("""## Recomendaciones de Política Pública

1. **Sustituir multas por capacitación voluntaria** — actas preventivas en primera 
   infracción reducen destrucción de capital sin eliminar señalización.
2. **Atenuar brecha costo laboral** — cofinanciar aportes previsionales primeros 
   3 años de REMYPE. Reducir `costo_fijo_formalidad`.
3. **Simplificar regímenes tributarios** — fusionar RER y RMT en régimen progresivo 
   único, eliminar topes rígidos que incentivan fragmentación.
4. **Estimular moral tributaria** — fortalecer sorteos de comprobantes. Elevar 
   `peso_moral` de 0.20 a 0.40 reduce informalidad más que doblar enforcement.

**Ninguna palanca aislada basta.** Reducir informalidad al 50% (meta gobierno) 
requiere actuar en enforcement + costos + cultura tributaria simultáneamente.
"""))

# Cell 14: dashboard note
cells.append(md_cell("""## Dashboard Interactivo (Streamlit)

El dashboard completo corre con Streamlit (más estable que Solara):

```bash
streamlit run src/visualizacion.py
```

Incluye: grid visual, gráfica de convergencia al equilibrio, panel de implicaciones 
con zonas temporales, métricas en vivo, banner de estado, 12 escenarios preset.
"""))

# Cell 15: grid visual
cells.append(code_cell("""import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Grid visual
ax1.set_aspect("equal")
ax1.set_xticks([])
ax1.set_yticks([])
ax1.set_title("Grid del mercado — estado final")
colores = {"formal": "green", "evasor": "orange", "informal": "red"}
for agent in modelo.agents:
    if not hasattr(agent, "pos") or agent.pos is None:
        continue
    x, y = agent.pos
    if isinstance(agent, Comerciante):
        if getattr(agent, "en_quiebra", False):
            ax1.scatter(x, y, c="gray", s=60, marker="x", alpha=0.3)
        else:
            c = colores.get(agent.estrategia, "gray")
            ax1.scatter(x, y, c=c, s=120, marker="s", edgecolors="black", linewidths=0.5)
    elif isinstance(agent, Sunat):
        ax1.scatter(x, y, c="black", s=150, marker="X")
    elif isinstance(agent, Consumidor):
        ax1.scatter(x, y, c="royalblue", s=10, marker=".", alpha=0.15)

handles = [
    mpatches.Patch(color="green", label="Formal"),
    mpatches.Patch(color="orange", label="Evasor"),
    mpatches.Patch(color="red", label="Informal"),
    mpatches.Patch(color="gray", label="En quiebra"),
    plt.Line2D([0], [0], marker="X", color="w", markerfacecolor="black", markersize=10, label="SUNAT"),
]
ax1.legend(handles=handles, loc="upper left", fontsize=7)

# Convergencia
ax2.plot(df.index, df["pct_formal"], color="green", label="Formal")
ax2.plot(df.index, df["pct_evasor"], color="orange", label="Evasor")
ax2.plot(df.index, df["pct_informal"], color="red", label="Informal")
ax2.set_title("Convergencia al equilibrio")
ax2.set_xlabel("Ciclo")
ax2.set_ylabel("%")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
"""))

# Build notebook
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.14.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

out_path = ROOT / "trilema_gamarra.ipynb"
with open(out_path, "w") as f:
    json.dump(nb, f, indent=1)

print(f"Notebook generado: {out_path}")
print(f"Celdas: {len(cells)}")
