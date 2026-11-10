# Reporte de calidad de datos

- Filas crudas: 25
- Filas válidas: 24
- Columnas finales: 37

## Problemas detectados

- Se eliminaron 1 fila(s) completamente vacía(s).
- 2 persona(s) dicen NO estudiar una carrera pero indican tipo de carrera (filas 18, 23 del CSV). Se conservan tal cual.
- 1 persona(s) no respondieron si estudian una carrera.
- 1 persona(s) dicen no haber conseguido trabajo por el curso pero marcan que el trabajo es IT (probablemente se refieren a su trabajo actual).
- 4 persona(s) sin equipo asignado.
- Los rangos de edad del formulario se solapan (20-22 / 22-24) y no existen 24-28: conviene corregirlos en la próxima edición.
- Datos personales (nombre, apellido, email, links) se eliminan del dataset procesado; solo se conserva si cada link fue informado.

## Nulos por columna (solo columnas con nulos)

| Columna | Nulos |
|---|---|
| estudia_carrera | 1 |
| carrera_it | 10 |
| tipo_carrera | 9 |
| cursaba_carrera_antes | 2 |
| trabajo_es_it | 8 |
| emprendio_por_curso | 9 |
| primer_trabajo | 7 |
| equipo | 4 |
