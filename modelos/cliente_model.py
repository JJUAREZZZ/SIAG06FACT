import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class ClienteModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento de datos maestros (MAE_CLIENTE).")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # habilitar soporte nativo de restricciones de integridad referencial (foreign keys)
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # validación de migración: si existía la tabla 'cliente' minimalista antigua, la removemos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cliente';")
        if cursor.fetchone():
            print("[DEBUG] Detectada estructura heredada 'cliente'. Ejecutando migración de esquema corporativo.")
            cursor.execute("DROP TABLE cliente;")
            conn.commit()

        # 1. crear tabla maestra de categorías de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CATEGORIA_CLIENTE (
                id_categoria_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL
            )
        """)

        # semillero de categoría base: insertar una fila inicial si la tabla está vacía
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_CATEGORIA_CLIENTE")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("INSERT INTO MAE_CATEGORIA_CLIENTE (nombre) VALUES ('General')")
            conn.commit()

        # 2. crear tabla maestra principal de clientes (con campos completos y llaves foráneas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CLIENTE (
                dni_ruc VARCHAR(15) PRIMARY KEY,
                tipo_documento VARCHAR(20) NOT NULL DEFAULT 'DNI',
                nombre_razon_social VARCHAR(150) NOT NULL,
                id_categoria_cliente INTEGER NULL,
                direccion VARCHAR(200),
                email VARCHAR(100),
                telefono VARCHAR(15),
                estado VARCHAR(20) DEFAULT 'Activo',
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_categoria_cliente) REFERENCES MAE_CATEGORIA_CLIENTE (id_categoria_cliente) ON DELETE SET NULL
            )
        """)
        conn.commit()
        conn.close()

    def obtener_todos(self):
        """Obtiene la lista de clientes completa desde la persistencia formal MAE_CLIENTE."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # mantenemos las columnas exactas que tu clientecontroller y clienteview esperan mapear
        cursor.execute("""
            SELECT dni_ruc, tipo_documento, nombre_razon_social, direccion, email, telefono, estado, fecha_registro 
            FROM MAE_CLIENTE
        """)
        resultado = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return resultado

    def insertar_cliente(self, datos):
        """Inserta un nuevo registro de forma parametrizada y aislada contra inyecciones SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # tu formulario actual envía una tupla de 5 elementos: (dni_ruc, nombre_razon_social, direccion, email, telefono)
            dni_ruc, nombre_razon_social, direccion, email, telefono = datos
            
            # evaluamos dinámicamente el tipo de documento basándonos en la longitud del identificador
            # si tiene 11 caracteres asumimos ruc corporativo, de lo contrario se guarda como dni base
            tipo_doc = "RUC" if len(dni_ruc) == 11 else "DNI"
            
            # recuperamos el id de la categoría por defecto 'general' creada en el inicializador
            cursor.execute("SELECT id_categoria_cliente FROM MAE_CATEGORIA_CLIENTE WHERE nombre = 'General' LIMIT 1")
            row_cat = cursor.fetchone()
            id_categoria_base = row_cat["id_categoria_cliente"] if row_cat else 1

            # blindaje inyección sql: los parámetros se inyectan de forma segura mediante placeholders '?'
            query = """
                INSERT INTO MAE_CLIENTE (dni_ruc, tipo_documento, nombre_razon_social, id_categoria_cliente, direccion, email, telefono)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (dni_ruc, tipo_doc, nombre_razon_social, id_categoria_base, direccion, email, telefono))
            conn.commit()
            print("[DEBUG] Transacción de inserción en MAE_CLIENTE completada con éxito.")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            conn.close()

    def actualizar_cliente(self, dni_ruc, nombre_razon_social, direccion, email, telefono):
        """Actualiza la información de un cliente en la base de datos de forma segura contra inyecciones SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # evaluamos el tipo de documento basándonos en la longitud del identificador
            tipo_doc = "RUC" if len(dni_ruc) == 11 else "DNI"
            
            cursor.execute("""
                UPDATE MAE_CLIENTE
                SET tipo_documento = ?, nombre_razon_social = ?, direccion = ?, email = ?, telefono = ?
                WHERE dni_ruc = ?
            """, (tipo_doc, nombre_razon_social, direccion, email, telefono, dni_ruc))
            conn.commit()
            print(f"[DEBUG] Cliente {dni_ruc} actualizado en MAE_CLIENTE.")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            conn.close()

    def modificar_estado_cliente(self, dni_ruc, nuevo_estado):
        """Actualiza el estado administrativo aislando estrictamente las variables de entrada."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # blindaje inyección sql: parámetros tipados como texto plano para evitar escapes de comandos sql
        cursor.execute("""
            UPDATE MAE_CLIENTE 
            SET estado = ? 
            WHERE dni_ruc = ?
        """, (nuevo_estado, dni_ruc))
        
        conn.commit()
        conn.close()
        print("[DEBUG] Modificación de estado en MAE_CLIENTE realizada con éxito.")

    def obtener_con_saldo_pendiente_count(self):
        """Devuelve la cantidad de clientes únicos con al menos una factura pendiente."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(DISTINCT dni_ruc) FROM TRS_FACTURA WHERE estado = 'Pendiente'")
            return cursor.fetchone()[0]
        except Exception:
            return 0
        finally:
            conn.close()