---
name: ajustar-keywords-bo-caba
description: >-
  Diagnosticar, proponer, comparar, aplicar, validar y documentar cambios
  auditables en las keywords, keywords condicionales, verbos de acción, normas
  curadas y organismos prioritarios del detector del Boletín Oficial CABA, y
  revisar estrategias de detección sobre un período de registros. Use when
  the assistant (Claude Code or Codex) works in the relevamiento_boletin_oficial_caba
  repository and the user asks to add, replace or remove a detection term or
  pattern, correct a false positive or an identified omission through
  configuration, tune manual-review routing, or review how terms performed in
  a period. Require evidence, a prior comparison against the stored records,
  explicit approval of the exact proposal, tests and an entry in
  docs/seguimiento/log_ajustes.md. Never create an ADR.
---

# Ajustar keywords del detector BO CABA

Aplicar cambios de configuración pequeños, trazables y basados en evidencia real. Preservar la lógica explícita del detector y evitar que una corrección puntual amplíe silenciosamente el universo de resultados.

El skill tiene dos modos:

- **Ajuste puntual:** el usuario aporta un caso (falso positivo, omisión identificada, variante no reconocida).
- **Revisión de estrategias:** el usuario pide analizar un período para proponer incorporaciones, modificaciones o retiros.

En ambos modos, toda propuesta pasa por la **comparación previa** y por la aprobación explícita de su ficha antes de tocar la configuración.

## Preparar el diagnóstico

1. Confirmar que el repositorio contiene:
   - `config/config_keywords.json`;
   - `bo_detector/classifier.py`;
   - `scripts/revisar_estrategias.py`;
   - `docs/seguimiento/log_ajustes.md`.
2. Leer el `AGENTS.md` vigente (en Claude Code se carga mediante `CLAUDE.md`) y ejecutar `git status -sb` antes de editar.
3. Leer completamente [references/criterios-configuracion.md](references/criterios-configuracion.md).
4. Inspeccionar el caso aportado y la implementación actual. No inferir el efecto de una lista solamente por su nombre.
5. En un ajuste puntual, reunir como mínimo:
   - ejemplar o período;
   - norma y sumario observados;
   - categoría obtenida;
   - decisión profesional o categoría esperada;
   - motivo bibliotecario o normativo del cambio.
6. Si falta evidencia esencial, solicitarla antes de proponer una modificación. No agregar términos sólo porque parezcan relacionados temáticamente.

## Revisión de estrategias

Usar cuando el usuario pide revisar el desempeño de los términos en un período.

1. Acordar el período (por defecto, todo el histórico) y ejecutar desde la raíz del repositorio:

   ```bat
   python scripts\revisar_estrategias.py terminos --desde AAAA-MM-DD --hasta AAAA-MM-DD
   ```

2. Leer el informe Markdown generado en `data/informes_estrategias/`. Presentar:
   - período, boletines y normas, con el reparto de la referencia profesional (relevantes, no relevantes por decisión, no relevantes según la lectura completa, sin información);
   - candidatos a revisión con su cantidad de casos y ejemplos: un 100 % no relevante es una señal para revisar, no una orden de retiro; 2 de 2 no equivale a 150 de 150;
   - términos que aportaron relevantes;
   - términos con coincidencias pero sin base de evaluación: no asignarles 0 % ni 100 %.
3. Distinguir **coincidencia** de **efecto**: la columna «Decide / sigue» indica cuántas normas dejarían la lista principal si se retira el término y cuántas seguirían por otra regla.
4. Proponer cambios concretos sólo con evidencia. Usar las omisiones identificadas para proponer mejoras de recuperación, sin inventar decisiones profesionales.
5. Tratar cada propuesta como un ajuste: comparación previa, ficha, aprobación y registro. Una aprobación de la revisión general no aprueba cambios concretos.

## Seleccionar el tipo correcto

Elegir una de estas áreas admitidas:

- `KEYWORDS`: frase temática suficiente por sí sola.
- `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`: frase amplia que sólo es suficiente con acción y contexto normativos; mantenerla también en `KEYWORDS`.
- `VERBOS_ACCION`: regex que reconoce una acción normativa y afecta keywords condicionales y revisión manual.
- `LISTA_NORMAS_CURADAS`: regex para una referencia normativa concreta.
- `LISTA_ORGANISMOS_PRIORIDAD`: nombre o sigla que deriva casos opacos a revisión manual cuando existe una señal adicional.

No modificar `PODERES_INCLUIDOS` ni `TIPOS_NORMA_INCLUIDOS`. Esos campos cambian el filtro estructural y están fuera del alcance del skill.

No modificar `bo_detector/classifier.py` ni `bo_detector/config.py`. Si el resultado esperado requiere cambiar lógica, esquema o categorías, detenerse y explicar que no es un ajuste de configuración. No crear un ADR ni proponerlo automáticamente.

## Comparación previa (obligatoria)

Antes de presentar la ficha, medir el efecto del cambio sobre los registros guardados. El script no modifica la configuración ni los JSON semanales.

1. Escribir la propuesta en `data/informes_estrategias/propuesta_AAAAMMDD_descripcion.json` (UTF-8):

   ```json
   {
     "descripcion": "Motivo breve",
     "cambios": [
       {"lista": "KEYWORDS", "operacion": "eliminar", "valor": "término"},
       {"lista": "KEYWORDS", "operacion": "agregar", "valor": "término nuevo"},
       {"lista": "LISTA_NORMAS_CURADAS", "operacion": "reemplazar", "valor": "regex actual", "nuevo": "regex nueva"}
     ]
   }
   ```

2. Ejecutar:

   ```bat
   python scripts\revisar_estrategias.py comparar --propuesta data\informes_estrategias\propuesta_AAAAMMDD_descripcion.json
   ```

3. Llevar a la ficha la tabla de efectos del informe: relevantes recuperadas, relevantes perdidas, irrelevantes evitadas o añadidas (por decisión y por lectura completa), normas sin información afectadas y cambios entre `RELEVANTE` y `REVISION_MANUAL`, con cantidades, porcentajes y bases.
4. Mostrar siempre por separado las relevantes perdidas. No compensarlas con un total neto.
5. Para retiros, informar cuántas normas siguen seleccionadas por otra regla: no atribuir al retiro una reducción que no produce.
6. Distinguir lo medido sobre el histórico del efecto esperado en boletines futuros.

## Preparar la ficha de cambio

Antes de editar, presentar:

1. **Evidencia:** ejemplar, norma, sumario y decisión profesional, o período e informe por término.
2. **Problema:** omisión identificada, falso positivo, exceso de revisión manual o variante no reconocida.
3. **Tipo de ajuste:** lista exacta y operación `agregar`, `reemplazar` o `eliminar`.
4. **Cambio exacto:** valor actual, si existe, y valor propuesto.
5. **Motivo:** por qué esa configuración representa correctamente el caso.
6. **Comparación previa:** tabla de efectos medidos, con bases explícitas y ejemplos.
7. **Controles:** caso positivo, caso negativo y registros históricos que conviene revisar.
8. **Archivos:** configuración, prueba específica y log.

Esperar aprobación explícita de esta ficha. Una autorización genérica anterior no sustituye la aprobación del valor exacto. Si la propuesta no se aprueba, no modificar la configuración ni los registros.

## Aplicar el cambio aprobado

1. Confirmar con `git status -sb` que `config/config_keywords.json` no tiene cambios previos sin registrar. Si los tiene, detenerse e informar.
2. Editar `config/config_keywords.json` con un parche mínimo.
3. Conservar UTF-8, indentación, orden de claves y orden relativo de los valores existentes.
4. Insertar una nueva entrada según la convención visible de la lista. No normalizar ni reordenar masivamente.
5. Tratar un reemplazo como una única modificación del valor existente, no como una limpieza general.
6. No crear ni versionar backups `config_keywords.backup_*.json`.
7. No modificar `data/seguimiento/*.json`. Leerlos sólo mediante el script o para un análisis histórico explícitamente necesario.
8. Agregar una prueba pequeña en `tests/test_classifier.py` o el archivo específico correspondiente:
   - reproducir el sumario real cuando sea posible;
   - verificar categoría y motivo de detección;
   - agregar un control negativo cuando exista riesgo de sobrecaptura.

## Validar

Ejecutar primero el validador incluido (desde la raiz del repositorio):

```bat
python .claude\skills\ajustar-keywords-bo-caba\scripts\validate_detector_config.py .
```

Después ejecutar:

```bat
python -m unittest discover -s tests
```

Si alguna validación falla, no registrar el cambio como favorable ni ofrecer commit. Corregir dentro del alcance aprobado o informar el bloqueo.

## Fallo al guardar o registrar

Nunca dejar una configuración modificada sin su registro. Si la validación no puede corregirse dentro del alcance aprobado, o si falla la escritura del log:

1. Revertir la configuración al estado registrado: `git checkout -- config/config_keywords.json` (sólo es seguro porque el paso 1 de «Aplicar» confirmó que no había cambios previos).
2. Retirar la prueba agregada para ese cambio.
3. Verificar con `git status -sb` que la configuración quedó sin cambios.
4. Informar la causa y el estado final.

## Registrar en el log

Después de superar las validaciones, agregar una entrada append-only a `docs/seguimiento/log_ajustes.md` usando la plantilla de la referencia.

Registrar siempre:

- evidencia y problema;
- lista, operación y valor anterior y nuevo exactos;
- justificación;
- resultado de la comparación previa (período, efectos y bases) e informe utilizado;
- efecto esperado;
- pruebas ejecutadas y resultado;
- período futuro de revisión;
- `ADR: no corresponde`.

Las propuestas no aprobadas no se registran en el log: quedan sólo en `data/informes_estrategias/`. El log contiene únicamente cambios aplicados.

No crear ni modificar archivos en `docs/adr/`. La creación o actualización del skill tampoco constituye un ajuste del detector y no genera una entrada en el log.

## Seguimiento de un ajuste anterior

Para completar «Revisar resultado» de una entrada del log, ejecutar el informe por término sobre los boletines **posteriores** a la fecha del ajuste y comparar el desempeño del valor modificado. Indicar período y base. Distinguir la comparación sobre un conjunto fijo de las variaciones debidas a boletines nuevos. No fijar metas ni periodicidad no acordadas.

## Cerrar el trabajo

1. Revisar `git diff --check`, el diff de los archivos tocados y `git status -sb`.
2. Confirmar que no se mezclaron datos reales, cambios de lógica ni ediciones ajenas. Los informes de `data/informes_estrategias/` no se versionan.
3. Informar el resultado, las pruebas y los riesgos residuales.
4. Indicar que la aplicación debe reiniciarse para cargar la configuración:

```bat
stop_desktop.bat
run_desktop.bat
```

5. Pedir al usuario que recargue `http://127.0.0.1:7862/`.
6. Preguntar si desea registrar y subir los cambios. No hacer commit ni push sin confirmación explícita.
