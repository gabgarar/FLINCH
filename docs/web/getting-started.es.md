# Primeros pasos

## Instalación

FLINCH necesita Python 3.10 o posterior.

```
git clone https://github.com/gabgarar/FLINCH.git
cd FLINCH
python -m venv venv
venv/Scripts/python -m pip install -e ".[analysis,dev]"     # Windows
venv/bin/python -m pip install -e ".[analysis,dev]"         # Linux y macOS
```

La distribución se llama `flinch-rv` (el nombre `flinch` está ocupado en PyPI por un paquete
que no tiene relación); el nombre para importar es `flinch`.

| Extra | Añade | Hace falta para |
|---|---|---|
| `analysis` | SciPy, Matplotlib, Astropy | Figuras, forma de las líneas, lectura de los espectros |
| `dev` | pytest | Las pruebas |
| `docs` | mkdocs-material, mkdocstrings, mkdocs-static-i18n | Construir esta web |
| `notebooks` | ipykernel | Cuadernos |

## Las órdenes

Todo se ejecuta con `python -m flinch <orden>`.

| Orden | Qué hace | Tiempo | Descarga |
|---|---|---|---|
| `download` | Listas y posiciones de fulguraciones (GOES) y tabla de velocidades (NEID) | 1 min | 22 MB |
| `coverage` | Qué fulguraciones ocurrieron mientras NEID observaba | segundos | ninguna |
| `replication` | La medida de la velocidad con NEID y con HARPS-N, y los dos juntos | 2 min | 64 MB la primera vez (tabla de HARPS-N) |
| `robustness` | El resultado de NEID con otras ventanas, fondos y controles | 1 min | 380 MB la primera vez (flujos de rayos X minuto a minuto) |
| `pilot` | El primer análisis de NEID, con la potencia de las oscilaciones | 10 s | ninguna |
| `spectra` | Extractos de cada espectro de una ventana de tiempo | 10 s por espectro | 113 MB por espectro |
| `campaign` | `spectra` desatendido para las fulguraciones más intensas, o para sus ventanas de control | horas | 113 MB por espectro |
| `chromosphere` | Respuesta de los índices espectrales a las fulguraciones con espectros | 1 min | ninguna |
| `paper-figures` | Las figuras del artículo, en PDF con estilo de revista | 1 min | ninguna |

Una primera sesión:

```
python -m flinch download
python -m flinch coverage
python -m flinch replication
python -m pytest
```

## Dónde van los datos

Las descargas van a `data/` dentro del repositorio, o a la carpeta que indique la variable de
entorno `FLINCH_DATA`. Las tablas van a `results/` y las figuras a `docs/web/img/`.

!!! warning "Los espectros pesan mucho"
    Un espectro de nivel 2 de NEID ocupa 113 MB y el archivo no sirve rangos de bytes, así que
    cada uno se descarga entero, se reduce a un extracto de 0,2 MB y se borra. Una campaña de
    700 espectros mueve 80 GB por la red y conserva 140 MB. El ordenador tiene que seguir
    despierto: en un portátil, déjalo enchufado y con la tapa abierta.

## Pruebas

```
python -m pytest
```

Las pruebas usan datos sintéticos y no tocan la red.
