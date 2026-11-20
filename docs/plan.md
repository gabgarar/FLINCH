# FLINCH: plan de trabajo

**FL**are-**IN**duced **CH**anges in Sun-as-a-star radial velocities.
*¿Contaminan las fulguraciones solares la detección de análogos terrestres por velocidad radial?*

Estado a 20 de noviembre de 2026: fases 0 a 3 hechas para la velocidad (resultado nulo, con
controles, robustez e inyecciones) y fase 4 avanzada (12 fulguraciones X con espectros).
Los resultados están en [resultados.md](resultados.md).

**Enfoque del artículo, decidido el 20-11-2026:** el resultado principal es la velocidad,
que es lo que no ha hecho nadie para el Sol (solo hay dos fulguraciones publicadas, en
Pietrow et al. 2024). La respuesta cromosférica ya se conoce por trabajos con otros
instrumentos y pasa a ser el apoyo: demuestra que los mismos espectros sí ven las
fulguraciones.

## 1. La pregunta

Los espectrógrafos que buscan exoplanetas miden la velocidad radial de una estrella con
precisión de decenas de centímetros por segundo. NEID (Kitt Peak, Arizona) observa además el
Sol cada día como si fuera una estrella lejana, con un espectro cada 83 segundos.

Queremos saber tres cosas:

1. Si una fulguración solar deja huella en la velocidad radial del Sol visto como estrella.
2. A partir de qué tamaño de fulguración, y cuánto.
3. Qué implica para la búsqueda de planetas en estrellas de tipo solar, donde no se puede
   ver la fulguración por separado.

La señal que la Tierra imprime en el Sol es de 9 cm/s. Esa cifra es la vara de medir: si las
fulguraciones mueven la velocidad más que eso, importan para detectar gemelos de la Tierra;
si no, se pueden ignorar.

## 2. Qué hay publicado

Búsqueda en ADS por título y resumen el 19 de noviembre de 2026 (no exhaustiva):

- **Pietrow et al. 2024** (A&A 682, A46): dos fulguraciones (X2.2 y X9.3) vistas con
  HARPS-N. Es el único estudio de fulguraciones en un espectrógrafo de este tipo que
  aparece; 40 citas en dos años.
- **Fulguraciones con NEID**: ningún resultado.
- **Estudio estadístico** de la respuesta en velocidad radial: ningún resultado.

Antes de escribir hay que repetir la búsqueda a texto completo y revisar los artículos que
citan a Pietrow et al. 2024.

## 3. Datos

Todo es público y sin registro. Se descarga con `python -m flinch download` (20 MB).

| Dato | Fuente | Comprobado |
|---|---|---|
| Velocidades del Sol | Archivo solar de NEID, tabla `neidsolarl2` (servicio TAP) | Sí |
| Lista de fulguraciones | Resúmenes de GOES-16 y GOES-18 XRS, calidad científica (NOAA) | Sí |
| Posición de cada fulguración | Productos `xrsf-l2-flloc` y `suvi-l2-flloc` de GOES | Existen; sin abrir |
| Eyecciones (CME) | Catálogo CDAW de SOHO/LASCO, hasta el 31-08-2026 | Sí |
| Espectros completos de NEID | Archivo de NEID | **No**: la dirección probada dio error 404 |
| HARPS-N y KPF solares | DACE y KOA | Sin comprobar |

Tabla de NEID: 366 180 espectros entre el 11-12-2020 y el 12-11-2026, con error fotónico
por medida de unos 0,3 m/s.

| Año | Días observados | Espectros |
|---|---|---|
| 2020 | 21 | 4 076 |
| 2021 | 334 | 70 722 |
| 2022 | 212 | 50 199 |
| 2023 | 310 | 72 146 |
| 2024 | 163 | 38 742 |
| 2025 | 302 | 70 390 |
| 2026 | 260 | 59 905 |

Las caídas de 2022 y 2024 tienen causa por confirmar.

## 4. La muestra

Resultado de `python -m flinch coverage` (se guarda en `results/flare_sample.csv`):

| Clase GOES | Fulguraciones en el periodo | NEID observando en el pico | Con 30 min antes y después |
|---|---|---|---|
| M1 a M4 | 1833 | 236 | 208 |
| M5 a M9 | 185 | 24 | 21 |
| X | 104 | 19 | 19 |
| **Total** | **2122** | **279** | **248** |

Entre las de clase X está la mayor de mayo de 2024 (X8.6 según GOES-16, 14-05-2024 16:51 UT).

Criterios: "en el pico" es al menos un espectro a menos de 2 minutos del máximo en rayos X;
"con 30 min" exige además 5 espectros en la media hora anterior al inicio y 5 en la
posterior al máximo. GOES-16 es la lista principal y GOES-18 cubre sus huecos y continúa
desde abril de 2025. La clase de una misma fulguración cambia unas centésimas entre
satélites (X8.5 o X8.6).

## 5. Qué esperamos ver

Tres mecanismos posibles, de más a menos previsible:

1. **Desequilibrio de rotación.** La fulguración es una mancha brillante en un disco que
   gira. Si está en la mitad que se acerca (este), la velocidad debería bajar; en la que se
   aleja (oeste), subir. Es una predicción comprobable: el signo depende de la longitud.
2. **Líneas alteradas.** La emisión cromosférica rellena o deforma algunas líneas del
   espectro y sesga la medida. Magnitud desconocida.
3. **Oscilaciones globales.** Una fulguración grande podría aumentar la amplitud de las
   oscilaciones de 5 minutos (propuesto por Karoff y Kjeldsen en 2008; tema casi abandonado).

Estimación a mano, por comprobar en la fase 2:

- **Señal esperada (mecanismo 1):** una fulguración X aumenta el brillo del disco entre
  10 y 100 partes por millón; con velocidades de rotación de hasta 2 km/s salen entre
  2 y 20 cm/s. Las de clase M darían centímetros por segundo o menos.
- **Sensibilidad:** con el ruido de las oscilaciones solares, unos 0,5 m/s por fulguración
  en una ventana de 10 minutos. Apilando 248 fulguraciones, unos 3 cm/s; solo las 19 de
  clase X, unos 10 cm/s.

Conclusión honesta: lo más probable es una cota superior del orden de los centímetros por
segundo, o una detección marginal en las de clase X. Las dos cosas responden a la pregunta.

## 6. Fases

### Fase 0. Viabilidad y proyecto (hecha)

Datos localizados, muestra contada, paquete `flinch` con descarga, cruce y tests.

### Fase 1. Muestra definitiva

- Cortes de calidad en NEID: columnas `rejected`, `flagged`, `extsnr`, `airmass`, `sunagl`.
- Posición (longitud y latitud) de cada fulguración.
- Etiqueta eruptiva o confinada cruzando con el catálogo de CME.
- Duración e impulsividad a partir de GOES.

Entregable: tabla de fulguraciones con todos los atributos.

### Fase 2. Piloto y base segura

- Para cada fulguración: velocidades de -60 a +90 minutos respecto al máximo, restando la
  tendencia lenta ajustada fuera de la fulguración.
- Apilado por clase, con errores por remuestreo.
- **Muestra de control:** ventanas sin fulguración, a las mismas horas del día y en las
  mismas épocas. Sin esto no se puede distinguir una señal de un efecto del instrumento o
  de la atmósfera.

Empezar por las 19 de clase X. Entregable: curva media de velocidad alrededor del máximo y
detección o cota superior por clase.

**Decisión tras el piloto:**

- Si el ruido medido en el control coincide con el estimado, seguir.
- Si dominan las nubes o la masa de aire, restringir a los mejores datos y recalcular.
- Si la cota queda por encima de unos 30 cm/s, no dice nada útil: el peso del artículo
  pasa a la fase 4.

### Fase 3. Pruebas físicas

- Signo del cambio según la longitud de la fulguración (este frente a oeste).
- Escalado con el flujo máximo y con la energía integrada.
- Eruptivas frente a confinadas; impulsivas frente a graduales.

Entregable: qué mecanismo domina, o qué mecanismos quedan descartados.

### Fase 4. Parte ambiciosa: los espectros

- Resolver primero la descarga de los espectros completos (cliente `pyNEID`) y medir cuánto
  ocupan.
- Para las mayores fulguraciones: perfiles de contraste de las líneas cromosféricas
  (Ca II H y K, H alfa, He I D3, Na D) y búsqueda de asimetrías hacia el azul, que es la
  huella de una eyección que se intenta detectar en otras estrellas.
- Comparación con las dos fulguraciones de Pietrow et al. 2024.

Entregable: qué líneas responden, desde qué clase, y si las eruptivas se distinguen.

### Fase 5. Opcional

- Amplitud de las oscilaciones de 5 minutos antes y después de las fulguraciones.
- Comprobación con un segundo espectrógrafo (HARPS-N o KPF).

### Fase 6. Artículo y documentación

- Revista objetivo: A&A; Solar Physics como alternativa.
- Título de trabajo: *Does the Sun flinch? The radial-velocity response of the Sun as a
  star to M- and X-class flares*.
- Documentación con mkdocs sobre la carpeta `docs/`.

## 7. Comprobaciones pendientes

| Asunto | Por qué importa |
|---|---|
| `obsjd` frente a `ccfjdsum` | Difieren unos 6,8 minutos; el segundo parece estar en otro sistema de tiempo. Se usa `obsjd`, pero hay que confirmarlo en la documentación de NEID. |
| Si `obsjd` es el inicio o el centro de la exposición | Desplaza hasta medio minuto. |
| Qué correcciones lleva `ccfrvmod` | Rotación de la Tierra, extinción diferencial y movimiento Sol-observador dejan tendencias diarias. |
| Significado de `rejected` y `flagged` | Definen los cortes de calidad. |
| Escala de tiempo de GOES | Posible desfase de segundos por los segundos intercalares. |
| Artículos de descripción de los datos solares de NEID | Hay que citarlos y leer sus avisos. |

## 8. Riesgos

| Riesgo | Qué hacemos |
|---|---|
| Resultado nulo | Es publicable como cota, y la fase 4 aporta señales que sí se esperan. |
| Otro grupo publica antes | Empezar por la base segura, que es rápida, y vigilar ADS y arXiv. |
| Efectos sistemáticos mayores que la señal | Muestra de control desde el primer día. |
| Los espectros no se pueden descargar o pesan demasiado | La base segura no depende de ellos; limitarse a las fulguraciones mayores. |

## 9. Revisión externa del plan (20-11-2026)

Una revisión del plan pidió reforzar seis puntos. Estado de cada uno:

| Petición | Qué se ha hecho |
|---|---|
| No apilar solo por el máximo de GOES | Ventanas en el inicio, en el máximo y en la fase impulsiva (máximo de la derivada del flujo). |
| El análisis con signo como eje, no como comprobación | El ajuste frente a flujo × rotación proyectada es uno de los tres resultados principales. |
| Escala física explícita | Se formula como ΔRV ≈ (ΔF/F) · v_rot · K y la cota se da sobre K · ΔF/F. |
| Fijar el modelo de fondo | Opciones por defecto escritas y tabla de robustez variándolas. Se fijaron tras el primer piloto, no antes. |
| Sucesos no independientes | Bootstrap por día de observación y, como comprobación, por región activa (81 grupos): los errores cambian menos de un 2 %. |
| Controles falsos más exigentes | Inyección a 5, 10, 20 y 50 cm/s y permutación de posiciones. Los controles del mismo día solo existen para 8 fulguraciones. |

## 10. Referencias de partida

- Pietrow et al. 2024, A&A 682, A46 (2024A&A...682A..46P).
- Karoff y Kjeldsen 2008, ApJ 678, L73 (2008ApJ...678L..73K).
- Kumar et al. 2017, MNRAS: fulguraciones y ondas globales con GOLF y VIRGO.
