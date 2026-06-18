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
        
        # deshabilitar temporalmente llaves foráneas para poder reestructurar sin conflictos
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # limpieza por migración: si existía la tabla 'usuario' antigua, se reestructura
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario';")
        if cursor.fetchone():
            print("[DEBUG] Detectada estructura heredada 'usuario'. Ejecutando migración automática.")
            cursor.execute("DROP TABLE usuario;")
            conn.commit()
        
        # creación de la tabla bajo lineamientos oficiales (nombres completos sin abreviaturas)
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
        # reactivar llaves foráneas
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
            # blindaje inyección sql: uso estricto de placeholders '?'
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
        
        # blindaje inyección sql: consulta parametrizada segura, inmune a manipulación de comillas
        cursor.execute("""
            SELECT id_usuario, nombre, username, password_hash, salt, rol 
            FROM MAE_USUARIO 
            WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        # mensaje neutral para evitar técnicas de enumeración maliciosa de cuentas
        if not row:
            print("[DEBUG AUTH] Autenticación fallida: Las credenciales ingresadas no coinciden con los registros.")
            return None
            
        usuario = dict(row)
        salt_bytes = bytes.fromhex(usuario["salt"])
        
        print("[DEBUG AUTH] Ejecutando algoritmo de validación criptográfica unidireccional.")
        hash_calc = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000).hex()
        
        # logs sanitizados: se eliminó cualquier impresión de fragmentos de hashes o nombres de usuario reales
        if hash_calc == usuario["password_hash"]:
            print("[DEBUG AUTH] Validación exitosa. Otorgando acceso al entorno principal del sistema.")
            return usuario
            
        print("[DEBUG AUTH] Autenticación fallida: Firma de verificación de clave no válida.")
        return None