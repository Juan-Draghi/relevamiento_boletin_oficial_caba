# ADR-001 - Registro semanal y revisión manual persistente

Estado: aceptado; la política de versionado fue sustituida por ADR-003
Fecha: 2026-07-13

## Contexto y evidencia

La aplicación calculaba conteos por consulta, pero los mantenía únicamente en memoria. No existía una exportación operativa, una forma de registrar decisiones profesionales por norma ni un control de consultas repetidas.

Los indicadores acordados necesitan conservar la categoría automática original y compararla con la decisión profesional. Esta comparación permite distinguir relevantes confirmadas, casos surgidos de REVISION_MANUAL y falsos negativos.

## Opciones consideradas

1. Registro manual en Markdown.
2. Una fila semanal en CSV.
3. Un único archivo JSON acumulativo.
4. Un archivo JSON por semana, consultado por la aplicación.

Markdown y CSV son sencillos, pero no permiten reabrir las decisiones por norma desde la interfaz sin procesamiento adicional. Un único JSON crecería de manera continua y aumentaría el impacto de una escritura defectuosa.

## Decisión

Utilizar un JSON por semana ISO, de lunes a domingo, dentro de `data/seguimiento`.

Cada archivo conserva:

- ejemplares identificados por número o fecha;
- normas identificadas por `id_norma`, `id_sdin` o una huella estable;
- categoría automática original;
- decisión manual separada de la clasificación;
- evidencia breve únicamente cuando se confirma un falso negativo;
- estado del control complementario;
- ajustes derivados y observaciones semanales reservados para el skill de configuracion.

Los indicadores se calculan desde los registros guardados y no se duplican como totales persistidos.

Las normas NO_RELEVANTE y DESCARTADA_FILTRO_ESTRUCTURAL permanecen ocultas en acordeones. Sólo se despliegan cuando la revisión profesional necesita registrar un falso negativo.

La interfaz de configuración se retira. El resumen de configuración permanece en modo de solo lectura.

Las observaciones opcionales para decisiones ordinarias y para el cierre del ejemplar se descartan. El registro adicional se limita a la evidencia necesaria para documentar un falso negativo.

Los ajustes derivados y sus motivos no se cargan desde la pestaña Indicadores. Se registran mediante el skill de configuración para mantener un procedimiento uniforme y trazable.

## Consecuencias y riesgos

- Una consulta repetida no vuelve a sumar las mismas normas.
- La fecha del indicador es la fecha de publicación del ejemplar.
- La categoría original no cambia al reprocesar un ejemplar.
- Los JSON son legibles, pero los archivos operativos reales no se versionan junto con el código según ADR-003.
- No se reconstruyen períodos anteriores sin evidencia.
- Una futura modificación del esquema requerirá una nueva versión y, si cambia las definiciones, un ADR adicional.

## Forma de verificación

- pruebas de consultas repetidas y normas duplicadas;
- semanas sin actividad;
- controles pendientes, parciales y completos;
- falsos negativos con evidencia obligatoria;
- preservación de decisiones al reprocesar;
- validación de UTF-8 y JSON;
- revisión de `git diff --check` y de la suite completa.

## Relación con otras decisiones

- [ADR-002 - Indicadores de desempeño y gobernanza de la configuración](ADR-002-indicadores-y-gobernanza-configuracion.md)
- [ADR-003 - Datos operativos fuera del repositorio de código](ADR-003-datos-operativos-fuera-del-repositorio.md)
