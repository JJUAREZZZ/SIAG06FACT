from vistas.ClienteView import FormularioClienteDialog
from PyQt6.QtWidgets import QMessageBox
from datetime import datetime

class ClienteController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # parametros de paginacion
        self.items_por_pagina = 10
        self.pagina_actual = 1
        self.clientes_filtrados = []

        # conexion con los triggers de la interfaz
        self.view.btn_abrir_formulario.clicked.connect(self.mostrar_formulario_emergente)
        self.view.btn_modificar.clicked.connect(self.modificar_cliente)
        self.view.btn_cambiar_estado.clicked.connect(self.alternar_estado_cliente)
        
        self.view.input_buscar.textChanged.connect(self.filtrar_datos)
        self.view.combo_categoria.currentTextChanged.connect(self.filtrar_datos)

        # conectar botones de paginacion
        self.view.btn_pag_prev.clicked.connect(self.pagina_anterior)
        self.view.btn_pag_next.clicked.connect(self.pagina_siguiente)
        for idx, btn in enumerate(self.view.pag_buttons):
            if btn.text() == "10":
                btn.clicked.connect(lambda checked, p=10: self.cambiar_pagina(p))
            else:
                btn.clicked.connect(lambda checked, p=int(btn.text()): self.cambiar_pagina(p))

        self.actualizar_modulo()

    def mostrar_formulario_emergente(self):
        dialogo = FormularioClienteDialog(self.view)
        if dialogo.exec() == FormularioClienteDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            tipo_doc, dni_ruc, nombre_razon_social, direccion, email, telefono = datos
            
            # validacion robusta
            if not dni_ruc or not nombre_razon_social:
                self.mostrar_alerta("Campos Requeridos", "El número de documento y el Nombre/Razón Social son obligatorios.")
                return
                
            if tipo_doc == "DNI":
                if not dni_ruc.isdigit() or len(dni_ruc) != 8:
                    self.mostrar_alerta("Identificación Inválida", "El DNI debe contener exactamente 8 dígitos numéricos.")
                    return
            elif tipo_doc == "RUC":
                if not dni_ruc.isdigit() or len(dni_ruc) != 11:
                    self.mostrar_alerta("Identificación Inválida", "El RUC debe contener exactamente 11 dígitos numéricos.")
                    return

            try:
                # pasamos la tupla esperada por el modelo (dni_ruc, nombre, dir, email, tel)
                self.model.insertar_cliente((dni_ruc, nombre_razon_social, direccion, email, telefono))
                self.mostrar_info("Cliente Guardado", "El cliente se ha registrado con éxito en la base de datos.")
                self.actualizar_modulo()
            except Exception as e:
                self.mostrar_alerta("Error al Guardar", f"No se pudo guardar el cliente en SQLite. Verifique si ya existe:\n{e}")

    def modificar_cliente(self):
        seleccion = self.view.obtener_cliente_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Debes seleccionar un cliente de la lista para modificarlo.")
            return
            
        dni_ruc, _ = seleccion
        
        # buscar los datos completos del cliente en la lista local para no re-consultar la base de datos
        cliente_datos = None
        for c in self.clientes_completos:
            if c["dni_ruc"] == dni_ruc:
                cliente_datos = c
                break
                
        if not cliente_datos:
            self.mostrar_alerta("Error", "No se encontraron los datos del cliente seleccionado.")
            return
            
        dialogo = FormularioClienteDialog(self.view)
        dialogo.precompletar(cliente_datos)
        
        if dialogo.exec() == FormularioClienteDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            _, _, nombre_razon_social, direccion, email, telefono = datos
            
            # validacion robusta
            if not nombre_razon_social:
                self.mostrar_alerta("Campos Requeridos", "El Nombre o Razón Social es obligatorio.")
                return
                
            try:
                self.model.actualizar_cliente(dni_ruc, nombre_razon_social, direccion, email, telefono)
                self.mostrar_info("Cliente Modificado", "El cliente se ha actualizado con éxito.")
                self.actualizar_modulo()
            except Exception as e:
                self.mostrar_alerta("Error al Actualizar", f"No se pudo actualizar el cliente en SQLite:\n{e}")

    def alternar_estado_cliente(self):
        """captura la seleccion de la tabla y cambia el estado dinamicamente."""
        seleccion = self.view.obtener_cliente_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Debes seleccionar un cliente de la lista para cambiar su estado.")
            return
            
        dni_ruc, estado_actual = seleccion
        nuevo_estado = "Inactivo" if estado_actual == "Activo" else "Activo"
        
        try:
            self.model.modificar_estado_cliente(dni_ruc, nuevo_estado)
            self.actualizar_modulo()
        except Exception as e:
            self.mostrar_alerta("Error", f"Error crítico al actualizar el estado en SQLite: {e}")

    def actualizar_modulo(self):
        try:
            self.clientes_completos = self.model.obtener_todos()
            self.filtrar_datos()
            
            # recalcular kpis reales desde la base de datos
            total_clientes = len(self.clientes_completos)
            
            # clientes nuevos en el mes actual
            ahora = datetime.now()
            clientes_nuevos = 0
            for c in self.clientes_completos:
                try:
                    c_date = datetime.strptime(c["fecha_registro"].split()[0], "%Y-%m-%d")
                    if c_date.month == ahora.month and c_date.year == ahora.year:
                        clientes_nuevos += 1
                except Exception:
                    pass
                
            # saldo pendiente count
            saldo_pendiente = self.model.obtener_con_saldo_pendiente_count()

            self.view.actualizar_kpis(total_clientes, clientes_nuevos, saldo_pendiente)
                
        except Exception as e:
            print(f"[DEBUG ERROR] Error al actualizar Clientes: {e}")

    def filtrar_datos(self):
        if not hasattr(self, 'clientes_completos'):
            return
            
        texto = self.view.input_buscar.text().strip().lower()
        categoria = self.view.combo_categoria.currentText()

        self.clientes_filtrados = []
        for c in self.clientes_completos:
            match_texto = (not texto or 
                           texto in c["dni_ruc"].lower() or 
                           texto in c["nombre_razon_social"].lower())
            
            match_cat = True
            if categoria == "Empresa":
                match_cat = (c.get("tipo_documento") == "RUC")
            elif categoria == "Particular":
                match_cat = (c.get("tipo_documento") == "DNI")

            if match_texto and match_cat:
                self.clientes_filtrados.append(c)

        # actualizar etiqueta resumen
        total = len(self.clientes_filtrados)
        activos = sum(1 for c in self.clientes_filtrados if c.get("estado") == "Activo")
        inactivos = total - activos
        self.view.lbl_info_clientes.setText(f"Total items(clientes): {total}  |  Clientes activos: {activos}  |  Clientes inactivos: {inactivos}")

        # recargar tabla con paginacion
        self.pagina_actual = 1
        self.cargar_tabla_paginada()

    def cargar_tabla_paginada(self):
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        items_pagina = self.clientes_filtrados[inicio:fin]
        
        self.view.cargar_tabla(items_pagina)
        self.actualizar_controles_paginacion()

    def actualizar_controles_paginacion(self):
        total_items = len(self.clientes_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        
        self.view.btn_pag_prev.setEnabled(self.pagina_actual > 1)
        self.view.btn_pag_next.setEnabled(self.pagina_actual < total_paginas)

        for idx, btn in enumerate(self.view.pag_buttons[:-1]):
            num = idx + 1
            btn.setVisible(num <= total_paginas)
            if num == self.pagina_actual:
                btn.setStyleSheet("background-color: #1B2A4A; color: white; border-radius: 4px; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px;")

        btn_last = self.view.pag_buttons[-1]
        btn_last.setText(str(total_paginas))
        btn_last.setVisible(total_paginas > 4)
        self.view.lbl_pag_dots.setVisible(total_paginas > 4)
        
        if self.pagina_actual == total_paginas and total_paginas > 4:
            btn_last.setStyleSheet("background-color: #1B2A4A; color: white; border-radius: 4px; font-weight: bold;")
        else:
            btn_last.setStyleSheet("background-color: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px;")

    def cambiar_pagina(self, pagina):
        total_items = len(self.clientes_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if 1 <= pagina <= total_paginas:
            self.pagina_actual = pagina
            self.cargar_tabla_paginada()

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.cargar_tabla_paginada()

    def pagina_siguiente(self):
        total_items = len(self.clientes_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self.cargar_tabla_paginada()

    def estilo_alerta(self, msg_box):
        msg_box.setStyleSheet("""
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
        self.estilo_alerta(msg)
        msg.exec()

    def mostrar_info(self, titulo, mensaje):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        self.estilo_alerta(msg)
        msg.exec()