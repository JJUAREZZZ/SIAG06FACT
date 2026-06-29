from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt

class CambiarEstadoFacturaDialog(QDialog):
    def __init__(self, num_factura, estado_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cambiar Estado de Factura")
        self.setFixedSize(360, 220)
        self.setStyleSheet("background-color: white;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel(f"Factura: {num_factura}\nEstado actual: {estado_actual}")
        lbl.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl)

        layout.addWidget(QLabel("Nuevo estado:", styleSheet="color: #7c7c7c; font-size: 11px; font-weight: bold;"))
        self.combo = QComboBox()
        self.combo.addItems(["Pagada", "Pendiente", "Anulada"])
        self.combo.setCurrentText(estado_actual)
        self.combo.setStyleSheet("""
            QComboBox { padding: 6px; border: 1px solid #CCD1D9; border-radius: 4px; background: white; color: black; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
        """)
        layout.addWidget(self.combo)

        self.input_notas = QLineEdit()
        self.input_notas.setPlaceholderText("Notas de la anulación (Opcional)")
        self.input_notas.setStyleSheet("padding: 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: #F4F6F9; color: black;")
        self.input_notas.setVisible(estado_actual == "Anulada" or self.combo.currentText() == "Anulada")
        layout.addWidget(self.input_notas)

        # mostrar/ocultar notas dinamicamente si elige anulada
        self.combo.currentTextChanged.connect(lambda text: self.input_notas.setVisible(text == "Anulada"))

        btn_lay = QHBoxLayout()
        btn_can = QPushButton("Cancelar")
        btn_can.setStyleSheet("background-color: #C00000; color: white; padding: 7px; border-radius: 4px; font-weight: bold; border: none;")
        btn_can.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Actualizar")
        btn_ok.setStyleSheet("background-color: #1B2A4A; color: white; padding: 7px; border-radius: 4px; font-weight: bold; border: none;")
        btn_ok.clicked.connect(self.accept)

        btn_lay.addWidget(btn_can)
        btn_lay.addWidget(btn_ok)
        layout.addLayout(btn_lay)

    def obtener_valores(self):
        return self.combo.currentText(), self.input_notas.text().strip()


class DetalleFacturaDialog(QDialog):
    def __init__(self, factura_data, asientos_data, parent=None):
        super().__init__(parent)
        num_factura = factura_data.get("num_factura", "")
        self.setWindowTitle(f"Detalle de Comprobante — {num_factura}")
        self.setMinimumSize(640, 520)
        self.setStyleSheet("background-color: white;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_titulo = QLabel(f"Detalle de {factura_data.get('tipo_documento', 'Comprobante')}")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2A4A;")
        layout.addWidget(lbl_titulo)

        grid = QGridLayout()
        grid.setSpacing(8)
        
        def _add_meta(row, label, val):
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet("color: #7c7c7c; font-weight: bold; font-size: 11px;")
            l_val = QLabel(str(val))
            l_val.setStyleSheet("color: #1B2A4A; font-size: 12px;")
            grid.addWidget(l_lbl, row, 0)
            grid.addWidget(l_val, row, 1)

        _add_meta(0, "Nro. Documento:", factura_data.get("num_factura"))
        _add_meta(1, "Cliente:", factura_data.get("cliente_nombre"))
        _add_meta(2, "RUC/DNI:", factura_data.get("dni_ruc"))
        _add_meta(3, "Fecha Emisión:", factura_data.get("fecha_emision"))
        _add_meta(4, "Forma de Pago:", factura_data.get("forma_pago"))
        _add_meta(5, "Método de Pago:", factura_data.get("metodo_pago") or "—")
        _add_meta(6, "Estado:", factura_data.get("estado"))

        layout.addLayout(grid)

        layout.addWidget(QLabel("ÍTEMS DEL COMPROBANTE:", styleSheet="color: #7c7c7c; font-weight: bold; font-size: 11px; margin-top: 10px;"))
        
        self.tabla_items = QTableWidget(0, 4)
        self.tabla_items.setHorizontalHeaderLabels(["Producto", "Cant.", "P. Unit.", "Total Linea"])
        self.tabla_items.horizontalHeader().setStretchLastSection(True)
        self.tabla_items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_items.verticalHeader().setVisible(False)
        self.tabla_items.setStyleSheet("QTableWidget { gridline-color: #E8EDF8; color: #1B2A4A; } QHeaderView::section { background-color: #1B2A4A; color: white; padding: 4px; font-weight: bold; }")
        
        simbolo = factura_data.get("moneda_simbolo", "S/")
        for it in factura_data.get("items", []):
            r = self.tabla_items.rowCount()
            self.tabla_items.insertRow(r)
            
            p_name = it.get("producto_nombre", "Prod")
            cant = it.get("cantidad", 1)
            p_unit = float(it.get("precio_unitario_historico", 0.0))
            t_line = p_unit * cant - float(it.get("monto_descuento_linea", 0.0))
            
            self.tabla_items.setItem(r, 0, QTableWidgetItem(p_name))
            self.tabla_items.setItem(r, 1, QTableWidgetItem(str(cant)))
            self.tabla_items.setItem(r, 2, QTableWidgetItem(f"{simbolo} {p_unit:.2f}"))
            self.tabla_items.setItem(r, 3, QTableWidgetItem(f"{simbolo} {t_line:.2f}"))
            
        layout.addWidget(self.tabla_items)

        totales_lay = QHBoxLayout()
        totales_lay.addStretch()
        lbl_tot = QLabel(f"TOTAL COMPROBANTE: {simbolo} {float(factura_data.get('total', 0.0)):.2f}")
        lbl_tot.setStyleSheet("font-size: 14px; font-weight: bold; color: #1B2A4A; padding: 5px;")
        totales_lay.addWidget(lbl_tot)
        layout.addLayout(totales_lay)

        btn_lay = QHBoxLayout()
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setStyleSheet("background-color: #1B2A4A; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; border: none; min-width: 80px;")
        self.btn_cerrar.clicked.connect(self.accept)
        
        self.btn_imprimir = QPushButton("Imprimir Comprobante")
        self.btn_imprimir.setStyleSheet("background-color: #70AD47; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; border: none; min-width: 120px;")
        
        btn_lay.addWidget(self.btn_imprimir)
        btn_lay.addStretch()
        btn_lay.addWidget(self.btn_cerrar)
        layout.addLayout(btn_lay)


class HistorialController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # parametros de paginacion
        self.items_por_pagina = 10
        self.pagina_actual = 1
        self.facturas_filtradas = []

        # conectar triggers de filtros
        self.view.input_buscar.textChanged.connect(self.filtrar_datos)
        self.view.combo_estado.currentTextChanged.connect(self.filtrar_datos)
        self.view.combo_fecha.currentTextChanged.connect(self.filtrar_datos)
        self.view.btn_cambiar_estado.clicked.connect(self.cambiar_estado_factura)
        self.view.btn_ver_asiento.clicked.connect(self.ver_asiento_contable)
        self.view.btn_imprimir.clicked.connect(self.imprimir_factura_seleccionada)
        self.view.tabla.doubleClicked.connect(self.mostrar_detalle_factura)

        # conectar botones de paginacion
        self.view.btn_pag_prev.clicked.connect(self.pagina_anterior)
        self.view.btn_pag_next.clicked.connect(self.pagina_siguiente)
        for idx, btn in enumerate(self.view.pag_buttons):
            # conectar cada boton numerico a su pagina correspondiente
            if btn.text() == "10":
                btn.clicked.connect(lambda checked, p=10: self.cambiar_pagina(p))
            else:
                btn.clicked.connect(lambda checked, p=int(btn.text()): self.cambiar_pagina(p))

        # cargar e inicializar datos
        self.inicializar_filtros_fecha()
        self.actualizar_modulo()

    def inicializar_filtros_fecha(self):
        try:
            # obtener todas las facturas y listar meses/anos unicos
            facturas = self.model.obtener_todas()
            fechas_unicas = set()
            for f in facturas:
                try:
                    # formato yyyy-mm-dd
                    f_date = f["fecha"].split("-")
                    anio = f_date[0]
                    mes = f_date[1]
                    nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    nombre_mes = nombres_meses[int(mes) - 1]
                    fechas_unicas.add(f"{nombre_mes} {anio}")
                except Exception:
                    pass

            self.view.combo_fecha.clear()
            self.view.combo_fecha.addItem("Ver todas")
            for f_str in sorted(list(fechas_unicas), reverse=True):
                self.view.combo_fecha.addItem(f_str)
                
            # por defecto seleccionar "ver todas" para mostrar todo el historial
            self.view.combo_fecha.setCurrentIndex(0)
        except Exception as e:
            print(f"[DEBUG ERROR] Error al poblar fechas únicas: {e}")

    def actualizar_modulo(self):
        try:
            self.facturas_completas = self.model.obtener_todas()
            self.filtrar_datos()
        except Exception as e:
            print(f"[DEBUG ERROR] Falló al cargar facturas en Historial: {e}")

    def filtrar_datos(self):
        if not hasattr(self, 'facturas_completas'):
            return
            
        texto_busqueda = self.view.input_buscar.text().strip().lower()
        estado_filtro = self.view.combo_estado.currentText()
        fecha_filtro = self.view.combo_fecha.currentText()

        # filtrado logico
        self.facturas_filtradas = []
        for f in self.facturas_completas:
            # 1. filtro de texto (numero de factura o nombre de cliente)
            match_texto = (not texto_busqueda or 
                           texto_busqueda in f["num_factura"].lower() or 
                           texto_busqueda in f["cliente_nombre"].lower())

            # 2. filtro de estado
            match_estado = (estado_filtro == "Ver todas" or f["estado"] == estado_filtro)

            # 3. filtro de fecha
            match_fecha = True
            if fecha_filtro != "Ver todas" and fecha_filtro != "":
                # convertir "mayo 2026" a mes5 anio2026
                partes = fecha_filtro.split()
                nomb_mes = partes[0]
                anio = partes[1]
                nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                mes_num = nombres_meses.index(nomb_mes) + 1
                
                f_date = f["fecha"].split("-")
                f_anio = int(f_date[0])
                f_mes = int(f_date[1])
                match_fecha = (f_mes == mes_num and f_anio == int(anio))

            if match_texto and match_estado and match_fecha:
                self.facturas_filtradas.append(f)

            # titulo dinamico con filtro
            if fecha_filtro != "Ver todas":
                self.view.lbl_titulo.setText(f"Historial de facturas emitidas (Filtro: {fecha_filtro.lower()})")
            else:
                self.view.lbl_titulo.setText("Historial de facturas emitidas")

        # recalcular estadisticas del periodo filtrado
        total_periodo = len(self.facturas_filtradas)
        pagadas = sum(1 for f in self.facturas_filtradas if f["estado"] == "Pagada")
        pendientes = sum(1 for f in self.facturas_filtradas if f["estado"] == "Pendiente")
        self.view.actualizar_resumen(total_periodo, pagadas, pendientes)

        # resetear paginacion y recargar tabla
        self.pagina_actual = 1
        self.cargar_tabla_paginada()

    def cargar_tabla_paginada(self):
        # calcular limites de la pagina actual
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        items_pagina = self.facturas_filtradas[inicio:fin]
        
        self.view.cargar_tabla(items_pagina)
        self.actualizar_controles_paginacion()

    def actualizar_controles_paginacion(self):
        total_items = len(self.facturas_filtradas)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        
        # deshabilitar botones de navegacion si corresponde
        self.view.btn_pag_prev.setEnabled(self.pagina_actual > 1)
        self.view.btn_pag_next.setEnabled(self.pagina_actual < total_paginas)

        # actualizar visualizacion de botones de paginas
        # si hay pocas paginas ocultar los dots y la ultima pagina estatica o mapearlos dinamicamente.
        # para simplificar y seguir el mockup si estamos en la pagina x resaltamos ese boton.
        for idx, btn in enumerate(self.view.pag_buttons[:-1]): # del 1 al 4
            num = idx + 1
            btn.setVisible(num <= total_paginas)
            if num == self.pagina_actual:
                btn.setStyleSheet("background-color: #1B2A4A; color: white; border-radius: 4px; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px;")

        # boton 10 (ultimo de la lista)
        btn_last = self.view.pag_buttons[-1]
        btn_last.setText(str(total_paginas))
        btn_last.setVisible(total_paginas > 4)
        self.view.lbl_pag_dots.setVisible(total_paginas > 4)
        
        if self.pagina_actual == total_paginas and total_paginas > 4:
            btn_last.setStyleSheet("background-color: #1B2A4A; color: white; border-radius: 4px; font-weight: bold;")
        else:
            btn_last.setStyleSheet("background-color: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px;")

    def cambiar_pagina(self, pagina):
        total_items = len(self.facturas_filtradas)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if 1 <= pagina <= total_paginas:
            self.pagina_actual = pagina
            self.cargar_tabla_paginada()

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.cargar_tabla_paginada()

    def pagina_siguiente(self):
        total_items = len(self.facturas_filtradas)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self.cargar_tabla_paginada()

    def cambiar_estado_factura(self):
        seleccion = self.view.obtener_factura_seleccionada()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione una factura de la tabla para cambiar su estado.")
            return

        num_factura, estado_actual = seleccion

        # bloquear modificacion de facturas ya anuladas (irreversible)
        if estado_actual == "Anulada":
            self.mostrar_alerta("Operación no permitida", "Las facturas anuladas no pueden ser modificadas.\nLa anulación es un estado permanente e irreversible.")
            return

        dialogo = CambiarEstadoFacturaDialog(num_factura, estado_actual, self.view)
        
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevo_estado, notas = dialogo.obtener_valores()
            if nuevo_estado == estado_actual:
                return

            # validar permisos: solo administrador y operador pueden anular
            from controladores.SecurityService import SecurityService
            usr_obj = SecurityService.get_usuario_actual()
            usr_name = usr_obj.get("username", "admin") if usr_obj else "admin"

            if nuevo_estado == "Anulada":
                usr_rol = usr_obj.get("rol", "") if usr_obj else ""
                if usr_rol == "Usuario":
                    self.mostrar_alerta("Permiso denegado", "No tiene permisos para anular facturas.\nContacte a un administrador.")
                    return

                # confirmacion especial para anulaciones
                box_confirmar = QMessageBox(self.view)
                box_confirmar.setIcon(QMessageBox.Icon.Warning)
                box_confirmar.setWindowTitle("Confirmar Anulación")
                box_confirmar.setText(
                    f"⚠ ATENCIÓN: La anulación de la factura {num_factura} es IRREVERSIBLE.\n\n"
                    f"Se revertirá el stock y se generará un asiento de extorno contable.\n\n"
                    f"¿Está seguro de continuar?"
                )
                box_confirmar.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                box_confirmar.setDefaultButton(QMessageBox.StandardButton.No)
                self.estilo_alerta(box_confirmar)
                if box_confirmar.exec() != QMessageBox.StandardButton.Yes:
                    return

            # ejecutar modificacion en la base de datos
            exito, msg = self.model.modificar_estado_factura(num_factura, nuevo_estado, notas, usuario=usr_name)

            if exito:
                self.mostrar_info("Estado Actualizado", f"La factura {num_factura} ahora está {nuevo_estado}.")
                self.actualizar_modulo()
            else:
                self.mostrar_alerta("Error al Modificar", msg)

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
        msg.exec()

    def ver_asiento_contable(self):
        """busca el asiento contable de la factura seleccionada y abre el dialogo correspondiente."""
        seleccion = self.view.obtener_factura_seleccionada()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione una factura de la tabla para ver su asiento contable.")
            return

        num_factura, _ = seleccion
        
        try:
            # consultar base de datos para obtener los asientos asociados a la factura
            from modelos.asiento_model import AsientoModel
            asiento_model = AsientoModel()
            asientos = asiento_model.obtener_asiento_por_factura(num_factura)
            
            # abrir el dialogo visual
            from vistas.AsientoContableDialog import AsientoContableDialog
            dialogo = AsientoContableDialog(num_factura, asientos, self.view)
            dialogo.exec()
            
        except Exception as e:
            self.mostrar_alerta("Error al cargar asiento", f"No se pudo cargar el asiento contable: {e}")

    def imprimir_factura_seleccionada(self):
        seleccion = self.view.obtener_factura_seleccionada()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione una factura de la tabla para imprimir.")
            return

        num_factura, _ = seleccion
        try:
            factura_completa = self.model.obtener_factura_por_numero(num_factura)
            if not factura_completa:
                self.mostrar_alerta("Error", "No se encontraron los datos de la factura.")
                return
            self._imprimir_directo(factura_completa)
        except Exception as e:
            self.mostrar_alerta("Error al Imprimir", f"Ocurrió un error al imprimir la factura:\n{e}")

    def mostrar_detalle_factura(self):
        seleccion = self.view.obtener_factura_seleccionada()
        if not seleccion:
            return

        num_factura, _ = seleccion
        try:
            factura_completa = self.model.obtener_factura_por_numero(num_factura)
            if not factura_completa:
                return

            from modelos.asiento_model import AsientoModel
            asiento_model = AsientoModel()
            asientos = asiento_model.obtener_asiento_por_factura(num_factura)

            dialogo = DetalleFacturaDialog(factura_completa, asientos, self.view)
            dialogo.btn_imprimir.clicked.connect(lambda: self._imprimir_directo(factura_completa))
            dialogo.exec()
        except Exception as e:
            self.mostrar_alerta("Error", f"No se pudo cargar el detalle:\n{e}")

    def _imprimir_directo(self, factura_completa):
        try:
            try:
                conn = self.model._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT valor FROM MAE_CONFIGURACION WHERE clave = 'formato_impresion_defecto'")
                row_f = cursor.fetchone()
                conn.close()
                formato_def = row_f["valor"] if row_f else "A4"
            except Exception:
                formato_def = "A4"

            formato_imp = "Ticket" if "Ticket" in formato_def else "A4"

            from controladores import ImpresionHelper
            ImpresionHelper.imprimir_factura_html(factura_completa, formato_impresion=formato_imp, parent_widget=self.view)
        except Exception as e:
            self.mostrar_alerta("Error al Imprimir", f"Ocurrió un error al imprimir:\n{e}")
