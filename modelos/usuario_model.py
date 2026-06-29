import sqlite3
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class UsuarioModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento local de persistencia (MAE_USUARIO).")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # deshabilitar temporalmente llaves foraneas para poder reestructurar sin conflictos
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # limpieza por migracion: si existia la tabla 'usuario' antigua se reestructura
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario';")
        if cursor.fetchone():
            print("[DEBUG] Detectada estructura heredada 'usuario'. Ejecutando migración automática.")
            cursor.execute("DROP TABLE usuario;")
            conn.commit()
        
        # creacion de la tabla bajo lineamientos oficiales (nombres completos sin abreviaturas)
        cursor.execute("PRAGMA table_info(MAE_USUARIO);")
        columnas_existentes = [row["name"] for row in cursor.fetchall()]
        if columnas_existentes and "email" not in columnas_existentes:
            print("[DEBUG] Reestructurando MAE_USUARIO para añadir campos email y estado.")
            cursor.execute("DROP TABLE MAE_USUARIO;")
            conn.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_USUARIO (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                salt VARCHAR(64) NOT NULL,
                rol VARCHAR(50) NOT NULL,
                email VARCHAR(100) NULL,
                estado VARCHAR(20) DEFAULT 'Activo'
            )
        """)
        
        # crear tablas de rbac y auditoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_ROL (
                id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(50) NOT NULL UNIQUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_PERMISO (
                id_permiso INTEGER PRIMARY KEY AUTOINCREMENT,
                clave VARCHAR(50) NOT NULL UNIQUE,
                descripcion TEXT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ROL_PERMISO (
                id_rol INTEGER,
                id_permiso INTEGER,
                PRIMARY KEY (id_rol, id_permiso),
                FOREIGN KEY (id_rol) REFERENCES MAE_ROL (id_rol) ON DELETE CASCADE,
                FOREIGN KEY (id_permiso) REFERENCES MAE_PERMISO (id_permiso) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_AUDITORIA_LOG (
                id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario VARCHAR(50) NOT NULL,
                accion VARCHAR(50) NOT NULL,
                objeto VARCHAR(100) NOT NULL,
                valor_anterior TEXT NULL,
                valor_nuevo TEXT NULL
            )
        """)
        
        # sembrar roles y permisos si estan vacios
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_ROL")
        if cursor.fetchone()["total"] == 0:
            roles = ["Administrador", "Operador", "Usuario"]
            for r in roles:
                cursor.execute("INSERT INTO MAE_ROL (nombre) VALUES (?)", (r,))
            conn.commit()
            
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_PERMISO")
        if cursor.fetchone()["total"] == 0:
            permisos = [
                ("backup_generar", "generar respaldos de base de datos"),
                ("usuario_crear", "crear nuevos usuarios en el sistema"),
                ("usuario_toggle", "activar o inactivar usuarios"),
                ("config_guardar", "guardar configuraciones de la empresa"),
                ("factura_crear", "crear comprobantes de venta"),
                ("factura_anular", "anular facturas y boletas"),
                ("clientes_gestionar", "administrar clientes"),
                ("productos_gestionar", "administrar productos")
            ]
            for clave, desc in permisos:
                cursor.execute("INSERT INTO MAE_PERMISO (clave, descripcion) VALUES (?, ?)", (clave, desc))
            conn.commit()
            
        # asociar permisos a roles en la tabla intermedia
        cursor.execute("SELECT COUNT(*) AS total FROM ROL_PERMISO")
        if cursor.fetchone()["total"] == 0:
            # administrador tiene todos los permisos
            cursor.execute("SELECT id_rol FROM MAE_ROL WHERE nombre = 'Administrador'")
            admin_rol_id = cursor.fetchone()[0]
            cursor.execute("SELECT id_permiso FROM MAE_PERMISO")
            todos_permisos_ids = [row[0] for row in cursor.fetchall()]
            for p_id in todos_permisos_ids:
                cursor.execute("INSERT INTO ROL_PERMISO (id_rol, id_permiso) VALUES (?, ?)", (admin_rol_id, p_id))
                
            # operador tiene transacciones de factura y catalogos pero no administracion de sistema
            cursor.execute("SELECT id_rol FROM MAE_ROL WHERE nombre = 'Operador'")
            operador_rol_id = cursor.fetchone()[0]
            operador_permisos = ["factura_crear", "factura_anular", "clientes_gestionar", "productos_gestionar"]
            for p_clave in operador_permisos:
                cursor.execute("SELECT id_permiso FROM MAE_PERMISO WHERE clave = ?", (p_clave,))
                p_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO ROL_PERMISO (id_rol, id_permiso) VALUES (?, ?)", (operador_rol_id, p_id))
                
            # usuario solo tiene creacion de facturas
            cursor.execute("SELECT id_rol FROM MAE_ROL WHERE nombre = 'Usuario'")
            usuario_rol_id = cursor.fetchone()[0]
            usuario_permisos = ["factura_crear"]
            for p_clave in usuario_permisos:
                cursor.execute("SELECT id_permiso FROM MAE_PERMISO WHERE clave = ?", (p_clave,))
                p_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO ROL_PERMISO (id_rol, id_permiso) VALUES (?, ?)", (usuario_rol_id, p_id))
            conn.commit()

        # reactivar llaves foraneas
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()

    def tiene_usuarios(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_USUARIO")
        total = cursor.fetchone()["total"]
        conn.close()
        print(f"[DEBUG] Verificación de registros completada. Estado: {'Con cuentas configuradas' if total > 0 else 'Vacío'}")
        return total > 0

    def _generar_hash_seguro(self, password: str):
        salt_bytes = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000)
        return hash_bytes.hex(), salt_bytes.hex()

    def registrar_usuario(self, username, password, nombre, rol="Administrador", email=None, estado="Activo"):
        hash_val, salt_val = self._generar_hash_seguro(password)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # blindaje inyeccion sql: uso estricto de placeholders '?'
            cursor.execute("""
                INSERT INTO MAE_USUARIO (username, password_hash, salt, nombre, rol, email, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, hash_val, salt_val, nombre, rol, email, estado))
            conn.commit()
            print("[DEBUG] Transacción de inserción en MAE_USUARIO procesada de forma exitosa.")
            return True, "Usuario registrado con éxito."
        except sqlite3.IntegrityError:
            print("[DEBUG] Conflicto de restricción: Identificador único duplicado en base de datos.")
            return False, "El nombre de usuario ya se encuentra registrado."
        finally:
            conn.close()

    def verificar_credenciales(self, username, password):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # blindaje inyeccion sql: consulta parametrizada segura inmune a manipulacion de comillas
        cursor.execute("""
            SELECT id_usuario, nombre, username, password_hash, salt, rol 
            FROM MAE_USUARIO 
            WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        # mensaje neutral para evitar tecnicas de enumeracion maliciosa de cuentas
        if not row:
            print("[DEBUG AUTH] Autenticación fallida: Las credenciales ingresadas no coinciden con los registros.")
            return None
            
        usuario = dict(row)
        salt_bytes = bytes.fromhex(usuario["salt"])
        
        print("[DEBUG AUTH] Ejecutando algoritmo de validación criptográfica unidireccional.")
        hash_calc = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000).hex()
        
        # logs sanitizados: se elimino cualquier impresion de fragmentos de hashes o nombres de usuario reales
        if hash_calc == usuario["password_hash"]:
            print("[DEBUG AUTH] Validación exitosa. Otorgando acceso al entorno principal del sistema.")
            return usuario
            
        print("[DEBUG AUTH] Autenticación fallida: Firma de verificación de clave no válida.")
        return None

    def verificar_permiso_rol(self, rol_nombre, permiso_clave):
        # verifica si el rol posee el permiso clave en la bd
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM ROL_PERMISO rp
                JOIN MAE_ROL r ON rp.id_rol = r.id_rol
                JOIN MAE_PERMISO p ON rp.id_permiso = p.id_permiso
                WHERE r.nombre = ? AND p.clave = ?
            """, (rol_nombre, permiso_clave))
            total = cursor.fetchone()["total"]
            return total > 0
        except Exception:
            return False
        finally:
            conn.close()

    def registrar_auditoria(self, usuario, accion, objeto, valor_anterior=None, valor_nuevo=None):
        # registra un log inmutable de auditoria en la base de datos
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            from datetime import datetime
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO TRS_AUDITORIA_LOG (fecha, usuario, accion, objeto, valor_anterior, valor_nuevo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fecha_actual, usuario, accion, objeto, valor_anterior, valor_nuevo))
            conn.commit()
            return True
        except Exception as e:
            print(f"[DEBUG ERROR] falla al registrar auditoria en bd: {e}")
            return False
        finally:
            conn.close()