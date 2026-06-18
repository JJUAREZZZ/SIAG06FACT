from vistas.ProductoView import FormularioProductoDialog
from PyQt6.QtWidgets import QMessageBox

class ProductoController:
    """
    Controlador maestro para la gestión del catálogo de productos y servicios.
    Sincroniza de forma segura la vista ProductoView con el modelo relacional MAE_PRODUCTO.
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # parámetros de paginación
        self.items_por_pagina = 10
        self.pagina_actual = 1
        self.productos_filtrados = []

        # suscribir manejadores de eventos (handlers)
        self.view.btn_abrir_formulario.clicked.connect(self.mostrar_formulario_emergente)
        self.view.btn_modificar.clicked.connect(self.modificar_producto)
        self.view.btn_cambiar_estado.clicked.connect(self.alternar_estado_producto)
        
        self.view.input_buscar.textChanged.connect(self.filtrar_datos)
        self.view.combo_categoria.currentTextChanged.connect(self.filtrar_datos)

        # conectar botones de paginación
        self.view.btn_pag_prev.clicked.connect(self.pagina_anterior)
        self.view.btn_pag_next.clicked.connect(self.pagina_siguiente)
        for idx, btn in enumerate(self.view.pag_buttons):
            if btn.text() == "10":
                btn.clicked.connect(lambda checked, p=10: self.cambiar_pagina(p))
            else:
                btn.clicked.connect(lambda checked, p=int(btn.text()): self.cambiar_pagina(p))

        # cargar categorías iniciales e inventario
        self.inicializar_categorias_filtro()
        self.actualizar_modulo()

    def inicializar_categorias_filtro(self):
        try:
            categorias = self.model.obtener_categorias()
            self.view.combo_categoria.clear()
            self.view.combo_categoria.addItem("Ver todas")
            for cat in categorias:
                self.view.combo_categoria.addItem(cat["nombre"])
        except Exception as e:
            print(f"[DEBUG ERROR] Falló al cargar categorías en filtro: {e}")

    def mostrar_formulario_emergente(self):
        """Instancia el asistente de registro modal, poblando sus desplegables desde la BD."""
        dialogo = FormularioProductoDialog(self.view)
        
        try:
            # extraer los datos relacionales de las tablas maestras de soporte de sqlite
            categorias = self.model.obtener_categorias()
            impuestos = self.model.obtener_impuestos()
            
            # poblar dinámicamente los qcombobox del formulario emergente
            dialogo.poblar_selectores(categorias, impuestos)
        except Exception as e:
            self.mostrar_alerta("Error de Carga", f"No se pudieron recuperar las categorías o impuestos base:\n{e}")
            return

        # si el usuario completa los datos y presiona el botón "guardar producto"
        if dialogo.exec() == FormularioProductoDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            
            # validación estricta de seguridad en campos obligatorios antes de insertar
            if not datos["codigo_barra"] or not datos["nombre"]:
                self.mostrar_alerta("Campos Requeridos", "El código de barra y el nombre del producto son obligatorios.")
                return

            if datos["stock"] < 0:
                self.mostrar_alerta("Valor Incorrecto", "El stock inicial no puede ser negativo.")
                return

            if datos["precio_unitario"] <= 0:
                self.mostrar_alerta("Valor Incorrecto", "El precio unitario debe ser mayor a 0.")
                return
                
            try:
                # invocar al método avanzado mapeando el diccionario de forma limpia
                self.model.insertar_producto_avanzado(datos)
                print("[DEBUG] Transacción de inventario completada de forma conforme.")
                self.actualizar_modulo()
            except Exception as e:
                self.mostrar_alerta("Error de Integridad", f"El motor relacional rechazó el registro. Verifique claves duplicadas:\n{e}")

    def modificar_producto(self):
        seleccion = self.view.obtener_producto_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Aviso de Selección", "Por favor, seleccione un producto de la lista para modificarlo.")
            return
            
        codigo, _ = seleccion
        
        # buscar los datos completos del producto en la lista local
        producto_datos = None
        for p in self.productos_completos:
            if p["codigo"] == codigo:
                producto_datos = p
                break
                
        if not producto_datos:
            self.mostrar_alerta("Error", "No se encontraron los datos del producto seleccionado.")
            return

        dialogo = FormularioProductoDialog(self.view)
        
        try:
            categorias = self.model.obtener_categorias()
            impuestos = self.model.obtener_impuestos()
            dialogo.poblar_selectores(categorias, impuestos)
        except Exception as e:
            self.mostrar_alerta("Error de Carga", f"No se pudieron recuperar las categorías o impuestos base:\n{e}")
            return

        # precompletar el formulario
        dialogo.precompletar(producto_datos)
        
        if dialogo.exec() == FormularioProductoDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            
            # validación estricta
            if not datos["nombre"]:
                self.mostrar_alerta("Campos Requeridos", "El nombre del producto es obligatorio.")
                return

            if datos["stock"] < 0:
                self.mostrar_alerta("Valor Incorrecto", "El stock no puede ser negativo.")
                return

            if datos["precio_unitario"] <= 0:
                self.mostrar_alerta("Valor Incorrecto", "El precio unitario debe ser mayor a 0.")
                return
                
            try:
                self.model.actualizar_producto(datos)
                self.mostrar_info("Producto Modificado", "El producto se ha actualizado con éxito.")
                self.actualizar_modulo()
            except Exception as e:
                self.mostrar_alerta("Error de Actualización", f"El motor relacional rechazó la actualización:\n{e}")

    def alternar_estado_producto(self):
        """Detecta el ítem seleccionado de la grilla y conmuta su estado (Activo / Inactivo)."""
        seleccion = self.view.obtener_producto_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Aviso de Selección", "Por favor, seleccione una fila de la tabla para mutar su estado administrativo.")
            return
            
        codigo, estado_actual = seleccion
        nuevo_estado = "Inactivo" if estado_actual != "Inactivo" else "Activo"
        
        try:
            self.model.modificar_estado_producto(codigo, nuevo_estado)
            print(f"[DEBUG] Estado del producto '{codigo}' modificado a [{nuevo_estado}].")
            self.actualizar_modulo()
        except Exception as e:
            self.mostrar_alerta("Error de Actualización", f"Fallo en la ejecución de la consulta de actualización:\n{e}")

    def actualizar_modulo(self):
        """Sincroniza la grilla de visualización y recalcula los KPIs en caliente basándose en la BD."""
        try:
            # sincronizar símbolo de moneda base activa
            simbolo_moneda = self.model.obtener_moneda_base_activa()
            self.view.set_simbolo_moneda(simbolo_moneda)

            self.productos_completos = self.model.obtener_todos()
            self.filtrar_datos()
            
            # kpis en caliente para las tarjetas superiores (basados en productos activos)
            total_stock        = sum(p.get("stock", 0) for p in self.productos_completos if p.get("estado") == "Activo")
            productos_en_stock = sum(1 for p in self.productos_completos if p.get("stock", 0) > 0 and p.get("estado") == "Activo")
            items_bajo_stock   = sum(1 for p in self.productos_completos if 0 < p.get("stock", 0) <= 5 and p.get("estado") == "Activo")
            
            self.view.actualizar_kpis(total_stock, productos_en_stock, items_bajo_stock)
        except Exception as e:
            print(f"[DEBUG ERROR] No se pudo sincronizar de forma correcta el estado del módulo: {e}")

    def filtrar_datos(self):
        if not hasattr(self, 'productos_completos'):
            return
            
        texto = self.view.input_buscar.text().strip().lower()
        categoria = self.view.combo_categoria.currentText()

        self.productos_filtrados = []
        for p in self.productos_completos:
            match_texto = (not texto or 
                           texto in p["codigo"].lower() or 
                           texto in p["nombre"].lower())
            
            match_cat = (categoria == "Ver todas" or p.get("categoria_nombre") == categoria)

            if match_texto and match_cat:
                self.productos_filtrados.append(p)

        # actualizar etiqueta resumen (mockup 3)
        total_stk = sum(p.get("stock", 0) for p in self.productos_filtrados if p.get("estado") == "Activo")
        prods_stk = sum(1 for p in self.productos_filtrados if p.get("stock", 0) > 0 and p.get("estado") == "Activo")
        bajo_stk = sum(1 for p in self.productos_filtrados if 0 < p.get("stock", 0) <= 5 and p.get("estado") == "Activo")
        self.view.lbl_info_productos.setText(f"Total stock: {total_stk}  |  Productos en stock: {prods_stk}  |  Items bajo stock: {bajo_stk}")

        # recargar tabla con paginación
        self.pagina_actual = 1
        self.cargar_tabla_paginada()

    def cargar_tabla_paginada(self):
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        items_pagina = self.productos_filtrados[inicio:fin]
        
        self.view.cargar_tabla(items_pagina)
        self.actualizar_controles_paginacion()

    def actualizar_controles_paginacion(self):
        total_items = len(self.productos_filtrados)
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
        total_items = len(self.productos_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if 1 <= pagina <= total_paginas:
            self.pagina_actual = pagina
            self.cargar_tabla_paginada()

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.cargar_tabla_paginada()

    def pagina_siguiente(self):
        total_items = len(self.productos_filtrados)
        total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self.cargar_tabla_paginada()

    def mostrar_alerta(self, titulo, mensaje):
        """Despliega una notificación modal controlando estrictamente las hojas de estilo (QSS)."""
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; border: none; min-width: 70px; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        msg.exec()

    def mostrar_info(self, titulo, mensaje):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; border: none; min-width: 70px; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        msg.exec()