---
name: ajustar-keywords-bo-caba
description: >-
  Diagnosticar, proponer, aplicar, validar y documentar cambios auditables en
  las keywords, keywords condicionales, verbos de acción, normas curadas y
  organismos prioritarios del detector del Boletín Oficial CABA. Use when
  the assistant (Claude Code or Codex) works in the relevamiento_boletin_oficial_caba repository and the user
  asks to add, replace or remove a detection term or pattern, correct a false
  positive or false negative through configuration, or tune manual-review
  routing. Require evidence, explicit approval of the exact proposal, tests
  and an entry in docs/seguimiento/log_ajustes.md. Never create an ADR.
---

# Ajustar keywords del detector BO CABA

Aplicar cambios de configuración pequeños, trazables y basados en evidencia real. Preservar la lógica explícita del detector y evitar que una corrección puntual amplíe silenciosamente el universo de resultados.

## Preparar el diagnóstico

1. Confirmar que el repositorio contiene:
   - `config/config_keywords.json`;
   - `bo_detector/classifier.py`;
   - `docs/seguimiento/log_ajustes.md`.
2. Leer el `AGENTS.md` vigente (en Claude Code se carga mediante `CLAUDE.md`) y ejecutar `git status -sb` antes de editar.
3. Leer completamente [references/criterios-configuracion.md](references/criterios-configuracion.md).
4. Inspeccionar el caso aportado y la implementación actual. No inferir el efecto de una lista solamente por su nombre.
5. Reunir, como mínimo:
   - ejemplar o período;
   - norma y sumario observados;
   - categoría obtenida;
   - decisión profesional o categoría esperada;
   - motivo bibliotecario o normativo del cambio.
6. Si falta evidencia esencial, solicitarla antes de proponer una modificación. No agregar términos sólo porque parezcan relacionados temáticamente.

## Seleccionar el tipo correcto

Elegir una de estas áreas admitidas:

- `KEYWORDS`: frase temática suficiente por sí sola.
- `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`: frase amplia que sólo es suficiente con acción y contexto normativos; mantenerla también en `KEYWORDS`.
- `VERBOS_ACCION`: regex que reconoce una acción normativa y afecta keywords condicionales y revisión manual.
- `LISTA_NORMAS_CURADAS`: regex para una referencia normativa concreta.
- `LISTA_ORGANISMOS_PRIORIDAD`: nombre o sigla que deriva casos opacos a revisión manual cuando existe una señal adicional.

No modificar `PODERES_INCLUIDOS` ni `TIPOS_NORMA_INCLUIDOS`. Esos campos cambian el filtro estructural y están fuera del alcance del skill.

No modificar `bo_detector/classifier.py` ni `bo_detector/config.py`. Si el resultado esperado requiere cambiar lógica, esquema o categorías, detenerse y explicar que no es un ajuste de configuración. No crear un ADR ni proponerlo automáticamente.

## Preparar la ficha de cambio

Antes de editar, presentar:

1. **Evidencia:** ejemplar, norma, sumario y decisión profesional.
2. **Problema:** falso negativo, falso positivo, exceso de revisión manual o variante no reconocida.
3. **Tipo de ajuste:** lista exacta y operación `agregar`, `reemplazar` o `eliminar`.
4. **Cambio exacto:** valor actual, si existe, y valor propuesto.
5. **Motivo:** por qué esa configuración representa correctamente el caso.
6. **Impacto esperado:** clasificación buscada y posibles efectos colaterales.
7. **Controles:** caso positivo, caso negativo y registros históricos que conviene revisar.
8. **Archivos:** configuración, prueba específica y log.

Esperar aprobación explícita de esta ficha. Una autorización genérica anterior no sustituye la aprobación del valor exacto.

## Aplicar el cambio aprobado

1. Editar `config/config_keywords.json` con un parche mínimo.
2. Conservar UTF-8, indentación, orden de claves y orden relativo de los valores existentes.
3. Insertar una nueva entrada según la convención visible de la lista. No normalizar ni reordenar masivamente.
4. Tratar un reemplazo como una única modificación del valor existente, no como una limpieza general.
5. No crear ni versionar backups `config_keywords.backup_*.json`.
6. No leer ni modificar `data/seguimiento/*.json` salvo para un análisis histórico explícitamente necesario y siempre de solo lectura.
7. Agregar una prueba pequeña en `tests/test_classifier.py` o el archivo específico correspondiente:
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

## Registrar en el log

Después de superar las validaciones, agregar una entrada append-only a `docs/seguimiento/log_ajustes.md` usando la plantilla de la referencia.

Registrar siempre:

- evidencia y problema;
- lista, operación y valor exactos;
- justificación;
- efecto esperado;
- pruebas ejecutadas y resultado;
- período futuro de revisión;
- `ADR: no corresponde`.

No crear ni modificar archivos en `docs/adr/`. La creación del skill tampoco constituye un ajuste del detector y no genera una entrada en el log.

## Cerrar el trabajo

1. Revisar `git diff --check`, el diff de los archivos tocados y `git status -sb`.
2. Confirmar que no se mezclaron datos reales, cambios de lógica ni ediciones ajenas.
3. Informar el resultado, las pruebas y los riesgos residuales.
4. Indicar que la aplicación debe reiniciarse para cargar la configuración:

```bat
stop_desktop.bat
run_desktop.bat
```

5. Pedir al usuario que recargue `http://127.0.0.1:7862/`.
6. Preguntar si desea registrar y subir los cambios. No hacer commit ni push sin confirmación explícita.
