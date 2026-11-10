"""
ETL de la encuesta de egresados del curso.

Extrae el CSV crudo exportado de Google Forms, lo limpia, normaliza y anonimiza,
y escribe:
  - data/processed/respuestas_limpias.csv  (una fila por persona, columnas tipadas)
  - data/processed/calidad_datos.md        (reporte de problemas detectados)

Uso:
    python src/etl.py
"""
from pathlib import Path
import re
import unicodedata

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "form_respuestas.csv"
OUT = ROOT / "data" / "processed" / "respuestas_limpias.csv"
REPORT = ROOT / "data" / "processed" / "calidad_datos.md"

# Nombres de columna cortos, en snake_case (mismo orden que el formulario)
COLUMNAS = [
    "timestamp", "apellido", "nombre", "trabajo_antes_raw", "edad", "email",
    "linkedin_url", "estudia_carrera", "carrera_it", "tipo_carrera", "nivel_ingles",
    "estudios_completados", "cursaba_carrera_antes", "trabajo_por_curso_raw",
    "linkedin_antes", "github_antes", "cv_antes_raw", "trabajo_es_it",
    "cambio_autopercepcion", "cambios_raw", "emprendimiento_raw",
    "emprendio_por_curso", "primer_trabajo", "github_url", "repo_url",
    "estudia_idioma_raw", "equipo", "calificacion", "programaba_antes",
]

CAMBIOS = {
    "Tengo mejor autoestima/autopercepcion": "cambio_autoestima",
    "Me siento mas organizado": "cambio_organizacion",
    "Trabajo tengo mas herramientas para trabajar mejor en equipo": "cambio_trabajo_equipo",
    "Tengo mas disciplina": "cambio_disciplina",
    "Me siento mas comodo saliendo de mi zona del comfort": "cambio_zona_confort",
    "Tengo mejor autoconocimiento": "cambio_autoconocimiento",
}

ORDEN_EDAD = ["17-19", "20-22", "22-24", "28-30"]
ORDEN_INGLES = ["Principiante (A1-A3)", "Intermedio (B1-B2)", "Avanzado (C1-C2)"]
PII = ["apellido", "nombre", "email", "linkedin_url", "github_url", "repo_url"]


def _norm(x):
    """Minúsculas, sin tildes, sin espacios sobrantes. NaN/'' -> None."""
    if pd.isna(x):
        return None
    s = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    s = s.strip().lower()
    return s or None


def a_bool(x):
    """'Sí'/'si'/'Si, pero...' -> True, 'No...' -> False, vacío -> <NA>."""
    s = _norm(x)
    if s is None:
        return pd.NA
    if s.startswith("si"):
        return True
    if s.startswith("no"):
        return False
    return pd.NA


def url_valida(x):
    s = _norm(x)
    return bool(s and re.match(r"https?://", s))


def transformar(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    problemas = []
    df = raw.copy()
    df.columns = COLUMNAS

    # 1. Filas totalmente vacías (Google Forms deja una fila en blanco al final)
    vacias = df.drop(columns="emprendimiento_raw").isna().all(axis=1)
    if vacias.any():
        problemas.append(f"Se eliminaron {int(vacias.sum())} fila(s) completamente vacía(s).")
    df = df[~vacias].reset_index(drop=True)

    # 2. Tipos básicos
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%m/%d/%Y %H:%M")
    df["calificacion"] = pd.to_numeric(df["calificacion"], errors="coerce").astype("Int64")
    df["edad"] = pd.Categorical(df["edad"].str.strip(), categories=ORDEN_EDAD, ordered=True)

    # 3. Respuestas con texto libre que codifican dos variables
    t = df["trabajo_antes_raw"].map(_norm)
    df["trabajaba_antes"] = t.map(lambda s: pd.NA if s is None else s.startswith("si")).astype("boolean")
    df["cambio_trabajo_en_curso"] = t.fillna("").str.contains("cambie")

    cv = df["cv_antes_raw"].map(_norm)
    df["cv_antes"] = df["cv_antes_raw"].map(a_bool).astype("boolean")
    df["cv_mejorado_en_curso"] = cv.fillna("").str.contains("mejorar")

    tr = df["trabajo_por_curso_raw"].map(_norm)
    df["consiguio_trabajo"] = df["trabajo_por_curso_raw"].map(a_bool).astype("boolean")
    df["trabajo_via_red_pescar"] = tr.fillna("").str.contains("red de pescar")

    idi = df["estudia_idioma_raw"].map(_norm)
    df["estudia_idioma"] = idi.map(lambda s: pd.NA if s is None else s.startswith("si")).astype("boolean")
    df["planea_estudiar_idioma"] = idi.fillna("").str.contains("planeo")

    # 4. Booleanos simples
    for c in ["estudia_carrera", "carrera_it", "cursaba_carrera_antes", "linkedin_antes",
              "github_antes", "trabajo_es_it", "cambio_autopercepcion",
              "emprendio_por_curso", "primer_trabajo", "programaba_antes"]:
        df[c] = df[c].map(a_bool).astype("boolean")

    # 5. Categóricas
    ingles = {"a1-a3 - principiante": ORDEN_INGLES[0],
              "b1-b2 - intermedio": ORDEN_INGLES[1],
              "c1-c2 - avanzado": ORDEN_INGLES[2]}
    df["nivel_ingles"] = pd.Categorical(df["nivel_ingles"].map(_norm).map(ingles),
                                        categories=ORDEN_INGLES, ordered=True)
    df["tipo_carrera"] = df["tipo_carrera"].map(_norm).map(
        {"de grado": "Grado", "tecnicatura": "Tecnicatura"})
    df["estudios_completados"] = df["estudios_completados"].str.strip()
    df["emprendimiento"] = df["emprendimiento_raw"].map(_norm).map(
        {"antes": "Antes del curso", "durante": "Durante el curso"}).fillna("Sin emprendimiento / sin respuesta")
    df["equipo"] = df["equipo"].str.strip()

    # 6. Multi-selección -> one-hot
    for texto, col in CAMBIOS.items():
        df[col] = df["cambios_raw"].fillna("").str.contains(texto, regex=False)
    df["n_cambios"] = df[list(CAMBIOS.values())].sum(axis=1)

    # 7. Variables derivadas de los links (antes de anonimizar)
    df["linkedin_despues"] = df["linkedin_url"].map(url_valida)
    df["github_despues"] = df["github_url"].map(url_valida)
    df["entrego_repo"] = df["repo_url"].map(url_valida)

    # 8. Chequeos de consistencia
    inc = df[(df["estudia_carrera"] == False) & df["tipo_carrera"].notna()]
    if len(inc):
        problemas.append(f"{len(inc)} persona(s) dicen NO estudiar una carrera pero indican tipo de carrera "
                         f"(filas {', '.join(str(i + 2) for i in inc.index)} del CSV). Se conservan tal cual.")
    sin_carrera = df[df["estudia_carrera"].isna()]
    if len(sin_carrera):
        problemas.append(f"{len(sin_carrera)} persona(s) no respondieron si estudian una carrera.")
    inc2 = df[(df["consiguio_trabajo"] == False) & (df["trabajo_es_it"] == True)]
    if len(inc2):
        problemas.append(f"{len(inc2)} persona(s) dicen no haber conseguido trabajo por el curso pero "
                         "marcan que el trabajo es IT (probablemente se refieren a su trabajo actual).")
    sin_equipo = df["equipo"].isna().sum()
    if sin_equipo:
        problemas.append(f"{sin_equipo} persona(s) sin equipo asignado.")
    problemas.append("Los rangos de edad del formulario se solapan (20-22 / 22-24) y no existen 24-28: "
                     "conviene corregirlos en la próxima edición.")
    problemas.append("Datos personales (nombre, apellido, email, links) se eliminan del dataset procesado; "
                     "solo se conserva si cada link fue informado.")

    # 9. Anonimizar y ordenar
    df.insert(0, "id", range(1, len(df) + 1))
    df = df.drop(columns=PII + [c for c in df.columns if c.endswith("_raw")])
    return df, problemas


def main():
    raw = pd.read_csv(RAW, dtype=str)
    df, problemas = transformar(raw)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    lines = ["# Reporte de calidad de datos", "",
             f"- Filas crudas: {len(raw)}",
             f"- Filas válidas: {len(df)}",
             f"- Columnas finales: {df.shape[1]}", "",
             "## Problemas detectados", ""] + [f"- {p}" for p in problemas] + [
             "", "## Nulos por columna (solo columnas con nulos)", "",
             "| Columna | Nulos |", "|---|---|"]
    nulos = df.isna().sum()
    lines += [f"| {c} | {n} |" for c, n in nulos[nulos > 0].items()]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK -> {OUT.relative_to(ROOT)} ({len(df)} filas, {df.shape[1]} columnas)")
    for p in problemas:
        print(" -", p)


if __name__ == "__main__":
    main()
