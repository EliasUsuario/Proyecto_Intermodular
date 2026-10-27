
-- Alumno: Elías Martínez
-- *IMPORTANTE:Ejecutar después de gestormaterial.sql

-- USUARIOS (id 1, 2, 3)
-- Contraseñas de prueba: admin1234 / laura1234 / pedro1234
-- Los hashes los generé con generar_hash.py (carpeta backend), que usa bcrypt

INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES
    ('Admin Taller', 'admin@gestormaterial.com', '$2b$12$uzo7zMuw.AEso2vXAfURn.WOdoN16tmnswZm8AxsHHLvtasKIIigG', 'administrador'),
    ('Laura Gómez',  'laura@gestormaterial.com', '$2b$12$eQ0LG3Sxxdu9cPEfrkp5t.NbutzoPfMvs0cWwJecJBZy/MlacdOaO', 'operario'),
    ('Pedro Ruiz',   'pedro@gestormaterial.com', '$2b$12$ZqAi.9NOnYC5/28f84KqK.oEHj5DAVV6.RaY4DJEdIR15YwtGy2AK', 'operario');

-- CATEGORIAS (id 1 a 5)
INSERT INTO categorias (nombre) VALUES
    ('Cables'), --id 1
    ('Conectores'), -- 2
    ('Tornillería'), -- 3
    ('Herramienta eléctrica'), -- 4
    ('Medición');  --id 5



-- ARTICULOS (id 1 a 7): los 4 primeros son consumibles y los 3 últimos maquinas

INSERT INTO articulos (nombre, descripcion, id_categoria, tipo) VALUES
    ('Cable 2,5 mm', 'Cable de cobre para instalaciones', 1, 'consumible'),  --id 1
    ('Conector', 'Conector de red', 2, 'consumible'),  -- 2
    ('Tornillo M4 x 20', 'Tornillo de metrica 4', 3, 'consumible'),  -- 3
    ('Terminal', 'Terminal para cable', 2, 'consumible'),  -- 4
    ('Taladro percutor', 'Taladro con percusión', 4, 'maquinaria'),  -- 5
    ('Multímetro', 'Medidor de voltage y amperaje', 5, 'maquinaria'),  -- 6
    ('Soldador de estaño', 'Soldador estaño', 4, 'maquinaria');  -- 7

-- CONSUMIBLES (el id es el mismo que el del artículo)
-- El artículo 3 tiene 50 reservados para una obra (se ve en tabla de reservas que está más abajo).

INSERT INTO consumibles (id_articulo, codigo_qr, unidad_medida, stock_actual, stock_reservado) VALUES
    (1, 'CON-0001', 'm', 120, 0),
    (2, 'CON-0002', 'uds', 80, 0),
    (3, 'CON-0003', 'uds', 500, 50),
    (4, 'CON-0004', 'uds', 12, 0);



-- MAQUINAS (id 1 a 5)
-- Para probar todos los estados:
--   1 disponible, 2 en_uso (la tiene Laura), 3 en_mantenimiento (incidencia abierta), 4 disponible, 5 reservada (obra futura)

INSERT INTO maquinas (id_articulo, numero_serie, codigo_qr, estado) VALUES
    (5, 'TAL-XXXX-001', 'MAQ-0001', 'disponible'), -- 1
    (5, 'TAL-XXXX-002', 'MAQ-0002', 'en_uso'), -- 2
    (6, 'MUL-XXXX-014', 'MAQ-0003', 'en_mantenimiento'), -- 3
    (6, 'MUL-XXXX-015', 'MAQ-0004', 'disponible'), -- 4
    (7, 'SOL-XXXX-003', 'MAQ-0005', 'reservada');  -- 5


-- PRESTAMOS (id 1 a 3)
-- 1: abierto, Laura tiene el taladro 2 desde hace 2 horas
-- 2: devuelto por Pedro, el multímetro 3 (con incidencia, ver en la tabla de abajo)
-- 3: devuelto por Pedro, el taladro 1 sin problemas

INSERT INTO prestamos (id_maquina, id_usuario, fecha_salida, fecha_devolucion) VALUES
    (2, 2, NOW() - INTERVAL '2 hours',  NULL),
    (3, 3, NOW() - INTERVAL '2 days',   NOW() - INTERVAL '1 day'),
    (1, 3, NOW() - INTERVAL '5 days',   NOW() - INTERVAL '4 days 21 hours');

-- INCIDENCIAS: la del préstamo 2 (multímetro 3) sigue sin resolver

INSERT INTO incidencias (id_prestamo, descripcion, resuelta) VALUES
    (2, 'Se me cayó al suelo y la pantalla ya no enciende', FALSE);


-- MOVIMIENTOS DE CONSUMIBLES (cantidad negativa = gasto)
-- OJO: el stock de arriba ya es el stock actual, no he restado estos movimientos a mano, solo están para tener histórico que enseñar.

INSERT INTO movimientos_consumible (id_articulo, id_usuario, cantidad) VALUES
    (1, 1,  50),    -- el admin añade 50 m de cable (nuevo material)
    (1, 2,  -5),
    (2, 3, -10),
    (3, 3, -20),
    (4, 2,  -3);

-- RESERVAS (fase 2): una máquina (la 5) y 50 uds del consumible 3

INSERT INTO reservas (id_admin, id_maquina, id_articulo, cantidad, motivo) VALUES
    (1, 5, NULL, NULL, 'Obra: instalación nave Polígono Sur'),
    (1, NULL, 3, 50,   'Obra: instalación nave Polígono Sur');
