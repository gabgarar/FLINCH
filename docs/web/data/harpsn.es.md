# Velocidades de HARPS-N

El segundo instrumento. Sirve para repetir la medida de la velocidad con datos que no
comparten nada con NEID: otro espectrógrafo, otro lugar, otras fulguraciones.

## Qué es

HARPS-N es un espectrógrafo estabilizado del Telescopio Nazionale Galileo, en La Palma. Un
pequeño telescopio solar lo alimenta con la luz de todo el disco cada día despejado desde
julio de 2015, con exposiciones de 5 minutos, una cada 324 s. Dumusque et al. (2026, A&A 706,
A231) publicaron diez años de estos datos. La publicación incluye una tabla con la velocidad
y los índices de actividad de cada exposición: 109 466 filas hasta mayo de 2025, 64 MB.

`python -m flinch replication` descarga esa tabla en `data/harpsn/` la primera vez.

## Qué se espera de él

| | NEID | HARPS-N |
|---|---|---|
| Lugar | Kitt Peak, Arizona | La Palma |
| Horas de observación (UT) | 16:30 a 22:30 | 9 a 17 |
| Años | 2020 a 2026 | 2015 a 2025 |
| Cadencia | 83 s | 324 s |
| Dispersión de una velocidad | 0,81 m/s | 0,44 m/s |
| Fulguraciones M y X medidas | 139 | 115 |

Los dos miran el Sol a horas distintas, así que ven fulguraciones distintas: solo una está en
las dos muestras. Una respuesta del Sol a las fulguraciones tiene que aparecer en los dos; un
artefacto de un instrumento, no.

## Cómo se procesa

| Paso | Qué se hace |
|---|---|
| Tiempo | La marca de tiempo UTC del nombre de cada archivo es el inicio de la exposición; se le suma media exposición. La fecha baricéntrica de la tabla es unos siete minutos anterior y no se usa. |
| Nubes | Se descartan las exposiciones con el indicador de calidad de la publicación por debajo de 0,99, o marcadas por su cadena de reducción. La publicación recomienda 0,9; con ese valor el resultado es el mismo (−0,005 ± 0,038 m/s en 126 fulguraciones). |
| Tendencia diaria | Un polinomio de grado 2 por día, con el mismo recorte y el mismo corte en la dispersión del día que en NEID. Un día necesita 20 exposiciones conservadas. Con 10 o 40 el cambio medio queda entre −0,008 y −0,021 ± 0,04 m/s, y el corte en la dispersión no elimina ningún día (el 99 % de los días se dispersa menos de 0,7 m/s). |
| Resultado | 93 593 velocidades en 1671 días. |
| Fulguraciones | Las de las listas de GOES-16 y GOES-18, que empiezan en febrero de 2017: 1750 de clase M o X, de las que 122 tienen las ventanas completas y 115 al menos tres controles. |

Las ventanas, los controles y el remuestreo son los de [el método](../method.md); solo cambia
con la cadencia el número mínimo de puntos por ventana (tres exposiciones antes de la
fulguración, una durante).

Véanse `flinch.harpsn` y `flinch.replication` en la [referencia de la API](../api/velocity.md).
