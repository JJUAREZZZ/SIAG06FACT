import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFrame, QLabel, QDialog, QAbstractItemView, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPixmap

#
# formulario modal de registro con fijacion estetica
#
class FormularioProductoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir nuevo producto")
        self.setFixedSize(460, 500) # ampliado para dar holgura a los nuevos campos de isc
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # estilo forzado corporativo para corregir el bug de letras invisibles
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: bold; }
            QLineEdit { 
                padding: 8px; 
                border: 1px solid #CCD1D9; 
                border-radius: 4px; 
                background: #F4F6F9; 
                color: black; 
                font-size: 13px; 
                min-height: 28px;
            }
            QLineEdit:focus { border: 1.5px solid #1B2A4A; background: white; }
            QComboBox { 
                padding: 7px; 
                border: 1px solid #CCD1D9; 
                border-radius: 4px; 
                background: #F4F6F9; 
                color: black; 
                font-size: 13px; 
                min-height: 28px;
            }
            QComboBox:focus { border: 1.5px solid #1B2A4A; background: white; }
            
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        lbl_title = QLabel("Registrar Producto Comercial")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2A4A; margin-bottom: 5px;")
        layout.addWidget(lbl_title)

        # rejilla simetrica para acomodar los cuadros de entrada uniformemente
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(15)

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Código de barra / único (Obligatorio)")
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del producto (Obligatorio)")

        self.combo_categoria = QComboBox()
        self.combo_impuesto = QComboBox()
        
        # sitema 1: isc ad valorem ()
        self.input_impuesto_extra = QLineEdit("0.00")
        self.input_impuesto_extra.setPlaceholderText("Tasa porcentual (Ej: 40.00)")

        # sistema 2: isc monto fijo por unidad de volumen (s/)
        self.input_isc_monto_fijo = QLineEdit("0.00")
        self.input_isc_monto_fijo.setPlaceholderText("Monto por litro (Ej: 3.40)")

        # metrica obligatoria para el calculo especifico de volumen
        self.input_volumen_litros = QLineEdit("0.000")
        self.input_volumen_litros.setPlaceholderText("Contenido en Litros (Ej: 0.750)")

        self.input_stock = QLineEdit()
        self.input_stock.setPlaceholderText("Cantidad inicial en almacén")

        self.input_precio = QLineEdit()
        self.input_precio.setPlaceholderText("Precio base unitario (Ej: 45.90)")
        
        self.input_descripcion = QLineEdit()
        self.input_descripcion.setPlaceholderText("Detalles o especificaciones adicionales")

        # mapeo posicional limpio dentro de la rejilla
        grid.addWidget(QLabel("Código barra:"), 0, 0)
        grid.addWidget(self.input_codigo, 0, 1)
        
        grid.addWidget(QLabel("Nombre:"), 1, 0)
        grid.addWidget(self.input_nombre, 1, 1)

        grid.addWidget(QLabel("Categoría:"), 2, 0)
        grid.addWidget(self.combo_categoria, 2, 1)

        grid.addWidget(QLabel("Afectación IGV:"), 3, 0)
        grid.addWidget(self.combo_impuesto, 3, 1)

        grid.addWidget(QLabel("ISC Ad Valorem (%):"), 4, 0)
        grid.addWidget(self.input_impuesto_extra, 4, 1)

        grid.addWidget(QLabel("ISC Monto Fijo (S/):"), 5, 0)
        grid.addWidget(self.input_isc_monto_fijo, 5, 1)

        grid.addWidget(QLabel("Volumen (Litros):"), 6, 0)
        grid.addWidget(self.input_volumen_litros, 6, 1)

        grid.addWidget(QLabel("Stock Inicial:"), 7, 0)
        grid.addWidget(self.input_stock, 7, 1)

        grid.addWidget(QLabel("Precio Unitario:"), 8, 0)
        grid.addWidget(self.input_precio, 8, 1)
        
        grid.addWidget(QLabel("Descripción:"), 9, 0)
        grid.addWidget(self.input_descripcion, 9, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        layout.addLayout(grid)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #C00000; color: white; padding: 9px; border-radius: 4px; font-weight: bold; border: none;")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar_form = QPushButton("Guardar Producto")
        self.btn_guardar_form.setStyleSheet("background-color: #70AD47; color: white; padding: 9px; border-radius: 4px; font-weight: bold; border: none;")
        self.btn_guardar_form.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar_form)
        layout.addLayout(btn_layout)

        # conectar senal de categoria para automatizar reglas de afectacion sunat e isc
        self.combo_categoria.currentTextChanged.connect(self._al_cambiar_categoria)

    def _al_cambiar_categoria(self, cat_nombre):
        # 1. bienes exonerados del apendice i (libros y educacion alimentos basicos)
        if cat_nombre in ["Libros y Educación", "Alimentos Básicos"]:
            # preseleccionar afectacion igv: exonerado (id_impuesto  2)
            index_exo = self.combo_impuesto.findData(2)
            if index_exo != -1:
                self.combo_impuesto.setCurrentIndex(index_exo)
            
            # deshabilitar isc ad valorem isc monto fijo y volumen
            self.input_impuesto_extra.setText("0.00")
            self.input_impuesto_extra.setEnabled(False)
            self.input_isc_monto_fijo.setText("0.00")
            self.input_isc_monto_fijo.setEnabled(False)
            self.input_volumen_litros.setText("0.000")
            self.input_volumen_litros.setEnabled(False)
            
        # 2. combustibles y carbones (apendice iii - isc monto fijo  volumen obligatorio)
        elif cat_nombre in ["Combustibles", "Combustibles y Carbones"]:
            # deshabilitar isc ad valorem (ad valorem es para licores/vehiculos no combustibles)
            self.input_impuesto_extra.setText("0.00")
            self.input_impuesto_extra.setEnabled(False)
            
            # habilitar monto fijo y volumen
            self.input_isc_monto_fijo.setEnabled(True)
            self.input_volumen_litros.setEnabled(True)
            
            # seleccionar igv normal por defecto (id_impuesto  1)
            index_igv = self.combo_impuesto.findData(1)
            if index_igv != -1:
                self.combo_impuesto.setCurrentIndex(index_igv)
                
        # 3. licores y especiales (apendice iv - isc ad valorem)
        elif cat_nombre == "Licores y Especiales":
            self.input_impuesto_extra.setEnabled(True)
            self.input_isc_monto_fijo.setText("0.00")
            self.input_isc_monto_fijo.setEnabled(False)
            self.input_volumen_litros.setText("0.000")
            self.input_volumen_litros.setEnabled(False)
            
            # seleccionar igv normal (id_impuesto  1)
            index_igv = self.combo_impuesto.findData(1)
            if index_igv != -1:
                self.combo_impuesto.setCurrentIndex(index_igv)
        
        # 4. otras categorias generales
        else:
            self.input_impuesto_extra.setEnabled(True)
            self.input_isc_monto_fijo.setEnabled(True)
            self.input_volumen_litros.setEnabled(True)

    def precompletar(self, datos):
        self.setWindowTitle("Modificar producto")
        self.input_codigo.setText(datos.get("codigo", ""))
        self.input_codigo.setReadOnly(True)
        self.input_codigo.setStyleSheet("QLineEdit { padding: 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: #E2EAF8; color: #555555; font-size: 13px; min-height: 28px; }")
        
        self.input_nombre.setText(datos.get("nombre", ""))
        self.input_descripcion.setText(datos.get("descripcion", "") or "")
        self.input_stock.setText(str(datos.get("stock", 0)))
        self.input_precio.setText(f"{float(datos.get('precio_unitario', 0.0)):.2f}")
        self.input_impuesto_extra.setText(f"{float(datos.get('impuesto_extra', 0.0)):.2f}")
        self.input_isc_monto_fijo.setText(f"{float(datos.get('isc_monto_fijo', 0.0)):.2f}")
        self.input_volumen_litros.setText(f"{float(datos.get('volumen_litros', 0.000)):.3f}")
        
        # seleccionar categoria
        idx_cat = self.combo_categoria.findData(datos.get("id_categoria_producto"))
        if idx_cat != -1:
            self.combo_categoria.setCurrentIndex(idx_cat)
            
        # seleccionar impuesto
        idx_imp = self.combo_impuesto.findData(datos.get("id_impuesto"))
        if idx_imp != -1:
            self.combo_impuesto.setCurrentIndex(idx_imp)

        # aplicar el habilitado/deshabilitado basandose en la categoria actual pre-poblada
        self._al_cambiar_categoria(self.combo_categoria.currentText())

    def poblar_selectores(self, categorias, impuestos):
        self.combo_categoria.clear()
        for cat in categorias:
            self.combo_categoria.addItem(cat["nombre"], cat["id_categoria_producto"])
            
        self.combo_impuesto.clear()
        for imp in impuestos:
            self.combo_impuesto.addItem(f"{imp['nombre']} ({imp['porcentaje']}%)", imp["id_impuesto"])

    def accept(self):
        from PyQt6.QtWidgets import QMessageBox
        
        # validar codigo y nombre
        if not self.input_codigo.text().strip():
            QMessageBox.warning(self, "Campos Requeridos", "El código de barra es obligatorio.")
            return
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Campos Requeridos", "El nombre del producto es obligatorio.")
            return

        # validar stock inicial
        stock_text = self.input_stock.text().strip()
        if not stock_text:
            QMessageBox.warning(self, "Campos Requeridos", "El stock inicial es obligatorio.")
            return
        try:
            stock_val = int(stock_text)
            if stock_val < 0:
                QMessageBox.warning(self, "Valor Incorrecto", "El stock inicial no puede ser negativo.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valor Incorrecto", "El stock inicial debe ser un número entero válido.")
            return

        # validar precio unitario
        precio_text = self.input_precio.text().strip()
        if not precio_text:
            QMessageBox.warning(self, "Campos Requeridos", "El precio unitario es obligatorio.")
            return
        try:
            precio_val = float(precio_text)
            if precio_val <= 0:
                QMessageBox.warning(self, "Valor Incorrecto", "El precio unitario debe ser mayor a 0.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valor Incorrecto", "El precio unitario debe ser un número decimal válido.")
            return

        # validar impuesto extra (isc porcentual)
        extra_text = self.input_impuesto_extra.text().strip()
        if extra_text:
            try:
                extra_val = float(extra_text)
                if extra_val < 0:
                    QMessageBox.warning(self, "Valor Incorrecto", "El ISC Ad Valorem (%) no puede ser negativo.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Valor Incorrecto", "El ISC Ad Valorem (%) debe ser un número decimal válido.")
                return

        # validar isc monto fijo
        fijo_text = self.input_isc_monto_fijo.text().strip()
        if fijo_text:
            try:
                fijo_val = float(fijo_text)
                if fijo_val < 0:
                    QMessageBox.warning(self, "Valor Incorrecto", "El ISC Monto Fijo no puede ser negativo.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Valor Incorrecto", "El ISC Monto Fijo debe ser un número decimal válido.")
                return

        # validar volumen litros
        volumen_text = self.input_volumen_litros.text().strip()
        if volumen_text:
            try:
                volumen_val = float(volumen_text)
                if volumen_val < 0:
                    QMessageBox.warning(self, "Valor Incorrecto", "El volumen en litros no puede ser negativo.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Valor Incorrecto", "El volumen en litros debe ser un número decimal válido.")
                return

        # validar combustibles y carbones (apendice iii - requiere volumen  0)
        cat_nombre = self.combo_categoria.currentText()
        if cat_nombre in ["Combustibles", "Combustibles y Carbones"]:
            try:
                vol_val = float(volumen_text)
                if vol_val <= 0:
                    QMessageBox.warning(self, "Valor Incorrecto", "Para combustibles, el volumen (Litros) es obligatorio y debe ser mayor a 0.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Valor Incorrecto", "El volumen (Litros) debe ser un número decimal válido y mayor a 0.")
                return

        super().accept()

    def obtener_datos(self):
        stock_text = self.input_stock.text().strip()
        stock = int(stock_text) if stock_text else 0
        
        precio_text = self.input_precio.text().strip()
        precio = float(precio_text) if precio_text else 0.0

        extra_text = self.input_impuesto_extra.text().strip()
        extra = float(extra_text) if extra_text else 0.0

        fijo_text = self.input_isc_monto_fijo.text().strip()
        isc_fijo = float(fijo_text) if fijo_text else 0.0

        volumen_text = self.input_volumen_litros.text().strip()
        volumen = float(volumen_text) if volumen_text else 0.000

        return {
            "codigo_barra":           self.input_codigo.text().strip(),
            "nombre":                 self.input_nombre.text().strip(),
            "id_categoria_producto":  self.combo_categoria.currentData(),
            "id_impuesto":            self.combo_impuesto.currentData(),
            "descripcion":            self.input_descripcion.text().strip(),
            "stock":                  stock,
            "precio_unitario":        precio,
            "impuesto_extra":         extra,
            "isc_monto_fijo":         isc_fijo,
            "volumen_litros":         volumen
        }


#
# interfaz grafica principal del panel de productos
#
class ProductoView(QWidget):
    def __init__(self):
        super().__init__()
        
        falso_layout = QHBoxLayout(self)
        falso_layout.setContentsMargins(0, 0, 0, 0)

        self.contenido_widget = QWidget()
        self.contenido_widget.setStyleSheet("background-color: #F4F6F9;")
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        
        lbl_titulo = QLabel("Gestión de productos y servicios")
        lbl_titulo.setStyleSheet("color: #1B2A4A; font-size: 20px; font-weight: bold;")
        contenido_layout.addWidget(lbl_titulo)

        kpi_layout = QHBoxLayout()
        
        card_stock_total = QFrame()
        card_stock_total.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 10px;")
        layout_t = QVBoxLayout(card_stock_total)
        layout_t.addWidget(QLabel("Total stock", styleSheet="color: #7c7c7c; font-size: 11px; font-weight: bold;"))
        self.lbl_val_stock_total = QLabel("0", styleSheet="color: #1B2A4A; font-size: 18px; font-weight: bold;", alignment=Qt.AlignmentFlag.AlignCenter)
        layout_t.addWidget(self.lbl_val_stock_total)
        kpi_layout.addWidget(card_stock_total)

        card_en_stock = QFrame()
        card_en_stock.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 10px;")
        layout_a = QVBoxLayout(card_en_stock)
        layout_a.addWidget(QLabel("Productos en stock", styleSheet="color: #7c7c7c; font-size: 11px; font-weight: bold;"))
        self.lbl_val_en_stock = QLabel("0", styleSheet="color: #70AD47; font-size: 18px; font-weight: bold;", alignment=Qt.AlignmentFlag.AlignCenter)
        layout_a.addWidget(self.lbl_val_en_stock)
        kpi_layout.addWidget(card_en_stock)

        card_bajo_stock = QFrame()
        card_bajo_stock.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 10px;")
        layout_i = QVBoxLayout(card_bajo_stock)
        layout_i.addWidget(QLabel("Items bajo stock", styleSheet="color: #7c7c7c; font-size: 11px; font-weight: bold;"))
        self.lbl_val_bajo_stock = QLabel("0", styleSheet="color: #E67E22; font-size: 18px; font-weight: bold;", alignment=Qt.AlignmentFlag.AlignCenter)
        layout_i.addWidget(self.lbl_val_bajo_stock)
        kpi_layout.addWidget(card_bajo_stock)

        contenido_layout.addLayout(kpi_layout)
        contenido_layout.addSpacing(10)

        self.simbolo_moneda = "S/"

        acc_layout = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Búsqueda por código o nombre...")
        self.input_buscar.setStyleSheet("QLineEdit { padding: 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: white; color: black; min-height: 28px; }")
        
        # filtrar por categoria
        self.combo_categoria = QComboBox()
        self.combo_categoria.setStyleSheet("""
            QComboBox { padding: 7px; border: 1px solid #CCD1D9; border-radius: 4px; background: white; color: black; min-height: 28px; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
        """)
        self.combo_categoria.addItem("Ver todas")

        self.btn_cambiar_estado = QPushButton("Inactivar / Activar")
        self.btn_cambiar_estado.setStyleSheet("QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2C3E6B; }")
        
        self.btn_modificar = QPushButton("Modificar seleccionado")
        self.btn_modificar.setStyleSheet("QPushButton { background-color: #EEF2FA; color: #1B2A4A; border: 1px solid #C0CCEA; font-weight: bold; padding: 8px 15px; border-radius: 4px; } QPushButton:hover { background-color: #D8E2F5; }")

        self.btn_abrir_formulario = QPushButton("Añadir nuevo item")
        self.btn_abrir_formulario.setStyleSheet("QPushButton { background-color: #70AD47; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #5B9337; }")
        
        acc_layout.addWidget(self.input_buscar, 4)
        acc_layout.addWidget(QLabel("Filtrar por categoría:"))
        acc_layout.addWidget(self.combo_categoria, 2)
        acc_layout.addWidget(self.btn_cambiar_estado, 2)
        acc_layout.addWidget(self.btn_modificar, 3)
        acc_layout.addWidget(self.btn_abrir_formulario, 3)
        contenido_layout.addLayout(acc_layout)
        contenido_layout.addSpacing(10)

        self.tabla = QTableWidget(0, 9)
        self.tabla.setHorizontalHeaderLabels(["Código", "Nombre", "Categoría", "Afectación", "Tasa %", "Imp. Extra", "Stock", "P. Unit (S/)", "Estado"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: white; color: black; border: 1px solid #E6E9ED; border-radius: 4px; }
            QTableWidget::item { color: black; background-color: white; }
            QTableWidget::item:selected { background-color: #E6E9ED; color: #1B2A4A; }
            QHeaderView::section { background-color: #1B2A4A; color: white; padding: 8px; font-weight: bold; border: none; }
        """)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        contenido_layout.addWidget(self.tabla)
        
        # paginacion y resumen de productos (mockup 3)
        bottom_layout = QHBoxLayout()
        self.pag_layout = QHBoxLayout()
        self.pag_layout.setSpacing(6)
        
        self.btn_pag_prev = QPushButton("<")
        self.btn_pag_prev.setFixedSize(30, 30)
        self.btn_pag_prev.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #E6E9ED; color: black; }")
        self.pag_layout.addWidget(self.btn_pag_prev)
        
        self.pag_buttons = []
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; } QPushButton:hover { background: #E6E9ED; color: black; }")
            self.pag_layout.addWidget(btn)
            self.pag_buttons.append(btn)
            
        self.lbl_pag_dots = QLabel("...")
        self.lbl_pag_dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pag_dots.setStyleSheet("color: #1B2A4A; font-weight: bold;")
        self.pag_layout.addWidget(self.lbl_pag_dots)
        
        self.btn_pag_last = QPushButton("10")
        self.btn_pag_last.setFixedSize(30, 30)
        self.btn_pag_last.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; } QPushButton:hover { background: #E6E9ED; color: black; }")
        self.pag_layout.addWidget(self.btn_pag_last)
        self.pag_buttons.append(self.btn_pag_last)
        
        self.btn_pag_next = QPushButton(">")
        self.btn_pag_next.setFixedSize(30, 30)
        self.btn_pag_next.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #E6E9ED; color: black; }")
        self.pag_layout.addWidget(self.btn_pag_next)
        
        bottom_layout.addLayout(self.pag_layout)
        bottom_layout.addStretch()

        self.lbl_info_productos = QLabel("Total stock: 0  |  Productos en stock: 0  |  Items bajo stock: 0")
        self.lbl_info_productos.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        bottom_layout.addWidget(self.lbl_info_productos)

        contenido_layout.addLayout(bottom_layout)

        falso_layout.addWidget(self.contenido_widget)

    def obtener_producto_seleccionado(self):
        fila_actual = self.tabla.currentRow()
        if fila_actual != -1:
            return self.tabla.item(fila_actual, 0).text(), self.tabla.item(fila_actual, 8).text()
        return None

    def actualizar_kpis(self, total_stock, en_stock, bajo_stock):
        self.lbl_val_stock_total.setText(str(total_stock))
        self.lbl_val_en_stock.setText(str(en_stock))
        self.lbl_val_bajo_stock.setText(str(bajo_stock))

    def set_simbolo_moneda(self, simbolo):
        self.simbolo_moneda = simbolo

    def cargar_tabla(self, productos):
        self.tabla.setRowCount(0)
        fuente_negrita = QFont()
        fuente_negrita.setBold(True)

        for prod in productos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            item_cod = QTableWidgetItem(str(prod.get("codigo", "")))
            item_nom = QTableWidgetItem(str(prod.get("nombre", "")))
            item_cat = QTableWidgetItem(str(prod.get("categoria_nombre", "General")))
            item_imp = QTableWidgetItem(str(prod.get("impuesto_nombre", "IGV")))
            item_tas = QTableWidgetItem(f"{prod.get('impuesto_porcentaje', 18.00)}%")
            item_ext = QTableWidgetItem(f"{prod.get('impuesto_extra', 0.00)}%")
            
            stock_val = prod.get("stock", 0)
            item_stk = QTableWidgetItem(str(stock_val))
            
            precio_val = prod.get("precio_unitario", 0.0)
            item_prc = QTableWidgetItem(f"{self.simbolo_moneda} {precio_val:.2f}")
            
            item_est = QTableWidgetItem(str(prod.get("estado", "Activo")))
            item_est.setFont(fuente_negrita)
            
            if prod.get("estado") == "Inactivo":
                item_est.setForeground(QColor("#C00000"))
            elif stock_val <= 5:
                item_est.setText("Bajo Stock")
                item_est.setForeground(QColor("#E67E22"))
            else:
                item_est.setForeground(QColor("#70AD47"))

            for item in (item_cod, item_nom, item_cat, item_imp, item_tas, item_ext, item_stk, item_prc):
                item.setForeground(QColor("#1B2A4A"))

            self.tabla.setItem(row, 0, item_cod)
            self.tabla.setItem(row, 1, item_nom)
            self.tabla.setItem(row, 2, item_cat)
            self.tabla.setItem(row, 3, item_imp)
            self.tabla.setItem(row, 4, item_tas)
            self.tabla.setItem(row, 5, item_ext)
            self.tabla.setItem(row, 6, item_stk)
            self.tabla.setItem(row, 7, item_prc)
            self.tabla.setItem(row, 8, item_est)