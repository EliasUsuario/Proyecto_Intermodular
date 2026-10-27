-- Alumno: Elías Martínez
-- Cómo ejecutarlo:
--   1) Crear la BD:  CREATE DATABASE gestormaterial;
--   2) Ejecutar gestormaterial.sql para crear las tablas y la vista
--   3) Después ejecutar datos_prueba.sql

-- * BORRADO PREVIO
-- Borro todo para poder ejecutar el script las veces que haga falta mientras desarrollo (primero las tablas que dependen de otras).
-- ACLARACIÓN: esto borra TODOS los datos. No ejecutarlo si ya hay datos buenos.

DROP VIEW  IF EXISTS v_stock_bajo;
DROP TABLE IF EXISTS reservas CASCADE;
DROP TABLE IF EXISTS incidencias CASCADE;
DROP TABLE IF EXISTS prestamos CASCADE;
DROP TABLE IF EXISTS movimientos_consumible CASCADE;
DROP TABLE IF EXISTS maquinas CASCADE;
DROP TABLE IF EXISTS consumibles CASCADE;
DROP TABLE IF EXISTS articulos CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- 1_USUARIOS
-- Guarda a los operarios y a los administradores de la app.
-- El rol decide lo que puede hacer cada uno (se comprueba en la API).
-- El password se guarda encriptado (hash) en la API, no aquí. Aquí solo se define el campo.

CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL, -- NUNCA hay que guardar la contraseña en texto plano, siempre el hash (bcrypt)
    rol VARCHAR(20) NOT NULL DEFAULT 'operario',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_alta TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_usuarios_rol CHECK (rol IN ('operario', 'administrador'))
);


-- 2_CATEGORIAS
-- Para agrupar el material
CREATE TABLE categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
);

-- 3_ ARTICULOS (catalogo maestro)
-- Material, sea consumible o maquinaria.
-- "activo" = FALSE significa que el admin lo ha bloqueado / dado de baja.
-- El campo "tipo" dice en cuál de las dos tablas siguientes hay más datos.

CREATE TABLE articulos (
    id_articulo SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion	TEXT,
    id_categoria INT REFERENCES categorias(id_categoria),
    tipo VARCHAR(15) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_articulos_tipo CHECK (tipo IN ('consumible', 'maquinaria'))
);

-- Índice para las búsquedas por nombre del buscador
-- *COMPROBAR: comprobar si sirve con ILIKE '%texto%' o si hace falta otra cosa

CREATE INDEX idx_articulos_nombre ON articulos(nombre);


-- 4_CONSUMIBLES (material a granel)
-- Relación 1 a 1 con articulos (misma clave primaria).
-- Cada consumible tiene un QR para toda la referencia (no uno por unidad).
-- El stock lo dejo en INT aunque el cable se mida en metros y podría haber decimales (2,5 m). De momento metros enteros.
-- *A TENER EN CUENTA: nada impide meter aquí un artículo que sea de tipo 'maquinaria', eso lo compruebo en la API.

CREATE TABLE consumibles (
    id_articulo INT PRIMARY KEY REFERENCES articulos(id_articulo) ON DELETE CASCADE,
    codigo_qr VARCHAR(30) NOT NULL UNIQUE,
    unidad_medida VARCHAR(10) NOT NULL DEFAULT 'uds',   -- uds, m, kg...
    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 0,  -- por debajo de esto salta la alerta
    stock_reservado  INT NOT NULL DEFAULT 0,  -- bloqueo por el admin para una obra futura
    CONSTRAINT chk_stock_actual CHECK (stock_actual >= 0),
    CONSTRAINT chk_stock_minimo CHECK (stock_minimo >= 0),
     CONSTRAINT chk_stock_reservado CHECK (stock_reservado >= 0 AND stock_reservado <= stock_actual)
);

-- El operario solo puede restar de (stock_actual - stock_reservado)"
-- ** NO está aquí, hay que comprobarla en la API antes de hacer el UPDATE.


-- 5_MAQUINAS (activos únicos)
-- Resumen de Caracteristicas:
-- Cada fila es UNA unidad física con su propio QR (dos taladros iguales = dos filas con el mismo id_articulo).

-- Estados posibles:
-- disponible = se puede coger,
-- en_uso = la tiene un operario (ver tabla prestamos),
-- en_mantenimiento = bloqueada por una incidencia hasta que el admin la revise,
-- reservada = reservada por gerencia para una obra futura.

CREATE TABLE maquinas (
    id_maquina SERIAL PRIMARY KEY,
    id_articulo INT NOT NULL REFERENCES articulos(id_articulo),
    numero_serie VARCHAR(50) UNIQUE,
    codigo_qr VARCHAR(30) NOT NULL UNIQUE,
    estado VARCHAR(20) NOT NULL DEFAULT 'disponible',
    CONSTRAINT chk_maquinas_estado CHECK (estado IN ('disponible', 'en_uso', 'en_mantenimiento', 'reservada'))
);
-- * RECORDATORIO: el cambio de estado (disponible, en_uso, etc.) lo hace la API cuando se registra un préstamo, una devolución o una incidencia.


-- 6_FUNCIONES

-- 6.1 PRESTAMOS: quién se lleva qué máquina y cuándo la devuelve.
-- * RECORDATORIO:Si fecha_devolucion es NULL, el préstamo sigue abierto (la máquina está en uso).

CREATE TABLE prestamos (
    id_prestamo SERIAL PRIMARY KEY,
    id_maquina INT NOT NULL REFERENCES maquinas(id_maquina),
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    fecha_salida TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_devolucion TIMESTAMP,

    -- FUTURO (auditoría fotográfica): de momento van siempre a NULL, no se programa

    foto_salida VARCHAR(255),
    foto_devolucion VARCHAR(255),
    CONSTRAINT chk_prestamos_fechas CHECK (fecha_devolucion IS NULL OR fecha_devolucion >= fecha_salida)
);

-- Esto evita que una misma máquina tenga dos préstamos abiertos a la vez (el problema de que dos operarios la escaneen a la vez).

CREATE UNIQUE INDEX uq_prestamo_abierto ON prestamos(id_maquina) WHERE fecha_devolucion IS NULL;

CREATE INDEX idx_prestamos_usuario ON prestamos(id_usuario);

-- 6.2 INCIDENCIAS: daños reportados por el operario al devolver la máquina.
-- Cuelgan del préstamo (así sé quién la tenía cuando se dañó).
CREATE TABLE incidencias (
    id_incidencia SERIAL PRIMARY KEY,
    id_prestamo INT NOT NULL REFERENCES prestamos(id_prestamo),
    descripcion TEXT NOT NULL,
    fecha_reporte TIMESTAMP NOT NULL DEFAULT NOW(),
    resuelta BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_resolucion TIMESTAMP,
    id_admin_resuelve INT REFERENCES usuarios(id_usuario)
);
-- *RECORDATORIO: al resolver una incidencia hay que poner la máquina en 'disponible' (desde la API).

-- 6.3 MOVIMIENTOS_CONSUMIBLE: histórico de cada +1 / -1 (o más) que se hace al stock.
-- (Cantidad es positiva si se añade stock y negativa si se gasta).

CREATE TABLE movimientos_consumible (
    id_movimiento SERIAL PRIMARY KEY,
    id_articulo INT NOT NULL REFERENCES consumibles(id_articulo),
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    cantidad INT NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT NOW(),
    -- FUTURO (modo offline): id que generaría el móvil para no duplicar peticiones. No se usa todavía.
    id_operacion VARCHAR(40),
    CONSTRAINT chk_mov_cantidad CHECK (cantidad <> 0)
);

CREATE INDEX idx_mov_articulo ON movimientos_consumible(id_articulo);

-- 6.4 RESERVAS: el admin bloquea una máquina o una cantidad de consumible para una obra futura. 
-- O es de una máquina o es de un consumible, nunca de las dos cosas a la vez (el CHECK de abajo lo controla).
CREATE TABLE reservas (
    id_reserva SERIAL PRIMARY KEY,
    id_admin INT NOT NULL REFERENCES usuarios(id_usuario),
    id_maquina INT REFERENCES maquinas(id_maquina),
    id_articulo INT REFERENCES consumibles(id_articulo),
    cantidad INT,
    motivo VARCHAR(200) NOT NULL,        -- p. ej. nombre de la obra
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_reservas_destino CHECK (
        (id_maquina IS NOT NULL AND id_articulo IS NULL AND cantidad IS NULL)
        OR
        (id_maquina IS NULL AND id_articulo IS NOT NULL AND cantidad IS NOT NULL AND cantidad > 0)
    )
);
-- * A TENER EN CUENTA: al crear una reserva de consumible hay que sumar la cantidad a consumibles.stock_reservado, y al cancelarla restarla. 
-- * Y para máquinas, cambiar el estado a 'reservada'. Todo desde la API.



-- 7. VISTA STOCK BAJO
-- Consumibles cuyo stock ha caído por debajo del mínimo.
-- La usa el endpoint GET /stock-bajo para el administrador.

CREATE VIEW v_stock_bajo AS
SELECT a.id_articulo,
       a.nombre,
       c.stock_actual,
       c.stock_minimo,
       c.unidad_medida
FROM consumibles c
JOIN articulos a ON a.id_articulo = c.id_articulo
WHERE c.stock_actual < c.stock_minimo
  AND a.activo = TRUE;
