import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class ClienteModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento de datos maestros (MAE_CLIENTE).")
        self._cache_clientes = None
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
        
        # validacion de migracion: si existia la tabla 'cliente' minimalista antigua la removemos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cliente';")
        if cursor.fetchone():
            print("[DEBUG] Detectada estructura heredada 'cliente'. Ejecutando migración de esquema corporativo.")
            cursor.execute("DROP TABLE cliente;")
            conn.commit()

        # 1. crear tabla maestra de categorias de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CATEGORIA_CLIENTE (
                id_categoria_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL
            )
        """)

        # semillero de categoria base: insertar una fila inicial si la tabla esta vacia
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_CATEGORIA_CLIENTE")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("INSERT INTO MAE_CATEGORIA_CLIENTE (nombre) VALUES ('General')")
            conn.commit()

        # 2. crear tabla maestra principal de clientes (con campos completos y llaves foraneas)
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
                usuario_creacion VARCHAR(50),
                fecha_creacion DATETIME,
                usuario_modificacion VARCHAR(50),
                fecha_modificacion DATETIME,
                FOREIGN KEY (id_categoria_cliente) REFERENCES MAE_CATEGORIA_CLIENTE (id_categoria_cliente) ON DELETE SET NULL
            )
        """)
        conn.commit()
        conn.close()

    def obtener_todos(self):
        # usar cache local
        if self._cache_clientes is not None:
            return self._cache_clientes

        conn = self._get_connection()
        cursor = conn.cursor()
        
        # mantenemos las columnas y agregamos las de auditoria
        cursor.execute("""
            SELECT dni_ruc, tipo_documento, nombre_razon_social, direccion, email, telefono, estado, fecha_registro,
                   usuario_creacion, fecha_creacion, usuario_modificacion, fecha_modificacion
            FROM MAE_CLIENTE
        """)
        resultado = [dict(row) for row in cursor.fetchall()]
        conn.close()
        self._cache_clientes = resultado
        return resultado

    def insertar_cliente(self, datos, usuario="admin"):
        # insertar un nuevo registro de forma parametrizada y limpiar cache
        self._cache_clientes = None
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            dni_ruc, nombre_razon_social, direccion, email, telefono = datos
            tipo_doc = "RUC" if len(dni_ruc) == 11 else "DNI"
            
            cursor.execute("SELECT id_categoria_cliente FROM MAE_CATEGORIA_CLIENTE WHERE nombre = 'General' LIMIT 1")
            row_cat = cursor.fetchone()
            id_categoria_base = row_cat["id_categoria_cliente"] if row_cat else 1

            from datetime import datetime
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            query = """
                INSERT INTO MAE_CLIENTE (dni_ruc, tipo_documento, nombre_razon_social, id_categoria_cliente, direccion, email, telefono, usuario_creacion, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (dni_ruc, tipo_doc, nombre_razon_social, id_categoria_base, direccion, email, telefono, usuario, fecha_actual))
            conn.commit()
            print("[DEBUG] Transacción de inserción en MAE_CLIENTE completada con éxito.")
            
            # log audit event to trs_auditoria_log after commit to avoid locks
            try:
                import json
                from controladores.AuditoriaService import AuditoriaService
                val_nuevo = {
                    "dni_ruc": dni_ruc, "tipo_documento": tipo_doc, 
                    "nombre_razon_social": nombre_razon_social, "direccion": direccion, 
                    "email": email, "telefono": telefono
                }
                AuditoriaService.registrar("CREAR_CLIENTE", dni_ruc, None, json.dumps(val_nuevo))
            except Exception as ae:
                print(f"[DEBUG ERROR] falla al registrar auditoria: {ae}")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            conn.close()

    def actualizar_cliente(self, dni_ruc, nombre_razon_social, direccion, email, telefono, usuario="admin"):
        # actualizar informacion del cliente y limpiar cache
        self._cache_clientes = None
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            tipo_doc = "RUC" if len(dni_ruc) == 11 else "DNI"
            
            # obtener datos anteriores
            cursor.execute("SELECT nombre_razon_social, direccion, email, telefono, tipo_documento FROM MAE_CLIENTE WHERE dni_ruc = ?", (dni_ruc,))
            row_old = cursor.fetchone()
            val_ant = dict(row_old) if row_old else None
            
            from datetime import datetime
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                UPDATE MAE_CLIENTE
                SET tipo_documento = ?, nombre_razon_social = ?, direccion = ?, email = ?, telefono = ?, usuario_modificacion = ?, fecha_modificacion = ?
                WHERE dni_ruc = ?
            """, (tipo_doc, nombre_razon_social, direccion, email, telefono, usuario, fecha_actual, dni_ruc))
            conn.commit()
            print(f"[DEBUG] Cliente {dni_ruc} actualizado en MAE_CLIENTE.")
            
            # log audit event to trs_auditoria_log after commit to avoid locks
            try:
                import json
                from controladores.AuditoriaService import AuditoriaService
                val_nuevo = {
                    "dni_ruc": dni_ruc, "tipo_documento": tipo_doc,
                    "nombre_razon_social": nombre_razon_social, "direccion": direccion,
                    "email": email, "telefono": telefono
                }
                AuditoriaService.registrar("MODIFICAR_CLIENTE", dni_ruc, json.dumps(val_ant) if val_ant else None, json.dumps(val_nuevo))
            except Exception as ae:
                print(f"[DEBUG ERROR] falla al registrar auditoria: {ae}")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise e
        finally:
            conn.close()

    def modificar_estado_cliente(self, dni_ruc, nuevo_estado, usuario="admin"):
        # cambiar estado del cliente y limpiar cache
        self._cache_clientes = None
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # obtener estado anterior
        cursor.execute("SELECT estado FROM MAE_CLIENTE WHERE dni_ruc = ?", (dni_ruc,))
        row_old = cursor.fetchone()
        estado_ant = row_old["estado"] if row_old else None
        
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE MAE_CLIENTE 
            SET estado = ?, usuario_modificacion = ?, fecha_modificacion = ?
            WHERE dni_ruc = ?
        """, (nuevo_estado, usuario, fecha_actual, dni_ruc))
        
        conn.commit()
        conn.close()
        print("[DEBUG] Modificación de estado en MAE_CLIENTE realizada con éxito.")
        
        # log audit event to trs_auditoria_log after commit to avoid locks
        try:
            from controladores.AuditoriaService import AuditoriaService
            AuditoriaService.registrar("CAMBIAR_ESTADO_CLIENTE", dni_ruc, estado_ant, nuevo_estado)
        except Exception as ae:
            print(f"[DEBUG ERROR] falla al registrar auditoria: {ae}")

    def obtener_con_saldo_pendiente_count(self):
        # obtiene la cantidad de clientes unicos con al menos una factura pendiente
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(DISTINCT dni_ruc) FROM TRS_FACTURA WHERE estado = 'Pendiente'")
            return cursor.fetchone()[0]
        except Exception:
            return 0
        finally:
            conn.close()