# Pipeline v2 — Detector de Normativa Boletín Oficial CABA
## Diseño técnico consolidado · Abril 2026

---

## 1. Contexto y objetivo

El Boletín Oficial de la Ciudad de Buenos Aires expone una **API REST pública** (`https://api-restboletinoficial.buenosaires.gob.ar`) que permite acceder de forma estructurada a las normas publicadas en cada boletín, incluyendo metadatos, sumarios, enlaces a los documentos y anexos.

El objetivo del pipeline es detectar normativa relevante para el ejercicio profesional de la arquitectura, el urbanismo, la construcción y materias afines, utilizando como señal principal el **sumario** de cada norma.

La premisa central del diseño es:

- El `sumario` del Boletín Oficial es una señal editorial breve pero de alta densidad informativa.
- Si una keyword temática directa aparece en el `sumario`, la norma se considera **relevante**.
- Algunas keywords amplias, como `espacio público`, requieren contexto normativo adicional para evitar falsos positivos por permisos individuales.
- El pipeline no usa SVM ni otro modelo supervisado, porque el volumen histórico de positivos es demasiado bajo para entrenar un clasificador robusto.
- Los casos ambiguos se derivan a revisión manual solo cuando hay señales normativas concretas, no por longitud del sumario.

---

## 2. Fuente de datos

### 2.1 Endpoint principal

El pipeline parte del consumo del endpoint:

```text
GET /obtenerBoletin/{parametro}/true
```

Donde:

- `parametro = 0` devuelve el último boletín publicado.
- `parametro = dd-mm-yyyy` devuelve el boletín de una fecha determinada.
- `parametro = {número}` devuelve un boletín por número.

La respuesta contiene:

- metadatos del boletín
- secciones
- normas agrupadas jerárquicamente
- enlaces de descarga de norma y anexos

### 2.2 Estructura relevante de la respuesta

Cada norma se obtiene dentro de una estructura anidada:

```text
Poder -> Tipo de norma -> Organismo -> [lista de normas]
```

Para cada norma, el pipeline utiliza:

- `poder`
- `tipo_norma`
- `organismo`
- `nombre`
- `sumario`
- `id_norma`
- `url_norma`
- `anexos`
- `id_sdin`, si estuviera disponible

### 2.3 Normalización inicial

La salida de la API se aplana para generar un registro por norma:

```text
[poder, tipo_norma, organismo, nombre, sumario, id_norma, url_norma, anexos]
```

Para las búsquedas textuales, el sistema normaliza texto:

- minúsculas
- remoción de tildes
- normalización de espacios

La configuración se mantiene en español legible, con tildes. La normalización se aplica internamente al comparar.

---

## 3. Diseño del pipeline

### 3.1 Principio rector

El pipeline maximiza detección por sumario, pero evita retener casos ambiguos sin señales normativas suficientes.

La lógica general es:

- si hay keyword directa o norma curada en sumario, la norma es `RELEVANTE`
- si hay keyword condicional, solo es `RELEVANTE` cuando existe contexto de acción normativa
- si no hay keyword ni norma curada, pero hay combinación de organismo prioritario + acción normativa opaca, pasa a `REVISION_MANUAL`
- si no hay señales suficientes, se clasifica como `NO_RELEVANTE`
- si no supera el filtro estructural, se clasifica como `DESCARTADA_FILTRO_ESTRUCTURAL`

### 3.2 Diagrama general

```text
obtenerBoletin(fecha, carga_datos=True)
        │
        ▼
aplanar_normas()
[poder, tipo_norma, organismo, nombre, sumario, id_norma, url_norma, anexos]
        │
        ▼
CAPA 0 — Filtro estructural
        │
        ├─ Si poder/tipo_norma no están incluidos
        │    → DESCARTADA_FILTRO_ESTRUCTURAL
        │
        ▼
CAPA 1 — Match directo sobre sumario
        │
├─ Keyword directa o norma curada en sumario
        │    → RELEVANTE
        │
        ├─ Keyword condicional + acción normativa
        │    → RELEVANTE
        │
        └─ Sin keyword relevante
             ▼
CAPA 2 — Casos para revisión manual
             │
             ├─ Organismo prioritario + acción normativa opaca
             │    → REVISION_MANUAL
             │
             └─ Sin señales adicionales
                  → NO_RELEVANTE
```

### 3.3 Capa 0 — Filtro estructural

Esta capa reduce ruido antes de evaluar el sumario.

Se conservan únicamente las normas cuyo `poder` pertenezca a:

- Poder Legislativo
- Poder Ejecutivo

Y cuyo `tipo_norma` pertenezca a:

- Ley
- Ley de Aprobación Inicial
- Decreto
- Decreto de Necesidad y Urgencia
- Resolución
- Disposición

Quedan excluidos, sin clasificación temática:

- Poder Judicial
- licitaciones
- edictos
- convocatorias
- comunicados
- tipos documentales ajenos al universo normativo de interés

### 3.4 Capa 1 — Match directo sobre sumario

Sobre el campo `sumario` se ejecuta la búsqueda de `KEYWORDS` y `LISTA_NORMAS_CURADAS`.

**Regla principal:**

Si una keyword temática directa o una norma perteneciente a `LISTA_NORMAS_CURADAS` aparece en el `sumario`, la norma se considera `RELEVANTE`.

Esto aplica incluso a términos que podrían parecer generales fuera del Boletín Oficial, como:

- `habilitación`
- `catastro`
- `impacto ambiental`

En este pipeline, si esos términos aparecen en el sumario, se consideran señal suficiente de relevancia.

#### Keywords condicionales

Algunas keywords son demasiado amplias para disparar relevancia por sí solas. El caso definido actualmente es:

- `espacio público`
- `uso del espacio público`
- `vía pública`

Estas keywords solo disparan `RELEVANTE` si el sumario también contiene acción normativa y contexto normativo, por ejemplo:

- modifica requisitos
- aprueba reglamento
- establece procedimiento
- deroga normativa
- sustituye pautas

Esto evita detectar permisos individuales, por ejemplo:

```text
Otorga permiso de uso temporario y revocable del espacio público para emplazar andamios...
```

Pero conserva casos como:

```text
Modifica los requisitos para el otorgamiento de permisos de uso del espacio público...
```

#### Motivos de detección

Ejemplos:

- `keyword_sumario: código urbanístico`
- `keyword_sumario: habilitación`
- `keyword_sumario: impacto ambiental`
- `keyword_condicional_sumario: uso del espacio público`
- `referencia_norma_curada: [Dd]ecreto(?: [Nn]°?)? ?116/25`

### 3.5 Capa 2 — Casos para revisión manual

Esta capa se aplica únicamente a normas que no tuvieron match de relevancia en Capa 1.

El objetivo no es descargar ni analizar automáticamente el texto completo, sino listar casos con señales normativas concretas para revisión humana.

Una norma pasa a `REVISION_MANUAL` cuando ocurre esta condición:

- el organismo emisor pertenece a `LISTA_ORGANISMOS_PRIORIDAD` y el sumario contiene un verbo de acción normativa más una referencia normativa

Ejemplos:

- `Modifícase el Decreto 116/25`
- `Derógase la Disposición 526/DGFYCO/24`
- `Sustitúyese la Resolución 96/AGC/25`

El pipeline **no** usa longitud mínima de sumario como criterio de revisión manual. Se eliminó `UMBRAL_TOKENS_OPACO` porque generaba demasiado ruido administrativo.

Ejemplos de motivos:

- `sumario_opaco_patron`
- `organismo_prioritario: DGROC`

---

## 4. Tipos de salida

### 4.1 RELEVANTE

Una norma se marca como `RELEVANTE` cuando:

- contiene una keyword directa en el sumario
- o contiene una norma perteneciente a `LISTA_NORMAS_CURADAS` en el sumario
- o contiene una keyword condicional con acción normativa y contexto normativo suficiente

### 4.2 REVISION_MANUAL

Una norma se marca como `REVISION_MANUAL` cuando:

- no contiene keyword directa o condicional suficiente
- no contiene norma curada
- pero combina organismo prioritario con acción normativa opaca

### 4.3 NO_RELEVANTE

Una norma se marca como `NO_RELEVANTE` cuando:

- supera el filtro estructural
- no contiene keyword relevante
- no referencia normas curadas
- no presenta señales suficientes para revisión manual

### 4.4 DESCARTADA_FILTRO_ESTRUCTURAL

Una norma se marca como `DESCARTADA_FILTRO_ESTRUCTURAL` cuando:

- su `poder` no está incluido
- o su `tipo_norma` no está incluido

---

## 5. Parámetros configurables

| Parámetro | Descripción |
|---|---|
| `PODERES_INCLUIDOS` | Poderes procesados por Capa 0 |
| `TIPOS_NORMA_INCLUIDOS` | Tipos de norma procesados por Capa 0 |
| `KEYWORDS` | Términos temáticos que disparan relevancia directa |
| `KEYWORDS_REQUIEREN_ACCION_NORMATIVA` | Keywords amplias que requieren contexto normativo adicional |
| `VERBOS_ACCION` | Patrones verbales de modificación, derogación, aprobación, sustitución, etc. |
| `LISTA_NORMAS_CURADAS` | Patrones regex de normas cuya referencia dispara relevancia directa |
| `LISTA_ORGANISMOS_PRIORIDAD` | Organismos que activan revisión solo combinados con acción normativa opaca |

---

## 6. Salida mínima por norma retenida

Para toda norma marcada como `RELEVANTE` o `REVISION_MANUAL`, el pipeline devuelve:

- `poder`
- `tipo_norma`
- `organismo`
- `nombre`
- `sumario`
- `url_norma`
- `anexos`
- `motivo_deteccion`
- `categoria_salida`

Opcionalmente, en modo auditoría puede devolver también `NO_RELEVANTE` y `DESCARTADA_FILTRO_ESTRUCTURAL`.

---

## 7. Criterios de mantenimiento

El sistema debe evolucionar principalmente por ajuste de configuración, no por reentrenamiento de modelos supervisados.

Las mejoras esperables provienen de:

- incorporar nuevas keywords surgidas de casos reales
- mover keywords demasiado amplias a `KEYWORDS_REQUIEREN_ACCION_NORMATIVA`
- ampliar o depurar `LISTA_NORMAS_CURADAS`
- mantener actualizada `LISTA_ORGANISMOS_PRIORIDAD`
- corregir términos defectuosos o ruidosos en la configuración

Este diseño prioriza:

- simplicidad
- auditabilidad
- bajo costo de mantenimiento
- alta sensibilidad sobre sumarios
- control humano en casos ambiguos con señales normativas reales

---

## 8. Decisiones adoptadas

1. Se descarta el uso de SVM como componente activo del pipeline.
2. La aparición de una keyword directa en el sumario se considera criterio suficiente de relevancia.
3. Algunas keywords amplias requieren acción normativa adicional para evitar falsos positivos.
4. Se elimina `UMBRAL_TOKENS_OPACO`; la longitud del sumario no dispara revisión manual.
5. Las normas curadas son criterio de relevancia directa cuando aparecen en el sumario.
6. Los casos ambiguos se derivan a revisión manual por organismo prioritario combinado con acción normativa opaca.
7. No se descarga ni analiza automáticamente el texto completo en esta versión del pipeline.
