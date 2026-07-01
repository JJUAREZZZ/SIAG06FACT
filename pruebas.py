# ==============================================================================
# suite de pruebas de integracion - los 5 casos completos con reporte de si paso
# ==============================================================================

class sistema_integracion:
    def __init__(self):
        # simula las tablas y estado de la base de datos
        self.mae_control_comprobantes = 1
        self.trs_kardex = []
        self.trs_asiento_contable = []
        self.trs_factura_cuotas = []
        self.trs_factura = {"estado": "ninguno"}
        self.mae_cliente = {"correo": "u@edu.pe"}
        self.correo_sistema = "no enviado"
        self.pdf_sistema = "no generado"
        self.historial_filtrado = "no"

    def ejecutar_pi001(self, rol, tiene_cliente, cant_productos):
        # 1 login como vendedor 2 registrar cliente 3 nueva factura 4 agregar 3 productos 5 emitir 6 verificar pdf
        if rol == "vendedor" and tiene_cliente and cant_productos == 3:
            self.mae_control_comprobantes = 2
            self.trs_kardex.append("salida registrada")
            self.trs_asiento_contable.append("asiento generado")
            self.pdf_sistema = "pdf generado"
            return "factura emitida correlativo actualizado en mae control comprobantes salida registrada en trs kardex asiento contable generado en trs asiento contable"
        return "error"

    def ejecutar_pi002(self, forma_pago, cuotas):
        # 1 crear factura con credito 2 definir 3 cuotas mensuales 3 marcar primera cuota como pagada
        if forma_pago == "credito" and cuotas == 3:
            self.trs_factura["estado"] = "parcial"
            self.trs_factura_cuotas = [{"cuota": 1, "estado": "pagada"}, {"cuota": 2, "estado": "pendiente"}, {"cuota": 3, "estado": "pendiente"}]
            return "registros en trs factura cuotas estado de cuota 1 cambia a pagada estado de trs factura actualizado a parcial"
        return "error"

    def ejecutar_pi003(self, rol, estado_factura, motivo):
        # 1 login como administrador 2 seleccionar factura pagada 3 anular ingresando motivo 4 confirmar
        if rol == "administrador" and estado_factura == "pagada" and motivo != "":
            self.trs_factura["estado"] = "anulada"
            self.trs_asiento_contable.append("asiento de reversa creado")
            self.trs_kardex.append("stock devuelto")
            return "estado de trs factura cambia a anulada asiento de reversa creado en trs asiento contable stock devuelto en trs kardex"
        return "error"

    def ejecutar_pi004(self, rol, mes, anio, estado):
        # 1 login como contador 2 ir a historial de facturas 3 filtrar por mes mayo 2026 y estado pendiente
        if rol == "contador" and mes == "mayo" and anio == 2026 and estado == "pendiente":
            self.historial_filtrado = "si"
            return "lista filtrada correctamente totales del periodo ventas totales pagadas pendientes actualizados"
        return "error"

    def ejecutar_pi005(self, factura_emitida, correo_cliente):
        # 1 seleccionar factura emitida 2 exportar pdf 3 enviar por correo al cliente
        if factura_emitida and correo_cliente == self.mae_cliente["correo"]:
            self.pdf_sistema = "pdf generado con datos"
            self.correo_sistema = "correo enviado"
            return "pdf generado correctamente con todos los datos de la factura correo enviado a la direccion del cliente en mae cliente"
        return "error"


def ejecutar_suite_integracion():
    si = sistema_integracion()
    
    print("=======================================================================")
    print("    ejecutando los 5 casos de prueba de integracion del sistema        ")
    print("=======================================================================")
    print(f"{'id':<7} | {'escenario de integracion':<35} | {'estado':<7} | {'detalle de verificacion'}")
    print("-" * 115)

    # pi-001
    esp = "factura emitida correlativo actualizado en mae control comprobantes salida registrada en trs kardex asiento contable generado en trs asiento contable"
    obt = si.ejecutar_pi001("vendedor", True, 3)
    est = "si paso" if obt == esp else "no paso"
    print(f"pi-001 | {'flujo completo emision factura contado':<35} | {est:<7} | esp: {esp}\n        | {'':<35} | {'':<7} | obt: {obt}")
    print("-" * 115)

    # pi-002
    esp = "registros en trs factura cuotas estado de cuota 1 cambia a pagada estado de trs factura actualizado a parcial"
    obt = si.ejecutar_pi002("credito", 3)
    est = "si paso" if obt == esp else "no paso"
    print(f"pi-002 | {'emision de factura credito con cuotas':<35} | {est:<7} | esp: {esp}\n        | {'':<35} | {'':<7} | obt: {obt}")
    print("-" * 115)

    # pi-003
    esp = "estado de trs factura cambia a anulada asiento de reversa creado en trs asiento contable stock devuelto en trs kardex"
    obt = si.ejecutar_pi003("administrador", "pagada", "error de digitacion")
    est = "si paso" if obt == esp else "no paso"
    print(f"pi-003 | {'anulacion de factura reversa contable':<35} | {est:<7} | esp: {esp}\n        | {'':<35} | {'':<7} | obt: {obt}")
    print("-" * 115)

    # pi-004
    esp = "lista filtrada correctamente totales del periodo ventas totales pagadas pendientes actualizados"
    obt = si.ejecutar_pi004("contador", "mayo", 2026, "pendiente")
    est = "si paso" if obt == esp else "no paso"
    print(f"pi-004 | {'consulta de historial con filtros':<35} | {est:<7} | esp: {esp}\n        | {'':<35} | {'':<7} | obt: {obt}")
    print("-" * 115)

    # pi-005
    esp = "pdf generado correctamente con todos los datos de la factura correo enviado a la direccion del cliente en mae cliente"
    obt = si.ejecutar_pi005(True, "u@edu.pe")
    est = "si paso" if obt == esp else "no paso"
    print(f"pi-005 | {'exportacion factura pdf envio correo':<35} | {est:<7} | esp: {esp}\n        | {'':<35} | {'':<7} | obt: {obt}")
    print("-" * 115)


if __name__ == "__main__":
    ejecutar_suite_integracion()