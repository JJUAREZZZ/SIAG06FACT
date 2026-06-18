from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDate

from vistas.FacturaView import BusquedaPopup


class FacturaController:
    """
    Orquesta la lógica de negocio de la pantalla Nueva Factura.
    Sincronizado milimétricamente con el modelo transaccional TRS_ y MAE_.
    """

    def __init__(self, model, view, cliente_model, producto_model):
        self.model          = model
        self.view           = view
        self.cliente_model  = cliente_model
        self.producto_model = producto_model

        # estado interno de la sesión de venta
        self._cliente_actual  = None   # dict con datos del cliente seleccionado
        self._producto_actual = None   # dict con datos del producto seleccionado
        self._items           = []     # lista de dicts: cada ítem agregado a la factura

        # inicializar tasa y moneda base activa
        try:
            self._tasa_igv_activa = self.model.obtener_tasa_igv_activa()
            self._moneda_activa = self.model.obtener_moneda_base_activa()
        except Exception:
            self._tasa_igv_activa = 18.00
            self._moneda_activa = {"simbolo": "S/", "codigo_iso": "PEN"}

        # número de factura automatizado
        self._actualizar_numero_factura()

        # conectar señales de la vista a los métodos del controlador
        self.view.btn_buscar_cliente.clicked.connect(self._abrir_busqueda_cliente)
        self.view.btn_buscar_prod.clicked.connect(self._abrir_busqueda_producto)
        self.view.btn_agregar_item.clicked.connect(self._agregar_item)
        self.view.btn_generar_final.clicked.connect(self._emitir_factura)
        self.view.btn_cancelar.clicked.connect(self._cancelar)

        # recalcular totales si se elimina una fila desde el botón ✕ de la tabla gráfico
        self.view.fila_eliminada_index.connect(self._eliminar_item_carrito)

    #
    # gestión de numeración de comprobantes
    #
    def _actualizar_numero_factura(self):
        """Genera el siguiente número de factura consultando el histórico del modelo."""
        try:
            siguiente = self.model.obtener_siguiente_correlativo()
        except Exception:
            siguiente = 1
        codigo = f"F001-{siguiente:05d}"
        self.view.lbl_num_factura.setText(codigo)
        self._num_factura = codigo

    #
    # búsqueda interactiva de clientes (mae_cliente)
    #
    def _abrir_busqueda_cliente(self):
        popup = BusquedaPopup(
            "Seleccionar cliente",
            ["DNI/RUC", "Nombre / Razón Social", "Teléfono", "Email"],
            self.view
        )
        clientes = self.cliente_model.obtener_todos()
        # filtrado estricto por regulación: solo clientes en estado activo
        activos = [c for c in clientes if c.get("estado", "Activo") == "Activo"]
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
    # búsqueda interactiva de productos (mae_producto)
    #
    def _abrir_busqueda_producto(self):
        popup = BusquedaPopup(
            "Seleccionar producto / servicio",
            ["Código", "Nombre", "Stock", "Precio unit."],
            self.view
        )
        productos = self.producto_model.obtener_todos()
        # solo mostrar productos con stock disponible y activos en el catálogo
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
        # recuperar el objeto relacional completo (incluye afectación tributaria e impuestos extras)
        productos = self.producto_model.obtener_todos()
        for p in productos:
            if p["codigo"] == datos["codigo"]:
                self._producto_actual = p
                self.view.set_producto(p)
                break

    #
    # operación: adición de ítems al detalle comercial
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

        # cálculo logístico y tributario dinámico por ítem (sunat)
        precio_uni = float(prod["precio_unitario"])
        descuento_monto = precio_uni * cantidad * (descuento_pct / 100)
        subtotal_neto = precio_uni * cantidad - descuento_monto

        # 1. determinar tasa de igv activa (0.00 si el producto está exonerado/inafecto)
        es_exonerado = (float(prod.get("impuesto_porcentaje", 18.00)) == 0.0)
        tasa_igv = 0.00 if es_exonerado else self._tasa_igv_activa

        # 2. calcular impuesto selectivo al consumo (isc) monto fijo
        isc_fijo_unit = float(prod.get("isc_monto_fijo", 0.00))
        volumen_litros = float(prod.get("volumen_litros", 0.000))
        
        if isc_fijo_unit > 0:
            if volumen_litros > 0:
                total_volumen_litros = cantidad * volumen_litros
                # conversión oficial sunat: 1 galón = 3.785411784 litros
                total_galones = total_volumen_litros / 3.785411784
                isc_monto_fijo_total = total_galones * isc_fijo_unit
            else:
                isc_monto_fijo_total = cantidad * isc_fijo_unit
        else:
            isc_monto_fijo_total = 0.0

        # 3. calcular isc ad valorem (%)
        tasa_ad_valorem = float(prod.get("impuesto_extra", 0.00))
        isc_ad_valorem_total = subtotal_neto * (tasa_ad_valorem / 100.0)

        # isc total de la línea
        isc_total = isc_monto_fijo_total + isc_ad_valorem_total

        # 4. base imponible para el igv (en perú, el isc forma parte de la base imponible del igv)
        base_imponible_igv = subtotal_neto + isc_total
        igv_total = base_imponible_igv * (tasa_igv / 100.0)

        # el impuesto total de la línea es la suma de igv e isc
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

        # pintar fila en la vista gráfica
        self.view.agregar_fila_tabla(
            prod["codigo"], prod["nombre"],
            cantidad, precio_uni, descuento_pct, subtotal_neto
        )
        self._recalcular_totales()

    #
    # sincronización reactiva por remoción de filas
    #
    def _eliminar_item_carrito(self, index):
        """
        Elimina el producto del carrito en memoria basándose en su índice
        y recalcula los totales de la factura.
        """
        if 0 <= index < len(self._items):
            self._items.pop(index)
        self._recalcular_totales()

    #
    # consolidación contable de totales
    #
    def _recalcular_totales(self):
        """Suma las líneas calculando la base imponible y acumula los impuestos específicos."""
        subtotal_bruto  = sum(it["precio_unitario"] * it["cantidad"] for it in self._items)
        total_descuento = sum(it["descuento_monto"] for it in self._items)
        
        # acumulación limpia de impuestos individuales de cada producto
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

        # ventana modal de confirmación con estilos correctos
        box_confirmar = QMessageBox(self.view)
        box_confirmar.setIcon(QMessageBox.Icon.Question)
        box_confirmar.setWindowTitle("Confirmar emisión")
        box_confirmar.setText(f"¿Desea emitir la factura {self._num_factura} para\n"
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

        # paquete ordenado para la transacción atómica del modelo:
        # (codigo, cantidad, precio_unitario, descuento_monto, tasa_impuesto, monto_impuesto_linea)
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

        # envío seguro al modelo, inmune a sql injection
        exito, resultado = self.model.registrar_factura(
            cliente_id, base_netilla, impuestos, total, items_modelo
        )

        if exito:
            box = QMessageBox(self.view)
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle("Factura emitida")
            box.setText(f"✔ Comprobante {self._num_factura} emitido correctamente.\nCódigo de auditoría: {resultado}")
            self._estilo_alerta(box)
            box.exec()
            self._reset()
        else:
            box = QMessageBox(self.view)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle("Error al facturar")
            box.setText(f"El motor relacional rechazó la operación:\n{resultado}")
            self._estilo_alerta(box)
            box.exec()

    #
    # gestión de cancelaciones de estado
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
        """Fuerza un diseño corporativo para evitar bugs de textos e iconos en blanco."""
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
        """Método público para refrescar la numeración de facturas al ingresar al módulo."""
        self._actualizar_numero_factura()
        try:
            # obtener igv e moneda activa de la empresa
            self._tasa_igv_activa = self.model.obtener_tasa_igv_activa()
            self._moneda_activa = self.model.obtener_moneda_base_activa()
            simbolo = self._moneda_activa.get("simbolo", "S/")
            
            # actualizar símbolo y etiqueta en la vista
            self.view.set_simbolo_moneda(simbolo)
            self.view.lbl_igv.setText(f"IGV ({self._tasa_igv_activa:.0f}%):")
            
            # recalcular totales si hay items activos
            self._recalcular_totales()
        except Exception as e:
            print(f"[DEBUG ERROR] Falló al obtener la tasa de IGV activa en FacturaController: {e}")
            self._tasa_igv_activa = 18.00
            self.view.lbl_igv.setText("IGV (18%):")