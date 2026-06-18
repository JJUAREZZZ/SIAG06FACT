import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class FacturaModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento transaccional (TRS_FACTURA / TRS_DETALLE_FACTURA).")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # forzar restricciones de integridad referencial nativas
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # limpieza por migración: si existían las tablas provisorias previas, las removemos en orden
        for tabla_antigua in ["detalle_factura", "factura"]:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla_antigua}';")
            if cursor.fetchone():
                print(f"[DEBUG] Detectada estructura heredada '{tabla_antigua}'. Migrando a tablas TRS_.")
                cursor.execute(f"DROP TABLE {tabla_antigua};")
                conn.commit()

        # 1. crear tabla maestra de monedas (requerida por empresa y factura)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_MONEDA (
                id_moneda INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_iso VARCHAR(3) NOT NULL,
                nombre VARCHAR(50) NOT NULL,
                simbolo VARCHAR(5) NOT NULL
            )
        """)

        # 2. crear tabla maestra de empresas (módulo corporativo multi-empresa)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_EMPRESA (
                id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
                razon_social VARCHAR(150) NOT NULL,
                ruc VARCHAR(11) NOT NULL UNIQUE,
                direccion VARCHAR(200),
                email VARCHAR(100),
                idioma_region VARCHAR(50),
                tasa_impositiva DECIMAL(5,2) NOT NULL DEFAULT 18.00,
                id_moneda_base INTEGER NOT NULL,
                FOREIGN KEY (id_moneda_base) REFERENCES MAE_MONEDA (id_moneda)
            )
        """)

        # semillero de configuración inicial corporativa para evitar tablas vacías
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_MONEDA")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("INSERT INTO MAE_MONEDA (codigo_iso, nombre, simbolo) VALUES ('PEN', 'Soles', 'S/')")
            id_moneda_base = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO MAE_EMPRESA (razon_social, ruc, direccion, email, id_moneda_base)
                VALUES ('UCSM SISTEMAS S.A.C.', '20123456789', 'Urb. San José s/n, Arequipa', 'contacto@ucsm.edu.pe', ?)
            """, (id_moneda_base,))
            conn.commit()

        # 3. crear tabla transaccional de cabecera de factura
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_FACTURA (
                num_factura VARCHAR(20) PRIMARY KEY,
                serie_comprobante VARCHAR(4) NOT NULL,
                correlativo_comprobante INTEGER NOT NULL,
                id_empresa INTEGER NOT NULL,
                dni_ruc VARCHAR(15) NOT NULL,
                id_usuario INTEGER NOT NULL,
                id_moneda INTEGER NOT NULL,
                id_descuento INTEGER,
                tipo_documento VARCHAR(50) NOT NULL DEFAULT 'Factura Electrónica',
                forma_pago VARCHAR(20) NOT NULL DEFAULT 'Contado',
                fecha_emision DATE NOT NULL,
                fecha_vencimiento DATE,
                tasa_cambio DECIMAL(6,4) NOT NULL DEFAULT 1.0000,
                subtotal DECIMAL(10,2) NOT NULL,
                monto_descuento DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                total_impuestos DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                total DECIMAL(10,2) NOT NULL,
                estado VARCHAR(20) DEFAULT 'Pendiente',
                metodo_pago VARCHAR(50),
                notas_anulacion TEXT,
                FOREIGN KEY (id_empresa) REFERENCES MAE_EMPRESA (id_empresa),
                FOREIGN KEY (dni_ruc) REFERENCES MAE_CLIENTE (dni_ruc),
                FOREIGN KEY (id_usuario) REFERENCES MAE_USUARIO (id_usuario),
                FOREIGN KEY (id_moneda) REFERENCES MAE_MONEDA (id_moneda)
            )
        """)

        # 4. crear tabla transaccional de detalle de facturas (líneas de venta)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_DETALLE_FACTURA (
                id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                num_factura VARCHAR(20) NOT NULL,
                id_producto INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                unidad_medida VARCHAR(10) NOT NULL DEFAULT 'UND',
                precio_unitario_historico DECIMAL(10,2) NOT NULL,
                id_descuento INTEGER,
                monto_descuento_linea DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                tasa_impuesto_aplicada DECIMAL(5,2) NOT NULL,
                monto_impuesto_linea DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (num_factura) REFERENCES TRS_FACTURA (num_factura) ON DELETE CASCADE,
                FOREIGN KEY (id_producto) REFERENCES MAE_PRODUCTO (id_producto)
            )
        """)
        
        conn.commit()
        conn.close()

        # inicializar el modelo de asientos contables para crear tablas y migrar facturas en caliente
        from modelos.asiento_model import AsientoModel
        AsientoModel()

    def obtener_todas(self):
        """Devuelve el historial completo de facturas para renderizar la tabla o autoincrementar el número."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # mapeamos los alias 'id' y 'fecha' para mantener compatibilidad absoluta con tu controlador actual
            cursor.execute("""
                SELECT f.num_factura AS id, f.num_factura, f.fecha_emision AS fecha, f.subtotal, f.total_impuestos AS igv, f.total, f.estado, f.dni_ruc,
                       c.nombre_razon_social AS cliente_nombre 
                FROM TRS_FACTURA f
                JOIN MAE_CLIENTE c ON f.dni_ruc = c.dni_ruc
                ORDER BY f.fecha_emision DESC
            """)
            resultado = [dict(row) for row in cursor.fetchall()]
            return resultado
        finally:
            conn.close()

    def registrar_factura(self, cliente_id, subtotal, igv, total, items):
        """Registra una venta bajo el estándar gubernamental usando una transacción segura y aislada."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION;")
            
            # 1. recuperar ids corporativos base por defecto de forma segura
            cursor.execute("SELECT id_empresa, id_moneda_base FROM MAE_EMPRESA LIMIT 1")
            emp_row = cursor.fetchone()
            id_empresa = emp_row["id_empresa"]
            id_moneda = emp_row["id_moneda_base"]
            
            cursor.execute("SELECT id_usuario FROM MAE_USUARIO LIMIT 1")
            id_usuario = cursor.fetchone()["id_usuario"]
            
            # 2. calcular la numeración del correlativo oficial de forma segura (max + 1)
            cursor.execute("SELECT IFNULL(MAX(correlativo_comprobante), 0) AS ultimo FROM TRS_FACTURA")
            siguiente_correlativo = cursor.fetchone()["ultimo"] + 1
            num_factura_formateado = f"F001-{siguiente_correlativo:05d}"
            fecha_actual = datetime.now().strftime("%Y-%m-%d")

            # blindaje inyección sql: insertar la cabecera transaccional parametrizada
            cursor.execute("""
                INSERT INTO TRS_FACTURA (
                    num_factura, serie_comprobante, correlativo_comprobante, id_empresa, 
                    dni_ruc, id_usuario, id_moneda, fecha_emision, subtotal, total_impuestos, total, estado
                ) VALUES (?, 'F001', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Emitido')
            """, (num_factura_formateado, siguiente_correlativo, id_empresa, cliente_id, 
                  id_usuario, id_moneda, fecha_actual, subtotal, igv, total))
            
            # 3. procesar las líneas de venta detalladas
            # 'items' viene del controlador como: (codigo_barra, cantidad, precio_unitario, desc_linea, tasa_imp, impuesto_linea)
            for item in items:
                codigo_barra, cantidad, precio_uni, desc_linea, tasa_imp, impuesto_linea = item
                
                # buscamos el id_producto interno de sqlite basándonos en su código de barra único
                cursor.execute("SELECT id_producto, stock FROM MAE_PRODUCTO WHERE codigo_barra = ?", (codigo_barra,))
                row_prod = cursor.fetchone()
                if not row_prod:
                    raise ValueError(f"El producto con código {codigo_barra} no existe.")
                    
                id_producto = row_prod["id_producto"]
                stock_actual = row_prod["stock"]
                
                # blindaje stock negativo (deficiencia c3)
                if stock_actual < cantidad:
                    raise ValueError(f"Stock insuficiente para producto con código {codigo_barra}. Disponible: {stock_actual}, solicitado: {cantidad}")
                
                # insertar en la tabla transaccional de detalles
                cursor.execute("""
                    INSERT INTO TRS_DETALLE_FACTURA (
                        num_factura, id_producto, cantidad, precio_unitario_historico, 
                        monto_descuento_linea, tasa_impuesto_aplicada, monto_impuesto_linea
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (num_factura_formateado, id_producto, cantidad, precio_uni, desc_linea, tasa_imp, impuesto_linea))
                
                # descontar stock de la tabla maestra con consulta parametrizada
                cursor.execute("""
                    UPDATE MAE_PRODUCTO 
                    SET stock = stock - ? 
                    WHERE id_producto = ?
                """, (cantidad, id_producto))
            
            # generar el asiento contable dentro de la misma transacción (deficiencia s1)
            from modelos.asiento_model import AsientoModel
            asiento_model = AsientoModel()
            asiento_model.crear_asiento_para_factura(cursor, num_factura_formateado, subtotal, igv, total, fecha_actual)

            conn.commit()
            print(f"[DEBUG] Venta {num_factura_formateado} procesada y guardada exitosamente en tablas TRS con su asiento contable.")
            return True, num_factura_formateado
            
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"[DEBUG ERROR] Deshaciendo cambios en la transacción por anomalía: {e}")
            return False, str(e)
        finally:
            conn.close()

    def obtener_tasa_igv_activa(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tasa_impositiva FROM MAE_EMPRESA LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return float(row["tasa_impositiva"]) if row else 18.00

    def obtener_moneda_base_activa(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.simbolo, m.codigo_iso
            FROM MAE_EMPRESA e
            JOIN MAE_MONEDA m ON e.id_moneda_base = m.id_moneda
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {"simbolo": "S/", "codigo_iso": "PEN"}

    def modificar_estado_factura(self, num_factura, nuevo_estado, notas=None):
        """Actualiza el estado de una factura (Pagada, Pendiente, Anulada) y notas opcionales."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            
            if nuevo_estado == "Anulada":
                # 1. revertir el stock de todos los ítems de la factura (deficiencia i3)
                cursor.execute("SELECT id_producto, cantidad FROM TRS_DETALLE_FACTURA WHERE num_factura = ?", (num_factura,))
                items = cursor.fetchall()
                for item in items:
                    cursor.execute("""
                        UPDATE MAE_PRODUCTO 
                        SET stock = stock + ? 
                        WHERE id_producto = ?
                    """, (item["cantidad"], item["id_producto"]))

                # 2. generar el asiento contable de extorno (deficiencia s1)
                from modelos.asiento_model import AsientoModel
                asiento_model = AsientoModel()
                asiento_model.crear_asiento_anulacion(cursor, num_factura)

                # 3. actualizar estado
                cursor.execute("""
                    UPDATE TRS_FACTURA 
                    SET estado = ?, notas_anulacion = ? 
                    WHERE num_factura = ?
                """, (nuevo_estado, notas, num_factura))
            else:
                cursor.execute("""
                    UPDATE TRS_FACTURA 
                    SET estado = ?, notas_anulacion = NULL 
                    WHERE num_factura = ?
                """, (nuevo_estado, num_factura))
                
            conn.commit()
            return True, f"Estado de factura {num_factura} actualizado a {nuevo_estado}."
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, str(e)
        finally:
            conn.close()

    def obtener_siguiente_correlativo(self):
        """Devuelve el siguiente número correlativo disponible consultando el MAX."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT IFNULL(MAX(correlativo_comprobante), 0) AS ultimo FROM TRS_FACTURA")
            return cursor.fetchone()["ultimo"] + 1
        except Exception:
            return 1
        finally:
            conn.close()