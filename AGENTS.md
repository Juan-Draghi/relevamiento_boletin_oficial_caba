# AGENTS.md

Instrucciones para asistentes tecnicos que trabajen en este repositorio.

## Contexto del proyecto

Este repositorio contiene una aplicacion local para detectar normativa relevante del Boletin Oficial CABA para el servicio de referencia especializada de la Biblioteca CPAU.

El proyecto es una evolucion del enfoque anterior basado en ML/TDS+SVM. No reintroducir aprendizaje supervisado salvo pedido explicito del usuario. La decision vigente es usar reglas trazables, configuracion editable y revision manual, porque la proporcion historica de positivos es muy baja y el modelo supervisado terminaba funcionando como una busqueda de palabras clave.

## Objetivo operativo

La herramienta debe ayudar a revisar boletines diarios y retrospectivos, reduciendo el volumen de lectura y dejando visibles los casos relevantes o dudosos.

Categorias de salida:

- `RELEVANTE`
- `REVISION_MANUAL`
- `NO_RELEVANTE`
- `DESCARTADA_FILTRO_ESTRUCTURAL`

## Criterios vigentes del detector

- Si una keyword de `KEYWORDS` aparece en el sumario, la norma es `RELEVANTE`.
- Si una referencia coincide con `LISTA_NORMAS_CURADAS`, la norma es `RELEVANTE`.
- Algunas keywords amplias, como las vinculadas con espacio publico, requieren contexto de accion normativa para evitar permisos individuales irrelevantes.
- Una norma va a `REVISION_MANUAL` cuando no fue relevante por Capa 1, pero combina:
  - organismo, sigla en nombre o sigla en sumario perteneciente a `LISTA_ORGANISMOS_PRIORIDAD`;
  - verbo de accion normativa o referencia normativa opaca, cuando el objeto no queda suficientemente claro.
- Si una norma contiene una keyword suficiente y contexto de accion normativa cuando corresponde, debe clasificarse como `RELEVANTE`, no como `REVISION_MANUAL`.
- No usar longitud de sumario como disparador de revision manual. `UMBRAL_TOKENS_OPACO` fue descartado.
- No descargar ni interpretar automaticamente texto completo para resolver casos opacos. La decision se deja a revision humana.

## Archivos principales

- `bo_detector/api.py`: cliente de la API del Boletin Oficial CABA.
- `bo_detector/flatten.py`: aplanamiento del payload de la API.
- `bo_detector/classifier.py`: reglas de clasificacion.
- `bo_detector/config.py`: carga y validacion de configuracion.
- `bo_detector/text.py`: normalizacion y busqueda textual.
- `config/config_keywords.json`: parametros curados.
- `desktop_app/app.py`: aplicacion Flask local.
- `desktop_app/templates/index.html`: interfaz.
- `desktop_app/static/styles.css`: estilos.
- `tests/`: pruebas unitarias.

## Configuracion

El archivo `config/config_keywords.json` es parte central del proyecto. Contiene:

- `PODERES_INCLUIDOS`
- `TIPOS_NORMA_INCLUIDOS`
- `KEYWORDS`
- `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`
- `VERBOS_ACCION`
- `LISTA_NORMAS_CURADAS`
- `LISTA_ORGANISMOS_PRIORIDAD`

Precauciones:

- No borrar ni reordenar listas sin una razon operativa.
- Si se ajusta una regex de `LISTA_NORMAS_CURADAS`, validar que compile.
- Los patrones de leyes deben contemplar variantes con y sin punto de miles, por ejemplo `6\.?927`.
- Los cambios de configuracion deben commitearse cuando responden a un ajuste real de deteccion.
- La app puede generar backups `config/config_keywords.backup_*.json`; no versionarlos.

## Aplicacion de escritorio

Scripts de uso:

- `install_desktop.bat`: instala dependencias.
- `run_desktop.bat`: inicia la app.
- `run_desktop_silencioso.vbs`: lanzador sin consola visible.
- `stop_desktop.bat`: cierra la app.
- `crear_acceso_directo_escritorio.bat`: crea acceso directo en el Escritorio.

La app corre en:

```text
http://127.0.0.1:7862/
```

Si se modifica codigo o configuracion y la app ya esta abierta, indicar siempre al usuario que debe reiniciarla para aplicar los cambios. Acompanar la indicacion con estos pasos:

```bat
stop_desktop.bat
run_desktop.bat
```

Luego pedir que abra o recargue:

```text
http://127.0.0.1:7862/
```

## Pruebas

Antes de commitear cambios de logica o configuracion, ejecutar:

```bat
python -m unittest discover -s tests
```

Cuando se corrige un falso negativo o falso positivo, agregar una prueba especifica si es posible. Preferir tests pequenos que reproduzcan el sumario real y el resultado esperado.

## Flujo de trabajo con Git

Antes de modificar o commitear:

```bat
git status -sb
```

No mezclar cambios de logica con cambios de listas si pueden separarse.

Despues de cada cambio funcional, de configuracion o documentacion, preguntar al usuario si desea registrar y subir los cambios a GitHub. No hacer commit ni push sin confirmacion explicita.

Mensajes recomendados:

- `Actualizar listados de configuracion`
- `Ajustar patrones de normas curadas`
- `Detectar siglas prioritarias en normas opacas`
- `Corregir falso positivo de espacio publico`

Despues de validar:

```bat
git add <archivos>
git commit -m "<mensaje>"
git push origin main
```

Si el usuario pide crear un PR, abrirlo como draft salvo que indique lo contrario. Si luego pide "ejecutar el PR", interpretar la accion como marcar el PR listo para revision y fusionarlo en la rama base, siempre verificando antes que el PR corresponda a los cambios ya validados.

## Estilo de implementacion

- Priorizar Python simple y mantenible.
- Evitar sobreingenieria.
- Mantener reglas explicitas y auditables.
- Explicar cambios en lenguaje claro.
- Preservar la orientacion bibliotecaria del proyecto.
- No afirmar que algo esta resuelto sin prueba o verificacion.

## Consideraciones de codificacion

El proyecto corre en Windows y rutas de Google Drive. Tener cuidado con:

- codificacion Unicode en PowerShell;
- acentos y variantes Unicode;
- normalizacion de texto;
- permisos de Google Drive;
- procesos Flask viejos escuchando en el puerto `7862`.

Para pruebas manuales desde shell, si aparecen caracteres `?` en acentos, usar strings sin acentos o escapes Unicode.
