# ADR-002 - Indicadores de desempeño y gobernanza de la configuración

Estado: aceptado  
Fecha: 2026-07-13

## Contexto

El registro semanal definido en ADR-001 permite comparar la categoría automática original con la decisión profesional. Los conteos de actividad son necesarios, pero no alcanzan para evaluar si el detector reduce lectura sin perder trazabilidad ni para observar cómo se comportan las alertas automáticas y los casos derivados a revisión humana.

Al mismo tiempo, los ajustes de keywords y patrones modifican el comportamiento del detector. Mantener un editor libre dentro de la aplicación dificultaría reconstruir quién cambió un criterio, con qué evidencia y por qué.

## Opciones consideradas

1. Mostrar solamente conteos de eventos.
2. Incorporar métricas clásicas de clasificación, incluidos recall y F1.
3. Calcular indicadores operativos sobre las decisiones realmente registradas.
4. Mantener la configuración editable desde la interfaz.
5. Retirar el editor y aplicar los cambios mediante un skill específico con registro de motivos.

Recall y F1 son útiles cuando existe una verdad de referencia completa. En el uso diario inicial, las normas no relevantes y descartadas sólo se revisan de forma complementaria; por lo tanto, no puede afirmarse que todos los falsos negativos sean conocidos.

## Decisión

### Indicadores

Separar en la interfaz dos grupos:

- **volumen operativo**, para describir la actividad registrada;
- **indicadores de desempeño**, para relacionar la clasificación automática con las decisiones profesionales disponibles.

Calcular semanalmente:

- **Cobertura de validación:** decisiones profesionales registradas / normas procesadas.
- **Precisión automática:** normas originalmente `RELEVANTE` confirmadas / normas originalmente `RELEVANTE` validadas.
- **Tasa de falsos positivos:** normas originalmente `RELEVANTE` descartadas / normas originalmente `RELEVANTE` validadas.
- **Tasa de revisión manual:** normas originalmente `REVISION_MANUAL` / normas procesadas.
- **Rendimiento de revisión manual:** casos `REVISION_MANUAL` confirmados como relevantes / casos `REVISION_MANUAL` resueltos.
- **Reducción de lectura:** normas originalmente `NO_RELEVANTE` o `DESCARTADA_FILTRO_ESTRUCTURAL` / normas procesadas.

Cada indicador debe mostrar una descripción breve y su base de cálculo. Si el denominador no existe, el resultado es `N/D`.

No calcular recall ni F1 hasta contar con un universo revisado de forma suficientemente completa y controlada. La incorporación futura de estas métricas requerirá verificar la metodología y actualizar este ADR o crear uno nuevo.

### Revisión manual

- Usar casillas mutuamente excluyentes para registrar la decisión profesional.
- No solicitar observaciones opcionales en las decisiones ordinarias.
- Exigir evidencia breve sólo cuando se confirma un falso negativo.
- Mantener `NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL` ocultas en acordeones.
- Registrar el control complementario como pendiente, parcial o completo y confirmar visualmente el guardado.

### Configuración

- Retirar el editor de configuración de la interfaz.
- Mantener únicamente un resumen de solo lectura.
- Aplicar futuros cambios de keywords, patrones y organismos mediante un skill específico.
- Registrar en `docs/seguimiento/log_ajustes.md` la evidencia, el problema, el cambio y el resultado esperado.
- No modificar la configuración mediante la interfaz ni mediante ajustes informales sin trazabilidad.

## Consecuencias

- Los indicadores pueden consultarse dentro de la misma aplicación y se recalculan desde los JSON semanales.
- La precisión y la tasa de falsos positivos sólo representan los casos que recibieron decisión profesional.
- Una cobertura baja advierte que los porcentajes deben interpretarse con cautela.
- La reducción de lectura mide ahorro operativo, no exactitud semántica.
- El uso diario permitirá observar tendencias y decidir más adelante si corresponde establecer metas institucionales.
- La eliminación del editor agrega un paso al ajuste de configuración, pero mejora la auditabilidad.
- El skill de configuración queda como una etapa posterior y no forma parte de esta implementación.

## Riesgos y mitigaciones

- **Sesgo de validación:** pueden revisarse primero los casos más evidentes. Se muestra la cobertura y la base de cada tasa.
- **Confusión terminológica:** cada indicador incluye una definición visible y la documentación conserva la fórmula.
- **Falsa certeza sobre omisiones:** falsos negativos es `N/D` mientras el control complementario no esté completo y no haya casos confirmados.
- **Cambios no documentados:** la interfaz no permite editar la configuración y AGENTS.md exige el uso del skill y del log.

## Forma de verificación

- pruebas unitarias de denominadores y estados sin actividad;
- verificación de `N/D` cuando no existe base suficiente;
- comprobación en navegador de las descripciones, bases y porcentajes;
- comprobación de casillas mutuamente excluyentes;
- confirmación visible del guardado del control complementario;
- revisión periódica con datos de uso diario.

## Relación con otras decisiones

- [ADR-001 - Registro semanal y revisión manual persistente](ADR-001-registro-semanal-revision-manual.md)
