# ADR-004 - Reglas trazables en lugar de aprendizaje supervisado

Estado: aceptado

Fecha de la decisión original: 2026-04-21

Documentado retrospectivamente: 2026-07-14

## Contexto y evidencia

El proyecto anterior exploró un clasificador de normativa relevante basado en TF-IDF y SVM. La clase positiva representaba menos de aproximadamente el 3 % del universo histórico. Las pruebas y reentrenamientos no produjeron una mejora estable: el modelo terminaba reproduciendo, en términos operativos, una búsqueda de palabras clave sin ofrecer una explicación sencilla de cada resultado.

Para un servicio de referencia especializado, los criterios deben poder ser revisados, corregidos y explicados. La complejidad del modelo supervisado no se justificaba si la señal efectiva seguía siendo léxica y la base positiva era escasa.

La evidencia conservada incluye el hilo de diseño iniciado el 2026-04-21, el antecedente enlazado en `README.md`, `docs/pipeline_v2_diseño.md` y la primera implementación funcional del commit `fa15f55`. El notebook original no forma parte del repositorio actual, por lo que esta decisión no reconstruye detalles de código o métricas que no estén preservados.

## Opciones consideradas

1. Mantener TF-IDF + SVM y continuar ampliando el conjunto de entrenamiento.
2. Combinar el modelo con puntajes y reglas auxiliares.
3. Reemplazar el modelo por reglas explícitas, configuración curada y revisión profesional.

La primera alternativa mantenía el desbalance y una carga de entrenamiento sin una ganancia demostrada. La segunda agregaba complejidad y hacía más difícil atribuir el resultado a un criterio concreto.

## Decisión

Utilizar un detector basado en:

- reglas explícitas y ordenadas;
- normalización de texto;
- keywords y patrones curados;
- organismos y siglas prioritarias;
- motivos de clasificación visibles;
- revisión profesional para casos dudosos y control complementario de posibles omisiones.

No utilizar aprendizaje supervisado como componente del detector vigente. No reintroducirlo salvo una nueva decisión explícita basada en un corpus adecuado, una metodología defendible y una mejora medible frente a las reglas.

## Consecuencias

- Cada clasificación puede relacionarse con una señal concreta.
- Los ajustes pueden probarse, documentarse y revertirse con bajo costo.
- La calidad depende de la curaduría y de la revisión profesional.
- Las reglas pueden requerir mantenimiento frente a nuevas formas de redacción.
- El sistema no pretende inferir relevancia semántica general fuera de los criterios configurados.
- La revisión manual y los indicadores posteriores complementan las limitaciones de las reglas sin ocultarlas detrás de un puntaje probabilístico.

## Forma de verificación

- pruebas unitarias con sumarios reales o representativos;
- motivos de clasificación conservados en cada resultado;
- registro de falsos positivos, falsos negativos y cambios de configuración;
- comparación periódica de indicadores sobre decisiones profesionales;
- prohibición documental de presentar recall o F1 sin un universo suficientemente revisado.

## Fuentes históricas

- hilo `019dd44f-f333-7c22-b47c-3c73353d905d`;
- commit `fa15f55`;
- `README.md`;
- `docs/pipeline_v2_diseño.md`.

## Relación con otras decisiones

- [ADR-005 - Pipeline API por capas y revisión humana](ADR-005-pipeline-api-por-capas-y-revision-humana.md)
- [ADR-002 - Indicadores de desempeño y gobernanza de la configuración](ADR-002-indicadores-y-gobernanza-configuracion.md)
