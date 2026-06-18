import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class ProductoModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento local de persistencia (MAE_PRODUCTO Avanzado).")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # desactivar temporalmente llaves foráneas para poder reestructurar sin conflictos
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # 1. crear la tabla de categorías si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CATEGORIA_PRODUCTO (
                id_categoria_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT
            )
        """)

        # control de migración de categorías: no destructivo
        # solo inicializamos si la tabla de categorías está vacía, sin borrar datos de producción
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_CATEGORIA_PRODUCTO")
        total_cats = cursor.fetchone()["total"]

        # semillero integrado de macro-categorías comerciales
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_CATEGORIA_PRODUCTO")
        if cursor.fetchone()["total"] == 0:
            categorias_semilla = [
                ("Sistemas y Hardware", "Componentes de cómputo, laptops y almacenamiento."),
                ("Servicios de Redes", "Soporte técnico, cableado y conectividad."),
                ("Libros y Educación", "Textos, novelas y material de estudio exonerado."),
                ("Alimentos Básicos", "Productos de primera necesidad y abarrotes."),
                ("Licores y Especiales", "Bebidas alcohólicas sujetas a tasas ISC."),
                ("Limpieza y Aseo", "Detergentes, desinfectantes y útiles de limpieza."),
                ("Cuidado Personal", "Artículos de higiene, belleza, cosméticos y farmacia."),
                ("Muebles y Decoración", "Mobiliario, iluminación y artículos del hogar."),
                ("Cocina y Menaje", "Vajilla, utensilios y electrodomésticos menores."),
                ("Papelería y Útiles", "Útiles de escritorio, cuadernos y papelería comercial."),
                ("Electrónica de Consumo", "Gadgets, audio, video y accesorios móviles."),
                ("Software y Suscripciones", "Licencias digitales, nube y herramientas TI."),
                ("Deportes y Fitness", "Equipamiento deportivo y suplementos de rendimiento."),
                ("Hobbies y Ocio", "Juegos de mesa, coleccionables y manualidades."),
                ("Mascotas", "Alimentos, juguetes y cuidado animal."),
                ("Moda y Accesorios", "Prendas de vestir, calzado y joyería."),
                ("Bienestar", "Vitaminas, suplementos naturales y nutrición."),
                ("Seguros y Servicios", "Servicios de salud, asesorías y soporte técnico.")
            ]
            for nombre, descripcion in categorias_semilla:
                cursor.execute("INSERT INTO MAE_CATEGORIA_PRODUCTO (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
            conn.commit()

        # 2. tabla de impuestos estándar de gobierno
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_IMPUESTO (
                id_impuesto INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(50) NOT NULL,
                porcentaje DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                tipo VARCHAR(20) NOT NULL DEFAULT 'PERCENT'
            )
        """)

        cursor.execute("SELECT COUNT(*) AS total FROM MAE_IMPUESTO")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("INSERT INTO MAE_IMPUESTO (nombre, porcentaje, tipo) VALUES ('IGV Normal', 18.00, 'PERCENT')")
            cursor.execute("INSERT INTO MAE_IMPUESTO (nombre, porcentaje, tipo) VALUES ('Exonerado (Libros/Alimentos)', 0.00, 'PERCENT')")
            cursor.execute("INSERT INTO MAE_IMPUESTO (nombre, porcentaje, tipo) VALUES ('Inafecto', 0.00, 'PERCENT')")
            conn.commit()

        # control de migración avanzado para isc: si la tabla de productos existe pero no tiene el campo 'volumen_litros',
        # la limpiamos de forma segura para asentar las nuevas columnas de auditoría tributaria.
        cursor.execute("PRAGMA table_info(MAE_PRODUCTO);")
        columnas_existentes = [row["name"] for row in cursor.fetchall()]
        if columnas_existentes and "volumen_litros" not in columnas_existentes:
            print("[DEBUG] Reestructurando MAE_PRODUCTO para añadir soporte de volumen e ISC específico.")
            cursor.execute("DROP TABLE IF EXISTS MAE_PRODUCTO;")
            conn.commit()

        # 3. tabla maestra de productos final (con soporte completo para los 3 sistemas de isc)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_PRODUCTO (
                id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barra VARCHAR(50) NOT NULL UNIQUE,
                nombre VARCHAR(100) NOT NULL,
                id_categoria_producto INTEGER NULL,
                id_impuesto INTEGER NOT NULL,
                descripcion TEXT,
                stock INTEGER NOT NULL DEFAULT 0,
                precio_unitario DECIMAL(10,2) NOT NULL,
                impuesto_extra DECIMAL(5,2) NULL DEFAULT 0.00,  -- Funciona como ISC Ad Valorem (%)
                isc_monto_fijo DECIMAL(5,2) NULL DEFAULT 0.00,   -- Monto fijo por litro (S/)
                volumen_litros DECIMAL(6,3) NULL DEFAULT 0.000,  -- Contenido expresado en Litros
                estado VARCHAR(20) DEFAULT 'Activo',
                FOREIGN KEY (id_categoria_producto) REFERENCES MAE_CATEGORIA_PRODUCTO (id_categoria_producto) ON DELETE SET NULL,
                FOREIGN KEY (id_impuesto) REFERENCES MAE_IMPUESTO (id_impuesto)
            )
        """)
        
        # check if "combustibles y carbones" category exists, if not, insert it
        cursor.execute("SELECT COUNT(*) FROM MAE_CATEGORIA_PRODUCTO WHERE nombre = 'Combustibles y Carbones'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO MAE_CATEGORIA_PRODUCTO (nombre, descripcion) VALUES (?, ?)", 
                           ("Combustibles y Carbones", "Bienes del Apéndice III (Combustibles) sujetos a ISC monto fijo."))

        # reactivar las restricciones de integridad de llaves foráneas
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()

    def obtener_categorias(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_categoria_producto, nombre FROM MAE_CATEGORIA_PRODUCTO ORDER BY nombre ASC")
        res = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return res

    def obtener_impuestos(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_impuesto, nombre, porcentaje FROM MAE_IMPUESTO ORDER BY id_impuesto ASC")
        res = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return res

    def obtener_todos(self):
        """Devuelve el inventario relacional completo inyectando los campos de ISC específico y volumen."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id_producto, p.codigo_barra AS codigo, p.nombre, p.descripcion, p.stock, 
                   p.precio_unitario, p.impuesto_extra, p.isc_monto_fijo, p.volumen_litros, p.estado,
                   c.nombre AS categoria_nombre,
                   i.nombre AS impuesto_nombre, i.porcentaje AS impuesto_porcentaje
            FROM MAE_PRODUCTO p
            LEFT JOIN MAE_CATEGORIA_PRODUCTO c ON p.id_categoria_producto = c.id_categoria_producto
            JOIN MAE_IMPUESTO i ON p.id_impuesto = i.id_impuesto
        """)
        resultado = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return resultado

    def insertar_producto_avanzado(self, d: dict):
        """Inserta el producto resguardando de forma segura todos los parámetros contra inyección SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # blindaje inyección sql: consulta preparada con mapeo explícito de los nuevos campos de volumen
            query = """
                INSERT INTO MAE_PRODUCTO (
                    codigo_barra, nombre, id_categoria_producto, id_impuesto, 
                    descripcion, stock, precio_unitario, impuesto_extra, isc_monto_fijo, volumen_litros
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                d["codigo_barra"], d["nombre"], d["id_categoria_producto"], d["id_impuesto"], 
                d["descripcion"], d["stock"], d["precio_unitario"], 
                d.get("impuesto_extra", 0.00), d.get("isc_monto_fijo", 0.00), d.get("volumen_litros", 0.000)
            ))
            conn.commit()
            print("[DEBUG] Inserción tributaria avanzada procesada con éxito en MAE_PRODUCTO.")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            conn.close()

    def modificar_estado_producto(self, codigo, nuevo_estado):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE MAE_PRODUCTO SET estado = ? WHERE codigo_barra = ?", (nuevo_estado, codigo))
        conn.commit()
        conn.close()

    def actualizar_producto(self, d: dict):
        """Actualiza un producto en la base de datos de forma segura contra inyección SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            query = """
                UPDATE MAE_PRODUCTO
                SET nombre = ?, id_categoria_producto = ?, id_impuesto = ?, descripcion = ?, 
                    stock = ?, precio_unitario = ?, impuesto_extra = ?, isc_monto_fijo = ?, volumen_litros = ?
                WHERE codigo_barra = ?
            """
            cursor.execute(query, (
                d["nombre"], d["id_categoria_producto"], d["id_impuesto"], d["descripcion"],
                d["stock"], d["precio_unitario"], d.get("impuesto_extra", 0.00),
                d.get("isc_monto_fijo", 0.00), d.get("volumen_litros", 0.000), d["codigo_barra"]
            ))
            conn.commit()
            print(f"[DEBUG] Producto {d['codigo_barra']} actualizado en MAE_PRODUCTO.")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            conn.close()

    def obtener_moneda_base_activa(self):
        """Devuelve el símbolo de la moneda base activa configurada para la empresa."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.simbolo 
                FROM MAE_EMPRESA e
                JOIN MAE_MONEDA m ON e.id_moneda_base = m.id_moneda
                LIMIT 1
            """)
            row = cursor.fetchone()
            return row["simbolo"] if row else "S/"
        except Exception:
            return "S/"
        finally:
            conn.close()