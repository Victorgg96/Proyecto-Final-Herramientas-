# Diccionario de Datos — Proyecto SSN-UNAM v2

## Capa Bronze (`data/bronze/sismos_raw/`)
Parquet crudo particionado por `anio_evento`. Sin transformación de tipos (todo `string`).

| Campo | Tipo | Origen |
|---|---|---|
| Fecha | string | SSN |
| Hora | string | SSN |
| Magnitud | string | SSN |
| Latitud | string | SSN |
| Longitud | string | SSN |
| Profundidad | string | SSN |
| Referencia_de_localizacion | string | SSN |
| Fecha_UTC | string | SSN |
| Hora_UTC | string | SSN |
| Estatus | string | SSN |
| anio_evento | int | partición |

## Capa Silver (`data/silver/sismos_clean/`)
Parquet+Snappy particionado por `anio`.

| Campo | Tipo | Regla |
|---|---|---|
| fecha_local | datetime | Cast desde Fecha |
| hora_local | string | Conservada |
| fecha_utc / hora_utc | datetime / string | Cast |
| magnitud | float | Cast; NULL si no calculable |
| magnitud_disponible | bool | NOT NULL flag |
| clasificacion_magnitud | string | Micro/Menor/Ligero/Moderado/Fuerte/Mayor/Gran sismo |
| latitud / longitud / profundidad_km | float | En rango MX |
| referencia | string | Texto original |
| estado | string | Mapeado por regex |
| region_sismica | string | CENAPRED |
| zona_geografica | string | Pacifico/Golfo/Centro/etc |
| estatus | string | revisado / verificado |
| anio, mes, dia, hora_del_dia | int | Derivados |
| dia_semana, estacion | string | Derivados |
| decada | int | anio // 10 * 10 |

## Capa Gold

### gold_sismicidad_regional
`estado, region_sismica, zona_geografica, anio, total_sismos, magnitud_promedio, magnitud_maxima, profundidad_promedio, sismos_mag5_plus, sismos_mag7_plus`

### gold_patrones_temporales
`hora_del_dia, dia_semana, mes, estacion, total_sismos, magnitud_promedio, magnitud_maxima`

### gold_sismos_significativos (mag ≥ 5.0)
`fecha_local, hora_local, magnitud, clasificacion_magnitud, latitud, longitud, profundidad_km, estado, region_sismica, zona_geografica, distancia_cdmx_km, tsunami_probable, estatus, anio`

### gold_evolucion_historica_anual / mensual
`anio[, mes, decada], total_sismos, magnitud_promedio, magnitud_maxima, sismos_mag5_plus, sismos_mag7_plus`
