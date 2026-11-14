# CLAUDE.md

Las instrucciones del proyecto se mantienen en un unico archivo compartido por Codex y Claude Code:

@AGENTS.md

## Notas especificas de Claude Code

- El skill de ajuste de configuracion esta versionado en `.claude/skills/ajustar-keywords-bo-caba/` y se invoca como `/ajustar-keywords-bo-caba` (equivalente a `$ajustar-keywords-bo-caba` en Codex).
- `.claude/settings.json` bloquea la edicion de los JSON semanales reales de `data/seguimiento/`. No eludir esa regla.
- Si se modifica una regla del proyecto, editar `AGENTS.md`, no este archivo.
