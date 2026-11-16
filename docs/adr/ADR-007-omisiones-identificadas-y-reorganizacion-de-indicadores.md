# ADR-007 - Omisiones identificadas y reorganización de indicadores

Estado: aceptado  
Fecha: 2026-11-16

## Contexto

ADR-002 definió seis indicadores semanales y excluyó recall y F1 porque no existe un universo completamente revisado. El uso diario mostró dos necesidades:

- algunos nombres resultaban confusos: «Reducción de lectura» sugería un ahorro efectivo de lectura y «Cobertura de validación» podía leerse como porcentaje del boletín leído;
- faltaba una medida de las omisiones que la lectura complementaria del boletín encuentra entre las normas descartadas por el detector.

La aplicación registra una decisión para todas las alertas `RELEVANTE` y `REVISION_MANUAL`. Las omisiones se identifican al leer el boletín y se confirman como relevantes dentro de los acordeones `NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL`. No se exige una decisión individual sobre cada norma oculta.

Además, una misma norma puede publicarse en varios boletines. La decisión se guarda en la copia del boletín donde se registró, pero el cálculo tomaba la primera aparición. Una omisión marcada en una aparición posterior podía no contarse.

## Decisión

### Indicador de omisiones identificadas

- **Cantidad:** normas originalmente `NO_RELEVANTE` o `DESCARTADA_FILTRO_ESTRUCTURAL` confirmadas como relevantes. Los casos `REVISION_MANUAL` confirmados no son omisiones de la selección presentada.
- **Porcentaje:** omisiones identificadas / todas las relevantes confirmadas del mismo universo y período × 100. El denominador incluye relevantes automáticas, de revisión manual y omisiones recuperadas.
- **No calculable:** cuando no hay relevantes confirmadas. Nunca se muestra 0 % por falta de base.
- **Provisional:** cuando algún boletín del alcance no tiene control complementario `COMPLETO` o cuando quedan alertas `RELEVANTE` o `REVISION_MANUAL` sin decisión. El control completo no se toma por sí solo como garantía de que todas las decisiones estén registradas.
- **Límite:** mide omisiones identificadas entre las normas que ingresaron a la aplicación. No mide normas que nunca ingresaron ni garantiza la ausencia de omisiones no detectadas.

Este indicador no es recall. Recall y F1 siguen excluidos en los términos de ADR-002.

### Terminología

Se adopta «omisiones identificadas» en lugar de «falsos negativos» en la interfaz y la documentación, para dejar explícito que sólo se cuentan las omisiones encontradas por la revisión profesional.

### Presentación

- **Principales:** relevantes confirmadas; cantidad y porcentaje de omisiones identificadas; porcentaje de alertas automáticas descartadas tras la validación profesional. Este último usa como base las alertas originalmente `RELEVANTE` con decisión registrada y se destaca por sobre la precisión automática, que es su complemento.
- **Secundarios:** normas procesadas; normas con decisión registrada (antes «Cobertura de validación», misma fórmula, con aclaración de que no equivale al porcentaje del boletín leído); derivación a revisión manual; rendimiento de la revisión manual.
- **Datos complementarios, en una sección plegada:** días de uso, alertas automáticas, casos de revisión manual, relevantes desde revisión manual, precisión automática, normas excluidas de la selección principal (antes «Reducción de lectura», sin atribuirle ahorro de lectura) y estado del control complementario.

No se eliminan datos ni cálculos existentes.

### Consistencia y normas repetidas

- Cada norma se cuenta una vez, en su primera aparición, pero se usa la decisión registrada en cualquiera de sus copias.
- Si las copias tienen decisiones distintas, se usa la más reciente y se informa la contradicción.
- La pestaña Indicadores avisa sobre alertas sin decisión, boletines completos con alertas sin decisión y decisiones contradictorias.
- Los avisos sólo informan: no modifican los JSON semanales.

## Consecuencias

- El porcentaje de omisiones puede aparecer como provisional aunque todos los boletines estén completos, mientras quede alguna alerta sin decidir.
- La corrección de normas repetidas no cambió ningún valor del histórico disponible al 2026-11-16, pero evita perder omisiones marcadas en apariciones posteriores.
- Las claves técnicas del cálculo (`cobertura_validacion`, `reduccion_lectura`, etc.) se conservan; cambian los nombres visibles.

## Forma de verificación

- pruebas automatizadas con los ejemplos de aceptación: 2 omisiones de 20 relevantes = 10 %; el mismo caso con control parcial, provisional; sin relevantes, No calculable; 0 % con control pendiente, provisional;
- prueba de omisión marcada en la segunda aparición de una norma repetida;
- prueba de decisiones contradictorias;
- comparación de los valores semanales del histórico antes y después del cambio;
- comprobación en navegador sobre una copia temporal de los registros.

## Relación con otras decisiones

- Actualiza la presentación y la terminología de [ADR-002](ADR-002-indicadores-y-gobernanza-configuracion.md), sin modificar su exclusión de recall y F1.
- [ADR-001 - Registro semanal y revisión manual persistente](ADR-001-registro-semanal-revision-manual.md)
