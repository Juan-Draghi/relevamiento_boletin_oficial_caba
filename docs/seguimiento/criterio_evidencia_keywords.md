# Criterio de evidencia mínima para revisar keywords

Adoptado: 2026-11-16

## Objetivo

Definir cuántos datos hacen falta para proponer cambios de keywords, normas curadas u organismos prioritarios a partir del informe por término (`scripts/revisar_estrategias.py terminos`). Evita retirar términos con poca evidencia y, a la vez, evita esperar sin necesidad cuando la evidencia ya es suficiente.

El criterio fija la evidencia **mínima para proponer** un cambio. No ordena cambios automáticos: toda propuesta requiere comparación previa, ficha y aprobación profesional mediante el skill `ajustar-keywords-bo-caba`.

## Cómo leer un «0 relevantes»

Si un término tuvo **0 relevantes en n casos evaluados**, la tasa real de relevantes podría ser baja pero no nula. Con la *regla de tres*, una aproximación estadística estándar, se estima con 95 % de confianza que esa tasa no supera **3/n**.

| Casos evaluados sin relevantes (n) | Tasa real de relevantes, como máximo (3/n) |
|---|---|
| 5 | 60 % |
| 15 | 20 % |
| 30 | 10 % |
| 60 | 5 % |
| 100 | 3 % |
| 150 | 2 % |

Casos evaluados = relevantes + no relevantes por decisión + no relevantes según la lectura completa. Las normas sin información no cuentan.

El informe por término calcula este valor en la columna **Tasa máx. (3/n)** y clasifica cada término en la columna **Evidencia**: «Cumple el mínimo» (sección «Candidatos a revisión»), «En observación», «Aporta relevantes» o «Sin base».

## Reglas

1. **Retirar o restringir un término:** proponerlo sólo con **al menos 30 casos evaluados y ninguno relevante** (tasa máxima cercana al 10 %). Informar siempre n y la tasa máxima 3/n.
2. **Términos con menos de 30 casos evaluados:** no proponer su retiro. Esperar a que acumulen casos. Al generar pocas alertas, su costo de lectura es bajo.
3. **Términos ligados a normas estacionales o anuales** (por ejemplo, leyes tarifarias, presupuesto, resoluciones de inicio de año): no retirarlos hasta contar con **un ciclo anual completo** de registros.
4. **Agregar términos o patrones:** no requiere esperar. Cada omisión identificada, con su evidencia, alcanza para proponer un ajuste puntual.
5. **Opción intermedia para términos amplios:** antes de eliminar un término con muchas alertas irrelevantes, evaluar convertirlo en keyword condicional (`KEYWORDS_REQUIEREN_ACCION_NORMATIVA`) o reemplazarlo por una frase más específica, si la comparación previa muestra que así se conservan los casos normativos generales.
6. **Términos que sí aportan relevantes:** no evaluar su precisión mientras haya pocas relevantes confirmadas en el período. Hacen falta varias decenas de relevantes en total para que esos porcentajes sean estables.

## Calendario de revisión

Calculado sobre los registros disponibles al adoptar el criterio (13/07/2026 a 06/11/2026: 84 boletines, 13 relevantes confirmadas).

| Momento | Alcance |
|---|---|
| Noviembre de 2026 | Términos que ya cumplen la regla 1. |
| Enero de 2027 (unos 6 meses de datos) | Repetir el informe para los términos que lleguen a 30 casos evaluados. |
| Julio de 2027 (un año completo) | Revisión general, incluidos los términos estacionales (regla 3) y, si la base de relevantes lo permite, el rendimiento de los términos que aportan relevantes (regla 6). |

El calendario es orientativo. No fija metas ni obliga a hacer cambios.

## Situación al adoptar el criterio

Términos que cumplían la regla 1 según el informe del 16/11/2026: habilitación (128 casos), consulta obligatoria (66), AGIP (58), AGC (35), aptitud ambiental (35), certificado de aptitud ambiental (35) y superficie (35). Aptitud ambiental y certificado de aptitud ambiental coinciden siempre en las mismas normas: retirar sólo uno no cambia la selección.

## Relación con otros documentos

- Procedimiento de ajuste: `.claude/skills/ajustar-keywords-bo-caba/SKILL.md`.
- Registro de cambios aplicados: [log_ajustes.md](log_ajustes.md).
- Indicadores y referencia profesional: [registro_operativo.md](registro_operativo.md) y ADR-007.
