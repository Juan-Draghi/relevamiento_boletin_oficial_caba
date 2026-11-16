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
7. Indicar si el control complementario fue pendiente, parcial o completo. Al marcarlo como completo, la aplicación avisa si quedan normas RELEVANTE o REVISION_MANUAL sin decisión y lista cuáles son. Se puede volver a revisar o guardar igual como completo. Las normas de los acordeones no generan aviso, porque no requieren una decisión individual.
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

Dentro de una semana o de un período, cada clave se cuenta una sola vez, en el primer boletín en que aparece. Por eso el total de un período puede ser menor que la suma de sus semanas: una norma publicada varios días seguidos (por ejemplo, un llamado a concurso) se computa una vez. El número de boletín identifica el ejemplar; si falta, se utiliza su fecha de publicación.

## Indicadores

- **Período:** lunes a domingo de la semana seleccionada, o un rango de fechas de publicación (desde/hasta) elegido en la vista Período. El rango puede abarcar varias semanas o cortar una semana.
- **Cálculo por período:** los porcentajes se calculan con su fórmula sobre los totales del período; nunca se promedian porcentajes semanales.
- **Cobertura:** si el período no tiene boletines registrados se informa «Sin registros en el período seleccionado», no ceros. Si el rango empieza antes del primer registro o termina después del último, se avisa.
- **Normas repetidas:** cada norma se cuenta una vez, en su primera aparición, pero se usa la decisión registrada en cualquiera de sus copias. Si las copias tienen decisiones distintas, se usa la más reciente y se avisa la contradicción.
- **Días de uso:** fechas de publicación distintas incorporadas al registro.
- **Normas procesadas:** registros únicos guardados.
- **Alertas automáticas:** categoría automática original RELEVANTE.
- **Casos de REVISION_MANUAL:** categoría automática original REVISION_MANUAL.
- **Relevantes confirmadas:** decisiones RELEVANTE_CONFIRMADA, cualquiera sea la categoría original.
- **Relevantes surgidas de REVISION_MANUAL:** categoría original REVISION_MANUAL y decisión RELEVANTE_CONFIRMADA.
- **Omisiones identificadas:** categoría original NO_RELEVANTE o DESCARTADA_FILTRO_ESTRUCTURAL y decisión RELEVANTE_CONFIRMADA.
- **% de omisiones identificadas:** omisiones identificadas sobre relevantes confirmadas. «No calculable» sin relevantes confirmadas; «provisional» si algún boletín no tiene control completo o quedan alertas sin decisión.
- **% de alertas automáticas descartadas:** alertas RELEVANTE descartadas sobre alertas RELEVANTE con decisión.
- **Control complementario:** completo cuando todos los ejemplares están completos; parcial cuando existe control parcial o una combinación de estados; N/D cuando todos siguen pendientes; No utilizado cuando no hay ejemplares.
- **Normas con decisión registrada:** decisiones profesionales registradas sobre el total procesado (antes «cobertura de validación»).
- **Precisión automática:** relevantes automáticas confirmadas sobre alertas automáticas con decisión; complemento del porcentaje de alertas descartadas.
- **Derivación a revisión manual:** casos REVISION_MANUAL sobre el total procesado.
- **Rendimiento de la revisión manual:** relevantes confirmadas entre los casos REVISION_MANUAL resueltos.
- **Normas excluidas de la selección principal:** NO_RELEVANTE y DESCARTADA_FILTRO_ESTRUCTURAL sobre el total procesado (antes «reducción de lectura»). No mide ahorro efectivo de lectura.

La interfaz acompaña cada indicador con una descripción breve y la base utilizada para calcularlo, y avisa sobre alertas sin decisión, boletines completos con pendientes y decisiones contradictorias.

## Gobernanza de la configuración

Los ajustes derivados y sus motivos no forman parte de la carga ordinaria ni se editan desde la pestaña Indicadores. Deben aplicarse mediante `$ajustar-keywords-bo-caba` y registrarse en `docs/seguimiento/log_ajustes.md`. El skill exige aprobación del cambio exacto, validación y pruebas, y no crea ADR.

## Convenciones

- `0`: la métrica fue controlada y no hubo casos.
- `N/D`: la métrica no pudo determinarse.
- Las tasas de precisión, falsos positivos y rendimiento manual se informan como `N/D` cuando no existen decisiones suficientes para formar el denominador.
- `No utilizado`: no se registró actividad.
- `No calculable`: el porcentaje de omisiones no tiene relevantes confirmadas como base.
- `provisional`: el porcentaje de omisiones puede cambiar porque la revisión del alcance no está cerrada.
- Un 0 % de omisiones identificadas no garantiza ausencia de omisiones reales.
- Un caso de REVISION_MANUAL confirmado como relevante no es una omisión.
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
- Las omisiones identificadas requieren una observación breve como evidencia.
- Las decisiones ordinarias y el control complementario no solicitan observaciones opcionales.

## Decisiones relacionadas

- [ADR-001 - Registro semanal y revisión manual persistente](../adr/ADR-001-registro-semanal-revision-manual.md)
- [ADR-002 - Indicadores de desempeño y gobernanza de la configuración](../adr/ADR-002-indicadores-y-gobernanza-configuracion.md)
- [ADR-003 - Datos operativos fuera del repositorio de código](../adr/ADR-003-datos-operativos-fuera-del-repositorio.md)
