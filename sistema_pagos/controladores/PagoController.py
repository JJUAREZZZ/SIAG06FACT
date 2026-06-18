from PyQt6.QtWidgets import QMessageBox

class PagoController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # connect signals
        self.view.cliente_cambiado.connect(self._on_cliente_cambiado)
        self.view.combo_factura.currentTextChanged.connect(self._on_factura_cambiada)
        self.view.pago_solicitado.connect(self._registrar_pago)

        self.actualizar_modulo()

    def actualizar_modulo(self):
        """Refresca la información del selector de clientes y del número de recibo."""
        try:
            # cargar clientes con deuda activa
            clientes = self.model.obtener_clientes_con_deuda()
            self.view.cargar_clientes(clientes)

            # cargar correlativo del recibo
            siguiente_num = self.model.obtener_siguiente_num_pago()
            self.view.lbl_num_recibo.setText(siguiente_num)
        except Exception as e:
            print(f"[DEBUG ERROR] Falló al refrescar el módulo de Pagos: {e}")

    def _on_cliente_cambiado(self, dni_ruc):
        if not dni_ruc:
            return
        try:
            facturas = self.model.obtener_facturas_pendientes_cliente(dni_ruc)
            self.view.cargar_facturas(facturas)
        except Exception as e:
            print(f"[DEBUG ERROR] Error al cargar facturas de cliente {dni_ruc}: {e}")

    def _on_factura_cambiada(self, text):
        num_factura = self.view.combo_factura.currentData()
        self.view.set_factura_seleccionada(num_factura)

    def _registrar_pago(self, dni_ruc, num_factura, monto, metodo, notas):
        # confirmación
        box = QMessageBox(self.view)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Confirmar Pago")
        box.setText(f"¿Desea registrar el Recibo de Pago por S/ {monto:,.2f}?\n"
                     f"Esto cancelará la Factura {num_factura} a estado 'Pagada'.")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        self._estilo_alerta(box)
        
        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        # registrar
        exito, resultado = self.model.registrar_pago_cliente(dni_ruc, num_factura, monto, metodo, notas)

        if exito:
            box_ok = QMessageBox(self.view)
            box_ok.setIcon(QMessageBox.Icon.Information)
            box_ok.setWindowTitle("Pago Registrado")
            box_ok.setText(f"✔ Recibo de Caja {resultado} emitido correctamente.\n"
                           f"La factura {num_factura} ahora está PAGADA.")
            self._estilo_alerta(box_ok)
            box_ok.exec()
            self.actualizar_modulo()
        else:
            box_err = QMessageBox(self.view)
            box_err.setIcon(QMessageBox.Icon.Critical)
            box_err.setWindowTitle("Error al registrar pago")
            box_err.setText(f"No se pudo completar el cobro:\n{resultado}")
            self._estilo_alerta(box_err)
            box_err.exec()

    def _estilo_alerta(self, msg_box):
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
