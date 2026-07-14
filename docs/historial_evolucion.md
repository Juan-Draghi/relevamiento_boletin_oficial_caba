# Historial de evolución del detector

Este documento reconstruye retrospectivamente la evolución del proyecto desde el prototipo de aprendizaje supervisado hasta la aplicación local actual. Su propósito es conservar una cronología verificable y distinguir entre:

- decisiones estructurales, documentadas mediante ADR;
- ajustes del detector derivados de casos reales, registrados en el log;
- hitos de implementación, que no justifican por sí mismos un ADR ni una entrada operativa.

La reconstrucción fue realizada el 2026-07-14 a partir de los hilos de trabajo conservados, el historial Git, las pruebas y la documentación del repositorio.

## Alcance y límites de la reconstrucción

El notebook del prototipo original no está presente en este repositorio ni aparece en su historial Git. Por ese motivo, se puede documentar con suficiente respaldo la decisión de abandonar aquel enfoque y su relación con el proyecto anterior `boletin-oficial-caba-ml`, pero no reproducir el código exacto, las ejecuciones ni todas las métricas del notebook.

Las fechas que siguen corresponden a decisiones, pruebas o commits verificables. Cuando el motivo de un cambio no pudo recuperarse, se lo indica expresamente en lugar de inferirlo.

## Fuentes utilizadas

- hilo de diseño inicial `019dd44f-f333-7c22-b47c-3c73353d905d`;
- hilo de ajuste de revisión manual `019eace5-424a-7fe1-aba7-6706431200ec`;
- hilo de revisión manual, indicadores, interfaz y skills `019f5bf1-1ea5-77c3-868b-234b0bfdda03`;
- historial Git desde `01d1a9f` hasta `da72d1a`;
- `README.md`, `docs/pipeline_v2_diseño.md` y `docs/propuesta_parametros_desde_compilaciones.md`;
- configuración, pruebas y ADR vigentes.

## Cronología reconstruida

### Antecedente: prototipo con TF-IDF y SVM

Antes del repositorio actual se experimentó con un clasificador supervisado basado en TF-IDF y SVM. La proporción histórica de normas positivas era inferior aproximadamente al 3 % y el reentrenamiento no producía una mejora estable: en la práctica, el modelo tendía a comportarse como una búsqueda de palabras clave, con mayor complejidad y menor trazabilidad.

El 2026-04-21 se decidió sustituir ese enfoque por reglas explícitas, configuración curada y revisión humana. La decisión se formaliza retrospectivamente en [ADR-004](adr/ADR-004-reglas-trazables-en-lugar-de-ml-supervisado.md).

### 2026-04-21 a 2026-04-22: diseño del nuevo pipeline

Se definió que el sumario del Boletín Oficial sería la señal editorial principal. Una keyword suficiente debía producir relevancia directa, no un puntaje probabilístico. Para los casos opacos se descartó descargar e interpretar automáticamente el texto completo; la resolución quedaría a cargo de la revisión profesional con los metadatos y el enlace oficial disponibles.

También se analizaron compilaciones normativas CABA de 2018 a 2025 para proponer parámetros iniciales. La extracción recuperó 159 registros de 2019 a 2025. El archivo de 2018 era parcial y menos confiable, por lo que no se utilizó como una base equivalente. Este trabajo quedó documentado en `docs/propuesta_parametros_desde_compilaciones.md` y sus artefactos asociados.

### 2026-04-28: implementación del detector por capas

Se implementaron los módulos de configuración, normalización textual, clasificación, acceso a la API, aplanamiento del payload y ejecución del pipeline. La configuración inicial consolidó keywords, keywords condicionales, verbos de acción, normas curadas y organismos prioritarios.

La prueba con el BO 7355 permitió ajustar el diseño antes del primer commit funcional:

- el filtro estructural descartó 211 de 486 normas; entre los resultados principales quedaron 17 relevantes y 106 para revisión manual;
- el umbral de longitud del sumario generaba 97 de 101 casos de revisión manual después de depurar organismos prioritarios, por lo que fue eliminado;
- las expresiones amplias vinculadas con espacio público pasaron a requerir contexto de acción normativa, reduciendo los relevantes del ejemplar de 17 a 3;
- las normas curadas pasaron a producir relevancia directa.

La prueba con el BO 7275 identificó el tipo de norma `Aclaración`, que fue incorporado al filtro estructural para no excluir la referencia a la Ley Impositiva 2026.

El commit `fa15f55` reunió la primera implementación funcional. Las decisiones de arquitectura del pipeline se formalizan retrospectivamente en [ADR-005](adr/ADR-005-pipeline-api-por-capas-y-revision-humana.md). Los ajustes medidos sobre ejemplares reales se incorporan al log.

### 2026-04-28: aplicación local para uso diario

Se eligió una aplicación Flask local, accesible desde el navegador y acompañada por lanzadores para Windows. La interfaz permitió consultar el último boletín, una fecha específica o un parámetro avanzado. Esta decisión se documenta retrospectivamente en [ADR-006](adr/ADR-006-aplicacion-local-flask-para-uso-diario.md).

La primera versión incluyó un editor de configuración. Ese componente fue retirado el 2026-07-13 al establecerse una gobernanza auditable para los ajustes. La decisión vigente es la definida en ADR-002.

### 2026-05-13: siglas prioritarias en nombre y sumario

La Resolución N.º 194/SSGOU/26 del BO 7365 llegaba con `Jefatura de Gabinete de Ministros` en el campo organismo, mientras que la sigla prioritaria aparecía en el nombre y el sumario. El clasificador fue ampliado para buscar organismos y siglas prioritarias en los tres campos. El cambio y su prueba quedaron en el commit `77ce6b9` y se registran retrospectivamente en el log.

### 2026-05-19: leyes sin punto de miles

Un sumario citaba la Ley 6927 sin punto de miles, mientras que el patrón curado sólo contemplaba `6.927`. Los patrones de leyes 6.xxx fueron modificados para aceptar ambas grafías. El cambio y su prueba quedaron en el commit `ce7611d` y se registran retrospectivamente en el log.

### 2026-06-04: cambios de configuración con motivo no recuperado

El commit `1a7cf6a` incorporó el Decreto 740/07 y la Ley 1.540 a las normas curadas. El commit `5627044` redujo la lista de organismos prioritarios de 28 a 14 entradas.

El historial permite confirmar qué cambió, pero no conserva evidencia suficiente sobre los casos y motivos operativos exactos. Por esa razón, estos cambios se incluyen en la cronología pero no se les crea una entrada retrospectiva en el log. Un motivo no debe completarse por inferencia.

### 2026-06-09: ampliación de las señales de revisión manual

Se consolidó la regla vigente para los casos no relevantes por detección directa: un organismo o sigla prioritaria debe combinarse con un verbo de acción normativa **o** una referencia normativa opaca. La versión anterior exigía ambas señales simultáneamente y podía dejar fuera casos que justificaban inspección profesional.

El cambio quedó cubierto por pruebas específicas en `4266342` y fue integrado mediante el PR 1, commit `0aa38fc`. En la misma etapa se corrigió la selección automática del parámetro avanzado de la interfaz; ese arreglo fue un hito de usabilidad, no una decisión arquitectónica ni un ajuste del detector.

### 2026-07-13: revisión manual persistente e indicadores

Se agregó persistencia JSON por semana ISO, decisión profesional separada de la categoría automática, evidencia para falsos negativos, control complementario e indicadores consultables en la aplicación. Las categorías no relevantes y descartadas quedaron ocultas en acordeones para una revisión complementaria voluntaria.

También se retiró el editor de configuración y se reservó el registro de cambios para un flujo específico y auditable. La implementación corresponde al commit `499d814` y está documentada en ADR-001, ADR-002 y `LOG-2026-07-13`.

### 2026-07-14: interfaz, política de datos y skills

La interfaz fue rediseñada con un sistema visual compacto y orientado a tareas, sin alterar los contratos funcionales. El cambio quedó en `79b59a7`; no se creó un ADR porque fue una evolución de presentación dentro de la arquitectura vigente.

Los JSON operativos reales fueron excluidos del repositorio, se agregó un ejemplo ficticio del esquema y se documentó la necesidad de respaldo separado. Esta decisión corresponde a ADR-003 y al commit `da72d1a`.

Se crearon dos skills globales de Codex, fuera del repositorio:

- `disenar-interfaces-operativas`, para reutilizar el sistema visual;
- `ajustar-keywords-bo-caba`, para modificar la configuración con evidencia, aprobación explícita, pruebas y registro en el log, sin generar un ADR por cada ajuste.

El repositorio conserva el contrato de uso del segundo skill en `README.md` y `AGENTS.md`; su implementación reside en el directorio global de skills del equipo.

## Mapa de decisiones y registros

| Tema | Documento |
| --- | --- |
| Sustitución del ML supervisado por reglas trazables | ADR-004 |
| Pipeline API por capas y revisión humana | ADR-005 |
| Aplicación local Flask para Windows | ADR-006 |
| Persistencia semanal y revisión manual | ADR-001 |
| Indicadores y gobernanza de configuración | ADR-002 |
| Separación de datos operativos y código | ADR-003 |
| Ajustes derivados de ejemplares o normas reales | `docs/seguimiento/log_ajustes.md` |

## Criterio para futuras reconstrucciones

Un cambio histórico sólo debe incorporarse al log cuando puedan identificarse la evidencia, el problema, la modificación y el resultado esperado. Un ADR retrospectivo debe expresar una decisión estructural todavía vigente y declarar su fecha original y la fecha de documentación. Los commits sin motivo recuperable permanecen en esta cronología como brechas explícitas.
