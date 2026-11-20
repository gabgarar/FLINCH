# FLINCH: resultados

Estado a 20 de noviembre de 2026. Las secciones 1 a 3 se reproducen con `python -m flinch
pilot` y `python -m flinch robustness`; las tablas quedan en `results/` y las figuras en
`docs/web/img/`. La sección 4 es preliminar: la descarga de espectros sigue en curso.

## 1. La velocidad del Sol no cambia durante las fulguraciones

Con 139 fulguraciones de clase M y X, la velocidad radial del Sol visto como estrella no
cambia de forma detectable durante la fulguración.

![Velocidad media alrededor del máximo de la fulguración](web/img/pilot_profiles.png)

Cada fulguración se compara con sus propios controles (misma hora, otros días, sin
fulguraciones). Los errores salen de un bootstrap que remuestrea días enteros, porque las
fulguraciones de un mismo día (hasta 6) no son independientes.

| Magnitud | Valor (m/s) | Cota al 95 % (m/s) |
|---|---|---|
| Cambio medio de una fulguración M o X | −0,035 ± 0,035 | 0,09 |
| Cambio por fulguración de clase X1 (escalado con el flujo) | −0,010 ± 0,061 | 0,11 |
| Término de rotación por X1 en el limbo ecuatorial | −0,106 ± 0,082 | 0,24 |

La cota del cambio medio es del orden de los 0,09 m/s que la Tierra imprime en el Sol.

El término de rotación es el análisis con signo: se ajusta el cambio de velocidad frente al
flujo de la fulguración multiplicado por la velocidad de rotación proyectada en su posición.
Una mancha brillante en la mitad del disco que se acerca debería bajar la velocidad y en la
que se aleja subirla; el promedio simple cancelaría esa señal y este ajuste no. Tampoco
aparece: permutando las posiciones entre fulguraciones, un valor así sale el 10 % de las veces.

![Cambio de velocidad de cada fulguración frente a su clase y a su posición](web/img/pilot_events.png)

En términos físicos, el cambio esperado es ΔRV ≈ (ΔF/F) · v_rot · K, con ΔF/F el aumento
relativo de brillo en el visible, v_rot la rotación proyectada (hasta 1983 m/s) y K la
respuesta de la máscara de líneas. La cota del término de rotación equivale a
K · ΔF/F < 1,2 × 10⁻⁴ por fulguración X1.

## 2. El resultado no depende de las decisiones de análisis

| Variante | Fulguraciones | Cambio medio | Por X1 | Rotación por X1 |
|---|---|---|---|---|
| Por defecto | 139 | −0,035 ± 0,035 | −0,010 ± 0,061 | −0,106 ± 0,082 |
| Polinomio diario de grado 1 | 137 | −0,022 ± 0,036 | −0,015 ± 0,060 | −0,045 ± 0,080 |
| Polinomio diario de grado 3 | 139 | −0,001 ± 0,033 | +0,016 ± 0,049 | −0,079 ± 0,083 |
| Ventana: ±3 min del máximo de la derivada de GOES | 120 | −0,009 ± 0,042 | −0,019 ± 0,061 | −0,108 ± 0,135 |
| Ventana: primeros 10 min desde el inicio | 134 | −0,040 ± 0,035 | +0,006 ± 0,045 | −0,004 ± 0,080 |
| Ventana: ±5 min del máximo en rayos X | 126 | −0,021 ± 0,042 | −0,111 ± 0,085 | −0,134 ± 0,154 |
| Fondo: recta ajustada a ambos lados | 93 | −0,008 ± 0,040 | −0,032 ± 0,070 | −0,002 ± 0,113 |
| Solo clase X | 11 | −0,060 ± 0,088 | +0,011 ± 0,065 | −0,051 ± 0,104 |

Todo en m/s. "Por defecto" es: polinomio de grado 2 por día, ventana desde el inicio hasta
2 minutos después del máximo, línea base en los 35 minutos anteriores al inicio y controles
en otros días. El máximo de la derivada del flujo de GOES marca la fase impulsiva; de
mediana cae 3,5 minutos antes del máximo en rayos X.

Los controles del mismo día (a 2 y 3 horas) solo existen para 8 fulguraciones, porque casi
siempre caen fuera de la jornada de observación o cerca de otra fulguración. No dicen nada:
+0,07 ± 0,17 m/s.

### Sensibilidad demostrada

Una señal falsa añadida a los datos brutos y pasada por toda la cadena:

| Señal inyectada | Recuperada | Probabilidad de detectarla al 95 % |
|---|---|---|
| 5 cm/s | 4,9 cm/s | 40 % |
| 10 cm/s | 9,8 cm/s | 88 % |
| 20 cm/s | 19,5 cm/s | 100 % |
| 50 cm/s | 48,8 cm/s | 100 % |

## 3. Las fulguraciones no aumentan la amplitud de las oscilaciones del Sol

La potencia de las fluctuaciones de velocidad (dominada por las oscilaciones de 5 minutos) es
la misma en los 35 minutos posteriores al máximo que en los 35 anteriores al inicio.

| Magnitud | Fulguraciones | Muestras nulas | Cota al 95 % del exceso |
|---|---|---|---|
| ln(potencia después / antes) | −0,068 | 0,001 ± 0,053 | 0,16 |
| Lo mismo, pesando las frecuencias altas | −0,013 | −0,009 ± 0,060 | 0,10 |

En amplitud, un aumento medio superior al 8 % queda descartado. Es una prueba de la propuesta
de Karoff y Kjeldsen (2008), con la limitación de que la cadencia de 83 s solo llega a 6 mHz.

## 4. Las líneas cromosféricas sí responden (preliminar)

Los espectros completos de las fulguraciones más intensas muestran lo contrario que la
velocidad: los índices cromosféricos suben con claridad cuando la fulguración está sobre el
disco.

![Respuesta espectral a la fulguración X6.3 del 22 de febrero de 2024](web/img/event_20240222_2233_X6.3.png)

Cambio medio entre 8 minutos antes y 10 después del máximo, respecto a los espectros previos
al inicio, en partes por mil (velocidad en m/s):

| Fulguración | Posición | H alfa (núcleo) | Ca II H y K | Ca II 8542 | Velocidad |
|---|---|---|---|---|---|
| X6.3, 22-02-2024 | disco (r = 0,59) | +5,3 ± 0,5 | +6,9 ± 1,2 | +2,3 ± 0,6 | +1,0 ± 0,4 |
| X2.8, 14-12-2023 | disco (r = 0,76) | +1,57 ± 0,09 | +4,0 ± 1,4 | +1,7 ± 0,3 | −0,4 ± 0,2 |
| X8.6, 14-05-2024 | limbo (r = 1,00) | +0,6 ± 0,6 | +1,1 ± 0,8 | +0,7 ± 0,5 | −0,3 ± 0,7 |
| X1.9, 23-02-2025 | casi limbo (r = 0,96) | −1,4 ± 0,4 | +0,2 ± 0,8 | +0,4 ± 0,4 | +0,3 ± 0,6 |

Lo que se ve hasta ahora:

- **Sobre el disco, detección clara.** H alfa sube entre 0,6 y 0,8 partes por mil por cada
  unidad de clase X, con significación de 10 a 17 sigmas.
- **En el limbo, nada.** La emisión de los pies de la fulguración queda oculta o muy
  escorzada.
- **La velocidad sigue sin moverse** en los mismos espectros.

Avisos:

- Son cuatro fulguraciones. Otras tres ya descargadas se pierden por nubes o cielo inestable.
- Falta la muestra de control para los espectros: el valor negativo de la X1.9 puede ser una
  deriva lenta con la altura del Sol, y sin controles no se puede distinguir.
- El error de cada valor sale de la dispersión de los espectros previos y no incluye esa
  deriva.

## 5. Cómo se ha medido la velocidad

| Paso | Qué se hace |
|---|---|
| Calidad | Se descartan los espectros con error de velocidad no válido, con relación señal/ruido a más del 1 % de su mediana móvil (nubes) o a más de 5 sigmas de la tendencia del día, y los días con dispersión superior a 1,5 m/s. Quedan 233 857 de 366 180. |
| Tendencia diaria | Se resta un polinomio de grado 2 a cada día. La dispersión de un espectro es de 0,81 m/s, casi toda por las oscilaciones solares. |
| Muestra | Entran 140 fulguraciones con ventanas completas antes y durante (139 con al menos tres controles). De las 279 observadas en el pico se pierden 53 por días descartados y 89 por ventanas incompletas, 38 de ellas porque la fulguración empezó al abrir el telescopio. |
| Controles | Para cada fulguración, épocas a la misma hora del día en días cercanos (±15) sin fulguraciones M o X a menos de 45 minutos. |
| Ruido | La dispersión de los controles da 0,39 m/s por fulguración. |
| Oscilaciones de 5 minutos | No se filtran: las ventanas promedian varios espectros y el ruido que dejan está incluido en los controles. |

Los cortes de calidad se eligieron mirando solo el ruido de los controles y el número de
fulguraciones, nunca el resultado. Las opciones de análisis se fijaron después del primer
piloto, no antes; la tabla de la sección 2 muestra que el resultado no depende de ellas.

## 6. Lo que falta

- **Más espectros.** Terminar la descarga de las fulguraciones más intensas y de sus
  controles, y medir cómo escala la respuesta cromosférica con la clase y con la posición.
- **Eruptivas frente a confinadas.** Falta cruzar con el catálogo de eyecciones.
- **Búsqueda bibliográfica a texto completo** antes de escribir.
