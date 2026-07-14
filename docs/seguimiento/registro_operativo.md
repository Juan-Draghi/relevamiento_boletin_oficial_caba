# Registro operativo e indicadores semanales

## Objetivo

Registrar el uso real del detector, las decisiones profesionales sobre cada norma y los indicadores semanales sin reconstruir datos históricos ni duplicar consultas.

## Entradas

- respuesta de la API del Boletín Oficial CABA;
- categoría automática original asignada por el detector;
- decisión manual registrada en la interfaz;
- estado del control complementario;

## Salidas

La aplicación genera un archivo por semana ISO, de lunes a domingo:

```text
data/seguimiento/AAAA-WNN.json
```

La fecha utilizada es la fecha de publicación del ejemplar. No se generan registros para semanas que todavía no fueron utilizadas.

## Proceso

1. Consultar un ejemplar desde la pestaña Relevamiento.
2. La aplicación aplana, clasifica y deduplica las normas.
3. El ejemplar se incorpora al JSON de la semana correspondiente.
4. Una consulta repetida actualiza el mismo ejemplar y no suma nuevamente sus normas.
5. Revisar las normas RELEVANTE y REVISION_MANUAL.
6. Si la revisión profesional encuentra una omisión, abrir el acordeón NO_RELEVANTE o DESCARTADA_FILTRO_ESTRUCTURAL y confirmar la norma como relevante.
7. Indicar si el control complementario fue pendiente, parcial o completo.
8. Consultar los resultados agregados en la pestaña Indicadores.

## Decisiones manuales

- `SIN_REVISAR`: no hay decisión profesional registrada.
- `RELEVANTE_CONFIRMADA`: la revisión profesional confirmó la relevancia.
- `NO_RELEVANTE_CONFIRMADA`: la revisión profesional descartó la relevancia.

La categoría automática original se conserva aunque la configuración cambie posteriormente.

## Identidad y duplicados

La clave de una norma se construye en este orden:

1. `id_norma`;
2. `id_sdin`;
3. huella estable de los metadatos de la norma.

Dentro de una semana, cada clave se cuenta una sola vez. El número de boletín identifica el ejemplar; si falta, se utiliza su fecha de publicación.

## Indicadores

- **Período:** lunes a domingo de la semana seleccionada.
- **Días de uso:** fechas de publicación distintas incorporadas al registro.
- **Normas procesadas:** registros únicos guardados.
- **Clasificadas como RELEVANTE:** categoría automática original RELEVANTE.
- **Casos de REVISION_MANUAL:** categoría automática original REVISION_MANUAL.
- **Relevantes confirmadas en total:** decisiones RELEVANTE_CONFIRMADA, cualquiera sea la categoría original.
- **Relevantes surgidas de REVISION_MANUAL:** categoría original REVISION_MANUAL y decisión RELEVANTE_CONFIRMADA.
- **Falsos negativos:** categoría original NO_RELEVANTE o DESCARTADA_FILTRO_ESTRUCTURAL y decisión RELEVANTE_CONFIRMADA.
- **Control complementario:** completo cuando todos los ejemplares están completos; parcial cuando existe control parcial o una combinación de estados; N/D cuando todos siguen pendientes; No utilizado cuando no hay ejemplares.
- **Cobertura de validación:** decisiones profesionales registradas sobre el total procesado.
- **Precisión automática:** relevantes automáticas confirmadas sobre alertas automáticas validadas.
- **Tasa de falsos positivos:** alertas automáticas descartadas sobre alertas automáticas validadas.
- **Tasa de revisión manual:** casos REVISION_MANUAL sobre el total procesado.
- **Rendimiento de revisión manual:** relevantes confirmadas entre los casos REVISION_MANUAL resueltos.
- **Reducción de lectura:** NO_RELEVANTE y DESCARTADA_FILTRO_ESTRUCTURAL sobre el total procesado.

La interfaz acompaña cada indicador de desempeño con una descripción breve y la base utilizada para calcularlo.

## Gobernanza de la configuración

Los ajustes derivados y sus motivos no forman parte de la carga ordinaria ni se editan desde la pestaña Indicadores. Deben aplicarse mediante `$ajustar-keywords-bo-caba` y registrarse en `docs/seguimiento/log_ajustes.md`. El skill exige aprobación del cambio exacto, validación y pruebas, y no crea ADR.

## Convenciones

- `0`: la métrica fue controlada y no hubo casos.
- `N/D`: la métrica no pudo determinarse.
- Las tasas de precisión, falsos positivos y rendimiento manual se informan como `N/D` cuando no existen decisiones suficientes para formar el denominador.
- `No utilizado`: no se registró actividad.
- Si no se detectaron falsos negativos, el valor sólo puede ser `0` cuando el control complementario está completo.
- Si el control es parcial o está pendiente y no se detectaron casos, falsos negativos se informa como `N/D`.
- Un caso de REVISION_MANUAL confirmado como relevante no es un falso negativo.
- No se reconstruyen métricas históricas sin evidencia.

## Dependencias

La persistencia utiliza únicamente la biblioteca estándar de Python y archivos JSON UTF-8. No requiere bases de datos ni servicios externos adicionales.

## Riesgos y controles

- Los archivos JSON semanales contienen datos operativos reales y no forman parte del repositorio de código.
- `data/seguimiento/*.json` está excluido por Git; la única excepción es `ejemplo_seguimiento.json`, que contiene datos ficticios y documenta el esquema.
- Si un archivo real ya estuviera versionado, se retira solo del índice con `git rm --cached` y se verifica que el archivo local permanezca intacto.
- La sincronización de Google Drive no reemplaza una política de respaldo; se recomienda una copia periódica adicional en otra ubicación controlada.
- Una edición manual incorrecta del JSON puede invalidar el archivo; la aplicación valida el esquema al leerlo.
- Los archivos se escriben primero con extensión temporal y luego se reemplazan, para reducir el riesgo de corrupción.
- La categoría original y la decisión manual se preservan al repetir una consulta.
- Los falsos negativos requieren una observación breve como evidencia.
- Las decisiones ordinarias y el control complementario no solicitan observaciones opcionales.

## Decisiones relacionadas

- [ADR-001 - Registro semanal y revisión manual persistente](../adr/ADR-001-registro-semanal-revision-manual.md)
- [ADR-002 - Indicadores de desempeño y gobernanza de la configuración](../adr/ADR-002-indicadores-y-gobernanza-configuracion.md)
- [ADR-003 - Datos operativos fuera del repositorio de código](../adr/ADR-003-datos-operativos-fuera-del-repositorio.md)
