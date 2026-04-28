# Detector de normativa relevante del Boletin Oficial CABA

Aplicacion local para asistir el relevamiento diario de normativa del Boletin Oficial de la Ciudad de Buenos Aires vinculada con arquitectura, urbanismo, construccion, habilitaciones, ambiente, catastro, ejercicio profesional y temas afines al servicio de referencia especializada de la Biblioteca CPAU.

Este repositorio es una evolucion operativa de [`boletin-oficial-caba-ml`](https://github.com/Juan-Draghi/boletin-oficial-caba-ml), que exploraba un pipeline de aprendizaje supervisado con TF-IDF + SVM para detectar normativa relevante.

## Por que cambio el enfoque

El proyecto anterior demostro que el problema era relevante y que podia abordarse con automatizacion. Sin embargo, durante las pruebas operativas aparecio una limitacion estructural: la cantidad de normas verdaderamente relevantes para arquitectura, urbanismo y construccion es muy baja respecto del total publicado en cada boletin.

En la practica, el porcentaje de positivos era inferior al 3%. Con esa distribucion, el dataset disponible no permitia sostener un modelo supervisado robusto: los reentrenamientos agregaban ejemplos, pero el clasificador tendia a devolver principalmente coincidencias de palabras clave y no aportaba una mejora estable en la determinacion de relevancia.

Por ese motivo, esta version abandona el enfoque ML/TDS+SVM como componente central y adopta una arquitectura mas simple, trazable y mantenible:

- reglas explicitas,
- normalizacion de texto,
- palabras clave curadas,
- patrones regex de normas relevantes,
- organismos prioritarios,
- revision manual para casos opacos.

La decision es pragmatica: para un flujo bibliotecario de baja frecuencia positiva, una herramienta transparente y editable resulta mas util que un modelo dificil de entrenar, explicar y mantener.

## Que hace

La aplicacion consulta la API del Boletin Oficial CABA, procesa las normas publicadas y clasifica cada registro en categorias operativas:

- `RELEVANTE`: normas que deben revisarse o incorporarse al seguimiento.
- `REVISION_MANUAL`: casos indirectos u opacos que requieren decision humana.
- `NO_RELEVANTE`: normas que pasan el filtro estructural pero no tienen senales suficientes.
- `DESCARTADA_FILTRO_ESTRUCTURAL`: registros excluidos por poder o tipo de norma.

El criterio principal es deliberadamente sensible: si una keyword relevante aparece en el sumario, la norma se considera relevante. Esto responde a una caracteristica de la fuente: los sumarios son breves y, cuando mencionan terminos como habilitacion, catastro o impacto ambiental, esa mencion suele ser significativa.

## Fuente de datos

La fuente principal es la API del Boletin Oficial CABA:

```text
GET /obtenerBoletin/{parametro}/true
```

El parametro puede ser:

- `0`: ultimo boletin publicado.
- `dd-mm-aaaa`: boletin de una fecha especifica.
- numero de boletin: consulta directa por numero.

## Pipeline de deteccion

### 1. Filtro estructural

Se consideran solamente los poderes y tipos de norma definidos en `config/config_keywords.json`.

Ejemplos de tipos incluidos:

- Ley
- Ley de Aprobacion Inicial
- Decreto
- Decreto de Necesidad y Urgencia
- Resolucion
- Disposicion
- Aclaracion

### 2. Deteccion directa

Una norma se clasifica como `RELEVANTE` si el sumario contiene:

- una keyword de `KEYWORDS`, o
- una referencia que coincide con `LISTA_NORMAS_CURADAS`.

Las busquedas se realizan con texto normalizado para reducir problemas por mayusculas, acentos y variantes Unicode.

### 3. Keywords condicionales

Algunas expresiones, como las vinculadas con espacio publico, requieren contexto normativo adicional. Esto evita marcar como relevantes los permisos individuales de uso del espacio publico, pero permite detectar cambios en las reglas que regulan esos permisos.

### 4. Revision manual

Los casos opacos se derivan a `REVISION_MANUAL` cuando:

- el organismo pertenece a `LISTA_ORGANISMOS_PRIORIDAD`,
- el sumario contiene verbos de accion normativa,
- y hay una referencia normativa, pero el objeto no queda suficientemente claro.

La aplicacion no intenta resolver estos casos leyendo automaticamente el texto completo. Los muestra para revision experta.

## Aplicacion de escritorio

El proyecto incluye una aplicacion local en Flask pensada para uso diario en Windows.

Permite:

- consultar el ultimo boletin publicado;
- consultar boletines retrospectivos desde un calendario;
- ingresar un parametro avanzado, como numero de boletin;
- ver metricas del procesamiento;
- revisar normas detectadas;
- editar desde la interfaz:
  - `KEYWORDS`,
  - `LISTA_NORMAS_CURADAS`,
  - `LISTA_ORGANISMOS_PRIORIDAD`;
- crear backups automaticos antes de guardar cambios de configuracion;
- crear un acceso directo en el Escritorio.

## Instalacion

Requisitos:

- Windows
- Python 3.11 o superior
- conexion a internet para consultar la API

Desde la carpeta del proyecto, ejecutar:

```bat
install_desktop.bat
```

Esto instala las dependencias de la aplicacion local.

## Uso

Para abrir la aplicacion:

```bat
run_desktop.bat
```

La app se abre en:

```text
http://127.0.0.1:7862/
```

Para cerrarla:

```bat
stop_desktop.bat
```

Para crear un acceso directo en el Escritorio:

```bat
crear_acceso_directo_escritorio.bat
```

## Configuracion

El archivo principal de parametros es:

```text
config/config_keywords.json
```

Contiene:

- `PODERES_INCLUIDOS`
- `TIPOS_NORMA_INCLUIDOS`
- `KEYWORDS`
- `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`
- `VERBOS_ACCION`
- `LISTA_NORMAS_CURADAS`
- `LISTA_ORGANISMOS_PRIORIDAD`

Las listas `KEYWORDS` y `LISTA_ORGANISMOS_PRIORIDAD` se muestran ordenadas alfabeticamente en la interfaz. Al guardar cambios, la aplicacion genera una copia de respaldo en la carpeta `config`.

## Estructura del repositorio

```text
relevamiento_boletin_oficial_caba/
├── bo_detector/                 # Motor de consulta, normalizacion y clasificacion
├── config/                      # Parametros editables del detector
├── desktop_app/                 # Aplicacion local Flask
├── docs/                        # Documentacion tecnica y materiales de trabajo
├── tests/                       # Pruebas unitarias
├── install_desktop.bat          # Instalacion de dependencias
├── run_desktop.bat              # Ejecucion de la app local
├── run_desktop_silencioso.vbs   # Lanzador sin consola visible
├── stop_desktop.bat             # Cierre de la app local
└── crear_acceso_directo_escritorio.bat
```

## Pruebas

Para ejecutar las pruebas:

```bat
python -m unittest discover -s tests
```

Las pruebas cubren:

- normalizacion de texto;
- filtro estructural;
- deteccion por keywords;
- deteccion por normas curadas;
- casos de revision manual;
- exclusion de falsos positivos frecuentes;
- aplanamiento del payload de la API.

## Limitaciones

La herramienta no reemplaza la revision profesional. Su funcion es reducir el volumen de lectura diaria y hacer mas consistente la deteccion inicial.

El rendimiento depende de la calidad de los parametros curados. Por eso el flujo esperado es iterativo: revisar resultados reales, detectar falsos positivos o falsos negativos y ajustar las listas.

## Autor

Juan Draghi - Biblioteca CPAU, Consejo Profesional de Arquitectura y Urbanismo.

## Licencia

MIT.
