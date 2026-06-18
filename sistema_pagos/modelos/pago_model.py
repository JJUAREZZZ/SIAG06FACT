import sqlite3
import os
from datetime import datetime

# resolve absolute path to the parent directory database (deficiency 2.1)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FACTURACION_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")
DB_PAGOS_PATH = os.path.join(BASE_DIR, "sistema_pagos.db")

class PagoModel:
    def __init__(self):
        print(f"\n[DEBUG] PagoModel conectando con la BD de Pagos: {DB_PAGOS_PATH}")
        print(f"[DEBUG] PagoModel adjuntando BD de Facturación: {DB_FACTURACION_PATH}")
        # validar la presencia física del archivo de base de datos de facturación
        if not os.path.exists(DB_FACTURACION_PATH):
            raise FileNotFoundError(f"El archivo de base de datos de facturación '{DB_FACTURACION_PATH}' no existe.")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PAGOS_PATH)
        conn.row_factory = sqlite3.Row
        # adjuntar base de datos de facturación (limpiando separadores para sqlite)
        db_fact_clean = DB_FACTURACION_PATH.replace("\\", "/")
        conn.execute(f"ATTACH DATABASE '{db_fact_clean}' AS facturacion;")
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # crear tabla de pagos en bd pagos (sin fk cruzada ya que sqlite no la permite entre bds separadas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TRS_PAGO (
                    id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_pago VARCHAR(20) NOT NULL UNIQUE,
                    fecha DATE NOT NULL,
                    dni_ruc VARCHAR(15) NOT NULL,
                    num_factura VARCHAR(20) NOT NULL,
                    monto DECIMAL(10,2) NOT NULL,
                    metodo_pago VARCHAR(50) NOT NULL,
                    notas TEXT,
                    estado VARCHAR(20) DEFAULT 'Emitido'
                )
            """)
            
            # crear tabla maestra de cuentas contables en bd pagos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS MAE_CUENTA_CONTABLE (
                    id_cuenta INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo VARCHAR(20) NOT NULL UNIQUE,
                    nombre VARCHAR(100) NOT NULL
                )
            """)
            
            # crear tabla transaccional de cabecera de asientos contables en bd pagos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TRS_ASIENTO_CONTABLE (
                    id_asiento INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_asiento VARCHAR(20) NOT NULL UNIQUE,
                    fecha DATE NOT NULL,
                    glosa VARCHAR(255) NOT NULL,
                    num_factura VARCHAR(20),
                    estado VARCHAR(20) DEFAULT 'Cuadrado',
                    total_debe DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    total_haber DECIMAL(10,2) NOT NULL DEFAULT 0.00
                )
            """)
            
            # crear tabla transaccional de detalle de asientos contables en bd pagos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TRS_DETALLE_ASIENTO (
                    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_asiento INTEGER NOT NULL,
                    id_cuenta INTEGER NOT NULL,
                    debe DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    haber DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    FOREIGN KEY (id_asiento) REFERENCES TRS_ASIENTO_CONTABLE (id_asiento) ON DELETE CASCADE,
                    FOREIGN KEY (id_cuenta) REFERENCES MAE_CUENTA_CONTABLE (id_cuenta)
                )
            """)
            
            # semillero de cuentas contables de cobro (1041 y 1212)
            cursor.execute("SELECT COUNT(*) FROM MAE_CUENTA_CONTABLE")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO MAE_CUENTA_CONTABLE (codigo, nombre) VALUES ('1041', 'Cuentas corrientes operativas')")
                cursor.execute("INSERT INTO MAE_CUENTA_CONTABLE (codigo, nombre) VALUES ('1212', 'Emitidas en cartera (Clientes por cobrar)')")
            
            conn.commit()
        finally:
            conn.close()

    def obtener_clientes_con_deuda(self):
        """Devuelve clientes activos que tienen al menos una factura en estado Pendiente con saldo restante > 0."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # obtenemos todos los clientes con facturas pendientes
            cursor.execute("""
                SELECT DISTINCT c.dni_ruc, c.nombre_razon_social, c.telefono, c.email
                FROM facturacion.MAE_CLIENTE c
                JOIN facturacion.TRS_FACTURA f ON c.dni_ruc = f.dni_ruc
                WHERE f.estado IN ('Pendiente', 'Emitido') AND c.estado = 'Activo'
                ORDER BY c.nombre_razon_social ASC
            """)
            clientes = [dict(row) for row in cursor.fetchall()]
            
            # filtramos únicamente los clientes que posean saldo pendiente real (saldo restante > 0)
            clientes_con_saldo = []
            for c in clientes:
                facturas = self.obtener_facturas_pendientes_cliente(c["dni_ruc"])
                if facturas: # si tiene al menos una factura con saldo_restante > 0
                    clientes_con_saldo.append(c)
            return clientes_con_saldo
        finally:
            conn.close()

    def obtener_facturas_pendientes_cliente(self, dni_ruc):
        """Devuelve las facturas Pendientes de un cliente específico calculando el saldo restante."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # calculamos dinámicamente el saldo restante restando los cobros 'emitido'
            cursor.execute("""
                SELECT f.num_factura, f.fecha_emision, f.total, f.subtotal, f.total_impuestos,
                       (SELECT IFNULL(SUM(p.monto), 0) FROM TRS_PAGO p WHERE p.num_factura = f.num_factura AND p.estado = 'Emitido') AS total_pagado
                FROM facturacion.TRS_FACTURA f
                WHERE f.dni_ruc = ? AND f.estado IN ('Pendiente', 'Emitido')
                ORDER BY f.fecha_emision ASC
            """, (dni_ruc,))
            
            resultado = []
            for row in cursor.fetchall():
                f = dict(row)
                total = float(f["total"])
                total_pagado = float(f["total_pagado"])
                saldo_restante = total - total_pagado
                
                # solo agregamos si hay saldo pendiente por amortizar
                if saldo_restante > 0.01:
                    f["saldo_restante"] = saldo_restante
                    resultado.append(f)
            return resultado
        finally:
            conn.close()

    def registrar_pago_cliente(self, dni_ruc, num_factura, monto, metodo_pago, notas):
        """Registra un pago parcial o total en la base de datos de forma transaccional."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            
            # 1. verificar el estado de la factura y su saldo restante
            cursor.execute("""
                SELECT estado, total,
                       (SELECT IFNULL(SUM(p.monto), 0) FROM TRS_PAGO p WHERE p.num_factura = ? AND p.estado = 'Emitido') AS total_pagado
                FROM facturacion.TRS_FACTURA WHERE num_factura = ?
            """, (num_factura, num_factura))
            fact = cursor.fetchone()
            if not fact:
                raise ValueError(f"La factura {num_factura} no existe.")
            if fact["estado"] not in ("Pendiente", "Emitido"):
                raise ValueError(f"La factura {num_factura} ya no se encuentra pendiente (Estado: {fact['estado']}).")
                
            total_factura = float(fact["total"])
            total_pagado = float(fact["total_pagado"])
            saldo_restante = total_factura - total_pagado
            
            if monto > (saldo_restante + 0.01):
                raise ValueError(f"El monto a cobrar (S/ {monto:.2f}) excede el saldo restante (S/ {saldo_restante:.2f}).")
                
            # 2. generar número correlativo de recibo (r001-xxxxx) usando max
            cursor.execute("SELECT IFNULL(MAX(id_pago), 0) AS ultimo FROM TRS_PAGO")
            ultimo_id = cursor.fetchone()["ultimo"]
            siguiente = ultimo_id + 1
            num_pago = f"R001-{siguiente:05d}"
            fecha_actual = datetime.now().strftime("%Y-%m-%d")

            # 3. insertar el recibo de pago
            cursor.execute("""
                INSERT INTO TRS_PAGO (num_pago, fecha, dni_ruc, num_factura, monto, metodo_pago, notas, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Emitido')
            """, (num_pago, fecha_actual, dni_ruc, num_factura, monto, metodo_pago, notas))

            # 4. si el pago cubre el saldo pendiente, marcar la factura como 'pagada'
            if abs(monto - saldo_restante) < 0.01:
                cursor.execute("""
                    UPDATE facturacion.TRS_FACTURA
                    SET estado = 'Pagada', metodo_pago = ?
                    WHERE num_factura = ?
                """, (metodo_pago, num_factura))

            # 5. generar asiento contable del cobro (cobro de cliente)
            # cuenta 1041 (debe) -> cuenta corriente
            # cuenta 1212 (haber) -> facturas por cobrar
            anio = fecha_actual.split('-')[0]
            
            cursor.execute("SELECT COUNT(*) AS total FROM TRS_ASIENTO_CONTABLE WHERE num_asiento LIKE ?", (f"AC-COB-{anio}-%",))
            siguiente_asiento = cursor.fetchone()["total"] + 1
            num_asiento = f"AC-COB-{anio}-{siguiente_asiento:05d}"
            glosa = f"Por la cobranza de la Factura {num_factura}, Recibo {num_pago}"

            # cabecera de asiento
            cursor.execute("""
                INSERT INTO TRS_ASIENTO_CONTABLE (num_asiento, fecha, glosa, num_factura, estado, total_debe, total_haber)
                VALUES (?, ?, ?, ?, 'Cuadrado', ?, ?)
            """, (num_asiento, fecha_actual, glosa, num_factura, monto, monto))
            id_asiento = cursor.lastrowid

            # mapear ids de cuentas contables
            cursor.execute("SELECT id_cuenta, codigo FROM MAE_CUENTA_CONTABLE WHERE codigo IN ('1041', '1212')")
            cuentas_map = {row["codigo"]: row["id_cuenta"] for row in cursor.fetchall()}

            if '1041' not in cuentas_map:
                cursor.execute("INSERT INTO MAE_CUENTA_CONTABLE (codigo, nombre) VALUES ('1041', 'Cuentas corrientes operativas')")
                id_1041 = cursor.lastrowid
            else:
                id_1041 = cuentas_map['1041']
                
            id_1212 = cuentas_map['1212']

            # detalle asiento: 1041 al debe
            cursor.execute("""
                INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
                VALUES (?, ?, ?, 0.00)
            """, (id_asiento, id_1041, monto))

            # detalle asiento: 1212 al haber
            cursor.execute("""
                INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
                VALUES (?, ?, 0.00, ?)
            """, (id_asiento, id_1212, monto))

            cursor.execute("COMMIT;")
            return True, num_pago
        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
            except Exception:
                pass
            return False, str(e)
        finally:
            conn.close()

    def anular_pago_cliente(self, num_pago):
        """Anula un recibo de pago, revierte la factura a 'Pendiente' y genera un extorno contable."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            
            # 1. obtener datos del pago
            cursor.execute("SELECT num_factura, monto, estado, dni_ruc FROM TRS_PAGO WHERE num_pago = ?", (num_pago,))
            pago = cursor.fetchone()
            if not pago:
                raise ValueError(f"El recibo de pago {num_pago} no existe.")
            if pago["estado"] == "Anulado":
                raise ValueError(f"El recibo de pago {num_pago} ya está anulado.")
                
            num_factura = pago["num_factura"]
            monto = float(pago["monto"])
            
            # 2. cambiar estado del pago a anulado
            cursor.execute("UPDATE TRS_PAGO SET estado = 'Anulado' WHERE num_pago = ?", (num_pago,))
            
            # 3. regresar factura a estado 'pendiente' de forma segura
            cursor.execute("""
                UPDATE facturacion.TRS_FACTURA
                SET estado = 'Pendiente', metodo_pago = NULL
                WHERE num_factura = ?
            """, (num_factura,))
            
            # 4. generar asiento de extorno (reversión del cobro)
            # debe: 1212 (clientes)
            # haber: 1041 (caja/bancos)
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            anio = fecha_actual.split('-')[0]
            
            cursor.execute("SELECT COUNT(*) AS total FROM TRS_ASIENTO_CONTABLE WHERE num_asiento LIKE ?", (f"AC-EXT-COB-{anio}-%",))
            siguiente_asiento = cursor.fetchone()["total"] + 1
            num_asiento = f"AC-EXT-COB-{anio}-{siguiente_asiento:05d}"
            glosa = f"Extorno por anulación de Recibo {num_pago}, Factura {num_factura}"

            cursor.execute("""
                INSERT INTO TRS_ASIENTO_CONTABLE (num_asiento, fecha, glosa, num_factura, estado, total_debe, total_haber)
                VALUES (?, ?, ?, ?, 'Cuadrado', ?, ?)
            """, (num_asiento, fecha_actual, glosa, num_factura, monto, monto))
            id_asiento = cursor.lastrowid

            cursor.execute("SELECT id_cuenta, codigo FROM MAE_CUENTA_CONTABLE WHERE codigo IN ('1041', '1212')")
            cuentas_map = {row["codigo"]: row["id_cuenta"] for row in cursor.fetchall()}
            
            id_1041 = cuentas_map['1041']
            id_1212 = cuentas_map['1212']

            # 1212 al debe
            cursor.execute("""
                INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
                VALUES (?, ?, ?, 0.00)
            """, (id_asiento, id_1212, monto))

            # 1041 al haber
            cursor.execute("""
                INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
                VALUES (?, ?, 0.00, ?)
            """, (id_asiento, id_1041, monto))

            cursor.execute("COMMIT;")
            return True, num_asiento
        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
            except Exception:
                pass
            return False, str(e)
        finally:
            conn.close()

    def obtener_pagos(self):
        """Devuelve el historial completo de pagos emitidos."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.num_pago, p.num_factura, p.fecha, p.monto, p.metodo_pago, p.notas, p.estado,
                       c.nombre_razon_social AS cliente_nombre, c.dni_ruc
                FROM TRS_PAGO p
                JOIN facturacion.MAE_CLIENTE c ON p.dni_ruc = c.dni_ruc
                ORDER BY p.id_pago DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def obtener_siguiente_num_pago(self):
        """Devuelve el siguiente número correlativo disponible usando el MAX(id_pago) + 1."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT IFNULL(MAX(id_pago), 0) AS ultimo FROM TRS_PAGO")
            ultimo_id = cursor.fetchone()["ultimo"]
            return f"R001-{(ultimo_id + 1):05d}"
        finally:
            conn.close()

    def obtener_asiento_por_pago(self, num_pago, num_factura):
        """Obtiene el asiento contable de cobranza correspondiente a un recibo de pago."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_asiento, num_asiento, fecha, glosa, total_debe, total_haber
                FROM TRS_ASIENTO_CONTABLE
                WHERE num_factura = ? AND glosa LIKE ?
                LIMIT 1
            """, (num_factura, f"%Recibo {num_pago}%"))
            row = cursor.fetchone()
            if not row:
                return None
            asiento = dict(row)
            
            # obtener detalles
            cursor.execute("""
                SELECT d.debe, d.haber, c.codigo AS cuenta_codigo, c.nombre AS cuenta_nombre
                FROM TRS_DETALLE_ASIENTO d
                JOIN MAE_CUENTA_CONTABLE c ON d.id_cuenta = c.id_cuenta
                WHERE d.id_asiento = ?
                ORDER BY d.debe DESC, d.haber DESC
            """, (asiento["id_asiento"],))
            asiento["detalles"] = [dict(r) for r in cursor.fetchall()]
            return asiento
        finally:
            conn.close()
