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

## LOG-2026-11-05 - Agregar norma curada Resolución 227/SECGDU/26

> Registro retroactivo, documentado el 2026-11-14. El cambio de configuración se aplicó el 2026-11-05 en el commit `ccbe041` sin entrada en este log.

**Evidencia**

- Período o ejemplar: BO 7460 (2026-09-24) y BO 7489 (2026-11-05).
- Norma o conjunto de casos: Resolución N° 227/SECGDU/26, que establece que toda documentación que requiera la firma de profesionales intervinientes presentada ante las Direcciones Generales de la Secretaría deberá suscribirse mediante firma digital; y Resolución N° 252/SECGDU/26, cuyo sumario es "Prorroga la entrada en vigencia de la Resolución N° 227-SECGDU/26".
- Categoría obtenida y decisión profesional: ambas `REVISION_MANUAL` (`sumario_opaco_patron`, `organismo_prioritario: SECGDU`), confirmadas como `RELEVANTE_CONFIRMADA`.
- Resultado observado: los actos vinculados con la Resolución 227/SECGDU/26 sólo se detectaban por la vía indirecta de revisión manual.

**Problema detectado**

- Tipo: variante no cubierta.
- Descripción: una norma confirmada como relevante no estaba bajo seguimiento directo. Sus prórrogas o modificaciones dependían de que el sumario resultara opaco y de que interviniera un organismo prioritario.

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json` — `LISTA_NORMAS_CURADAS`.
- Operación: agregar.
- Valor anterior: no corresponde.
- Valor nuevo: `[Rr]esoluci[oó]n(?: [Nn]°?)? ?227(?:[-/]?GCABA)?[-/]?SECGDU[-/]?26`.
- Modificación: incorporación del patrón; contempla `N°` opcional, guion o barra, `GCABA` opcional y la sigla del organismo con el año.

**Motivo de incorporación o modificación**

- Justificación: la firma digital obligatoria de la documentación profesional presentada ante la Secretaría afecta directamente el ejercicio profesional de arquitectura y urbanismo. Corresponde seguir la norma y sus actos modificatorios o de prórroga.

**Validación**

- Prueba específica: `test_curated_resolution_227_secgdu_26_matches_real_variants` (sumario real de la Resolución 252/SECGDU/26 y dos variantes de grafía) y `test_curated_resolution_227_secgdu_26_does_not_match_neighbors` (228-SECGDU/26, 1227-SECGDU/26 y 227-SECGDU/25) en `tests/test_classifier.py`.
- Suite completa: `python -m unittest discover -s tests`, 41 pruebas; validador de configuración del skill.
- Resultado: favorable; configuración válida y todas las pruebas superadas.

**Efecto esperado**

- Resultado esperado: toda norma cuyo sumario cite la Resolución 227/SECGDU/26 se clasifica como `RELEVANTE` por `referencia_norma_curada`.
- Riesgo o efecto colateral observado: no se observó sobrecaptura; números y años vecinos no coinciden. Limitación: el patrón sólo actúa cuando el número de la resolución figura en el sumario.

**Referencias**

- Issue: no corresponde.
- Commit: `ccbe041` (cambio de configuración); `369330a` (registro y prueba).
- ADR: no corresponde.

**Revisar resultado**

- Período: próxima norma que cite la Resolución 227/SECGDU/26.
- Resultado: pendiente.

## LOG-2026-11-16 - Agregar keyword «régimen especial de adecuación y regularización»

**Evidencia**

- Período o ejemplar: BO 7458; detectada en la revisión de estrategias del período 2026-07-13 a 2026-11-06 (`data/informes_estrategias/20261116_182711_terminos.md`).
- Norma o conjunto de casos: Ley de Aprobación Inicial N° 1740/LCABA/26 (Poder Legislativo), cuyo sumario es "Crea el Régimen Especial de Adecuación y Regularización para Clubes de Barrio.".
- Categoría obtenida y decisión profesional: `NO_RELEVANTE`, confirmada como `RELEVANTE_CONFIRMADA`, con la evidencia "Crea un régimen especial para regularizar la situación edilicia de clubes de barrio y entidades deportivas.".
- Resultado observado: ninguna keyword coincidió; "regularización de obras" y "regularización de construcciones" no cubren esta redacción.

**Problema detectado**

- Tipo: falso negativo (omisión identificada).
- Descripción: un régimen de regularización edilicia, pertinente para el ejercicio profesional, quedó fuera de la lista principal.

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json` — `KEYWORDS`.
- Operación: agregar.
- Valor anterior: no corresponde.
- Valor nuevo: `régimen especial de adecuación y regularización`.
- Modificación: keyword directa (no condicional), insertada en orden alfabético después de "régimen de escuelas seguras de gestión privada".

**Motivo de incorporación o modificación**

- Justificación: la frase nombra el régimen de regularización edilicia, que es el objeto relevante. Se prefirió a la alternativa "clubes de barrio", que en el histórico tuvo el mismo efecto, porque esta última podría activarse con programas o subsidios a clubes ajenos al alcance (inferencia: en el período hubo unas 30 resoluciones de SECD sobre subsidios, inscripciones y rendiciones de clubes, aunque ninguna con la frase exacta).

**Comparación previa**

- Período y base: 2026-07-13 a 2026-11-06, 84 boletines, 27113 normas.
- Informe: `data/informes_estrategias/20261116_183117_comparacion.md` (no versionado); alternativa descartada en `20261116_183133_comparacion.md`.
- Relevantes recuperadas / perdidas: 1 de 1 / 0 de 12.
- Irrelevantes evitadas / añadidas (decisión + lectura completa): 0 de 518 / 0 de 26582.
- Sin información afectadas: 0.
- Siguen seleccionadas por otra regla (retiros): no corresponde.

**Validación**

- Prueba específica: `test_clubes_de_barrio_regularization_regime_is_relevant` (sumario real, categoría y motivo) y `test_club_subsidy_rendition_is_not_relevant` (Resolución N° 360/SECD/26, control negativo) en `tests/test_classifier.py`.
- Suite completa: `python -m unittest discover -s tests`, 78 pruebas; validador de configuración del skill.
- Resultado: favorable; configuración válida y todas las pruebas superadas.

**Efecto esperado**

- Resultado esperado: la aprobación definitiva de la ley y las normas que mencionen el régimen con esa denominación se clasifican como `RELEVANTE` por `keyword_sumario`.
- Riesgo o efecto colateral observado: sin sobrecaptura en el histórico. Limitación: si la ley definitiva o su reglamentación cambian la denominación del régimen, la frase no las detecta; cuando la ley tenga número definitivo, evaluar un patrón en `LISTA_NORMAS_CURADAS` como ajuste separado.

**Referencias**

- Issue: no corresponde.
- Commit: `a1ac7f1`.
- ADR: no corresponde.

**Revisar resultado**

- Período: boletines posteriores al 2026-11-16, en particular la aprobación definitiva de la ley tras la audiencia pública.
- Resultado: pendiente.

## LOG-2026-11-16 - Convertir «consulta obligatoria» en keyword condicional

**Evidencia**

- Período o ejemplar: 2026-07-13 a 2026-11-06, 84 boletines; informe `data/informes_estrategias/20261116_182711_terminos.md`.
- Norma o conjunto de casos: 66 disposiciones de DGIUR con "consulta obligatoria" en el sumario, todas referidas a una parcela o inmueble concreto ("Aprueba la Consulta Obligatoria…" 56, "Deniega la Consulta Obligatoria…" 8, "Deja sin efecto…" 1, "Deniega la solicitud…" 1). Ejemplo: Disposición N° 1251/DGIUR/26 (BO 7415).
- Categoría obtenida y decisión profesional: `RELEVANTE` por `keyword_sumario: consulta obligatoria`; las 66 confirmadas como `NO_RELEVANTE_CONFIRMADA`.
- Resultado observado: 0 relevantes en 66 casos evaluados; tasa máxima de relevantes 3/66 = 4,5 %. Cumple el criterio de evidencia mínima (`docs/seguimiento/criterio_evidencia_keywords.md`).

**Problema detectado**

- Tipo: falso positivo.
- Descripción: la keyword directa selecciona sistemáticamente actos individuales de DGIUR sin interés para el servicio de referencia.

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json` — `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`.
- Operación: agregar.
- Valor anterior: no corresponde (el término se conserva en `KEYWORDS`).
- Valor nuevo: `consulta obligatoria`.
- Modificación: la keyword pasa de directa a condicional; insertada en orden alfabético al inicio de la lista.

**Motivo de incorporación o modificación**

- Justificación: se eligió la opción intermedia del criterio de evidencia en lugar de eliminar el término. Como condicional sólo clasifica como `RELEVANTE` con verbo de acción y contexto normativo (régimen, procedimiento, requisitos, reglamento, referencia a otra norma, etc.), lo que conserva la detección de normas generales sobre el trámite.

**Comparación previa**

- Período y base: 2026-07-13 a 2026-11-06, 84 boletines, 27113 normas.
- Informe: `data/informes_estrategias/20261116_183633_comparacion.md` (no versionado); alternativa de eliminación en `20261116_183648_comparacion.md` (64 irrelevantes evitadas, mismas relevantes perdidas).
- Relevantes recuperadas / perdidas: 0 / 0 de 13.
- Irrelevantes evitadas / añadidas (decisión + lectura completa): 63 de 518 (12,2 %) / 0 de 26582.
- Sin información afectadas: 0.
- Siguen seleccionadas: Disposición N° 2250/DGIUR/26 (cumple la condición por citar otra disposición) y Disposiciones N° 1329 y 1497/DGIUR/26 (por "objeto territorial" y "urbanización").

**Validación**

- Prueba específica: `test_individual_consulta_obligatoria_is_not_relevant` (sumario real de la Disposición N° 1251/DGIUR/26) y `test_consulta_obligatoria_procedure_is_relevant_by_conditional_keyword` (sumario hipotético de procedimiento general) en `tests/test_classifier.py`.
- Suite completa: `python -m unittest discover -s tests`, 80 pruebas; validador de configuración del skill.
- Resultado: favorable; configuración válida y todas las pruebas superadas.

**Efecto esperado**

- Resultado esperado: las aprobaciones y denegaciones de Consulta Obligatoria por inmueble dejan de llegar a la lista principal; las normas generales sobre el trámite siguen como `RELEVANTE`.
- Riesgo o efecto colateral observado: actos individuales que citen otra norma (como la Disposición N° 2250/DGIUR/26) siguen seleccionados. Una norma general redactada sin verbo de acción ni vocabulario normativo reconocido no se detectaría por esta vía.

**Referencias**

- Issue: no corresponde.
- Commit: `5fdd2dd`.
- ADR: no corresponde.

**Revisar resultado**

- Período: boletines posteriores al 2026-11-16; revisar el término en el informe por término de enero de 2027.
- Resultado: pendiente.

## LOG-2026-11-16 - Convertir «habilitación» en keyword condicional

**Evidencia**

- Período o ejemplar: 2026-07-13 a 2026-11-06, 84 boletines; informe `data/informes_estrategias/20261116_182711_terminos.md`.
- Norma o conjunto de casos: 128 normas con "habilitación" en el sumario: DGSPCB, habilitaciones y renovaciones de seguridad privada (111); AGC, recursos jerárquicos contra rechazos de habilitación comercial de inmuebles concretos (9); DGSVI, habilitaciones de enseñanza de conducción y vehículos (7); SAISSP, curso de capacitación (1). Ejemplo: Disposición N° 191/DGSPCB/26 (BO 7409).
- Categoría obtenida y decisión profesional: `RELEVANTE` por `keyword_sumario: habilitación`; las 128 confirmadas como `NO_RELEVANTE_CONFIRMADA`.
- Resultado observado: 0 relevantes en 128 casos evaluados; tasa máxima de relevantes 3/128 = 2,3 %. Cumple el criterio de evidencia mínima (`docs/seguimiento/criterio_evidencia_keywords.md`).

**Problema detectado**

- Tipo: falso positivo.
- Descripción: la keyword directa es la que más alertas irrelevantes genera; selecciona actos individuales sobre empresas, personas o inmuebles.

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json` — `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`.
- Operación: agregar.
- Valor anterior: no corresponde (el término se conserva en `KEYWORDS`).
- Valor nuevo: `habilitación`.
- Modificación: la keyword pasa de directa a condicional; insertada en orden alfabético después de "espacio público".

**Motivo de incorporación o modificación**

- Justificación: se eligió la opción intermedia del criterio de evidencia en lugar de eliminar el término, con el mismo efecto medido. Como condicional conserva normas generales con verbo de acción y contexto normativo (por ejemplo, un procedimiento de habilitación). La cobertura temática se complementa con "código de habilitaciones", "código de habilitaciones y verificaciones" y "habilitación económica", que no cambian.

**Comparación previa**

- Período y base: 2026-07-13 a 2026-11-06, 84 boletines, 27113 normas; configuración vigente ya con «consulta obligatoria» condicional.
- Informe: `data/informes_estrategias/20261116_184216_comparacion.md` (no versionado); alternativa de eliminación en `20261116_184231_comparacion.md` (mismo resultado).
- Relevantes recuperadas / perdidas: 0 / 0 de 13.
- Irrelevantes evitadas / añadidas (decisión + lectura completa): 126 de 455 (27,7 %) / 0 de 26645.
- Sin información afectadas: 0.
- Siguen seleccionadas por otra regla: Resoluciones N° 350 y 370/AGC/26 (por "redistribución de usos").

**Validación**

- Prueba específica: `test_individual_private_security_habilitacion_is_not_relevant` (sumario real de la Disposición N° 191/DGSPCB/26) y `test_habilitacion_procedure_is_relevant_by_conditional_keyword` (sumario hipotético de procedimiento general) en `tests/test_classifier.py`.
- Suite completa: `python -m unittest discover -s tests`, 82 pruebas; validador de configuración del skill.
- Resultado: favorable; configuración válida y todas las pruebas superadas.

**Efecto esperado**

- Resultado esperado: las habilitaciones individuales y los recursos sobre inmuebles concretos dejan de llegar a la lista principal; las normas generales sobre habilitaciones siguen como `RELEVANTE`.
- Riesgo o efecto colateral observado: un acto individual con verbo de acción que cite otra norma seguiría seleccionado. Una norma general redactada sin verbo de acción ni vocabulario normativo reconocido no se detectaría por esta vía.

**Referencias**

- Issue: no corresponde.
- Commit: `75d0ac3`.
- ADR: no corresponde.

**Revisar resultado**

- Período: boletines posteriores al 2026-11-16; revisar el término en el informe por término de enero de 2027.
- Resultado: pendiente.

## LOG-2026-11-16 - Convertir «superficie» en keyword condicional

**Evidencia**

- Período o ejemplar: 2026-07-13 a 2026-11-06, 84 boletines; informe `data/informes_estrategias/20261116_182711_terminos.md`.
- Norma o conjunto de casos: 35 normas con "superficie" en el sumario: 34 disposiciones de DGIUR sobre inmuebles concretos (ampliación, regularización o redistribución de superficie) y la Ley N° 6979 ("Amplía la superficie concedida a favor de la Fundación Cultural Argentino Japonesa"). Ejemplo: Disposición N° 1240/DGIUR/26 (BO 7414).
- Categoría obtenida y decisión profesional: `RELEVANTE` por `keyword_sumario: superficie`; las 35 confirmadas como `NO_RELEVANTE_CONFIRMADA`.
- Resultado observado: 0 relevantes en 35 casos evaluados; tasa máxima de relevantes 3/35 = 8,6 %. Cumple el criterio de evidencia mínima (`docs/seguimiento/criterio_evidencia_keywords.md`), con poco margen.

**Problema detectado**

- Tipo: falso positivo.
- Descripción: palabra genérica que, como keyword directa, selecciona autorizaciones individuales por inmueble.

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json` — `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`.
- Operación: agregar.
- Valor anterior: no corresponde (el término se conserva en `KEYWORDS`).
- Valor nuevo: `superficie`.
- Modificación: la keyword pasa de directa a condicional; insertada en orden alfabético después de "habilitación".

**Motivo de incorporación o modificación**

- Justificación: se eligió la opción intermedia del criterio de evidencia en lugar de eliminar el término, con el mismo efecto medido. Como condicional conserva normas generales sobre cómputo o regulación de superficies con verbo de acción y contexto normativo.

**Comparación previa**

- Período y base: 2026-07-13 a 2026-11-06, 84 boletines, 27113 normas; configuración vigente ya con «consulta obligatoria» y «habilitación» condicionales.
- Informe: `data/informes_estrategias/20261116_184557_comparacion.md` (no versionado); alternativa de eliminación en `20261116_184613_comparacion.md` (mismo resultado).
- Relevantes recuperadas / perdidas: 0 / 0 de 13.
- Irrelevantes evitadas / añadidas (decisión + lectura completa): 30 de 329 (9,1 %) / 0 de 26771.
- Sin información afectadas: 0.
- Siguen seleccionadas por otra regla: Disposición N° 1359/DGIUR/26 (por "redistribución de usos") y Disposiciones N° 2091, 2539, 2566 y 2592/DGIUR/26 (por "ampliación de rubro", término en observación).

**Validación**

- Prueba específica: `test_individual_surface_extension_is_not_relevant` (sumario real de la Disposición N° 1240/DGIUR/26) y `test_surface_criteria_is_relevant_by_conditional_keyword` (sumario hipotético de criterios generales) en `tests/test_classifier.py`.
- Suite completa: `python -m unittest discover -s tests`, 84 pruebas; validador de configuración del skill.
- Resultado: favorable; configuración válida y todas las pruebas superadas.

**Efecto esperado**

- Resultado esperado: las autorizaciones de superficie por inmueble dejan de llegar a la lista principal; las normas generales sobre superficies siguen como `RELEVANTE`.
- Riesgo o efecto colateral observado: un acto individual con verbo de acción que cite otra norma seguiría seleccionado. Una norma general redactada sin verbo de acción ni vocabulario normativo reconocido no se detectaría por esta vía.

**Referencias**

- Issue: no corresponde.
- Commit: pendiente.
- ADR: no corresponde.

**Revisar resultado**

- Período: boletines posteriores al 2026-11-16; revisar el término en el informe por término de enero de 2027.
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

**Comparación previa**

- Período y base:
- Informe:
- Relevantes recuperadas / perdidas:
- Irrelevantes evitadas / añadidas:
- Sin información afectadas:
- Siguen seleccionadas por otra regla (retiros):

**Efecto esperado**

- Resultado esperado:

**Referencias**

- Issue:
- Commit:
- ADR: no corresponde / ADR-XXX

**Revisar resultado**

- Período:
- Resultado: pendiente / favorable / desfavorable / inconcluso
