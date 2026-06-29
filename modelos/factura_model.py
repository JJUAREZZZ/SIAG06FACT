import sqlite3
import os
import json
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
        # forzar integridad referencial en cada conexion
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # forzar restricciones de integridad referencial nativas
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # limpieza por migracion: si existian las tablas provisorias previas las removemos en orden
        for tabla_antigua in ["detalle_factura", "factura"]:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla_antigua}';")
            if cursor.fetchone():
                print(f"[DEBUG] Detectada estructura heredada '{tabla_antigua}'. Migrando a tablas TRS_.")
                cursor.execute(f"DROP TABLE {tabla_antigua};")
                conn.commit()

        # control de migracion para factura: si existe la tabla trs_factura pero no tiene 'usuario_creacion'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TRS_FACTURA';")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(TRS_FACTURA);")
            cols = [row["name"] for row in cursor.fetchall()]
            if cols and "usuario_creacion" not in cols:
                print("[DEBUG] Reestructurando TRS_FACTURA para añadir soporte de auditoria.")
                cursor.execute("DROP TABLE IF EXISTS TRS_DETALLE_FACTURA;")
                cursor.execute("DROP TABLE IF EXISTS TRS_FACTURA_CUOTA;")
                cursor.execute("DROP TABLE IF EXISTS TRS_FACTURA;")
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

        # 2. crear tabla maestra de empresas (modulo corporativo multi-empresa)
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

        # semillero de configuracion inicial corporativa para evitar tablas vacias
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_MONEDA")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("INSERT INTO MAE_MONEDA (codigo_iso, nombre, simbolo) VALUES ('PEN', 'Soles', 'S/')")
            cursor.execute("INSERT INTO MAE_MONEDA (codigo_iso, nombre, simbolo) VALUES ('USD', 'Dólares', '$')")
            cursor.execute("INSERT INTO MAE_MONEDA (codigo_iso, nombre, simbolo) VALUES ('EUR', 'Euros', '€')")
            id_moneda_base = 1
            
            cursor.execute("""
                INSERT INTO MAE_EMPRESA (razon_social, ruc, direccion, email, id_moneda_base)
                VALUES ('Universidad Católica de Santa María (UCSM)', '20102030401', 'Urb. San José s/n, Arequipa 04013', 'ucsm@email.com', ?)
            """, (id_moneda_base,))
            conn.commit()

        # 3. crear tabla maestra de tipo de cambio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_TIPO_CAMBIO (
                id_tipo_cambio INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL UNIQUE,
                compra DECIMAL(6,4) NOT NULL,
                venta DECIMAL(6,4) NOT NULL
            )
        """)

        # semillar un tipo de cambio si no existe
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_TIPO_CAMBIO")
        if cursor.fetchone()["total"] == 0:
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO MAE_TIPO_CAMBIO (fecha, compra, venta) VALUES (?, 3.7200, 3.7500)", (fecha_hoy,))
            conn.commit()

        # 4. crear tabla maestra de descuentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_DESCUENTO (
                id_descuento INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                porcentaje DECIMAL(5,2) NOT NULL,
                id_categoria_producto INTEGER NULL,
                estado VARCHAR(20) DEFAULT 'Activo'
            )
        """)

        # 5. crear tabla de control de comprobantes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CONTROL_COMPROBANTE (
                id_control INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_comprobante VARCHAR(50) NOT NULL UNIQUE,
                serie VARCHAR(4) NOT NULL,
                correlativo_actual INTEGER NOT NULL
            )
        """)

        cursor.execute("SELECT COUNT(*) AS total FROM MAE_CONTROL_COMPROBANTE")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("INSERT INTO MAE_CONTROL_COMPROBANTE (tipo_comprobante, serie, correlativo_actual) VALUES ('Factura Electrónica', 'F001', 0)")
            cursor.execute("INSERT INTO MAE_CONTROL_COMPROBANTE (tipo_comprobante, serie, correlativo_actual) VALUES ('Boleta de Venta', 'B001', 0)")
            conn.commit()

        # 6. crear tabla transaccional de cabecera de factura con auditoria eer
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
                usuario_creacion VARCHAR(50),
                fecha_creacion DATETIME,
                usuario_modificacion VARCHAR(50),
                fecha_modificacion DATETIME,
                FOREIGN KEY (id_empresa) REFERENCES MAE_EMPRESA (id_empresa),
                FOREIGN KEY (dni_ruc) REFERENCES MAE_CLIENTE (dni_ruc),
                FOREIGN KEY (id_usuario) REFERENCES MAE_USUARIO (id_usuario),
                FOREIGN KEY (id_moneda) REFERENCES MAE_MONEDA (id_moneda)
            )
        """)

        # 7. crear tabla transaccional de detalle de facturas
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

        # 8. crear tabla transaccional de cuotas de factura
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_FACTURA_CUOTA (
                id_cuota INTEGER PRIMARY KEY AUTOINCREMENT,
                num_factura VARCHAR(20) NOT NULL,
                numero_cuota INTEGER NOT NULL,
                monto_cuota DECIMAL(10,2) NOT NULL,
                fecha_vencimiento_cuota DATE NOT NULL,
                estado_cuota VARCHAR(20) DEFAULT 'Pendiente',
                usuario_creacion VARCHAR(50),
                fecha_creacion DATETIME,
                usuario_modificacion VARCHAR(50),
                fecha_modificacion DATETIME,
                FOREIGN KEY (num_factura) REFERENCES TRS_FACTURA (num_factura) ON DELETE CASCADE
            )
        """)

        # 9. crear tabla transaccional de kardex tal como eer
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_KARDEX (
                id_kardex INTEGER PRIMARY KEY AUTOINCREMENT,
                id_producto INTEGER NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo_movimiento VARCHAR(20) NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario_historico DECIMAL(10,2) NOT NULL,
                stock_restante_historico INTEGER NOT NULL,
                num_documento_referencia VARCHAR(50) NOT NULL,
                detalle TEXT,
                usuario_creacion VARCHAR(50),
                fecha_creacion DATETIME,
                FOREIGN KEY (id_producto) REFERENCES MAE_PRODUCTO (id_producto)
            )
        """)

        # 10. crear tabla transaccional de auditoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_AUDITORIA (
                id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario VARCHAR(50) NOT NULL,
                fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                accion VARCHAR(50) NOT NULL,
                tabla_afectada VARCHAR(50) NOT NULL,
                registro_id VARCHAR(50) NOT NULL,
                estado_anterior TEXT,
                estado_posterior TEXT
            )
        """)
        
        conn.commit()
        conn.close()

        # inicializar el modelo de asientos contables
        from modelos.asiento_model import AsientoModel
        AsientoModel()

    def registrar_auditoria(self, cursor, usuario, accion, tabla, registro_id, anterior_dict, posterior_dict):
        # registra cambios de estado para auditoria
        ant_str = json.dumps(anterior_dict) if anterior_dict else None
        post_str = json.dumps(posterior_dict) if posterior_dict else None
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO TRS_AUDITORIA (usuario, fecha_hora, accion, tabla_afectada, registro_id, estado_anterior, estado_posterior)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario, fecha_actual, accion, tabla, str(registro_id), ant_str, post_str))

    def obtener_todas(self):
        # obtiene historial completo de facturas
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.num_factura AS id, f.num_factura, f.fecha_emision AS fecha, f.subtotal, f.total_impuestos AS igv, f.total, f.estado, f.dni_ruc,
                       f.tipo_documento, f.forma_pago, f.metodo_pago, m.simbolo AS moneda_simbolo,
                       c.nombre_razon_social AS cliente_nombre 
                FROM TRS_FACTURA f
                JOIN MAE_CLIENTE c ON f.dni_ruc = c.dni_ruc
                JOIN MAE_MONEDA m ON f.id_moneda = m.id_moneda
                ORDER BY f.fecha_emision DESC, f.num_factura DESC
            """)
            resultado = [dict(row) for row in cursor.fetchall()]
            return resultado
        finally:
            conn.close()

    def obtener_factura_por_numero(self, num_factura):
        # recupera cabecera completa y detalle de una factura especifica
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. cabecera con cliente empresa y moneda
            cursor.execute("""
                SELECT f.num_factura, f.serie_comprobante, f.correlativo_comprobante, f.tipo_documento,
                       f.forma_pago, f.metodo_pago, f.fecha_emision, f.fecha_vencimiento, f.tasa_cambio,
                       f.subtotal, f.monto_descuento, f.total_impuestos, f.total, f.estado, f.notas_anulacion,
                       f.dni_ruc, f.usuario_creacion, f.fecha_creacion,
                       c.nombre_razon_social AS cliente_nombre, c.direccion AS cliente_direccion, 
                       c.email AS cliente_email, c.telefono AS cliente_telefono,
                       e.razon_social AS empresa_nombre, e.ruc AS empresa_ruc, 
                       e.direccion AS empresa_direccion, e.email AS empresa_email, e.tasa_impositiva,
                       m.codigo_iso AS moneda_iso, m.simbolo AS moneda_simbolo
                FROM TRS_FACTURA f
                JOIN MAE_CLIENTE c ON f.dni_ruc = c.dni_ruc
                JOIN MAE_EMPRESA e ON f.id_empresa = e.id_empresa
                JOIN MAE_MONEDA m ON f.id_moneda = m.id_moneda
                WHERE f.num_factura = ?
            """, (num_factura,))
            
            row_cab = cursor.fetchone()
            if not row_cab:
                return None
                
            factura = dict(row_cab)
            
            # 2. detalle de items
            cursor.execute("""
                SELECT d.id_detalle, d.cantidad, d.precio_unitario_historico, d.monto_descuento_linea,
                       d.tasa_impuesto_aplicada, d.monto_impuesto_linea,
                       p.codigo_barra AS producto_codigo, p.nombre AS producto_nombre, p.descripcion AS producto_desc
                FROM TRS_DETALLE_FACTURA d
                JOIN MAE_PRODUCTO p ON d.id_producto = p.id_producto
                WHERE d.num_factura = ?
            """, (num_factura,))
            
            factura["items"] = [dict(row) for row in cursor.fetchall()]
            
            # 3. cuotas si es a credito
            cursor.execute("""
                SELECT numero_cuota, monto_cuota, fecha_vencimiento_cuota, estado_cuota
                FROM TRS_FACTURA_CUOTA
                WHERE num_factura = ?
                ORDER BY numero_cuota ASC
            """, (num_factura,))
            factura["cuotas"] = [dict(row) for row in cursor.fetchall()]

            return factura
        finally:
            conn.close()

    def registrar_factura(self, cliente_id, subtotal, igv, total, items, tipo_documento="Factura Electrónica", forma_pago="Contado", metodo_pago="Efectivo", usuario="admin", cuotas=None, moneda_iso="PEN", monto_descuento=0.00):
        # registra una factura de forma segura contra concurrencia e inyeccion sql
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # validacion defensiva de datos de entrada
            if not items:
                raise ValueError("No se puede registrar una factura sin productos.")
            if not cliente_id or not str(cliente_id).strip():
                raise ValueError("El identificador del cliente es obligatorio.")
            if subtotal < 0 or igv < 0 or total <= 0:
                raise ValueError("Los montos de la factura no pueden ser negativos o cero.")
            if monto_descuento < 0:
                raise ValueError("El monto de descuento no puede ser negativo.")
            for item in items:
                codigo, cantidad, precio_uni, desc_linea, tasa_imp, imp_linea = item
                if cantidad <= 0:
                    raise ValueError(f"La cantidad del producto {codigo} debe ser mayor a cero.")
                if precio_uni <= 0:
                    raise ValueError(f"El precio del producto {codigo} debe ser mayor a cero.")
                if desc_linea < 0:
                    raise ValueError(f"El descuento del producto {codigo} no puede ser negativo.")

            # bloqueo inmediato para evitar duplicidad de correlativo
            cursor.execute("BEGIN IMMEDIATE TRANSACTION;")
            
            # 1. recuperar ids corporativos
            cursor.execute("SELECT id_empresa, id_moneda_base FROM MAE_EMPRESA LIMIT 1")
            emp_row = cursor.fetchone()
            if not emp_row:
                raise ValueError("No existe una empresa configurada en el sistema.")
            id_empresa = emp_row["id_empresa"]
            
            cursor.execute("SELECT id_moneda FROM MAE_MONEDA WHERE codigo_iso = ?", (moneda_iso,))
            mon_row = cursor.fetchone()
            id_moneda = mon_row["id_moneda"] if mon_row else emp_row["id_moneda_base"]
            
            cursor.execute("SELECT id_usuario FROM MAE_USUARIO LIMIT 1")
            usr_row = cursor.fetchone()
            if not usr_row:
                raise ValueError("No existen usuarios registrados en el sistema.")
            id_usuario = usr_row["id_usuario"]

            # obtener tipo de cambio del dia
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT venta FROM MAE_TIPO_CAMBIO WHERE fecha = ?", (fecha_hoy,))
            tc_row = cursor.fetchone()
            tasa_cambio = float(tc_row["venta"]) if tc_row else 3.7500
            
            # 2. determinar serie y correlativo seguro
            serie = "F001" if "Factura" in tipo_documento else "B001"
            cursor.execute("""
                SELECT IFNULL(MAX(correlativo_comprobante), 0) AS ultimo 
                FROM TRS_FACTURA 
                WHERE tipo_documento = ? AND serie_comprobante = ?
            """, (tipo_documento, serie))
            siguiente_correlativo = cursor.fetchone()["ultimo"] + 1
            num_factura_formateado = f"{serie}-{siguiente_correlativo:05d}"
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            fecha_actual_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # estado inicial
            estado_ini = "Pagada" if forma_pago == "Contado" else "Pendiente"

            # 3. insertar cabecera de factura
            cursor.execute("""
                INSERT INTO TRS_FACTURA (
                    num_factura, serie_comprobante, correlativo_comprobante, id_empresa, 
                    dni_ruc, id_usuario, id_moneda, tipo_documento, forma_pago, metodo_pago,
                    fecha_emision, tasa_cambio, subtotal, monto_descuento, total_impuestos, total, estado,
                    usuario_creacion, fecha_creacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (num_factura_formateado, serie, siguiente_correlativo, id_empresa, cliente_id, 
                  id_usuario, id_moneda, tipo_documento, forma_pago, metodo_pago,
                  fecha_actual, tasa_cambio, subtotal, round(monto_descuento, 2), igv, total, estado_ini,
                  usuario, fecha_actual_timestamp))
            
            # 4. procesar detalles y descontar stock con registro en kardex
            for item in items:
                codigo_barra, cantidad, precio_uni, desc_linea, tasa_imp, impuesto_linea = item
                
                cursor.execute("SELECT id_producto, stock FROM MAE_PRODUCTO WHERE codigo_barra = ?", (codigo_barra,))
                row_prod = cursor.fetchone()
                if not row_prod:
                    raise ValueError(f"El producto con código {codigo_barra} no existe.")
                    
                id_producto = row_prod["id_producto"]
                stock_actual = row_prod["stock"]
                
                if stock_actual < cantidad:
                    raise ValueError(f"Stock insuficiente para producto con código {codigo_barra}. Disponible: {stock_actual}, solicitado: {cantidad}")
                
                # insertar detalle
                cursor.execute("""
                    INSERT INTO TRS_DETALLE_FACTURA (
                        num_factura, id_producto, cantidad, precio_unitario_historico, 
                        monto_descuento_linea, tasa_impuesto_aplicada, monto_impuesto_linea
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (num_factura_formateado, id_producto, cantidad, precio_uni, desc_linea, tasa_imp, impuesto_linea))
                
                # actualizar stock
                cursor.execute("""
                    UPDATE MAE_PRODUCTO 
                    SET stock = stock - ? 
                    WHERE id_producto = ?
                """, (cantidad, id_producto))
                
                # re-leer stock real despues del update (corrige kardex con productos duplicados)
                cursor.execute("SELECT stock FROM MAE_PRODUCTO WHERE id_producto = ?", (id_producto,))
                nuevo_stock = cursor.fetchone()["stock"]
                cursor.execute("""
                    INSERT INTO TRS_KARDEX (
                        id_producto, fecha, tipo_movimiento, cantidad, precio_unitario_historico, 
                        stock_restante_historico, num_documento_referencia, detalle, usuario_creacion, fecha_creacion
                    ) VALUES (?, ?, 'SALIDA', ?, ?, ?, ?, 'Venta de producto', ?, ?)
                """, (id_producto, fecha_actual_timestamp, cantidad, precio_uni, nuevo_stock, num_factura_formateado, usuario, fecha_actual_timestamp))

            # 5. procesar cuotas si es a credito
            if forma_pago == "Crédito" and cuotas:
                for c in cuotas:
                    cursor.execute("""
                        INSERT INTO TRS_FACTURA_CUOTA (
                            num_factura, numero_cuota, monto_cuota, fecha_vencimiento_cuota, estado_cuota,
                            usuario_creacion, fecha_creacion
                        ) VALUES (?, ?, ?, ?, 'Pendiente', ?, ?)
                    """, (num_factura_formateado, c["numero"], c["monto"], c["vencimiento"], usuario, fecha_actual_timestamp))

            # 6. generar asiento contable (con conversion a moneda nacional si es otra)
            factor_conversion = tasa_cambio if moneda_iso == "USD" else 1.0
            subtotal_pen = subtotal * factor_conversion
            igv_pen = igv * factor_conversion
            total_pen = total * factor_conversion
            
            from modelos.asiento_model import AsientoModel
            asiento_model = AsientoModel()
            asiento_model.crear_asiento_para_factura(cursor, num_factura_formateado, subtotal_pen, igv_pen, total_pen, fecha_actual, usuario)

            # 7. registrar bitacora de auditoria
            posterior_dict = {
                "num_factura": num_factura_formateado, "cliente_id": cliente_id, "total": total,
                "estado": estado_ini, "tipo_documento": tipo_documento, "forma_pago": forma_pago
            }
            self.registrar_auditoria(cursor, usuario, "CREACION", "TRS_FACTURA", num_factura_formateado, None, posterior_dict)

            # invalidar cache de productos por cambio de stock
            from modelos.producto_model import ProductoModel
            ProductoModel._cache_productos = None

            conn.commit()
            print(f"[DEBUG] Factura {num_factura_formateado} procesada y guardada con éxito.")
            
            # log audit event to trs_auditoria_log after commit to avoid locks
            try:
                import json
                from controladores.AuditoriaService import AuditoriaService
                AuditoriaService.registrar("CREAR_FACTURA", num_factura_formateado, None, json.dumps(posterior_dict))
            except Exception as ae:
                print(f"[DEBUG ERROR] falla al registrar auditoria: {ae}")
                
            return True, num_factura_formateado
            
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"[DEBUG ERROR] Rolled back transaction due to error: {e}")
            return False, str(e)
        finally:
            conn.close()

    def obtener_tasa_igv_activa(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tasa_impositiva FROM MAE_EMPRESA LIMIT 1")
            row = cursor.fetchone()
            return float(row["tasa_impositiva"]) if row else 18.00
        finally:
            conn.close()

    def obtener_moneda_base_activa(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.simbolo, m.codigo_iso
                FROM MAE_EMPRESA e
                JOIN MAE_MONEDA m ON e.id_moneda_base = m.id_moneda
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else {"simbolo": "S/", "codigo_iso": "PEN"}
        finally:
            conn.close()

    def obtener_formato_impresion(self):
        # obtiene el formato de impresion desde la configuracion del sistema
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT valor FROM MAE_CONFIGURACION WHERE clave = 'formato_impresion_defecto'")
            row = cursor.fetchone()
            return row["valor"] if row else "A4"
        except Exception:
            return "A4"
        finally:
            conn.close()

    def modificar_estado_factura(self, num_factura, nuevo_estado, notas=None, usuario="admin"):
        # actualiza el estado de la factura (con extorno y kardex si es anulada)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE TRANSACTION;")
            
            # obtener estado anterior para la auditoria
            cursor.execute("SELECT estado, subtotal, total_impuestos, total, dni_ruc, tipo_documento, forma_pago FROM TRS_FACTURA WHERE num_factura = ?", (num_factura,))
            row_old = cursor.fetchone()
            if not row_old:
                raise ValueError("La factura no existe.")
            
            anterior_dict = dict(row_old)
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # proteccion contra doble anulacion y transiciones invalidas
            if anterior_dict["estado"] == "Anulada":
                raise ValueError("La factura ya se encuentra anulada. No se permiten cambios.")
            if nuevo_estado == "Anulada" and anterior_dict["estado"] == "Anulada":
                raise ValueError("La factura ya fue anulada previamente.")

            if nuevo_estado == "Anulada":
                # 1. revertir stock y registrar en kardex
                cursor.execute("SELECT id_producto, cantidad FROM TRS_DETALLE_FACTURA WHERE num_factura = ?", (num_factura,))
                items = cursor.fetchall()
                for item in items:
                    cursor.execute("UPDATE MAE_PRODUCTO SET stock = stock + ? WHERE id_producto = ?", (item["cantidad"], item["id_producto"]))
                    
                    # re-leer stock real despues del update para kardex preciso
                    cursor.execute("SELECT stock FROM MAE_PRODUCTO WHERE id_producto = ?", (item["id_producto"],))
                    nuevo_stock = cursor.fetchone()["stock"]
                    
                    # obtener precio historico de la venta original
                    cursor.execute("SELECT precio_unitario_historico FROM TRS_DETALLE_FACTURA WHERE num_factura = ? AND id_producto = ? LIMIT 1", (num_factura, item["id_producto"]))
                    precio_row = cursor.fetchone()
                    precio_hist = float(precio_row["precio_unitario_historico"]) if precio_row else 0.00
                    
                    cursor.execute("""
                        INSERT INTO TRS_KARDEX (
                            id_producto, fecha, tipo_movimiento, cantidad, precio_unitario_historico, 
                            stock_restante_historico, num_documento_referencia, detalle, usuario_creacion, fecha_creacion
                        ) VALUES (?, ?, 'ENTRADA', ?, ?, ?, ?, 'Devolución por anulación', ?, ?)
                    """, (item["id_producto"], fecha_actual, item["cantidad"], precio_hist, nuevo_stock, num_factura, usuario, fecha_actual))

                # 2. generar asiento de extorno
                from modelos.asiento_model import AsientoModel
                asiento_model = AsientoModel()
                asiento_model.crear_asiento_anulacion(cursor, num_factura, usuario)

                # 3. actualizar estado
                cursor.execute("""
                    UPDATE TRS_FACTURA 
                    SET estado = ?, notas_anulacion = ?, usuario_modificacion = ?, fecha_modificacion = ? 
                    WHERE num_factura = ?
                """, (nuevo_estado, notas, usuario, fecha_actual, num_factura))
            else:
                cursor.execute("""
                    UPDATE TRS_FACTURA 
                    SET estado = ?, notas_anulacion = NULL, usuario_modificacion = ?, fecha_modificacion = ? 
                    WHERE num_factura = ?
                """, (nuevo_estado, usuario, fecha_actual, num_factura))
                
            # 4. registrar auditoria
            posterior_dict = {**anterior_dict, "estado": nuevo_estado, "notas_anulacion": notas}
            self.registrar_auditoria(cursor, usuario, "MODIFICACION", "TRS_FACTURA", num_factura, anterior_dict, posterior_dict)

            # invalidar cache de productos por reversion/cambio de stock
            from modelos.producto_model import ProductoModel
            ProductoModel._cache_productos = None

            conn.commit()
            
            # log audit event to trs_auditoria_log after commit to avoid locks
            try:
                import json
                from controladores.AuditoriaService import AuditoriaService
                AuditoriaService.registrar("ANULAR_FACTURA" if nuevo_estado == "Anulada" else "MODIFICAR_ESTADO_FACTURA", 
                                           num_factura, json.dumps(anterior_dict), json.dumps(posterior_dict))
            except Exception as ae:
                print(f"[DEBUG ERROR] falla al registrar auditoria: {ae}")
                
            return True, f"Estado de factura {num_factura} actualizado a {nuevo_estado}."
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, str(e)
        finally:
            conn.close()

    def obtener_siguiente_correlativo(self, tipo_documento="Factura Electrónica"):
        # devuelve el siguiente correlativo para el tipo de comprobante
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            serie = "F001" if "Factura" in tipo_documento else "B001"
            cursor.execute("""
                SELECT IFNULL(MAX(correlativo_comprobante), 0) AS ultimo 
                FROM TRS_FACTURA 
                WHERE tipo_documento = ? AND serie_comprobante = ?
            """, (tipo_documento, serie))
            return cursor.fetchone()["ultimo"] + 1
        except Exception:
            return 1
        finally:
            conn.close()