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
- desplegar `NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL` únicamente para registrar posibles falsos negativos;
- indicar si el control complementario está pendiente, parcial o completo;
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
- evidencia de falsos negativos cuando corresponde;
- estado del control complementario.

Una consulta repetida actualiza el mismo ejemplar y no vuelve a sumar sus normas. Los indicadores se calculan desde los registros guardados; no se persisten totales derivados.

Los JSON semanales contienen datos operativos reales y no se versionan en el repositorio de código. Permanecen en el equipo dentro de `data/seguimiento` y deben incluirse en una política de respaldo separada. La sincronización de Google Drive no reemplaza por sí sola ese respaldo.

El archivo versionado `data/seguimiento/ejemplo_seguimiento.json` documenta el esquema con datos ficticios. Los indicadores se recalculan siempre desde los JSON locales reales.

### Decisiones manuales

- `SIN_REVISAR`: todavía no existe una decisión profesional.
- `RELEVANTE_CONFIRMADA`: la relevancia fue confirmada.
- `NO_RELEVANTE_CONFIRMADA`: la norma fue descartada por la revisión profesional.

Un caso de `REVISION_MANUAL` confirmado como relevante no es un falso negativo. Sólo son falsos negativos las normas originalmente `NO_RELEVANTE` o `DESCARTADA_FILTRO_ESTRUCTURAL` luego confirmadas como relevantes.

## Indicadores semanales

La pestaña Indicadores separa dos grupos.

### Volumen operativo

- días de uso;
- normas procesadas;
- relevantes automáticas;
- casos de revisión manual;
- relevantes confirmadas;
- relevantes surgidas de revisión manual;
- falsos negativos;
- estado del control complementario.

### Desempeño del detector

- **Cobertura de validación:** decisiones profesionales registradas sobre el total procesado.
- **Precisión automática:** alertas automáticas confirmadas como relevantes sobre alertas automáticas validadas.
- **Tasa de falsos positivos:** alertas automáticas descartadas sobre alertas automáticas validadas.
- **Tasa de revisión manual:** casos `REVISION_MANUAL` sobre el total procesado.
- **Rendimiento de revisión manual:** casos confirmados como relevantes sobre casos de revisión manual resueltos.
- **Reducción de lectura:** normas `NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL` sobre el total procesado.

La interfaz muestra una descripción y la base utilizada para cada porcentaje. Cuando no existe un denominador suficiente, informa `N/D`.

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

La configuración ya no se edita desde la aplicación. Los cambios se realizan mediante `$ajustar-keywords-bo-caba`, que exige evidencia, presenta el ajuste exacto antes de aplicarlo, valida la configuración y las pruebas, y registra la justificación en `docs/seguimiento/log_ajustes.md`. Este flujo no genera ADR.

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

La suite cubre el detector, la persistencia semanal, deduplicación, decisiones manuales, falsos negativos, control complementario, indicadores y endpoints de la aplicación.

## Documentación

- [Registro operativo e indicadores](docs/seguimiento/registro_operativo.md)
- [Log de ajustes derivados](docs/seguimiento/log_ajustes.md)
- [ADR-001: registro semanal y revisión manual](docs/adr/ADR-001-registro-semanal-revision-manual.md)
- [ADR-002: indicadores y gobernanza de configuración](docs/adr/ADR-002-indicadores-y-gobernanza-configuracion.md)
- [ADR-003: datos operativos fuera del repositorio de código](docs/adr/ADR-003-datos-operativos-fuera-del-repositorio.md)

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
