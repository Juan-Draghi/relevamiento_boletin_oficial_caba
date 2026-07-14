# ADR-006 - Aplicación local Flask para uso diario

Estado: aceptado

Fecha de la decisión original: 2026-04-28

Documentado retrospectivamente: 2026-07-14

## Contexto y evidencia

El detector debía ser utilizable por personal bibliotecario en Windows sin ejecutar manualmente comandos de Python ni editar parámetros en el código para cada consulta. También debía admitir el último ejemplar publicado, fechas retrospectivas y parámetros avanzados de la API.

La aplicación era de uso local, con un único puesto o equipo de trabajo, y no requería autenticación, despliegue público ni una infraestructura de servidor. Ya existía una referencia funcional en otro proyecto de relevamiento del Boletín Oficial.

## Opciones consideradas

1. Mantener únicamente scripts de línea de comandos.
2. Crear una aplicación de escritorio empaquetada con un framework gráfico nativo.
3. Ejecutar una aplicación Flask local y abrirla en el navegador, acompañada por lanzadores de Windows.

La línea de comandos era menos accesible para el uso diario. Un empaquetado nativo agregaba complejidad de distribución y mantenimiento sin aportar una ventaja necesaria para este alcance.

## Decisión

Implementar una aplicación Flask local que:

- se ejecute en `http://127.0.0.1:7862/`;
- permita consultar el último boletín, una fecha específica o un parámetro avanzado;
- presente resultados y motivos de clasificación en una interfaz web;
- utilice scripts `.bat` y un lanzador `.vbs` para instalar, iniciar y detener la aplicación;
- mantenga la lógica del detector en módulos Python separados de la interfaz;
- no requiera un servicio remoto ni una base de datos para el alcance actual.

La primera versión incluyó un editor de configuración. Esa parte de la decisión fue sustituida el 2026-07-13 por ADR-002: la interfaz actual sólo muestra un resumen y los cambios se realizan mediante un flujo auditable.

Las posteriores mejoras visuales no alteran esta arquitectura y no requieren ADR independientes mientras conserven los endpoints, estados y contratos funcionales.

## Consecuencias

- El uso diario se realiza desde un navegador conocido, con una instalación liviana.
- La aplicación depende de un proceso Flask local y de que el puerto 7862 esté disponible.
- Después de cambios de código o configuración es necesario reiniciar el proceso.
- Los procesos antiguos pueden conservar código previo si no se detienen correctamente.
- La separación entre detector e interfaz facilita probar la lógica sin abrir el navegador.
- Un futuro despliegue multiusuario, autenticado o remoto requerirá reconsiderar esta decisión.

## Forma de verificación

- pruebas unitarias y de endpoints;
- validación manual en `127.0.0.1:7862`;
- pruebas de los tres modos de consulta;
- comprobación de los lanzadores en Windows;
- reinicio completo después de modificar código o configuración;
- verificación visual sin modificar datos operativos reales.

## Fuentes históricas

- hilo `019dd44f-f333-7c22-b47c-3c73353d905d`;
- commit `fa15f55`;
- scripts `install_desktop.bat`, `run_desktop.bat`, `run_desktop_silencioso.vbs` y `stop_desktop.bat`;
- `desktop_app/`.

## Relación con otras decisiones

- [ADR-005 - Pipeline API por capas y revisión humana](ADR-005-pipeline-api-por-capas-y-revision-humana.md)
- [ADR-001 - Registro semanal y revisión manual persistente](ADR-001-registro-semanal-revision-manual.md)
- [ADR-002 - Indicadores de desempeño y gobernanza de la configuración](ADR-002-indicadores-y-gobernanza-configuracion.md)
