# Log de ajustes derivados

Este archivo registra exclusivamente cambios motivados por la evaluación de resultados reales. No corresponde crear una entrada por cada ejecución ni convertir cada keyword en un ADR.

## LOG-2026-07-13 - Incorporación de revisión manual e indicadores

**Evidencia**

- Período: inicio de seguimiento operativo en `2026-W29`.
- Norma o conjunto de casos: ejemplar BO 7406, con 310 normas procesadas durante la validación funcional.
- Resultado observado: los conteos de una consulta no permitían conservar decisiones profesionales, identificar falsos negativos ni evaluar el comportamiento del detector a lo largo del tiempo.

**Problema detectado**

- Descripción: la aplicación mostraba la clasificación automática, pero no disponía de persistencia por norma, control complementario, trazabilidad semanal ni indicadores basados en decisiones profesionales. La edición libre de configuración desde la interfaz tampoco permitía normalizar los motivos de futuros ajustes.

**Cambio realizado**

- Archivo o parámetro: `bo_detector/review_store.py`, `desktop_app/app.py`, `desktop_app/templates/index.html`, `desktop_app/static/app.js`, `desktop_app/static/styles.css`, pruebas y documentación.
- Modificación: se agregó un JSON por semana ISO, decisiones manuales por norma, registro de falsos negativos con evidencia, acordeones para categorías ocultas, control complementario, pestaña de indicadores y seis métricas de desempeño. Se retiró el editor de configuración y se mantuvo un resumen de solo lectura. No se modificaron keywords ni patrones del detector.

**Efecto esperado**

- Resultado esperado: acumular evidencia de uso diario sin duplicar ejemplares, medir cobertura y desempeño sobre decisiones reales y asegurar que futuros cambios de configuración queden justificados mediante un skill específico.

**Referencias**

- Issue: no corresponde.
- Commit: pendiente.
- ADR: ADR-001 y ADR-002.

**Revisar resultado**

- Período: uso diario desde `2026-W29`.
- Resultado: pendiente.

## Plantilla

## LOG-AAAA-MM-DD - Título del ajuste

**Evidencia**

- Período:
- Norma o conjunto de casos:
- Resultado observado:

**Problema detectado**

- Descripción:

**Cambio realizado**

- Archivo o parámetro:
- Modificación:

**Efecto esperado**

- Resultado esperado:

**Referencias**

- Issue:
- Commit:
- ADR: no corresponde / ADR-XXX

**Revisar resultado**

- Período:
- Resultado: pendiente / favorable / desfavorable / inconcluso
