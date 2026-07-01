from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDate

from vistas.FacturaView import BusquedaPopup


class FacturaController:
    """
    orquesta la logica de negocio de la pantalla nueva factura.
    sincronizado milimetricamente con el modelo transaccional trs_ y mae_.
    """

    def __init__(self, model, view, cliente_model, producto_model):
        self.model          = model
        self.view           = view
        self.cliente_model  = cliente_model
        self.producto_model = producto_model

        # estado interno de la sesion de venta
        self._cliente_actual  = None   # dict con datos del cliente seleccionado
        self._producto_actual = None   # dict con datos del producto seleccionado
        self._items           = []     # lista de dicts: cada item agregado a la factura
        self._totales         = (0.0, 0.0, 0.0, 0.0)

        # inicializar tasa y moneda base activa
        try:
            self._tasa_igv_activa = self.model.obtener_tasa_igv_activa()
            self._moneda_activa = self.model.obtener_moneda_base_activa()
        except Exception:
            self._tasa_igv_activa = 18.00
            self._moneda_activa = {"simbolo": "S/", "codigo_iso": "PEN"}

        # numero de factura automatizado
        self._actualizar_numero_factura()

        # conectar senales de la vista a los metodos del controlador
        self.view.btn_buscar_cliente.clicked.connect(self._abrir_busqueda_cliente)
        self.view.btn_buscar_prod.clicked.connect(self._abrir_busqueda_producto)
        self.view.btn_agregar_item.clicked.connect(self._agregar_item)
        self.view.btn_generar_final.clicked.connect(self._emitir_factura)
        self.view.btn_cancelar.clicked.connect(self._cancelar)

        # conectar eventos de combo de tipo comprobante y moneda
        self.view.combo_tipo_comprobante.currentTextChanged.connect(self._actualizar_numero_factura)
        self.view.combo_moneda.currentTextChanged.connect(self._on_moneda_changed)

        # recalcular totales si se elimina una fila desde el boton  de la tabla grafico
        self.view.fila_eliminada_index.connect(self._eliminar_item_carrito)

    #
    # gestion de numeracion de comprobantes
    #
    def _actualizar_numero_factura(self):
        """genera el siguiente numero de factura consultando el historico del modelo."""
        try:
            tipo_doc = self.view.combo_tipo_comprobante.currentText()
            siguiente = self.model.obtener_siguiente_correlativo(tipo_doc)
        except Exception:
            siguiente = 1
        serie = "F001" if "Factura" in tipo_doc else "B001"
        codigo = f"{serie}-{siguiente:05d}"
        self.view.lbl_num_factura.setText(codigo)
        self._num_factura = codigo

        # Si ya hay un cliente seleccionado y se cambia a Factura, validar consistencia
        if hasattr(self, '_cliente_actual') and self._cliente_actual:
            doc_cliente = self._cliente_actual.get("dni_ruc", "")
            if tipo_doc == "Factura Electrónica" and len(doc_cliente) != 11:
                self._cliente_actual = None
                self.view.set_cliente({})
                self._msg_warn("El cliente seleccionado tiene DNI y no es válido para Factura Electrónica. Se ha deseleccionado.")

    def _on_moneda_changed(self):
        txt = self.view.combo_moneda.currentText()
        simbolo = "S/" if "PEN" in txt else "$"
        self.view.set_simbolo_moneda(simbolo)
        if self._producto_actual:
            self.view.set_producto(self._producto_actual)
        self._recalcular_totales()
        self._actualizar_tabla_items()

    def _actualizar_tabla_items(self):
        self.view.tabla_detalle.setRowCount(0)
        for it in self._items:
            self.view.agregar_fila_tabla(
                it["codigo"], it["nombre"],
                it["cantidad"], it["precio_unitario"],
                it["descuento_pct"], it["subtotal"]
            )

    #
    # busqueda interactiva de clientes (mae_cliente)
    #
    def _abrir_busqueda_cliente(self):
        tipo_comprobante = self.view.combo_tipo_comprobante.currentText()
        popup = BusquedaPopup(
            "Seleccionar cliente",
            ["DNI/RUC", "Nombre / Razón Social", "Teléfono", "Email"],
            self.view
        )
        clientes = self.cliente_model.obtener_todos()
        # filtrado estricto por regulacion: solo clientes en estado activo
        activos = [c for c in clientes if c.get("estado", "Activo") == "Activo"]
        
        # Filtrar segun tipo de comprobante seleccionado
        if tipo_comprobante == "Factura Electrónica":
            # Para Facturas, solo clientes con RUC (11 digitos)
            activos = [c for c in activos if c.get("tipo_documento") == "RUC" or len(c["dni_ruc"]) == 11]

        filas = [
            {
                "dni_ruc":            c["dni_ruc"],
                "nombre_razon_social": c["nombre_razon_social"],
                "telefono":           c.get("telefono", ""),
                "email":              c.get("email", ""),
            }
            for c in activos
        ]
        popup.cargar_datos(filas)
        popup.item_seleccionado.connect(self._on_cliente_seleccionado)
        popup.exec()

    def _on_cliente_seleccionado(self, datos: dict):
        # recuperar el diccionario estructurado completo desde el modelo
        clientes = self.cliente_model.obtener_todos()
        for c in clientes:
            if c["dni_ruc"] == datos["dni_ruc"]:
                self._cliente_actual = c
                self.view.set_cliente(c)
                break

    #
    # busqueda interactiva de productos (mae_producto)
    #
    def _abrir_busqueda_producto(self):
        popup = BusquedaPopup(
            "Seleccionar producto / servicio",
            ["Código", "Nombre", "Stock", "Precio unit."],
            self.view
        )
        productos = self.producto_model.obtener_todos()
        # solo mostrar productos con stock disponible y activos en el catalogo
        filas = [
            {
                "codigo":         p["codigo"],
                "nombre":         p["nombre"],
                "stock":          p.get("stock", 0),
                "precio_unitario": f"S/ {float(p['precio_unitario']):.2f}",
            }
            for p in productos
            if p.get("stock", 0) > 0 and p.get("estado", "Activo") == "Activo"
        ]
        popup.cargar_datos(filas)
        popup.item_seleccionado.connect(self._on_producto_seleccionado)
        popup.exec()

    def _on_producto_seleccionado(self, datos: dict):
        # recuperar el objeto relacional completo (incluye afectacion tributaria e impuestos extras)
        productos = self.producto_model.obtener_todos()
        for p in productos:
            if p["codigo"] == datos["codigo"]:
                self._producto_actual = p
                self.view.set_producto(p)
                break

    #
    # operacion: adicion de items al detalle comercial
    #
    def _agregar_item(self):
        if not self._cliente_actual:
            self._msg_warn("Selecciona un cliente antes de agregar productos.")
            return

        if not self._producto_actual:
            self._msg_warn("Selecciona un producto antes de agregar.")
            return

        # leer y validar campo cantidad
        try:
            cantidad = int(self.view.input_prod_cantidad.text().strip() or "1")
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            self._msg_warn("La cantidad debe ser un número entero positivo.")
            return

        # leer y validar tasa de descuento comercial
        try:
            descuento_pct = float(self.view.input_prod_descuento.text().strip() or "0")
            if not (0 <= descuento_pct < 100):
                raise ValueError
        except ValueError:
            self._msg_warn("El descuento debe ser un porcentaje entre 0 y 99.99.")
            return

        prod = self._producto_actual
        stock_disponible = prod.get("stock", 0)

        # controlar quiebre de stock sumando lo ya consolidado en memoria
        ya_en_tabla = sum(
            it["cantidad"]
            for it in self._items
            if it["codigo"] == prod["codigo"]
        )
        if cantidad + ya_en_tabla > stock_disponible:
            self._msg_warn(
                f"Stock insuficiente.\n"
                f"Disponible: {stock_disponible}  |  Ya en factura: {ya_en_tabla}  |  Pedido: {cantidad}"
            )
            return

        # calculo logistico y tributario dinamico por item (sunat)
        precio_uni = float(prod["precio_unitario"])
        if precio_uni <= 0:
            self._msg_warn("El precio del producto debe ser mayor a cero.")
            return
        descuento_monto = precio_uni * cantidad * (descuento_pct / 100)
        subtotal_neto = precio_uni * cantidad - descuento_monto

        # 1. determinar tasa de igv activa (0.00 si el producto esta exonerado/inafecto)
        es_exonerado = (float(prod.get("impuesto_porcentaje", 18.00)) == 0.0)
        tasa_igv = 0.00 if es_exonerado else self._tasa_igv_activa

        # 2. calcular impuesto selectivo al consumo (isc) monto fijo
        isc_fijo_unit = float(prod.get("isc_monto_fijo", 0.00))
        volumen_litros = float(prod.get("volumen_litros", 0.000))
        
        if isc_fijo_unit > 0:
            if volumen_litros > 0:
                total_volumen_litros = cantidad * volumen_litros
                # conversion oficial sunat: 1 galon  3.785411784 litros
                total_galones = total_volumen_litros / 3.785411784
                isc_monto_fijo_total = total_galones * isc_fijo_unit
            else:
                isc_monto_fijo_total = cantidad * isc_fijo_unit
        else:
            isc_monto_fijo_total = 0.0

        # 3. calcular isc ad valorem ()
        tasa_ad_valorem = float(prod.get("impuesto_extra", 0.00))
        isc_ad_valorem_total = subtotal_neto * (tasa_ad_valorem / 100.0)

        # isc total de la linea
        isc_total = isc_monto_fijo_total + isc_ad_valorem_total

        # 4. base imponible para el igv (en peru el isc forma parte de la base imponible del igv)
        base_imponible_igv = subtotal_neto + isc_total
        igv_total = base_imponible_igv * (tasa_igv / 100.0)

        # el impuesto total de la linea es la suma de igv e isc
        monto_impuesto_linea = igv_total + isc_total

        item = {
            "codigo":                prod["codigo"],
            "nombre":                prod["nombre"],
            "cantidad":              cantidad,
            "precio_unitario":       precio_uni,
            "descuento_pct":         descuento_pct,
            "descuento_monto":       descuento_monto,
            "subtotal":              subtotal_neto,
            "tasa_impuesto":         tasa_igv,
            "monto_impuesto_linea":  monto_impuesto_linea,
            "isc_total":             isc_total,
            "igv_total":             igv_total
        }
        self._items.append(item)

        # pintar fila en la vista grafica
        self.view.agregar_fila_tabla(
            prod["codigo"], prod["nombre"],
            cantidad, precio_uni, descuento_pct, subtotal_neto
        )
        self._recalcular_totales()

    #
    # sincronizacion reactiva por remocion de filas
    #
    def _eliminar_item_carrito(self, index):
        """
        elimina el producto del carrito en memoria basandose en su indice
        y recalcula los totales de la factura.
        """
        if 0 <= index < len(self._items):
            self._items.pop(index)
        self._recalcular_totales()

    #
    # consolidacion contable de totales
    #
    def _recalcular_totales(self):
        """suma las lineas calculando la base imponible y acumula los impuestos especificos."""
        subtotal_bruto  = sum(it["precio_unitario"] * it["cantidad"] for it in self._items)
        total_descuento = sum(it["descuento_monto"] for it in self._items)
        
        # acumulacion limpia de impuestos individuales de cada producto
        total_impuestos = sum(it["monto_impuesto_linea"] for it in self._items)
        
        base_imponible  = subtotal_bruto - total_descuento
        total_final     = base_imponible + total_impuestos

        self.view.actualizar_totales(subtotal_bruto, total_descuento, total_impuestos, total_final)
        self._totales = (subtotal_bruto, total_descuento, total_impuestos, total_final)

    #
    # persistencia transaccional de venta (trs_)
    #
    def _emitir_factura(self):
        if not self._cliente_actual:
            self._msg_warn("Debes seleccionar un cliente antes de emitir la factura.")
            return

        if not self._items:
            self._msg_warn("Agrega al menos un producto a la factura.")
            return

        tipo_doc = self.view.combo_tipo_comprobante.currentText()
        forma_pago = self.view.combo_forma_pago.currentText()
        metodo_pago = self.view.combo_metodo_pago.currentText()
        moneda_texto = self.view.combo_moneda.currentText()
        moneda_iso = moneda_texto.split()[0]

        # validacion sunat de consistencia tributaria
        doc_cliente = self._cliente_actual["dni_ruc"]
        if tipo_doc == "Factura Electrónica":
            if len(doc_cliente) != 11:
                self._msg_warn("Regla Tributaria SUNAT: Las Facturas Electrónicas solo pueden emitirse a clientes con RUC (11 dígitos).")
                return
        elif tipo_doc == "Boleta de Venta":
            if len(doc_cliente) not in (8, 11):
                self._msg_warn("Regla Tributaria SUNAT: Las Boletas de Venta requieren DNI (8 dígitos) o RUC (11 dígitos).")
                return

        # ventana modal de confirmacion con estilos correctos
        box_confirmar = QMessageBox(self.view)
        box_confirmar.setIcon(QMessageBox.Icon.Question)
        box_confirmar.setWindowTitle("Confirmar emisión")
        box_confirmar.setText(f"¿Desea emitir la {tipo_doc} {self._num_factura} para\n"
                              f"{self._cliente_actual['nombre_razon_social']}?\n\n"
                              f"Importe Total: {self.view.simbolo_moneda} {self._totales[3]:.2f}")
        box_confirmar.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box_confirmar.setDefaultButton(QMessageBox.StandardButton.No)
        self._estilo_alerta(box_confirmar)
        
        if box_confirmar.exec() != QMessageBox.StandardButton.Yes:
            return

        subtotal_bruto, total_desc, impuestos, total = self._totales
        cliente_id = self._cliente_actual["dni_ruc"]
        base_netilla = subtotal_bruto - total_desc

        # paquete ordenado para la transaccion atomica del modelo:
        # (codigo cantidad precio_unitario descuento_monto tasa_impuesto monto_impuesto_linea)
        items_modelo = [
            (
                it["codigo"], 
                it["cantidad"], 
                it["precio_unitario"], 
                it["descuento_monto"], 
                it["tasa_impuesto"], 
                it["monto_impuesto_linea"]
            )
            for it in self._items
        ]

        # generar cuotas para ventas al credito
        cuotas = []
        if forma_pago == "Crédito":
            from PyQt6.QtCore import QDate
            vencimiento = QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            cuotas.append({
                "numero": 1,
                "monto": total,
                "vencimiento": vencimiento
            })

        # obtener usuario actual de la sesion
        from controladores.SecurityService import SecurityService
        usr_obj = SecurityService.get_usuario_actual()
        usr_name = usr_obj.get("username", "admin") if usr_obj else "admin"

        # envio seguro al modelo inmune a sql injection
        exito, resultado = self.model.registrar_factura(
            cliente_id, base_netilla, impuestos, total, items_modelo,
            tipo_documento=tipo_doc, forma_pago=forma_pago, metodo_pago=metodo_pago,
            usuario=usr_name, cuotas=cuotas, moneda_iso=moneda_iso,
            monto_descuento=total_desc
        )

        if exito:
            # 1. generar datos de factura para impresion y xml
            factura_completa = self.model.obtener_factura_por_numero(resultado)
            
            # 2. generar xml ubl 2.1 estandar de sunat
            from controladores import ImpresionHelper
            try:
                xml_path = ImpresionHelper.generar_xml_ubl_sunat(factura_completa)
                print(f"[DEBUG] XML UBL 2.1 generado correctamente: {xml_path}")
            except Exception as e:
                print(f"[DEBUG ERROR] No se pudo generar el XML UBL 2.1: {e}")
                self._msg_warn(f"Advertencia: No se pudo generar el archivo XML SUNAT: {e}")

            # 3. preguntar si desea imprimir comprobante
            box_imprimir = QMessageBox(self.view)
            box_imprimir.setIcon(QMessageBox.Icon.Question)
            box_imprimir.setWindowTitle("Comprobante emitido")
            box_imprimir.setText(f"✔ Comprobante {resultado} emitido correctamente.\n"
                                 f"¿Desea imprimir el comprobante en este momento?")
            box_imprimir.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            box_imprimir.setDefaultButton(QMessageBox.StandardButton.Yes)
            self._estilo_alerta(box_imprimir)
            
            if box_imprimir.exec() == QMessageBox.StandardButton.Yes:
                try:
                    formato_def = self.model.obtener_formato_impresion()
                except Exception:
                    formato_def = "A4"
                
                formato_imp = "Ticket" if "Ticket" in formato_def else "A4"
                ImpresionHelper.imprimir_factura_html(factura_completa, formato_impresion=formato_imp, parent_widget=self.view)

            self._reset()
        else:
            box = QMessageBox(self.view)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle("Error al facturar")
            box.setText(f"El motor relacional rechazó la operación:\n{resultado}")
            self._estilo_alerta(box)
            box.exec()

    #
    # gestion de cancelaciones de estado
    #
    def _cancelar(self):
        if self._items:
            box_cancel = QMessageBox(self.view)
            box_cancel.setIcon(QMessageBox.Icon.Question)
            box_cancel.setWindowTitle("Cancelar factura")
            box_cancel.setText("¿Deseas cancelar la factura en curso?\nSe perderán todos los ítems agregados.")
            box_cancel.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            box_cancel.setDefaultButton(QMessageBox.StandardButton.No)
            self._estilo_alerta(box_cancel)
            
            if box_cancel.exec() != QMessageBox.StandardButton.Yes:
                return
        self._reset()

    def _reset(self):
        self._cliente_actual  = None
        self._producto_actual = None
        self._items           = []
        self._totales         = (0, 0, 0, 0)
        self.view.limpiar_formulario()
        self._actualizar_numero_factura()

    #
    # utilidades y control de hojas de estilo (qss)
    #
    def _estilo_alerta(self, msg_box):
        """fuerza un diseno corporativo para evitar bugs de textos e iconos en blanco."""
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)

    def _msg_warn(self, texto: str):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Aviso de Validación")
        msg.setText(texto)
        self._estilo_alerta(msg)
        msg.exec()

    def actualizar_modulo(self):
        """metodo publico para refrescar la numeracion de facturas al ingresar al modulo."""
        self._actualizar_numero_factura()
        try:
            # obtener igv e moneda activa de la empresa
            self._tasa_igv_activa = self.model.obtener_tasa_igv_activa()
            self._moneda_activa = self.model.obtener_moneda_base_activa()
            simbolo = self._moneda_activa.get("simbolo", "S/")
            
            # actualizar simbolo y etiqueta en la vista
            self.view.set_simbolo_moneda(simbolo)
            self.view.lbl_igv.setText(f"IGV ({self._tasa_igv_activa:.0f}%):")
            
            # recalcular totales si hay items activos
            self._recalcular_totales()
        except Exception as e:
            print(f"[DEBUG ERROR] Falló al obtener la tasa de IGV activa en FacturaController: {e}")
            self._tasa_igv_activa = 18.00
            self.view.lbl_igv.setText("IGV (18%):")