# FLINCH: resultados

Estado a 20 de noviembre de 2026.

Los resultados completos, con sus tablas y figuras, están en la web del proyecto, que tiene
versión en español:

- En el repositorio: [docs/web/results.es.md](web/results.es.md) (resultados) y
  [docs/web/method.es.md](web/method.es.md) (método).
- Publicada: <https://gabgarar.github.io/FLINCH/es/results/>.

Este archivo es solo el resumen, para no mantener dos copias del mismo texto.

## Resumen

**Pregunta.** ¿Contaminan las fulguraciones solares la detección de análogos terrestres por
velocidad radial?

**Respuesta.** No significativamente. Demostrado para el Sol, no para las estrellas de tipo
solar en general.

| Resultado | Valor |
|---|---|
| Cambio medio de velocidad durante una fulguración M o X, dos instrumentos (254 fulguraciones) | −0,029 ± 0,026 m/s; por debajo de 0,07 m/s al 95 % |
| Solo NEID (139) | −0,035 ± 0,035 m/s |
| Solo HARPS-N (115) | −0,021 ± 0,039 m/s |
| Clase X (18) | −0,074 ± 0,072 m/s; por debajo de 0,19 m/s |
| Término de rotación, para una X1 en el limbo | −0,006 ± 0,038 m/s; por debajo de 0,07 m/s |
| Cota de la luz de la fulguración | K · ΔF/F < 3,5 × 10⁻⁵ por X1, entre 1,5 y 3 veces lo máximo esperado |
| Señal añadida que se recupera | 98 % en los dos instrumentos |
| Respuesta de Ca II H y K, fulguraciones del disco | +5,3 ± 1,7 ‰ (8 de clase X), +2,2 ± 0,4 ‰ (6 de M5 a M9), 0,0 ± 0,2 ‰ (9 controles) |
| Respuesta del núcleo de H alfa | +3,3 ± 1,1 ‰, +2,0 ± 0,2 ‰, −0,1 ± 0,2 ‰ |
| Tiempo que el Sol pasa en fulguraciones M o X en el máximo del ciclo 25 | 1,5 % (0,1 % en las de clase X) |

## Cómo se reproduce

```
python -m flinch download
python -m flinch replication     # velocidad con NEID y HARPS-N
python -m flinch robustness      # variantes e inyecciones (NEID)
python -m flinch chromosphere    # respuesta de los espectros
python -m flinch paper-figures   # figuras del artículo
```

Las tablas quedan en `results/`. Los detalles de cada orden están en
[docs/web/reproduce.es.md](web/reproduce.es.md).

## Puntos abiertos

- **Un rasgo sin explicar.** De 60 a 50 minutos antes del máximo, las fulguraciones X de NEID
  están 0,44 ± 0,11 m/s por encima de la tendencia de su día (19 fulguraciones, 17 positivas).
  No aparece en las M ni en los controles, y HARPS-N no lo ve (−0,12 ± 0,11 en diez X). No se
  atribuye al Sol. En el artículo va en un apéndice.
- **Textos de agradecimiento** que piden NEID, WIYN, HARPS-N/TNG y DACE.
