import sqlite3
import os
from modelos.usuario_model import UsuarioModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class ConfigModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento de configuraciones (MAE_CONFIGURACION).")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CONFIGURACION (
                id_config INTEGER PRIMARY KEY AUTOINCREMENT,
                clave VARCHAR(50) NOT NULL UNIQUE,
                valor VARCHAR(255) NOT NULL,
                descripcion TEXT NULL
            )
        """)
        # asegurar monedas comunes (pen, usd, eur) en mae_moneda
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='MAE_MONEDA'")
        if cursor.fetchone():
            monedas = [
                ('PEN', 'Soles', 'S/'),
                ('USD', 'Dólares', '$'),
                ('EUR', 'Euros', '€')
            ]
            for cod, nom, simb in monedas:
                cursor.execute("SELECT COUNT(*) FROM MAE_MONEDA WHERE codigo_iso = ?", (cod,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO MAE_MONEDA (codigo_iso, nombre, simbolo) VALUES (?, ?, ?)", (cod, nom, simb))
        conn.commit()
        conn.close()

    def obtener_datos_empresa(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id_empresa, e.razon_social, e.ruc, e.direccion, e.email, e.idioma_region, e.tasa_impositiva, e.id_moneda_base,
                   m.simbolo AS moneda_simbolo, m.codigo_iso AS moneda_iso
            FROM MAE_EMPRESA e
            JOIN MAE_MONEDA m ON e.id_moneda_base = m.id_moneda
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def obtener_monedas(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_moneda, codigo_iso, nombre, simbolo FROM MAE_MONEDA ORDER BY nombre ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def guardar_datos_empresa(self, razon_social, ruc, direccion, email, idioma_region, id_moneda_base, tasa_impositiva):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute("""
                UPDATE MAE_EMPRESA
                SET razon_social = ?, ruc = ?, direccion = ?, email = ?, idioma_region = ?, id_moneda_base = ?, tasa_impositiva = ?
                WHERE id_empresa = 1
            """, (razon_social, ruc, direccion, email, idioma_region, int(id_moneda_base), float(tasa_impositiva)))
            
            # sincronizar la tasa de igv en la tabla maestra de impuestos (id_impuesto = 1 -> igv normal)
            cursor.execute("""
                UPDATE MAE_IMPUESTO
                SET porcentaje = ?
                WHERE id_impuesto = 1
            """, (float(tasa_impositiva),))
            
            cursor.execute("COMMIT;")
            return True, "Datos de la empresa y tasas de impuestos actualizados correctamente."
        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
            except Exception:
                pass
            return False, str(e)
        finally:
            conn.close()

    def obtener_configuraciones(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT clave, valor FROM MAE_CONFIGURACION")
        rows = cursor.fetchall()
        conn.close()
        return {row["clave"]: row["valor"] for row in rows}

    def actualizar_configuracion(self, clave, valor):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE MAE_CONFIGURACION
                SET valor = ?
                WHERE clave = ?
            """, (str(valor), clave))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def obtener_usuarios(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, username, rol, email, estado FROM MAE_USUARIO")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def registrar_usuario_avanzado(self, nombre, username, password, rol, email, estado="Activo"):
        user_model = UsuarioModel()
        return user_model.registrar_usuario(username, password, nombre, rol, email, estado)

    def cambiar_estado_usuario(self, id_usuario, nuevo_estado):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE MAE_USUARIO SET estado = ? WHERE id_usuario = ?", (nuevo_estado, id_usuario))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
