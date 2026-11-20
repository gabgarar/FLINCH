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
| Bootstrap por 81 regiones activas en vez de 111 días | 139 | −0,035 ± 0,035 | −0,010 ± 0,061 | −0,106 ± 0,082 |
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

## 4. Los mismos espectros sí ven las fulguraciones (preliminar)

Esta parte es el apoyo del resultado principal: demuestra que el resultado nulo en velocidad
no se debe a que los espectros no capten las fulguraciones. Que H alfa responda a las
fulguraciones en luz integrada ya se conoce (Otsu et al. 2022; Ma et al. 2024; Pietrow et
al. 2024).

![Respuesta espectral a la fulguración X6.3 del 22 de febrero de 2024](web/img/event_20240222_2233_X6.3.png)

Cambio medio entre 8 minutos antes y 10 después del máximo, en partes por mil, para las 12
fulguraciones X con espectros utilizables:

| Índice | Detectadas a más de 3 sigmas | Media en el disco (8) | Media cerca del limbo (4) | Dispersión de los controles (3) |
|---|---|---|---|---|
| H alfa, núcleo de 0,6 Å | 9 | +3,3 | +0,8 | 0,6 |
| Ca II H y K | 9 | +5,3 | +1,7 | 0,6 |
| H beta, núcleo (índice propio) | 9 | +2,2 | +0,9 | 0,14 |
| H alfa, banda de 1,6 Å | 8 | +1,1 | +0,4 | 0,12 |
| Ca II 8542 | 8 | +2,2 | +0,9 | 1,0 |
| Ca I 6573 (referencia fotosférica) | 1 | 0,0 | +0,2 | 0,17 |

- **Las ocho fulguraciones sobre el disco se detectan en H alfa**, de +1,0 a +10,9 partes
  por mil. Cerca del limbo la respuesta es débil o nula.
- **La respuesta sigue a la energía y a la posición, no a la clase**: correlación de rangos
  de 0,6 a 0,8 con la fluencia por el escorzo, y negativa con la clase GOES. Con 12 puntos
  es una indicación.
- **H beta es el índice más limpio.** El triplete infrarrojo del Ca II deriva tanto como
  responde. He I D3, Na I D, Paschen delta, Mn I 5395 y Mg I b2 no responden.
- **La velocidad no sigue a la respuesta cromosférica**: 0,06 ± 0,07 m/s por parte por mil
  de H alfa multiplicada por la rotación.
- **Nueve de las 12 tienen una eyección candidata** en el catálogo de LASCO; las que no,
  también responden.

La tabla fulguración a fulguración está en `results/spectral_response.csv` y en la web.

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

- **Controles espectrales.** Hay 3 ventanas utilizables; faltan las de las otras
  fulguraciones. La descarga depende de la velocidad de la conexión.
- **Comparar con los análisis publicados** de las fulguraciones en común (por ejemplo la
  X1.6 del 5 de agosto de 2023, en Otsu et al. 2024).
- **Leer completos** los artículos de Otsu et al. (2022, 2026) antes de afirmar qué es nuevo
  en la parte cromosférica.
