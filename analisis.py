"""
Análisis exploratorio sobre el dataset limpio.

Genera los gráficos de images/ y un resumen de métricas en
data/processed/metricas.json (los números que cita el README).

Uso:
    python src/analisis.py
"""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "respuestas_limpias.csv"
IMG = ROOT / "images"
METRICAS = ROOT / "data" / "processed" / "metricas.json"

# Paleta validada (colorblind-safe) + tinta y superficie
AZUL, NARANJA, GRIS_SERIE = "#2a78d6", "#eb6834", "#c3c2b7"
SUPERFICIE, TINTA, TINTA_2, TINTA_MUTED, GRILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
    "font.family": "DejaVu Sans", "font.size": 11, "text.color": TINTA,
    "axes.edgecolor": GRIS_SERIE, "axes.labelcolor": TINTA_2,
    "xtick.color": TINTA_MUTED, "ytick.color": TINTA_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def pct(serie):
    s = serie.dropna()
    return 100 * s.mean() if len(s) else 0.0


def _titulo(fig, titulo, subtitulo):
    fig.text(0.02, 0.97, titulo, fontsize=15, fontweight="bold", va="top", color=TINTA)
    fig.text(0.02, 0.905, subtitulo, fontsize=10.5, va="top", color=TINTA_2)


def _guardar(fig, nombre, fuente="Fuente: encuesta a egresados (n = 24)."):
    fig.text(0.02, 0.015, fuente, fontsize=8.5, color=TINTA_MUTED)
    fig.savefig(IMG / nombre, dpi=160)
    plt.close(fig)


def barras_h(ax, etiquetas, valores, color=AZUL, sufijo="%", maximo=100, anotaciones=None):
    y = range(len(etiquetas))
    ax.barh(list(y), valores, color=color, height=0.62, edgecolor=SUPERFICIE, linewidth=2)
    ax.set_yticks(list(y), etiquetas)
    ax.invert_yaxis()
    ax.set_xlim(0, maximo * 1.3)
    ax.xaxis.grid(True, color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    for i, v in enumerate(valores):
        txt = f"{v:.0f}{sufijo}"
        if anotaciones:
            txt += f"  {anotaciones[i]}"
        ax.text(v + maximo * 0.015, i, txt, va="center", fontsize=10, color=TINTA_2)


# ---------------------------------------------------------------- gráficos
def g1_perfil(d):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    fig.subplots_adjust(top=0.78, bottom=0.14, left=0.06, right=0.98, wspace=0.35)
    _titulo(fig, "¿Quiénes respondieron?",
            "La mitad tiene entre 20 y 24 años; 2 de cada 3 tienen inglés principiante")
    edad = d["edad"].value_counts().reindex(["17-19", "20-22", "22-24", "28-30"], fill_value=0)
    axes[0].bar(edad.index, edad.values, color=AZUL, width=0.6, edgecolor=SUPERFICIE, linewidth=2)
    axes[0].set_title("Rango de edad (personas)", fontsize=11.5)
    for i, v in enumerate(edad.values):
        axes[0].text(i, v + 0.2, str(v), ha="center", fontsize=10, color=TINTA_2)
    axes[0].set_yticks([])
    axes[0].spines["left"].set_visible(False)

    ing = d["nivel_ingles"].value_counts().reindex(
        ["Principiante (A1-A3)", "Intermedio (B1-B2)", "Avanzado (C1-C2)"], fill_value=0)
    barras_h(axes[1], ing.index, ing.values, sufijo="", maximo=ing.max(),
             anotaciones=[f"({100*v/len(d):.0f}%)" for v in ing.values])
    axes[1].set_title("Nivel de inglés (personas)", fontsize=11.5)
    axes[1].set_xticks([])
    axes[1].spines["bottom"].set_visible(False)
    _guardar(fig, "01_perfil.png")


def g2_presencia_digital(d):
    items = ["LinkedIn", "GitHub"]
    antes = [pct(d["linkedin_antes"]), pct(d["github_antes"])]
    despues = [pct(d["linkedin_despues"]), pct(d["github_despues"])]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(top=0.76, bottom=0.14, left=0.07, right=0.98)
    _titulo(fig, "La presencia profesional online casi se duplica",
            "% de egresados con cada herramienta, antes del curso vs. al responder la encuesta")
    x = range(len(items))
    w = 0.36
    b1 = ax.bar([i - w / 2 - 0.01 for i in x], antes, w, color=GRIS_SERIE, label="Antes del curso")
    b2 = ax.bar([i + w / 2 + 0.01 for i in x], despues, w, color=AZUL, label="Al finalizar")
    for barras in (b1, b2):
        for b in barras:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2, f"{b.get_height():.0f}%",
                    ha="center", fontsize=10, color=TINTA_2)
    ax.set_xticks(list(x), items, fontsize=11.5, color=TINTA)
    ax.set_ylim(0, 112)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 1.08), ncol=2, fontsize=10)
    _guardar(fig, "02_presencia_digital.png",
             "Fuente: encuesta (n = 24). 'Al finalizar' = informó el link a su perfil en la encuesta.")


def g3_empleabilidad(d):
    con = d[d["consiguio_trabajo"] == True]
    etiquetas = ["Consiguió trabajo gracias\nal curso o LinkedIn",
                 "… de ellos, a través de\nla red de Pescar",
                 "… de ellos, en el mundo IT",
                 "Cambió de trabajo\ndurante el curso"]
    valores = [pct(d["consiguio_trabajo"]), pct(con["trabajo_via_red_pescar"]),
               pct(con["trabajo_es_it"]), pct(d["cambio_trabajo_en_curso"])]
    notas = [f"({len(con)} de {len(d)})",
             f"({int(con['trabajo_via_red_pescar'].sum())} de {len(con)})",
             f"({int((con['trabajo_es_it'] == True).sum())} de {len(con)})",
             f"({int(d['cambio_trabajo_en_curso'].sum())} de {len(d)})"]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    fig.subplots_adjust(top=0.78, bottom=0.12, left=0.26, right=0.97)
    _titulo(fig, "4 de cada 10 egresados consiguió trabajo gracias al curso",
            "Y todos esos trabajos llegaron por la red de contactos de Pescar")
    barras_h(ax, etiquetas, valores, anotaciones=notas)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    _guardar(fig, "03_empleabilidad.png")


def g4_cambios(d):
    mapa = {"cambio_autoconocimiento": "Mejor autoconocimiento",
            "cambio_zona_confort": "Más cómodo/a fuera de la zona de confort",
            "cambio_trabajo_equipo": "Más herramientas para trabajar en equipo",
            "cambio_autoestima": "Mejor autoestima / autopercepción",
            "cambio_organizacion": "Más organizado/a",
            "cambio_disciplina": "Más disciplina"}
    s = d[list(mapa)].mean().mul(100).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(top=0.78, bottom=0.12, left=0.36, right=0.97)
    _titulo(fig, "El 100% siente que su autopercepción cambió",
            "% que marcó cada cambio (selección múltiple)")
    barras_h(ax, [mapa[c] for c in s.index], s.values)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    _guardar(fig, "04_cambios_percibidos.png")


def g5_empleo_por_perfil(d):
    filas = []
    def add(etq, mask):
        sub = d[mask]
        filas.append((etq, pct(sub["consiguio_trabajo"]), len(sub)))
    add("Programaba antes del curso", d["programaba_antes"] == True)
    add("No programaba antes", d["programaba_antes"] == False)
    add("Inglés intermedio o avanzado", d["nivel_ingles"] != "Principiante (A1-A3)")
    add("Inglés principiante", d["nivel_ingles"] == "Principiante (A1-A3)")
    add("Ya tenía LinkedIn", d["linkedin_antes"] == True)
    add("No tenía LinkedIn", d["linkedin_antes"] == False)
    etq, val, n = zip(*filas)
    colores = [AZUL if i % 2 == 0 else GRIS_SERIE for i in range(len(filas))]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(top=0.8, bottom=0.12, left=0.28, right=0.97)
    _titulo(fig, "Saber programar e inglés se asocian a más empleo",
            "% que consiguió trabajo gracias al curso, según perfil de entrada (n chico: leer como tendencia)")
    y = list(range(len(filas)))
    y = [i + (i // 2) * 0.5 for i in y]  # aire entre pares
    ax.barh(y, val, color=colores, height=0.7, edgecolor=SUPERFICIE, linewidth=2)
    ax.set_yticks(y, etq)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75], ["0%", "25%", "50%", "75%"])
    ax.xaxis.grid(True, color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    for yi, v, ni in zip(y, val, n):
        ax.text(v + 1.5, yi, f"{v:.0f}%  (n = {ni})", va="center", fontsize=10, color=TINTA_2)
    _guardar(fig, "05_empleo_segun_perfil.png")


def g6_calificacion(d):
    c = d["calificacion"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    fig.subplots_adjust(top=0.76, bottom=0.16, left=0.06, right=0.98)
    _titulo(fig, f"Calificación promedio: {d['calificacion'].mean():.2f} / 5",
            f"{(d['calificacion'] == 5).sum()} de {len(d)} personas le pusieron la nota máxima")
    ax.bar([str(i) for i in c.index], c.values,
           color=[GRIS_SERIE] * 4 + [AZUL], width=0.6, edgecolor=SUPERFICIE, linewidth=2)
    for i, v in enumerate(c.values):
        ax.text(i, v + 0.4, str(v), ha="center", fontsize=10, color=TINTA_2)
    ax.set_xlabel("Calificación (1 a 5)")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    _guardar(fig, "06_calificacion.png")


def g0_resumen(d):
    con = d[d["consiguio_trabajo"] == True]
    tiles = [
        (f"{pct(d['consiguio_trabajo']):.0f}%", "consiguió trabajo\ngracias al curso"),
        (f"{pct(con['trabajo_es_it']):.0f}%", "de esos trabajos\nson del mundo IT"),
        (f"{pct(d['linkedin_antes']):.0f}% → {pct(d['linkedin_despues']):.0f}%", "tiene LinkedIn\n(antes → después)"),
        (f"{d['calificacion'].mean():.2f}", "calificación promedio\ndel curso (sobre 5)"),
    ]
    fig = plt.figure(figsize=(12, 2.8))
    fig.text(0.02, 0.92, "El curso en cuatro números", fontsize=15, fontweight="bold", va="top")
    for i, (num, etq) in enumerate(tiles):
        x0 = 0.02 + i * 0.245
        ax = fig.add_axes([x0, 0.12, 0.225, 0.62])
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True); sp.set_color(GRILLA)
        ax.text(0.07, 0.68, num, fontsize=24, fontweight="bold", color=TINTA, va="center",
                transform=ax.transAxes)
        ax.text(0.07, 0.27, etq, fontsize=10.5, color=TINTA_2, va="center", transform=ax.transAxes)
        ax.axvline(0, color=AZUL, linewidth=6)
    fig.savefig(IMG / "00_resumen.png", dpi=160)
    plt.close(fig)


def g7_punto_de_partida(d):
    mapa = [("Tenía CV", d["cv_antes"]),
            ("Tenía LinkedIn", d["linkedin_antes"]),
            ("Estudiaba una carrera", d["estudia_carrera"]),
            ("Tenía GitHub", d["github_antes"]),
            ("Trabajaba", d["trabajaba_antes"]),
            ("Sabía programar", d["programaba_antes"])]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(top=0.78, bottom=0.12, left=0.22, right=0.97)
    _titulo(fig, "Desde dónde arrancaron",
            "% que ya tenía cada cosa al empezar el curso")
    barras_h(ax, [m[0] for m in mapa], [pct(m[1]) for m in mapa])
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    _guardar(fig, "07_punto_de_partida.png")


def g8_formacion(d):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    fig.subplots_adjust(top=0.78, bottom=0.12, left=0.13, right=0.97, wspace=0.7)
    _titulo(fig, "Formación académica",
            "8 de cada 10 tienen solo el secundario; la mitad de quienes estudian eligió una carrera IT")
    est = d["estudios_completados"].value_counts().reindex(
        ["Ninguno", "Secundaria", "Terciario", "Universitarios"], fill_value=0)
    barras_h(axes[0], est.index, est.values, sufijo="", maximo=est.max(),
             anotaciones=[f"({100*v/len(d):.0f}%)" for v in est.values])
    axes[0].set_title("Estudios completados (personas)", fontsize=11.5)
    axes[0].set_xticks([]); axes[0].spines["bottom"].set_visible(False)

    car = pd.Series({
        "Carrera relacionada a IT": int((d["carrera_it"] == True).sum()),
        "Carrera no IT": int((d["carrera_it"] == False).sum()),
        "No estudia / sin dato": int(d["carrera_it"].isna().sum()),
    })
    barras_h(axes[1], car.index, car.values, sufijo="", maximo=car.max(),
             anotaciones=[f"({100*v/len(d):.0f}%)" for v in car.values])
    axes[1].set_title("Carrera en curso (personas)", fontsize=11.5)
    axes[1].set_xticks([]); axes[1].spines["bottom"].set_visible(False)
    _guardar(fig, "08_formacion.png")


def g9_cambios_segun_empleo(d):
    mapa = {"cambio_autoconocimiento": "Autoconocimiento",
            "cambio_zona_confort": "Salir de la zona de confort",
            "cambio_trabajo_equipo": "Trabajo en equipo",
            "cambio_autoestima": "Autoestima",
            "cambio_organizacion": "Organización",
            "cambio_disciplina": "Disciplina"}
    con = d[d["consiguio_trabajo"] == True][list(mapa)].mean() * 100
    sin = d[d["consiguio_trabajo"] == False][list(mapa)].mean() * 100
    fig, ax = plt.subplots(figsize=(10, 5.4))
    fig.subplots_adjust(top=0.76, bottom=0.12, left=0.25, right=0.97)
    _titulo(fig, "Quienes consiguieron trabajo reportan más cambios",
             "% que marcó cada cambio, según si consiguió trabajo gracias al curso")
    y = list(range(len(mapa)))
    h = 0.36
    ax.barh([i - h / 2 - 0.01 for i in y], con.values, h, color=AZUL,
            label=f"Consiguió trabajo (n = {int(d['consiguio_trabajo'].sum())})")
    ax.barh([i + h / 2 + 0.01 for i in y], sin.values, h, color=GRIS_SERIE,
            label=f"No consiguió (n = {int((d['consiguio_trabajo'] == False).sum())})")
    for i in y:
        ax.text(con.values[i] + 1.2, i - h / 2, f"{con.values[i]:.0f}%", va="center", fontsize=9.5, color=TINTA_2)
        ax.text(sin.values[i] + 1.2, i + h / 2, f"{sin.values[i]:.0f}%", va="center", fontsize=9.5, color=TINTA_2)
    ax.set_yticks(y, list(mapa.values()))
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.xaxis.grid(True, color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, fontsize=10)
    _guardar(fig, "09_cambios_segun_empleo.png")


def g10_emprendimiento_idiomas(d):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    fig.subplots_adjust(top=0.76, bottom=0.12, left=0.19, right=0.97, wspace=0.7)
    _titulo(fig, "Emprendimiento e idiomas",
            "Casi la mitad ya emprendía; 9 de cada 10 estudian o piensan estudiar un idioma")
    emp = d["emprendimiento"].value_counts().reindex(
        ["Antes del curso", "Durante el curso", "Sin emprendimiento / sin respuesta"], fill_value=0)
    emp.index = ["Emprendía antes", "Empezó en el curso", "No emprende / s.d."]
    barras_h(axes[0], emp.index, emp.values, sufijo="", maximo=emp.max(),
             anotaciones=[f"({100*v/len(d):.0f}%)" for v in emp.values])
    axes[0].set_title("Emprendimiento (personas)", fontsize=11.5)
    axes[0].set_xticks([]); axes[0].spines["bottom"].set_visible(False)

    idi = pd.Series({
        "Estudia un idioma hoy": int(d["estudia_idioma"].sum()),
        "Planea hacerlo": int(d["planea_estudiar_idioma"].sum()),
        "No": int(len(d) - d["estudia_idioma"].sum() - d["planea_estudiar_idioma"].sum()),
    })
    barras_h(axes[1], idi.index, idi.values, sufijo="", maximo=idi.max(),
             anotaciones=[f"({100*v/len(d):.0f}%)" for v in idi.values])
    axes[1].set_title("Estudio de idiomas (personas)", fontsize=11.5)
    axes[1].set_xticks([]); axes[1].spines["bottom"].set_visible(False)
    _guardar(fig, "10_emprendimiento_idiomas.png")


# ---------------------------------------------------------------- métricas
def metricas(d):
    con = d[d["consiguio_trabajo"] == True]
    return {
        "n_respuestas": len(d),
        "pct_consiguio_trabajo": round(pct(d["consiguio_trabajo"]), 1),
        "n_consiguio_trabajo": int(d["consiguio_trabajo"].sum()),
        "pct_trabajo_via_red_pescar": round(pct(con["trabajo_via_red_pescar"]), 1),
        "pct_trabajo_it_entre_empleados": round(pct(con["trabajo_es_it"]), 1),
        "n_primer_trabajo": int((d["primer_trabajo"] == True).sum()),
        "pct_cambio_trabajo_en_curso": round(pct(d["cambio_trabajo_en_curso"]), 1),
        "linkedin_antes_pct": round(pct(d["linkedin_antes"]), 1),
        "linkedin_despues_pct": round(pct(d["linkedin_despues"]), 1),
        "github_antes_pct": round(pct(d["github_antes"]), 1),
        "github_despues_pct": round(pct(d["github_despues"]), 1),
        "pct_cv_mejorado": round(pct(d["cv_mejorado_en_curso"]), 1),
        "pct_cambio_autopercepcion": round(pct(d["cambio_autopercepcion"]), 1),
        "promedio_cambios_con_trabajo": round(con["n_cambios"].mean(), 2),
        "promedio_cambios_sin_trabajo": round(d.loc[d["consiguio_trabajo"] == False, "n_cambios"].mean(), 2),
        "calificacion_promedio": round(d["calificacion"].mean(), 2),
        "pct_calificacion_5": round(100 * (d["calificacion"] == 5).mean(), 1),
        "pct_programaba_antes": round(pct(d["programaba_antes"]), 1),
        "empleo_si_programaba": round(pct(d.loc[d["programaba_antes"] == True, "consiguio_trabajo"]), 1),
        "empleo_no_programaba": round(pct(d.loc[d["programaba_antes"] == False, "consiguio_trabajo"]), 1),
        "pct_emprendio_por_curso": round(pct(d["emprendio_por_curso"]), 1),
        "n_emprendio_durante": int((d["emprendimiento"] == "Durante el curso").sum()),
        "pct_estudia_o_planea_idioma": round(100 * (d["estudia_idioma"] | d["planea_estudiar_idioma"]).mean(), 1),
        "pct_entrego_repo": round(pct(d["entrego_repo"]), 1),
    }


def main():
    IMG.mkdir(exist_ok=True)
    d = pd.read_csv(DATA)
    g0_resumen(d)
    g1_perfil(d)
    g2_presencia_digital(d)
    g3_empleabilidad(d)
    g4_cambios(d)
    g5_empleo_por_perfil(d)
    g6_calificacion(d)
    g7_punto_de_partida(d)
    g8_formacion(d)
    g9_cambios_segun_empleo(d)
    g10_emprendimiento_idiomas(d)
    m = metricas(d)
    METRICAS.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(m, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
