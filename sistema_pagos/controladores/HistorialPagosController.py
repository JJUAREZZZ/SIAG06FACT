from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import Qt, QDate

class HistorialPagosController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # paginator properties
        self.items_por_pagina = 10
        self.pagina_actual = 1
        self.pagos_filtrados = []

        # connect signals
        self.view.input_buscar.textChanged.connect(self.filtrar_datos)
        self.view.combo_fecha.currentTextChanged.connect(self.filtrar_datos)
        self.view.btn_ver_asiento.clicked.connect(self.ver_asiento_contable)
        self.view.btn_anular.clicked.connect(self.anular_recibo_pago)

        # connect pagination buttons
        self.view.btn_pag_prev.clicked.connect(self.pagina_anterior)
        self.view.btn_pag_next.clicked.connect(self.pagina_siguiente)
        for idx, btn in enumerate(self.view.pag_buttons):
            if btn.text() == "10":
                btn.clicked.connect(lambda checked, p=10: self.cambiar_pagina(p))
            else:
                btn.clicked.connect(lambda checked, p=int(btn.text()): self.cambiar_pagina(p))

        self.actualizar_modulo()

    def actualizar_modulo(self):
        try:
            self.pagos_completos = self.model.obtener_pagos()
            self.filtrar_datos()
        except Exception as e:
            self.mostrar_alerta("Error de Carga", f"No se pudieron cargar los cobros desde la base de datos:\n{e}")
            self.pagos_completos = []
            self.filtrar_datos()

    def filtrar_datos(self):
        if not hasattr(self, 'pagos_completos'):
            return

        texto_busqueda = self.view.input_buscar.text().strip().lower()
        filtro_fecha = self.view.combo_fecha.currentText()

        # filtrar
        self.pagos_filtrados = []
        hoy = QDate.currentDate()
        for p in self.pagos_completos:
            # 1. filtro de texto (búsqueda)
            match_texto = (not texto_busqueda or 
                           texto_busqueda in p["num_pago"].lower() or 
                           texto_busqueda in p["num_factura"].lower() or 
                           texto_busqueda in p["cliente_nombre"].lower() or 
                           texto_busqueda in p["dni_ruc"].lower())
            
            # 2. filtro de rango de fechas
            match_fecha = True
            if filtro_fecha != "Todos":
                try:
                    p_date = QDate.fromString(p["fecha"], "yyyy-MM-dd")
                    if filtro_fecha == "Hoy":
                        match_fecha = (p_date == hoy)
                    elif filtro_fecha == "Esta Semana":
                        match_fecha = (p_date.daysTo(hoy) <= 7 and p_date.daysTo(hoy) >= 0)
                    elif filtro_fecha == "Este Mes":
                        match_fecha = (p_date.year() == hoy.year() and p_date.month() == hoy.month())
                except Exception:
                    pass
                    
            if match_texto and match_fecha:
                self.pagos_filtrados.append(p)

        # recalcular totales del periodo filtrado
        total_recaudado = sum(float(p["monto"]) for p in self.pagos_filtrados)
        cantidad_recibos = len(self.pagos_filtrados)
        self.view.actualizar_resumen(total_recaudado, cantidad_recibos)

        # resetear paginación y recargar tabla
        self.pagina_actual = 1
        self.cargar_tabla_paginada()

    def cargar_tabla_paginada(self):
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        items_pagina = self.pagos_filtrados[inicio:fin]
        
        self.view.cargar_tabla(items_pagina)
        self.actualizar_controles_paginacion()

    def actualizar_controles_paginacion(self):
        total_items = len(self.pagos_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        
        # habilitar/deshabilitar controles de navegación
        self.view.btn_pag_prev.setEnabled(self.pagina_actual > 1)
        self.view.btn_pag_next.setEnabled(self.pagina_actual < total_paginas)

        # actualizar visibilidad de botones
        for idx, btn in enumerate(self.view.pag_buttons[:-1]): # del 1 al 4
            num = idx + 1
            btn.setVisible(num <= total_paginas)
            if num == self.pagina_actual:
                btn.setStyleSheet("background-color: #1B2A4A; color: white; border-radius: 4px; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px;")

        # último botón
        btn_last = self.view.pag_buttons[-1]
        btn_last.setText(str(total_paginas))
        btn_last.setVisible(total_paginas > 4)
        self.view.lbl_pag_dots.setVisible(total_paginas > 4)
        
        if self.pagina_actual == total_paginas and total_paginas > 4:
            btn_last.setStyleSheet("background-color: #1B2A4A; color: white; border-radius: 4px; font-weight: bold;")
        else:
            btn_last.setStyleSheet("background-color: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px;")

    def cambiar_pagina(self, pagina):
        total_items = len(self.pagos_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if 1 <= pagina <= total_paginas:
            self.pagina_actual = pagina
            self.cargar_tabla_paginada()

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.cargar_tabla_paginada()

    def pagina_siguiente(self):
        total_items = len(self.pagos_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self.cargar_tabla_paginada()

    def ver_asiento_contable(self):
        seleccion = self.view.obtener_pago_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione un recibo de pago de la tabla para ver su asiento contable.")
            return

        num_pago, num_factura = seleccion
        
        try:
            # consultar base de datos para obtener el asiento específico de este recibo
            asiento = self.model.obtener_asiento_por_pago(num_pago, num_factura)
            
            # mostrar diálogo visual
            from vistas.AsientoPagoDialog import AsientoPagoDialog
            dialogo = AsientoPagoDialog(num_pago, num_factura, asiento, self.view)
            dialogo.exec()
        except Exception as e:
            self.mostrar_alerta("Error al cargar asiento", f"No se pudo cargar el asiento contable:\n{e}")

    def anular_recibo_pago(self):
        """Gestiona el proceso de anulación de un recibo seleccionado."""
        seleccion = self.view.obtener_pago_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione un recibo de pago de la tabla para proceder con su anulación.")
            return

        num_pago, num_factura = seleccion
        
        # primero verificar que no esté ya anulado y obtener el monto
        monto_pago = 0.0
        for p in self.pagos_completos:
            if p["num_pago"] == num_pago:
                if p.get("estado") == "Anulado":
                    self.mostrar_alerta("Acción Inválida", f"El recibo {num_pago} ya se encuentra anulado.")
                    return
                monto_pago = float(p["monto"])
                break

        # confirmar anulación
        box = QMessageBox(self.view)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Anular Recibo de Pago")
        box.setText(f"¿Está seguro de que desea ANULAR el recibo de pago {num_pago}?\n\n"
                    f"Esto revertirá el cobro de S/ {monto_pago:,.2f} y regresará la factura {num_factura} a estado 'Pendiente' en el sistema.")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        self.estilo_msg_box(box)

        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        exito, resultado = self.model.anular_pago_cliente(num_pago)

        if exito:
            box_ok = QMessageBox(self.view)
            box_ok.setIcon(QMessageBox.Icon.Information)
            box_ok.setWindowTitle("Recibo Anulado")
            box_ok.setText(f"✔ Recibo de Caja {num_pago} anulado con éxito.\n"
                           f"Se generó el asiento contable de extorno: {resultado}")
            self.estilo_msg_box(box_ok)
            box_ok.exec()
            self.actualizar_modulo()
        else:
            self.mostrar_alerta("Error al anular", f"El motor relacional rechazó la operación:\n{resultado}")

    def estilo_msg_box(self, box):
        box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)

    def mostrar_alerta(self, titulo, mensaje):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        msg.exec()
