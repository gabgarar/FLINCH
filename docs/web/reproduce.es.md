# Reproducir los resultados

Cada número y cada figura de [Resultados](results.md) sale de una orden. Las elecciones al
azar (controles, remuestreo) usan una semilla fija, así que las salidas son idénticas de una
ejecución a otra.

## Velocidad

```
python -m flinch download
python -m flinch coverage
python -m flinch replication
python -m flinch robustness
python -m flinch pilot
```

| Salida | La genera | Contenido |
|---|---|---|
| `results/flare_sample.csv` | `coverage` | Las 2122 fulguraciones M y X y su cobertura por NEID |
| `results/velocity_by_instrument.csv` | `replication` | Cambio medio, desplazamiento de una X1 y término de rotación, por clase y por instrumento, y los dos juntos |
| `results/replication_events.csv` | `replication` | Cada fulguración y cada control de los dos instrumentos, con su cambio de velocidad |
| `results/replication_profiles.csv` | `replication` | Velocidad media alrededor del máximo en intervalos de 10 minutos |
| `results/early_window.csv` | `replication` | Velocidad media de 60 a 50 minutos antes del máximo, por clase y por instrumento |
| `results/cleaning_variants.csv` | `replication --cleaning` | El cambio medio y el término de rotación con otros umbrales para descartar días y, en HARPS-N, con el indicador de calidad por encima de 0,9 |
| `results/robustness.csv` | `robustness` | La tabla de variantes (NEID) |
| `results/injections.csv` | `robustness` | Un desplazamiento añadido y medido después (NEID) |
| `results/pilot_*.csv` | `pilot` | El primer análisis de NEID, con la potencia de las oscilaciones |

`replication` descarga la tabla de HARPS-N (64 MB) la primera vez. `robustness` descarga los
flujos de rayos X minuto a minuto (380 MB) la primera vez.

## Espectros

```
python -m flinch campaign --min-class X1.0 --hours 4 --max-files 700
python -m flinch campaign --kind controls --hours 4 --max-files 700
python -m flinch campaign --min-class M5.0 --max-class X1.0 --clear-only --sparse --step 2 --before 26 --after 10
python -m flinch chromosphere
```

La primera orden descarga los espectros alrededor de las fulguraciones de clase X, de mayor a
menor, hasta agotar el tiempo o el número de archivos; la segunda descarga las mismas ventanas
del día sin fulguraciones más próximo. La tercera descarga las fulguraciones entre M5 y M9, y
de ellas solo las que tienen cielo despejado y estable, y solo esos espectros: los demás se
descartarían de todos modos, y cada uno cuesta 113 MB. Todas saltan lo que ya está en disco,
así que pueden pararse y repetirse. Los extractos van a `data/spectra/<fecha>_<hora>_<clase>/`.

| Salida | La genera | Contenido |
|---|---|---|
| `results/spectral_response.csv` | `chromosphere` | Respuesta de cada fulguración y cada control, con sus errores |
| `results/spectral_indices.csv` | `chromosphere` | Resumen de cada índice por banda de clase |

Una sola ventana:

```
python -m flinch spectra --start 2024-02-22T21:37 --end 2024-02-22T22:45 --name 20240222_2233_X6.3
```

## Figuras del artículo

```
python -m flinch paper-figures --out docs/paper/figuras
```

Escribe, como PDF vectorial con estilo de revista, el ejemplo del método, la velocidad media
alrededor del máximo en los dos instrumentos, el cambio de cada fulguración frente a su clase
y su posición, y la respuesta media de los espectros.

## Versiones

Las versiones exactas de los paquetes usados están en `requirements-lock.txt`. Los datos
cambian con el tiempo: la tabla de NEID crece cada día despejado y los archivos de GOES se
reeditan con una nueva fecha final, así que los recuentos que se dan aquí son los del 20 de
noviembre de 2026.
