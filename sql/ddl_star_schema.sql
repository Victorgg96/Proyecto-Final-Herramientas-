-- ============================================================================
-- DDL Star Schema - Proyecto Analisis Sismico SSN-UNAM
-- Compatible con DuckDB, Databricks SQL, PostgreSQL.
-- En v2 las tablas Gold materializan este modelo (denormalizado para OLAP).
-- ============================================================================

DROP TABLE IF EXISTS fact_sismos;
DROP TABLE IF EXISTS dim_ubicacion;
DROP TABLE IF EXISTS dim_tiempo;
DROP TABLE IF EXISTS dim_clasificacion_magnitud;

CREATE TABLE dim_ubicacion (
    id_ubicacion        INT PRIMARY KEY,
    referencia_original VARCHAR(200),
    estado              VARCHAR(50),
    region_sismica      VARCHAR(50),
    zona_geografica     VARCHAR(50)
);

CREATE TABLE dim_tiempo (
    id_tiempo    INT PRIMARY KEY,
    fecha        DATE,
    anio         SMALLINT,
    mes          TINYINT,
    dia          TINYINT,
    hora_del_dia TINYINT,
    dia_semana   VARCHAR(12),
    estacion     VARCHAR(10),
    decada       SMALLINT
);

CREATE TABLE dim_clasificacion_magnitud (
    id_clasificacion INT PRIMARY KEY,
    categoria        VARCHAR(20),
    rango_min        FLOAT,
    rango_max        FLOAT,
    descripcion      VARCHAR(100)
);

CREATE TABLE fact_sismos (
    id_sismo         BIGINT PRIMARY KEY,
    fecha_local      DATE,
    hora_local       VARCHAR(8),
    fecha_utc        DATE,
    hora_utc         VARCHAR(8),
    magnitud         FLOAT,
    latitud          FLOAT,
    longitud         FLOAT,
    profundidad_km   FLOAT,
    estatus          VARCHAR(20),
    id_ubicacion     INT,
    id_tiempo        INT,
    id_clasificacion INT,
    FOREIGN KEY (id_ubicacion)     REFERENCES dim_ubicacion(id_ubicacion),
    FOREIGN KEY (id_tiempo)        REFERENCES dim_tiempo(id_tiempo),
    FOREIGN KEY (id_clasificacion) REFERENCES dim_clasificacion_magnitud(id_clasificacion)
);

INSERT INTO dim_clasificacion_magnitud VALUES
  (1, 'Micro',      0.0, 2.0, 'Generalmente no se siente'),
  (2, 'Menor',      2.0, 4.0, 'Se siente ligeramente'),
  (3, 'Ligero',     4.0, 5.0, 'Sacudida notable'),
  (4, 'Moderado',   5.0, 6.0, 'Puede causar danos menores'),
  (5, 'Fuerte',     6.0, 7.0, 'Danos en zonas pobladas'),
  (6, 'Mayor',      7.0, 8.0, 'Danos graves en areas extensas'),
  (7, 'Gran sismo', 8.0, 10.0, 'Devastacion en cientos de km');
