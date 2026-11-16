# Detector de normativa relevante del Boletín Oficial CABA

Aplicación local para asistir el relevamiento diario de normativa del Boletín Oficial de la Ciudad de Buenos Aires vinculada con arquitectura, urbanismo, construcción, habilitaciones, ambiente, catastro, ejercicio profesional y temas afines al servicio de referencia especializada de la Biblioteca CPAU.

Este repositorio es una evolución operativa de [`boletin-oficial-caba-ml`](https://github.com/Juan-Draghi/boletin-oficial-caba-ml), que exploraba un pipeline de aprendizaje supervisado con TF-IDF + SVM.

## Enfoque vigente

La proporción histórica de normas relevantes es muy baja respecto del total publicado. En las pruebas del proyecto anterior, el modelo supervisado tendía a reproducir una búsqueda por palabras clave sin aportar una mejora estable que justificara su complejidad.

La versión actual utiliza un procedimiento más simple, trazable y mantenible:

- reglas explícitas;
- normalización de texto;
- palabras clave curadas;
- patrones regex de normas relevantes;
- organismos y siglas prioritarias;
- revisión profesional de casos relevantes, dudosos y posibles omisiones.

No se utiliza aprendizaje supervisado como componente del detector.

## Categorías de salida

Cada norma recibe una categoría automática original:

- `RELEVANTE`: presenta una señal suficiente de interés.
- `REVISION_MANUAL`: caso indirecto u opaco que requiere decisión profesional.
- `NO_RELEVANTE`: pasó el filtro estructural, pero no presenta señales suficientes.
- `DESCARTADA_FILTRO_ESTRUCTURAL`: quedó excluida por poder o tipo de norma.

La categoría automática se conserva aunque posteriormente se registre una decisión manual o cambie la configuración.

## Fuente de datos

La fuente principal es la API del Boletín Oficial CABA:

```text
GET /obtenerBoletin/{parametro}/true
```

El parámetro puede ser:

- `0`: último boletín publicado;
- `dd-mm-aaaa`: boletín de una fecha específica;
- número de boletín: consulta directa por número.

La fecha utilizada para el registro es la fecha de publicación informada por el ejemplar.

## Pipeline de detección

### 1. Filtro estructural

Se consideran los poderes y tipos de norma definidos en `config/config_keywords.json`.

### 2. Detección directa

Una norma se clasifica como `RELEVANTE` si el sumario contiene:

- una expresión de `KEYWORDS`; o
- una referencia que coincide con `LISTA_NORMAS_CURADAS`.

Las búsquedas usan texto normalizado para reducir problemas por mayúsculas, acentos y variantes Unicode.

### 3. Keywords condicionales

Algunas expresiones amplias, como las vinculadas con espacio público, requieren contexto de acción normativa. Esto evita marcar permisos individuales como relevantes y permite detectar cambios generales en las reglas.

### 4. Revisión manual

Una norma se deriva a `REVISION_MANUAL` cuando no fue relevante por detección directa y combina:

- un organismo o una sigla de `LISTA_ORGANISMOS_PRIORIDAD`; y
- una acción normativa o una referencia normativa opaca cuyo objeto no puede determinarse con seguridad.

La aplicación no descarga ni interpreta automáticamente el texto completo para resolver estos casos.

## Aplicación de escritorio

La aplicación Flask está pensada para el uso diario en Windows. Permite:

- consultar el último boletín publicado;
- consultar ejemplares retrospectivos desde un calendario;
- ingresar un número de boletín u otro parámetro admitido;
- revisar las normas `RELEVANTE` y `REVISION_MANUAL`;
- guardar una decisión profesional por norma mediante casillas de selección;
- desplegar `NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL` únicamente para registrar omisiones identificadas;
- indicar si el control complementario está pendiente, parcial o completo; al marcarlo como completo, la aplicación avisa si quedan alertas sin decisión;
- consultar volumen operativo e indicadores de desempeño en una pestaña separada;
- consultar un resumen de la configuración en modo de solo lectura.

La interfaz no incluye observaciones opcionales. Sólo se solicita una evidencia breve cuando una norma originalmente no relevante o descartada se confirma como relevante.

## Registro operativo

Cada consulta se guarda en un archivo JSON UTF-8 por semana ISO, de lunes a domingo:

```text
data/seguimiento/AAAA-WNN.json
```

El registro conserva:

- ejemplar y fecha de publicación;
- normas deduplicadas;
- categoría automática original;
- decisión profesional;
- evidencia de las omisiones identificadas cuando corresponde;
- estado del control complementario.

Una consulta repetida actualiza el mismo ejemplar y no vuelve a sumar sus normas. Los indicadores se calculan desde los registros guardados; no se persisten totales derivados.

Los JSON semanales contienen datos operativos reales y no se versionan en el repositorio de código. Permanecen en el equipo dentro de `data/seguimiento` y deben incluirse en una política de respaldo separada. La sincronización de Google Drive no reemplaza por sí sola ese respaldo.

El archivo versionado `data/seguimiento/ejemplo_seguimiento.json` documenta el esquema con datos ficticios. Los indicadores se recalculan siempre desde los JSON locales reales.

### Decisiones manuales

- `SIN_REVISAR`: todavía no existe una decisión profesional.
- `RELEVANTE_CONFIRMADA`: la relevancia fue confirmada.
- `NO_RELEVANTE_CONFIRMADA`: la norma fue descartada por la revisión profesional.

Un caso de `REVISION_MANUAL` confirmado como relevante no es una omisión. Sólo son omisiones identificadas las normas originalmente `NO_RELEVANTE` o `DESCARTADA_FILTRO_ESTRUCTURAL` luego confirmadas como relevantes.

## Indicadores semanales y por período

La pestaña Indicadores permite consultar una semana o un período de fechas (desde/hasta, o todo el histórico). En un período, cada norma se cuenta una sola vez aunque se haya publicado en varios boletines, y los porcentajes se calculan sobre los totales del período, sin promediar semanas. Si el período no tiene registros, se informa así en lugar de mostrar ceros.

La pestaña organiza los datos en tres niveles (ver ADR-007).

### Indicadores principales

- **Relevantes confirmadas:** normas confirmadas como relevantes, cualquiera sea su categoría automática original.
- **Omisiones identificadas:** normas originalmente `NO_RELEVANTE` o `DESCARTADA_FILTRO_ESTRUCTURAL` confirmadas como relevantes.
- **% de omisiones identificadas:** omisiones identificadas sobre todas las relevantes confirmadas. Es «No calculable» si no hay relevantes confirmadas y «provisional» si algún boletín no tiene control completo o quedan alertas sin decisión. Mide omisiones identificadas entre las normas que ingresaron a la aplicación; no mide normas que nunca ingresaron.
- **% de alertas automáticas descartadas:** alertas originalmente `RELEVANTE` descartadas sobre las alertas `RELEVANTE` con decisión registrada.

### Indicadores secundarios

- **Normas procesadas:** normas distintas incorporadas al registro.
- **Normas con decisión registrada:** decisiones profesionales sobre el total procesado. No equivale al porcentaje del boletín leído.
- **Derivación a revisión manual:** casos `REVISION_MANUAL` sobre el total procesado.
- **Rendimiento de la revisión manual:** casos confirmados como relevantes sobre casos de revisión manual resueltos.

### Datos complementarios

En una sección plegada: días de uso, alertas automáticas, casos de revisión manual, relevantes desde revisión manual, precisión automática (complemento del porcentaje de alertas descartadas), **normas excluidas de la selección principal** (`NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL` sobre el total procesado, sin atribuirle ahorro de lectura) y estado del control complementario.

### Avisos de consistencia

La pestaña avisa si hay alertas sin decisión, boletines marcados como completos con alertas sin decisión o normas repetidas con decisiones distintas en distintos boletines. Los avisos no modifican los registros.

La interfaz muestra una descripción y la base utilizada para cada porcentaje. Cuando no existe un denominador suficiente, informa `N/D` o «No calculable».

No se calculan recall ni F1 porque requieren un universo completamente revisado. Podrán evaluarse cuando el uso diario produzca una base de verdad suficientemente completa y controlada.

## Configuración y trazabilidad

El archivo central es:

```text
config/config_keywords.json
```

Contiene:

- `PODERES_INCLUIDOS`;
- `TIPOS_NORMA_INCLUIDOS`;
- `KEYWORDS`;
- `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`;
- `VERBOS_ACCION`;
- `LISTA_NORMAS_CURADAS`;
- `LISTA_ORGANISMOS_PRIORIDAD`.

La configuración ya no se edita desde la aplicación. Los cambios se realizan mediante el skill `ajustar-keywords-bo-caba` (versionado en `.claude/skills/`; se invoca como `/ajustar-keywords-bo-caba` en Claude Code o `$ajustar-keywords-bo-caba` en Codex), que exige evidencia, presenta el ajuste exacto antes de aplicarlo, valida la configuración y las pruebas, y registra la justificación en `docs/seguimiento/log_ajustes.md`. Este flujo no genera ADR.

## Revisión de estrategias

El script `scripts/revisar_estrategias.py` analiza los registros guardados para revisar los términos del detector. **Sólo lee:** no modifica la configuración ni los JSON semanales. Vuelve a clasificar en memoria las normas guardadas.

```bat
python scripts\revisar_estrategias.py terminos
python scripts\revisar_estrategias.py terminos --desde 2026-07-13 --hasta 2026-09-30
python scripts\revisar_estrategias.py comparar --propuesta data\informes_estrategias\propuesta.json
```

- **terminos:** para cada keyword, norma curada y organismo prioritario informa cuántas coincidencias tuvo en el período, cómo se reparten entre relevantes, no relevantes y sin información, si el término decide la selección o la norma seguiría seleccionada por otra regla, y ejemplos. Marca como candidatos a revisión los términos cuyas coincidencias evaluables resultaron todas no relevantes.
- **comparar:** aplica en memoria una propuesta de cambios y compara la selección vigente con la propuesta sobre los mismos boletines: relevantes recuperadas y perdidas, irrelevantes evitadas y añadidas, normas sin información afectadas y cambios entre `RELEVANTE` y `REVISION_MANUAL`.

Referencia profesional usada: decisión registrada; las normas ocultas sin marca de boletines con control completo cuentan como «no relevantes según la lectura completa» (dato separado); el resto, como «sin información». «Seleccionada» significa `RELEVANTE` o `REVISION_MANUAL`.

Los informes (Markdown y CSV) se guardan en `data/informes_estrategias/`, carpeta excluida de Git porque contiene sumarios reales. El skill `ajustar-keywords-bo-caba` usa este script como comparación previa obligatoria de todo ajuste.

La evidencia mínima para proponer el retiro o la restricción de un término (al menos 30 casos evaluados sin relevantes, ciclo anual completo para términos estacionales) está definida en [criterio_evidencia_keywords.md](docs/seguimiento/criterio_evidencia_keywords.md).

## Instalación

Requisitos:

- Windows;
- Python 3.11 o superior;
- conexión a internet para consultar la API.

Desde la carpeta del proyecto:

```bat
install_desktop.bat
```

## Uso

Para iniciar la aplicación:

```bat
run_desktop.bat
```

La interfaz se abre en:

```text
http://127.0.0.1:7862/
```

Para detenerla:

```bat
stop_desktop.bat
```

Para crear un acceso directo en el Escritorio:

```bat
crear_acceso_directo_escritorio.bat
```

Después de modificar código o configuración, detener y volver a iniciar la aplicación.

## Estructura principal

```text
relevamiento_boletin_oficial_caba/
├── bo_detector/
│   ├── api.py                  # Cliente de la API
│   ├── classifier.py           # Reglas de clasificación
│   ├── flatten.py              # Aplanamiento del payload
│   ├── review_store.py         # Persistencia e indicadores
│   ├── strategy_review.py      # Revisión de estrategias (solo lectura)
│   └── text.py                 # Normalización textual
├── config/
│   └── config_keywords.json    # Parámetros curados
├── data/seguimiento/           # Datos locales y ejemplo de esquema
├── desktop_app/
│   ├── app.py                  # Aplicación Flask y endpoints
│   ├── static/app.js           # Interacciones de la interfaz
│   ├── static/styles.css       # Estilos de la interfaz
│   └── templates/index.html    # Estructura de la interfaz
├── docs/                       # Documentación, ADR y log
├── scripts/
│   └── revisar_estrategias.py  # Informes por término y comparación de propuestas
├── tests/                      # Pruebas unitarias
├── install_desktop.bat
├── run_desktop.bat
├── run_desktop_silencioso.vbs
├── stop_desktop.bat
└── crear_acceso_directo_escritorio.bat
```

## Pruebas

Ejecutar:

```bat
python -m unittest discover -s tests
```

La suite cubre el detector, la persistencia semanal, deduplicación, decisiones manuales, omisiones identificadas, control complementario, indicadores y endpoints de la aplicación.

## Documentación

- [Historial de evolución del detector](docs/historial_evolucion.md)
- [Registro operativo e indicadores](docs/seguimiento/registro_operativo.md)
- [Log de ajustes derivados](docs/seguimiento/log_ajustes.md)
- [Criterio de evidencia mínima para revisar keywords](docs/seguimiento/criterio_evidencia_keywords.md)
- [ADR-001: registro semanal y revisión manual](docs/adr/ADR-001-registro-semanal-revision-manual.md)
- [ADR-002: indicadores y gobernanza de configuración](docs/adr/ADR-002-indicadores-y-gobernanza-configuracion.md)
- [ADR-003: datos operativos fuera del repositorio de código](docs/adr/ADR-003-datos-operativos-fuera-del-repositorio.md)
- [ADR-004: reglas trazables en lugar de aprendizaje supervisado](docs/adr/ADR-004-reglas-trazables-en-lugar-de-ml-supervisado.md)
- [ADR-005: pipeline API por capas y revisión humana](docs/adr/ADR-005-pipeline-api-por-capas-y-revision-humana.md)
- [ADR-006: aplicación local Flask para uso diario](docs/adr/ADR-006-aplicacion-local-flask-para-uso-diario.md)

## Limitaciones

La herramienta no reemplaza la revisión profesional. Su objetivo es reducir el volumen de lectura y hacer más consistente la detección inicial.

Los indicadores describen el desempeño observado sobre las decisiones registradas. Durante la etapa inicial deben interpretarse como métricas operativas en construcción y revisarse con el uso diario antes de establecer objetivos institucionales.

No se reconstruyen datos históricos sin evidencia y no se modifica retroactivamente la categoría automática original.

## Autor

Juan Draghi — Biblioteca CPAU, Consejo Profesional de Arquitectura y Urbanismo.

## Uso de herramientas de IA

El diseño metodológico, la implementación del código, la depuración del pipeline y la redacción de la documentación fueron desarrollados con asistencia de ChatGPT / Codex de OpenAI.

Las decisiones de alcance, los criterios de relevancia, la curaduría de palabras clave, la validación de resultados y la orientación bibliotecaria del proyecto fueron definidos por el autor.

## Licencia

MIT.
