# Log de ajustes derivados

Este archivo registra exclusivamente cambios motivados por la evaluación de resultados reales. No corresponde crear una entrada por cada ejecución ni convertir cada keyword en un ADR.

Las entradas anteriores a la creación de este archivo fueron reconstruidas el 2026-07-14 a partir de hilos de trabajo, commits, pruebas y documentación. Cuando el historial no conserva el motivo operativo de un cambio, éste se incluye en `docs/historial_evolucion.md` pero no se completa aquí por inferencia.

## LOG-2026-04-28 - Incorporación del filtro estructural

**Evidencia**

- Período: prueba de diseño del 2026-04-28.
- Norma o conjunto de casos: BO 7355, con 486 normas recibidas desde la API.
- Resultado observado: antes del filtro estructural se mostraban 159 resultados principales. Al aplicar poderes y tipos incluidos se descartaron estructuralmente 211 de las 486 normas; entre los resultados principales quedaron 17 relevantes y 106 para revisión manual.

**Problema detectado**

- Descripción: procesar con el mismo nivel de detalle todos los poderes y tipos de norma mantenía un volumen de lectura que no correspondía al alcance temático del servicio.

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json`, `bo_detector/classifier.py` y pruebas.
- Modificación: se incorporaron `PODERES_INCLUIDOS` y `TIPOS_NORMA_INCLUIDOS` como primera capa, con la categoría `DESCARTADA_FILTRO_ESTRUCTURAL` para preservar el motivo de exclusión.

**Efecto esperado**

- Resultado esperado: reducir el universo antes de aplicar señales temáticas, manteniendo visibles y auditables las exclusiones estructurales.

**Referencias**

- Issue: no corresponde.
- Commit: `fa15f55`.
- ADR: ADR-005.

**Revisar resultado**

- Período: BO 7355.
- Resultado: favorable; el filtro descartó 211 de 486 registros sin eliminarlos del resultado auditable.

## LOG-2026-04-28 - Eliminación del umbral de longitud para revisión manual

**Evidencia**

- Período: prueba de diseño del 2026-04-28.
- Norma o conjunto de casos: resultados de revisión manual del BO 7355.
- Resultado observado: después de depurar la lista de organismos prioritarios quedaban 101 casos de revisión manual; 97 eran disparados por la longitud del sumario, incluidos textos genéricos como transferencias de agentes y compensaciones de créditos.

**Problema detectado**

- Descripción: la longitud no expresaba opacidad temática de manera útil y generaba casi toda la cola de revisión manual.

**Cambio realizado**

- Archivo o parámetro: eliminación de `UMBRAL_TOKENS_OPACO` y del motivo `sumario_opaco_longitud` en la configuración y el clasificador.
- Modificación: se descartó la cantidad de tokens como disparador. La revisión manual quedó vinculada con organismos prioritarios y señales normativas explícitas.

**Efecto esperado**

- Resultado esperado: evitar que sumarios largos pero rutinarios saturen la revisión profesional.

**Referencias**

- Issue: no corresponde.
- Commit: `fa15f55`.
- ADR: ADR-005.

**Revisar resultado**

- Período: BO 7355.
- Resultado: favorable para la reducción de ruido; la regla fue ampliada posteriormente el 2026-06-09 sin reintroducir la longitud.

## LOG-2026-04-28 - Contexto obligatorio para keywords de espacio público

**Evidencia**

- Período: prueba de diseño del 2026-04-28.
- Norma o conjunto de casos: normas del BO 7355 con expresiones `espacio público`, `uso del espacio público` o `vía pública`.
- Resultado observado: la coincidencia directa marcaba como relevantes permisos individuales. Al exigir contexto de acción normativa, los relevantes del ejemplar pasaron de 17 a 3.

**Problema detectado**

- Descripción: ciertas expresiones amplias identificaban tanto cambios generales de reglas como autorizaciones particulares sin interés para el relevamiento.

**Cambio realizado**

- Archivo o parámetro: `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`, `VERBOS_ACCION`, `bo_detector/classifier.py` y pruebas.
- Modificación: las tres expresiones vinculadas con espacio público pasaron a requerir, además, una acción normativa en el sumario.

**Efecto esperado**

- Resultado esperado: conservar cambios normativos generales y reducir falsos positivos por permisos individuales.

**Referencias**

- Issue: no corresponde.
- Commit: `fa15f55`.
- ADR: ADR-005.

**Revisar resultado**

- Período: BO 7355.
- Resultado: favorable; la prueba redujo los relevantes de 17 a 3 y se agregaron casos unitarios para ambas ramas.

## LOG-2026-04-28 - Incorporación del tipo de norma Aclaración

**Evidencia**

- Período: prueba retrospectiva del 2026-04-28.
- Norma o conjunto de casos: BO 7275, Aclaración N.º 6927/LCABA/25, cuyo sumario refiere a la Ley Impositiva año 2026.
- Resultado observado: el tipo `Aclaración` no estaba incluido en el filtro estructural y podía excluir una norma relevante por su contenido.

**Problema detectado**

- Descripción: el listado inicial de tipos no contemplaba una categoría poco frecuente pero materialmente relevante.

**Cambio realizado**

- Archivo o parámetro: `TIPOS_NORMA_INCLUIDOS` en `config/config_keywords.json` y prueba específica.
- Modificación: se agregó `Aclaración` a los tipos admitidos por el filtro estructural.

**Efecto esperado**

- Resultado esperado: evitar la exclusión estructural de aclaraciones vinculadas con normativa de interés.

**Referencias**

- Issue: no corresponde.
- Commit: `fa15f55`.
- ADR: ADR-005.

**Revisar resultado**

- Período: BO 7275.
- Resultado: favorable; el caso quedó retenido y cubierto por una prueba.

## LOG-2026-05-13 - Detección de siglas prioritarias fuera del campo organismo

**Evidencia**

- Período: BO 7365.
- Norma o conjunto de casos: Resolución N.º 194/SSGOU/26.
- Resultado observado: la API informaba `Jefatura de Gabinete de Ministros` como organismo; la sigla prioritaria `SSGOU` aparecía en el nombre y el sumario, por lo que el caso no era derivado a revisión manual.

**Problema detectado**

- Descripción: buscar organismos prioritarios sólo en el campo organismo no contemplaba las siglas presentes en otros campos editoriales.

**Cambio realizado**

- Archivo o parámetro: `bo_detector/classifier.py` y prueba específica.
- Modificación: la coincidencia de `LISTA_ORGANISMOS_PRIORIDAD` pasó a evaluarse sobre la concatenación de organismo, nombre y sumario.

**Efecto esperado**

- Resultado esperado: derivar a revisión manual normas opacas de organismos prioritarios aunque la API informe una denominación institucional general.

**Referencias**

- Issue: no corresponde.
- Commit: `77ce6b9`.
- ADR: no corresponde.

**Revisar resultado**

- Período: BO 7365.
- Resultado: favorable; la resolución pasó a `REVISION_MANUAL` y el comportamiento quedó cubierto por una prueba.

## LOG-2026-05-19 - Referencias de leyes sin punto de miles

**Evidencia**

- Período: caso detectado el 2026-05-19.
- Norma o conjunto de casos: sumario con referencia a la Ley 6927, sin punto de miles.
- Resultado observado: el patrón curado contemplaba `6.927`, pero no la grafía `6927` utilizada en el sumario.

**Problema detectado**

- Descripción: una variante ortográfica habitual impedía reconocer una referencia normativa ya curada.

**Cambio realizado**

- Archivo o parámetro: patrones de leyes 6.xxx en `LISTA_NORMAS_CURADAS` y prueba específica.
- Modificación: el punto de miles pasó a ser opcional mediante patrones equivalentes a `6\.?927`.

**Efecto esperado**

- Resultado esperado: reconocer la misma ley con y sin punto de miles sin ampliar el patrón a números distintos.

**Referencias**

- Issue: no corresponde.
- Commit: `ce7611d`.
- ADR: no corresponde.

**Revisar resultado**

- Período: caso de Ley 6927.
- Resultado: favorable; ambas grafías quedaron cubiertas por pruebas.

## LOG-2026-06-09 - Ampliación de las señales de revisión manual

**Evidencia**

- Período: ajuste definido y probado el 2026-06-09.
- Norma o conjunto de casos: normas de organismos prioritarios con sumarios opacos que contienen una acción normativa o una referencia normativa, pero no necesariamente ambas.
- Resultado observado: la regla anterior exigía simultáneamente verbo de acción y referencia normativa, por lo que algunas variantes justificadas no ingresaban a revisión manual.

**Problema detectado**

- Descripción: la conjunción de las dos señales era demasiado restrictiva para sumarios cuyo objeto no podía determinarse con seguridad.

**Cambio realizado**

- Archivo o parámetro: `bo_detector/classifier.py`, pruebas y documentación de criterios.
- Modificación: para normas no relevantes por detección directa, un organismo o sigla prioritaria se combina con un verbo de acción normativa **o** una referencia normativa opaca. Se agregaron pruebas para cada rama y para la ausencia de ambas señales.

**Efecto esperado**

- Resultado esperado: recuperar variantes opacas que requieren inspección profesional sin volver a usar la longitud del sumario como señal.

**Referencias**

- Issue: PR 1.
- Commit: `4266342`; integración `0aa38fc`.
- ADR: ADR-005.

**Revisar resultado**

- Período: suite de pruebas e integración del 2026-06-09.
- Resultado: favorable; las ramas de acción, referencia y ausencia de señal quedaron verificadas.

## LOG-2026-07-13 - Incorporación de revisión manual e indicadores

**Evidencia**

- Período: inicio de seguimiento operativo en `2026-W29`.
- Norma o conjunto de casos: ejemplar BO 7406, con 310 normas procesadas durante la validación funcional.
- Resultado observado: los conteos de una consulta no permitían conservar decisiones profesionales, identificar falsos negativos ni evaluar el comportamiento del detector a lo largo del tiempo.

**Problema detectado**

- Descripción: la aplicación mostraba la clasificación automática, pero no disponía de persistencia por norma, control complementario, trazabilidad semanal ni indicadores basados en decisiones profesionales. La edición libre de configuración desde la interfaz tampoco permitía normalizar los motivos de futuros ajustes.

**Cambio realizado**

- Archivo o parámetro: `bo_detector/review_store.py`, `desktop_app/app.py`, `desktop_app/templates/index.html`, `desktop_app/static/app.js`, `desktop_app/static/styles.css`, pruebas y documentación.
- Modificación: se agregó un JSON por semana ISO, decisiones manuales por norma, registro de falsos negativos con evidencia, acordeones para categorías ocultas, control complementario, pestaña de indicadores y seis métricas de desempeño. Se retiró el editor de configuración y se mantuvo un resumen de solo lectura. No se modificaron keywords ni patrones del detector.

**Efecto esperado**

- Resultado esperado: acumular evidencia de uso diario sin duplicar ejemplares, medir cobertura y desempeño sobre decisiones reales y asegurar que futuros cambios de configuración queden justificados mediante un skill específico.

**Referencias**

- Issue: no corresponde.
- Commit: `499d814`.
- ADR: ADR-001 y ADR-002.

**Revisar resultado**

- Período: uso diario desde `2026-W29`.
- Resultado: pendiente.

## Plantilla

## LOG-AAAA-MM-DD - Título del ajuste

**Evidencia**

- Período:
- Norma o conjunto de casos:
- Resultado observado:

**Problema detectado**

- Descripción:

**Cambio realizado**

- Archivo o parámetro:
- Modificación:

**Efecto esperado**

- Resultado esperado:

**Referencias**

- Issue:
- Commit:
- ADR: no corresponde / ADR-XXX

**Revisar resultado**

- Período:
- Resultado: pendiente / favorable / desfavorable / inconcluso
