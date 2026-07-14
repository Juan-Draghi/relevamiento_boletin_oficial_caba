# ADR-003 - Datos operativos fuera del repositorio de código

Estado: aceptado
Fecha: 2026-07-14

## Contexto

La aplicación guarda cada ejemplar analizado y las decisiones profesionales en
`data/seguimiento/AAAA-WNN.json`. El primer uso diario completo incorporó cientos de
normas y varios miles de líneas en una sola ejecución.

El ADR-001 definió correctamente el JSON semanal como formato de persistencia, pero
dejó esos archivos dentro del control de versiones. Esa decisión mezcla dos ciclos
distintos:

- el código y la documentación cambian mediante desarrollos deliberados;
- los datos operativos cambian con cada análisis y cada decisión profesional.

Git es útil para revisar cambios de código, pero no debe actuar como base de datos ni
como mecanismo principal de respaldo de información operativa mutable.

## Decisión

Mantener los JSON semanales reales en `data/seguimiento`, pero fuera del seguimiento
de Git.

La política queda definida así:

1. `data/seguimiento/*.json` se excluye mediante `.gitignore`.
2. `data/seguimiento/ejemplo_seguimiento.json` es la única excepción versionada y
   documenta el esquema con datos ficticios.
3. Un JSON que ya estuviera versionado se retira únicamente del índice con
   `git rm --cached`; el archivo local no se elimina ni se modifica.
4. Los indicadores continúan calculándose desde los JSON locales. No se persisten ni
   versionan totales derivados.
5. Las pruebas manuales y de navegador usan copias temporales y verifican su
   eliminación.
6. La sincronización de Google Drive aporta disponibilidad, pero no reemplaza una
   política de respaldo. Se recomienda conservar además una copia periódica en una
   ubicación controlada distinta del directorio de trabajo.

## Consecuencias

- Los commits quedan limitados a código, configuración y documentación.
- Se evitan miles de líneas de ruido y conflictos por escrituras automáticas.
- Las decisiones profesionales no se publican automáticamente junto con el código.
- Clonar el repositorio no restaura los datos operativos; éstos deben recuperarse
  desde el respaldo correspondiente.
- La aplicación puede crear el directorio y los archivos semanales normalmente,
  aunque Git los ignore.
- Los JSON incluidos en commits anteriores permanecen en el historial. Eliminarlos
  del historial requeriría una operación destructiva y coordinada, fuera del alcance
  de esta decisión.

## Verificación

- `git check-ignore data/seguimiento/AAAA-WNN.json` debe confirmar la exclusión.
- El ejemplo sanitizado debe seguir visible para Git y ser JSON UTF-8 válido.
- El hash del archivo operativo local debe ser igual antes y después de retirarlo del
  índice.
- La suite de pruebas debe continuar utilizando directorios temporales.

## Relación con otras decisiones

- Sustituye únicamente la política de versionado de datos del
  [ADR-001](ADR-001-registro-semanal-revision-manual.md).
- No modifica las definiciones de indicadores del
  [ADR-002](ADR-002-indicadores-y-gobernanza-configuracion.md).
