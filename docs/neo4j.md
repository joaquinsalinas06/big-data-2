# Resultado de la ejecución local completa

Ejecución inicial en macOS el 28 de octubre de 2026; persistencia y aceptación verificadas nuevamente el 29 de octubre. Dataset `listenbrainz-2746`; análisis `listenbrainz-2746:4ef0e0d86bb699e7`. Estos resultados describen un lote de ingesta de ListenBrainz, no toda la plataforma.

## Carga y reconciliación

| Medida | Resultado |
| --- | ---: |
| Escuchas procesadas | 4 855 809 |
| Usuarios | 26 394 |
| Canciones por recording_msid | 1 420 842 |
| Nombres de artista | 286 291 |
| Relaciones ESCUCHO | 1 791 408 |
| Relaciones ESCUCHA_ARTISTA | 743 531 |
| Relaciones INTERPRETADA_POR | 1 424 734 |
| Preparación SQLite | 60.20 segundos |
| Carga Neo4j | 174.90 segundos |
| Análisis y publicación | 3.64 segundos |

Las sumas de `ESCUCHO.cantidad` y `ESCUCHA_ARTISTA.cantidad` coinciden con **4 855 809**. Los conteos de usuarios, destinos y fechas también coinciden con la preparación. SHA-256 del JSONL: `b82630bad34a8e85490943e9c0e54fb7f2aaecff5a894b9e57ae3ae155027d4a`.

Los tiempos corresponden a esta máquina y ejecución, no son un compromiso de rendimiento para otros equipos. Se observó aproximadamente 1,75 GiB de memoria del contenedor tras reiniciar y consultar; es una lectura puntual, no el máximo de la importación. El límite del servicio es 5 GiB.

## Afinidades y comunidades

| Medida | Resultado |
| --- | ---: |
| Artistas seleccionados | 500 |
| Artistas conectados / aislados | 425 / 75 |
| Afinidades retenidas | 1 553 |
| Comunidades | 13 |
| Modularidad ponderada | 0.782546 |
| Usuarios con recomendaciones | 16 372 |
| Cobertura sobre todos los usuarios del lote | 62.03 % |
| Usuarios con escuchas clasificadas | 16 374 |
| Escuchas clasificadas en comunidades | 1 153 631 |
| Proporción de escuchas clasificadas | 23.76 % |
| Diversidad media de usuarios clasificados | 0.416633 |

La cobertura se recalculó mediante recorridos en Neo4j y coincide con los 16 372 usuarios obtenidos en Python. Las audiencias de comunidades se recalcularon en Neo4j y coinciden con los valores publicados.

Solo el 23.76 % de las escuchas pertenece a artistas con comunidad bajo estos parámetros. Esto limita la interpretación de diversidad. Una modularidad alta puede reflejar también los umbrales y la poda de vecinos; no demuestra que los grupos sean géneros musicales reales.

| Comunidad | Artistas | Audiencia del lote | Representantes por grado ponderado |
| --- | ---: | ---: | --- |
| 1 | 39 | 3 556 | Travis Scott, Kendrick Lamar, Future, A$AP Rocky, Drake |
| 2 | 86 | 6 585 | Linkin Park, Three Days Grace, Korn, Disturbed, Breaking Benjamin |
| 3 | 84 | 6 348 | Ariana Grande, Charli xcx, Taylor Swift, Olivia Rodrigo, Sabrina Carpenter |
| 4 | 85 | 5 545 | The Rolling Stones, Metallica, AC/DC, Elton John, Queen |
| 5 | 15 | 1 611 | Ado, YOASOBI, Eve, ヨルシカ, DECO*27 |
| 6 | 17 | 1 217 | Jin, Jimin, j-hope, V, Agust D |
| 7 | 11 | 1 219 | Moby, Massive Attack, Air, Bonobo, The Chemical Brothers |
| 8 | 13 | 1 131 | ILLIT, LE SSERAFIM, aespa, IVE, NewJeans |
| 9 | 65 | 6 310 | Malcolm Todd, The Smiths, Radiohead, Clairo, TV Girl |
| 10 | 2 | 209 | Bill Withers, Marvin Gaye |
| 11 | 2 | 246 | Crystal Castles, Grimes |
| 12 | 2 | 242 | Hans Zimmer, Max Richter |
| 13 | 4 | 533 | Royal Blood, The Black Keys, Nothing But Thieves, The White Stripes |

Las audiencias se solapan: un usuario puede escuchar artistas de varias comunidades. Los números identifican una partición concreta y no son etiquetas musicales permanentes.

## Resultados de las consultas

En un caso local, una escucha de Motörhead permite recomendar Judas Priest: **17 oyentes compartidos**, Jaccard **0,091892** y puntaje **0,032819** al ponderarlo por el historial del usuario. El sistema explica también conexiones con Megadeth e Iron Maiden y excluye artistas ya escuchados en el lote. No se publica aquí el identificador del usuario.

La consulta de canciones devuelve **Breaking the Law**, de Judas Priest, con audiencia de nueve usuarios para ese recording_msid dentro del lote; no suma otras grabaciones o variantes con el mismo título. El camino entre Motörhead y Judas Priest tiene un salto de afinidad.

Radiohead aparece con coeficiente puente **0,634146**, que describe la distribución de sus conexiones entre comunidades. No significa que sea el artista más popular ni acredita influencia causal.

## Evidencia y reproducción

- Las pruebas unitarias están en `databases/neo4j/tests/`: validación, agregación, Jaccard, diversidad, análisis vacío, carga repetida, consultas, publicación atómica y CRUD. La carga interrumpida se repite desde el inicio, sin checkpoints.
- Aceptación del lote completo: reconciliación, cobertura independiente en Neo4j, exclusión de canciones/artistas escuchados, explicación del puntaje y consultas de la semana 12.
- Datos conservados después de recrear y reiniciar el contenedor; volumen persistente.
- Artefactos detallados locales: `data/neo4j/analysis.json` y registros de pruebas. Los archivos antiguos de aceptación son históricos, no comandos vigentes. Permanecen fuera de Git.

```bash
python -m databases.neo4j.crud --pause
python -m databases.neo4j.queries
pytest databases/neo4j/tests
```

La organización vigente está en [databases/neo4j/README.md](../databases/neo4j/README.md). Los tiempos anteriores pertenecen a la ejecución inicial; la reorganización conserva los cálculos.
