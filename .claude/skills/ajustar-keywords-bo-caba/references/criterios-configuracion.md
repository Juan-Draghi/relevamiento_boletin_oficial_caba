# Criterios para ajustar la configuración

## Índice

1. Principios
2. Tipos de configuración
3. Evidencia mínima
4. Evaluación de impacto
5. Operaciones admitidas
6. Pruebas
7. Registro en el log
8. Límites

## 1. Principios

- Basar cada ajuste en uno o más resultados reales, no en asociaciones temáticas hipotéticas.
- Elegir la lista por el efecto del clasificador, no por cómo denomina el usuario al término.
- Preferir la frase más específica que resuelva el caso.
- Revisar variantes ortográficas sin multiplicar sinónimos innecesarios.
- Evaluar sobrecaptura: una mejora de cobertura no debe introducir un volumen desproporcionado de falsos positivos.
- Mantener cada cambio pequeño y reversible mediante Git.
- Separar configuración de lógica. Este skill no cambia código del clasificador.

## 2. Tipos de configuración

### `KEYWORDS`

**Efecto:** una coincidencia completa en el sumario clasifica la norma como `RELEVANTE`, salvo que la misma frase esté declarada como condicional.

**Usar cuando:** el concepto es suficiente para el servicio de referencia incluso sin otra señal normativa.

**Revisar:**

- que la frase tenga significado inequívoco en el dominio;
- singular, plural, siglas y grafías realmente observadas;
- coincidencias dentro de frases administrativas irrelevantes;
- si ya existe una frase más general o específica que cubre el caso;
- duplicados después de minúsculas, eliminación de acentos y normalización de espacios.

**Control recomendado:** un sumario positivo real y uno que contenga vocabulario cercano pero no la frase completa.

### `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`

**Efecto:** convierte una entrada de `KEYWORDS` en condicional. Sólo clasifica como `RELEVANTE` cuando el sumario contiene además un patrón de `VERBOS_ACCION` y contexto normativo reconocido por el clasificador.

**Invariante:** toda keyword condicional debe existir también en `KEYWORDS`. Agregarla únicamente a la lista condicional no produce coincidencias. Eliminarla de la lista condicional, pero conservarla en `KEYWORDS`, la convierte en directa.

**Usar cuando:** el término es pertinente en normas generales, pero aparece también en permisos, autorizaciones o actuaciones individuales irrelevantes.

**Revisar:**

- ejemplos positivos con acción y contexto normativos;
- ejemplos negativos de actos individuales;
- que los verbos y el vocabulario de contexto presentes sean reconocidos por la lógica actual;
- que la condicionalidad no oculte casos relevantes redactados sin esos patrones.

**Controles recomendados:** un caso normativo positivo y un permiso individual negativo con la misma keyword.

### `VERBOS_ACCION`

**Efecto:** habilita keywords condicionales y también puede enviar normas de organismos prioritarios a `REVISION_MANUAL`.

**Usar cuando:** una acción normativa real no es reconocida por las regex existentes.

**Revisar:**

- forma conjugada, infinitivo y variantes con tilde observadas;
- límites de palabra para evitar coincidencias parciales;
- compilación con `re.IGNORECASE`;
- búsqueda sobre texto original: no asumir que los acentos se eliminan antes de aplicar la regex;
- efecto sobre todos los organismos prioritarios, no sólo sobre el caso aportado;
- si la expresión describe una decisión normativa general o una gestión administrativa individual.

**Controles recomendados:** el verbo real en contexto positivo y una palabra similar que no debe coincidir.

### `LISTA_NORMAS_CURADAS`

**Efecto:** una referencia coincidente en el sumario clasifica la norma como `RELEVANTE`.

**Usar cuando:** interesa seguir una ley, decreto, resolución, disposición u ordenanza concreta y sus actos modificatorios o relacionados.

**Revisar:**

- tipo y número exactos de la norma;
- variantes con y sin `N°`, punto de miles, guion, barra, `GCABA` y sigla del organismo;
- límites suficientes para no coincidir con números más largos;
- acentos, porque el patrón se prueba tanto sobre texto original como normalizado;
- evidencia documental de que la norma curada pertenece al alcance del servicio.

**Controles recomendados:** dos variantes reales de la referencia y un número vecino que no debe coincidir.

### `LISTA_ORGANISMOS_PRIORIDAD`

**Efecto:** el nombre o la sigla se busca en organismo, nombre y sumario. Sólo deriva a `REVISION_MANUAL` cuando el sumario contiene un verbo de acción o una referencia normativa opaca.

**Usar cuando:** la producción de un organismo tiene probabilidad suficiente de contener normativa pertinente, pero no corresponde clasificarla automáticamente como relevante.

**Revisar:**

- denominación y sigla oficiales;
- ambigüedad de siglas breves;
- coincidencias en otros contextos del sumario;
- volumen adicional de revisión manual;
- casos positivos y negativos históricos del organismo.

**Control recomendado:** un caso opaco que debe ir a revisión y otro sin señal normativa que debe continuar como `NO_RELEVANTE`.

## 3. Evidencia mínima

La ficha previa debe contener:

- fecha o número de ejemplar;
- tipo, número y organismo de la norma;
- sumario relevante o fragmento suficiente;
- categoría automática original;
- decisión profesional;
- tipo de problema: falso negativo, falso positivo, revisión manual innecesaria o variante no cubierta;
- motivo profesional para incorporar, reemplazar o retirar el criterio.

Un caso `REVISION_MANUAL` confirmado relevante no es un falso negativo. Un falso negativo requiere categoría original `NO_RELEVANTE` o `DESCARTADA_FILTRO_ESTRUCTURAL` y confirmación profesional como relevante.

## 4. Evaluación de impacto

Antes de proponer:

1. Buscar el valor y sus variantes en toda la configuración.
2. Revisar cómo lo consume `bo_detector/classifier.py`.
3. Ejecutar la comparación previa con `scripts/revisar_estrategias.py comparar` (ver SKILL.md). Mide sobre los registros guardados qué normas entran o salen de la lista principal, sin modificar archivos.
4. Para retiros, revisar cuántas normas siguen seleccionadas por otra regla.
5. Identificar al menos un control negativo cuando el ajuste amplía coincidencias.

No modificar ni normalizar `data/seguimiento/*.json`. Si no existe una base histórica suficiente, declararlo como limitación; no inventar un impacto cuantitativo. Con pocas relevantes confirmadas, los porcentajes son frágiles: mostrar siempre las cantidades.

## 5. Operaciones admitidas

### Agregar

Incorporar un valor nuevo sin alterar los existentes. Mantener la convención visible de orden y formato.

### Reemplazar

Cambiar un valor concreto cuando su regex, grafía o alcance sean incorrectos. Documentar valor anterior y nuevo. Verificar que el reemplazo cubra los casos previos que todavía sean válidos.

### Eliminar

Exigir evidencia de falsos positivos, redundancia o criterio obsoleto. Revisar si otra entrada conserva la cobertura necesaria. No usar la eliminación para ocultar un problema de lógica.

No realizar limpiezas generales, reordenamientos ni deduplicaciones ajenas al caso aprobado.

## 6. Pruebas

Para cada cambio agregar la prueba mínima que demuestre su efecto:

| Tipo | Prueba positiva | Control negativo |
|---|---|---|
| `KEYWORDS` | Sumario real relevante | Frase cercana no coincidente |
| Condicional | Keyword + acción + contexto | Misma keyword en acto individual |
| Verbo | Nueva forma verbal activa el caso | Palabra parcial o contexto no normativo |
| Norma curada | Referencia real con variantes | Número o norma vecina |
| Organismo | Caso opaco a revisión | Caso sin verbo ni referencia normativa |

Verificar también el `motivo_deteccion`, no sólo la categoría.

## 7. Registro en el log

Usar una entrada append-only con esta estructura:

```markdown
## LOG-AAAA-MM-DD - Acción, tipo y valor

**Evidencia**

- Período o ejemplar:
- Norma o conjunto de casos:
- Categoría obtenida y decisión profesional:
- Resultado observado:

**Problema detectado**

- Tipo: falso negativo / falso positivo / revisión innecesaria / variante no cubierta.
- Descripción:

**Cambio realizado**

- Archivo o parámetro: `config/config_keywords.json` — `NOMBRE_DE_LISTA`.
- Operación: agregar / reemplazar / eliminar.
- Valor anterior: no corresponde / `...`.
- Valor nuevo: no corresponde / `...`.
- Modificación:

**Motivo de incorporación o modificación**

- Justificación:

**Comparación previa**

- Período y base: AAAA-MM-DD a AAAA-MM-DD, N boletines, N normas.
- Informe: `data/informes_estrategias/AAAAMMDD_HHMMSS_comparacion.md` (no versionado).
- Relevantes recuperadas / perdidas: N de N / N de N.
- Irrelevantes evitadas / añadidas (decisión + lectura completa): N de N / N de N.
- Sin información afectadas: N.
- Siguen seleccionadas por otra regla (retiros): N de N.

**Validación**

- Prueba específica:
- Suite completa:
- Resultado:

**Efecto esperado**

- Resultado esperado:
- Riesgo o efecto colateral observado:

**Referencias**

- Issue: no corresponde / referencia.
- Commit: pendiente.
- ADR: no corresponde.

**Revisar resultado**

- Período:
- Resultado: pendiente.
```

No completar un commit inexistente. Puede quedar `pendiente` hasta que el usuario autorice registrar los cambios.

## 8. Límites

Detener el flujo sin editar cuando el pedido requiera:

- cambiar poderes o tipos incluidos;
- modificar filtros estructurales;
- introducir nuevas categorías;
- cambiar prioridades o precedencia entre capas;
- editar código del clasificador o del cargador;
- recalcular o alterar decisiones históricas;
- crear un ADR.

Informar que el pedido excede un ajuste de keywords. No expandir el alcance automáticamente.
