# ADR-005 - Pipeline API por capas y revisión humana

Estado: aceptado

Fecha de la decisión original: 2026-04-28

Documentado retrospectivamente: 2026-07-14

## Contexto y evidencia

Una vez descartado el enfoque supervisado, era necesario convertir los criterios bibliotecarios en un proceso simple y verificable que pudiera ejecutarse sobre ejemplares diarios y retrospectivos del Boletín Oficial CABA.

El sumario funciona como una señal editorial densa: cuando contiene una keyword suficiente o una referencia normativa curada, la norma debe considerarse relevante sin aplicar un puntaje. Al mismo tiempo, el boletín contiene poderes, tipos de norma, permisos individuales y referencias opacas que requieren tratamientos distintos para reducir ruido sin ocultar casos dudosos.

La prueba del 2026-04-28 con el BO 7355 mostró que un filtro estructural y las keywords condicionales reducían de forma material el volumen de lectura. La prueba con el BO 7275 permitió incorporar el tipo `Aclaración`. Estas decisiones quedaron consolidadas en el commit `fa15f55` y sus pruebas.

## Opciones consideradas

1. Procesar todo el texto completo de cada norma.
2. Aplicar una única lista de keywords a todos los registros.
3. Usar la API y un pipeline por capas, reservando los casos opacos para revisión humana.

La descarga e interpretación automática del texto completo aumentaba tiempo, fallas y complejidad sin una necesidad demostrada. Una lista plana no diferenciaba señales suficientes, expresiones contextuales, estructura documental ni organismos prioritarios.

## Decisión

Utilizar la API del Boletín Oficial CABA como fuente principal y ejecutar las siguientes capas:

1. aplanar y normalizar el payload sin perder los valores originales;
2. descartar poderes y tipos fuera de alcance mediante configuración explícita;
3. clasificar como `RELEVANTE` las coincidencias suficientes de keywords o normas curadas;
4. exigir contexto de acción normativa para keywords amplias definidas como condicionales;
5. derivar a `REVISION_MANUAL` los casos no relevantes por detección directa que combinan un organismo o sigla prioritaria con un verbo de acción normativa o una referencia normativa opaca;
6. conservar como `NO_RELEVANTE` los registros sin señales suficientes;
7. no descargar ni interpretar automáticamente el texto completo para resolver opacidad.

La búsqueda textual se realiza sobre texto normalizado para contemplar mayúsculas, acentos, espacios y variantes Unicode. El motivo conserva la señal reconocible para facilitar la auditoría.

## Consecuencias

- El orden de las capas es parte del comportamiento funcional y debe mantenerse cubierto por pruebas.
- El filtro estructural reduce el volumen antes de aplicar reglas semánticas.
- Las normas curadas y keywords suficientes producen relevancia directa.
- Las expresiones amplias pueden configurarse con un requisito adicional de acción normativa.
- Los casos que no pueden resolverse con seguridad permanecen visibles para decisión profesional.
- El sistema depende de la estabilidad de la API y de una configuración curada.
- Los cambios concretos de listas o patrones no requieren un ADR; deben seguir el skill de configuración y registrarse en el log cuando respondan a evidencia real.

## Forma de verificación

- pruebas unitarias por capa y precedencia;
- reproducción de casos reales que motivan ajustes;
- validación de regex al cargar la configuración;
- pruebas del cliente API y del aplanamiento;
- ejecución de la suite completa antes de integrar cambios;
- seguimiento de decisiones manuales e indicadores definidos en ADR-001 y ADR-002.

## Fuentes históricas

- hilo `019dd44f-f333-7c22-b47c-3c73353d905d`;
- BO 7355 y BO 7275, analizados el 2026-04-28;
- commit `fa15f55`;
- `docs/pipeline_v2_diseño.md`;
- `docs/propuesta_parametros_desde_compilaciones.md`.

## Relación con otras decisiones

- [ADR-004 - Reglas trazables en lugar de aprendizaje supervisado](ADR-004-reglas-trazables-en-lugar-de-ml-supervisado.md)
- [ADR-006 - Aplicación local Flask para uso diario](ADR-006-aplicacion-local-flask-para-uso-diario.md)
- [ADR-001 - Registro semanal y revisión manual persistente](ADR-001-registro-semanal-revision-manual.md)
- [ADR-002 - Indicadores de desempeño y gobernanza de la configuración](ADR-002-indicadores-y-gobernanza-configuracion.md)
