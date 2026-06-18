import sqlite3
import os
from datetime import datetime

# resolve absolute path (deficiency 2.1)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_facturacion.db")

class AsientoModel:
    def __init__(self):
        print("\n[DEBUG] Conectando con el almacenamiento contable (MAE_CUENTA_CONTABLE / TRS_ASIENTO_CONTABLE).")
        self._inicializar_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # activar restricciones de integridad
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 1. crear tabla maestra de cuentas contables (mae_cuenta_contable)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAE_CUENTA_CONTABLE (
                id_cuenta INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo VARCHAR(20) NOT NULL UNIQUE,
                nombre VARCHAR(100) NOT NULL
            )
        """)

        # semillero de cuentas contables (pcge de perú)
        cursor.execute("SELECT COUNT(*) AS total FROM MAE_CUENTA_CONTABLE")
        if cursor.fetchone()["total"] == 0:
            cuentas = [
                ('1212', 'Emitidas en cartera (Clientes por cobrar)'),
                ('40111', 'IGV - Cuenta Propia'),
                ('70111', 'Mercaderías - Venta Local')
            ]
            for cod, nom in cuentas:
                cursor.execute("INSERT INTO MAE_CUENTA_CONTABLE (codigo, nombre) VALUES (?, ?)", (cod, nom))
            conn.commit()
            print("[DEBUG] Semillero contable (MAE_CUENTA_CONTABLE) inicializado con cuentas 1212, 40111 y 70111.")

        # 2. crear tabla transaccional de cabecera de asientos contables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRS_ASIENTO_CONTABLE (
                id_asiento INTEGER PRIMARY KEY AUTOINCREMENT,
                num_asiento VARCHAR(20) NOT NULL UNIQUE,
                fecha DATE NOT NULL,
                glosa VARCHAR(255) NOT NULL,
                num_factura VARCHAR(20),
                estado VARCHAR(20) DEFAULT 'Cuadrado',
                total_debe DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                total_haber DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                FOREIGN KEY (num_factura) REFERENCES TRS_FACTURA (num_factura) ON DELETE SET NULL
            )
        """)

        # 3. crear tabla transaccional de detalle de asientos
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
        conn.commit()

        # ejecutar migración en caliente para facturas preexistentes que no tengan asiento
        self._migrar_facturas_sin_asiento(cursor)
        conn.commit()
        conn.close()

    def _migrar_facturas_sin_asiento(self, cursor):
        """Busca facturas que no tienen asiento contable asociado y les genera uno de manera retrospectiva."""
        cursor.execute("""
            SELECT f.num_factura, f.fecha_emision, f.subtotal, f.total_impuestos, f.total, f.estado
            FROM TRS_FACTURA f
            LEFT JOIN TRS_ASIENTO_CONTABLE a ON f.num_factura = a.num_factura
            WHERE a.id_asiento IS NULL
        """)
        facturas_sin = [dict(row) for row in cursor.fetchall()]
        
        if facturas_sin:
            print(f"[DEBUG] Se detectaron {len(facturas_sin)} facturas sin asiento contable. Migrando retrospectivamente...")
            for f in facturas_sin:
                try:
                    # crear asiento de venta
                    self.crear_asiento_para_factura(cursor, f["num_factura"], float(f["subtotal"]), float(f["total_impuestos"]), float(f["total"]), f["fecha_emision"])
                    # si ya estaba anulada, crear también el extorno
                    if f["estado"] == "Anulada":
                        self.crear_asiento_anulacion(cursor, f["num_factura"])
                except Exception as e:
                    print(f"[DEBUG ERROR] Error migrando asiento de factura {f['num_factura']}: {e}")

    def crear_asiento_para_factura(self, cursor, num_factura, subtotal, igv, total, fecha_emision=None):
        """Registra un asiento contable de ventas por partida doble."""
        if not fecha_emision:
            fecha_emision = datetime.now().strftime("%Y-%m-%d")

        # generar número de asiento ac-yyyy-xxxxx
        anio = fecha_emision.split('-')[0]
        cursor.execute("SELECT COUNT(*) AS total FROM TRS_ASIENTO_CONTABLE WHERE num_asiento LIKE ?", (f"AC-{anio}-%",))
        siguiente = cursor.fetchone()["total"] + 1
        num_asiento = f"AC-{anio}-{siguiente:05d}"
        glosa = f"Por la venta de mercadería, Factura {num_factura}"

        # 1. insertar cabecera de asiento
        cursor.execute("""
            INSERT INTO TRS_ASIENTO_CONTABLE (num_asiento, fecha, glosa, num_factura, estado, total_debe, total_haber)
            VALUES (?, ?, ?, ?, 'Cuadrado', ?, ?)
        """, (num_asiento, fecha_emision, glosa, num_factura, total, total))
        id_asiento = cursor.lastrowid

        # obtener ids de las cuentas contables (1212, 40111, 70111)
        cursor.execute("SELECT id_cuenta, codigo FROM MAE_CUENTA_CONTABLE WHERE codigo IN ('1212', '40111', '70111')")
        cuentas_map = {row["codigo"]: row["id_cuenta"] for row in cursor.fetchall()}

        # 2. insertar detalle de asiento (venta estándar: 1212 debe, 40111 haber, 70111 haber)
        # cuenta 1212 (clientes)
        cursor.execute("""
            INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
            VALUES (?, ?, ?, 0.00)
        """, (id_asiento, cuentas_map['1212'], total))

        # cuenta 40111 (igv)
        cursor.execute("""
            INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
            VALUES (?, ?, 0.00, ?)
        """, (id_asiento, cuentas_map['40111'], igv))

        # cuenta 70111 (ventas)
        cursor.execute("""
            INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
            VALUES (?, ?, 0.00, ?)
        """, (id_asiento, cuentas_map['70111'], subtotal))

        print(f"[DEBUG] Asiento contable de venta {num_asiento} registrado con éxito.")
        return num_asiento

    def crear_asiento_anulacion(self, cursor, num_factura):
        """Registra un asiento de extorno (asiento contable inverso) para netear la contabilidad."""
        # consultar la cabecera de la factura original
        cursor.execute("SELECT subtotal, total_impuestos, total, fecha_emision FROM TRS_FACTURA WHERE num_factura = ?", (num_factura,))
        fact = cursor.fetchone()
        if not fact:
            raise ValueError(f"No se puede extornar: La factura {num_factura} no existe.")

        subtotal = float(fact["subtotal"])
        igv = float(fact["total_impuestos"])
        total = float(fact["total"])
        fecha_actual = datetime.now().strftime("%Y-%m-%d")

        # generar número de asiento de extorno ac-ext-yyyy-xxxxx
        anio = fecha_actual.split('-')[0]
        cursor.execute("SELECT COUNT(*) AS total FROM TRS_ASIENTO_CONTABLE WHERE num_asiento LIKE ?", (f"AC-EXT-{anio}-%",))
        siguiente = cursor.fetchone()["total"] + 1
        num_asiento = f"AC-EXT-{anio}-{siguiente:05d}"
        glosa = f"Extorno por anulación de Factura {num_factura}"

        # 1. insertar cabecera de asiento de extorno
        cursor.execute("""
            INSERT INTO TRS_ASIENTO_CONTABLE (num_asiento, fecha, glosa, num_factura, estado, total_debe, total_haber)
            VALUES (?, ?, ?, ?, 'Cuadrado', ?, ?)
        """, (num_asiento, fecha_actual, glosa, num_factura, total, total))
        id_asiento = cursor.lastrowid

        # obtener ids de las cuentas contables (1212, 40111, 70111)
        cursor.execute("SELECT id_cuenta, codigo FROM MAE_CUENTA_CONTABLE WHERE codigo IN ('1212', '40111', '70111')")
        cuentas_map = {row["codigo"]: row["id_cuenta"] for row in cursor.fetchall()}

        # 2. insertar detalle de asiento extorno (contrario: 1212 haber, 40111 debe, 70111 debe)
        # cuenta 1212 (clientes)
        cursor.execute("""
            INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
            VALUES (?, ?, 0.00, ?)
        """, (id_asiento, cuentas_map['1212'], total))

        # cuenta 40111 (igv)
        cursor.execute("""
            INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
            VALUES (?, ?, ?, 0.00)
        """, (id_asiento, cuentas_map['40111'], igv))

        # cuenta 70111 (ventas)
        cursor.execute("""
            INSERT INTO TRS_DETALLE_ASIENTO (id_asiento, id_cuenta, debe, haber)
            VALUES (?, ?, ?, 0.00)
        """, (id_asiento, cuentas_map['70111'], subtotal))

        print(f"[DEBUG] Asiento contable de extorno {num_asiento} registrado con éxito.")
        return num_asiento

    def obtener_asiento_por_factura(self, num_factura):
        """Retorna todos los asientos contables asociados a una factura (el original y el extorno si existe)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # obtener cabeceras de asiento
            cursor.execute("""
                SELECT id_asiento, num_asiento, fecha, glosa, estado, total_debe, total_haber
                FROM TRS_ASIENTO_CONTABLE
                WHERE num_factura = ?
                ORDER BY id_asiento ASC
            """, (num_factura,))
            cabeceras = [dict(row) for row in cursor.fetchall()]

            # para cada cabecera, obtener sus detalles correspondientes
            asientos_completos = []
            for cab in cabeceras:
                cursor.execute("""
                    SELECT d.debe, d.haber, c.codigo AS cuenta_codigo, c.nombre AS cuenta_nombre
                    FROM TRS_DETALLE_ASIENTO d
                    JOIN MAE_CUENTA_CONTABLE c ON d.id_cuenta = c.id_cuenta
                    WHERE d.id_asiento = ?
                    ORDER BY d.debe DESC, d.haber DESC
                """, (cab["id_asiento"],))
                cab["detalles"] = [dict(row) for row in cursor.fetchall()]
                asientos_completos.append(cab)

            return asientos_completos
        finally:
            conn.close()
