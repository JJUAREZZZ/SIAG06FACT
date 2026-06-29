import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QFrame, QLabel, QDialog, QAbstractItemView,
    QHeaderView, QGridLayout, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIntValidator, QDoubleValidator


#
# popup de busqueda generico
#
class BusquedaPopup(QDialog):
    item_seleccionado = pyqtSignal(dict)

    def __init__(self, titulo: str, columnas: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(640, 420)
        self.setMinimumSize(500, 340)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog         { background: #F4F6F9; }
            QLabel          { color: #1B2A4A; font-weight: bold; font-size: 13px; }
            QLineEdit       { padding: 8px 12px; border: 1px solid #B0BAD0;
                              border-radius: 6px; background: white;
                              color: #1B2A4A; font-size: 13px; min-height: 28px; }
            QLineEdit:focus { border: 2px solid #1B2A4A; }
            QTableWidget    { background: white; color: #1B2A4A;
                              border: 1px solid #D0D8EE; border-radius: 6px;
                              gridline-color: #E8EDF8; font-size: 13px; }
            QTableWidget::item          { padding: 7px 10px; }
            QTableWidget::item:selected { background: #D0DCF5; color: #1B2A4A; }
            QHeaderView::section { background: #1B2A4A; color: white;
                                   padding: 9px 10px; font-weight: bold;
                                   font-size: 12px; border: none; }
            QPushButton { padding: 9px 24px; border-radius: 6px;
                          font-weight: bold; font-size: 13px; border: none; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(12)

        lbl = QLabel(titulo)
        lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #1B2A4A;")
        lay.addWidget(lbl)

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Escribe para filtrar resultados...")
        self.input_buscar.textChanged.connect(self._filtrar)
        lay.addWidget(self.input_buscar)

        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.doubleClicked.connect(self._confirmar_seleccion)
        lay.addWidget(self.tabla)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background:#C00000; color:white;")
        btn_cancelar.clicked.connect(self.reject)
        self.btn_seleccionar = QPushButton("Seleccionar")
        self.btn_seleccionar.setStyleSheet("background:#1B2A4A; color:white;")
        self.btn_seleccionar.clicked.connect(self._confirmar_seleccion)
        btn_row.addWidget(btn_cancelar)
        btn_row.addSpacing(8)
        btn_row.addWidget(self.btn_seleccionar)
        lay.addLayout(btn_row)

        self._datos = []

    def cargar_datos(self, filas: list):
        self._datos = filas
        self._poblar_tabla(filas)

    def _poblar_tabla(self, filas):
        self.tabla.setRowCount(0)
        cols = self.tabla.columnCount()
        for fila in filas:
            valores = list(fila.values())
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for c in range(min(cols, len(valores))):
                item = QTableWidgetItem(str(valores[c]))
                item.setData(Qt.ItemDataRole.UserRole, fila)
                self.tabla.setItem(row, c, item)

    def _filtrar(self, texto: str):
        t = texto.lower()
        self._poblar_tabla([f for f in self._datos
                            if any(t in str(v).lower() for v in f.values())])

    def _confirmar_seleccion(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        dato = self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        self.item_seleccionado.emit(dato)
        self.accept()


# vista principal de factura
class FacturaView(QWidget):
    fila_eliminada_index = pyqtSignal(int)   # emitida cada vez que se borra un item de la tabla con su indice

    def __init__(self):
        super().__init__()

        # sizepolicy expansiva para que el stackedwidget lo estire al 100
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # estilos globales
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; }

            QLabel { color: #000000; font-size: 13px; font-weight: bold; border: none; }

            QLineEdit {
                padding: 8px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 28px;
            }
            QLineEdit:focus { border: 1.5px solid #1B2A4A; }

            QComboBox {
                padding: 6px 12px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 28px;
            }
            QComboBox:focus { border: 1.5px solid #1B2A4A; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
            }

            QFrame#SeccionFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #E6E9ED;
            }
            QTableWidget {
                background-color: white;
                color: black;
                border: 1px solid #E6E9ED;
                border-radius: 4px;
                gridline-color: #E8EDF8;
                font-size: 13px;
            }
            QTableWidget::item {
                color: black;
                background-color: white;
                border-bottom: 1px solid #E6E9ED;
                padding: 7px 8px;
            }
            QTableWidget::item:selected { background-color: #D5E0F5; color: #1B2A4A; }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
            QHeaderView::section {
                background-color: #1B2A4A;
                color: white;
                padding: 9px 8px;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-right: 1px solid #2C3E6B;
            }
        """)

        # layout raiz igual estructura que los demas modulos
        falso_layout = QHBoxLayout(self)
        falso_layout.setContentsMargins(0, 0, 0, 0)
        falso_layout.setSpacing(0)

        # widget principal de contenido
        self.contenido_widget = QWidget()
        self.contenido_widget.setStyleSheet("background-color: #F4F6F9;")
        self.contenido_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        contenido_layout.setSpacing(14)

        falso_layout.addWidget(self.contenido_widget)

        # cabecera
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(10)

        lbl_titulo = QLabel("Nueva Factura")
        lbl_titulo.setStyleSheet(
            "color: #1B2A4A; font-size: 22px; font-weight: bold;"
        )
        header_layout.addWidget(lbl_titulo)

        self.lbl_num_factura = QLabel("F001-00001")
        self.lbl_num_factura.setStyleSheet("""
            color: #4A6FA5;
            font-size: 13px;
            font-weight: bold;
            background: #E2EAF8;
            border: 1px solid #B8CCEE;
            border-radius: 4px;
            padding: 4px 12px;
        """)
        header_layout.addWidget(self.lbl_num_factura)
        header_layout.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(38)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background: white; color: #C00000;
                border: 1.5px solid #C00000;
                border-radius: 5px; padding: 0px 20px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #FFF0F0; }
        """)

        self.btn_generar_final = QPushButton("Emitir Factura")
        self.btn_generar_final.setFixedHeight(38)
        self.btn_generar_final.setStyleSheet("""
            QPushButton {
                background-color: #70AD47; color: white;
                border: none; border-radius: 5px;
                padding: 0px 22px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #5B9337; }
        """)

        header_layout.addWidget(self.btn_cancelar)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.btn_generar_final)
        contenido_layout.addLayout(header_layout)

        # informacion del cliente
        cliente_frame = QFrame()
        cliente_frame.setObjectName("SeccionFrame")
        grid_cliente = QGridLayout(cliente_frame)
        grid_cliente.setContentsMargins(20, 15, 20, 15)
        grid_cliente.setVerticalSpacing(8)
        grid_cliente.setHorizontalSpacing(20)

        # titulo  boton buscar
        lbl_info_cli = QLabel("Información del cliente")
        lbl_info_cli.setStyleSheet("color: #1B2A4A; font-size: 15px; font-weight: bold;")
        grid_cliente.addWidget(lbl_info_cli, 0, 0, 1, 3)

        self.btn_buscar_cliente = QPushButton("Buscar cliente")
        self.btn_buscar_cliente.setFixedHeight(32)
        self.btn_buscar_cliente.setStyleSheet("""
            QPushButton {
                background: #EEF2FA; color: #1B2A4A;
                border: 1.5px solid #C0CCEA; border-radius: 5px;
                padding: 0px 14px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #D8E2F5; }
        """)
        grid_cliente.addWidget(self.btn_buscar_cliente, 0, 3,
                               Qt.AlignmentFlag.AlignRight)

        # fila 1: etiquetas
        for col, txt in enumerate(["Cliente / Razón Social", "DNI / RUC", "Fecha Emisión"]):
            lbl = QLabel(txt.upper())
            lbl.setStyleSheet(
                "color: #8A96B0; font-size: 10px; font-weight: bold; "
                "letter-spacing: 0.4px; border: none; padding: 0;"
            )
            grid_cliente.addWidget(lbl, 1, col)

        # fila 2: valores
        self.lbl_cli_nombre = self._val_label()
        self.lbl_cli_doc    = self._val_label()
        self.lbl_cli_fecha  = self._val_label(
            QDate.currentDate().toString("dd/MM/yyyy")
        )
        grid_cliente.addWidget(self.lbl_cli_nombre, 2, 0)
        grid_cliente.addWidget(self.lbl_cli_doc,    2, 1)
        grid_cliente.addWidget(self.lbl_cli_fecha,  2, 2)
        grid_cliente.addWidget(QWidget(),           2, 3)  # spacer

        # fila 3: etiquetas fila baja
        for col, txt in enumerate(["Dirección", "Teléfono", "Email"]):
            lbl = QLabel(txt.upper())
            lbl.setStyleSheet(
                "color: #8A96B0; font-size: 10px; font-weight: bold; "
                "letter-spacing: 0.4px; border: none; padding: 0; margin-top: 4px;"
            )
            grid_cliente.addWidget(lbl, 3, col)

        # fila 4: valores fila baja
        self.lbl_cli_dir   = self._val_label()
        self.lbl_cli_tel   = self._val_label()
        self.lbl_cli_email = self._val_label()
        grid_cliente.addWidget(self.lbl_cli_dir,   4, 0)
        grid_cliente.addWidget(self.lbl_cli_tel,   4, 1)
        grid_cliente.addWidget(self.lbl_cli_email, 4, 2)

        # fila 5: etiquetas combos de pago y moneda
        for col, txt in enumerate(["Tipo Comprobante", "Forma de Pago", "Método de Pago", "Moneda"]):
            lbl = QLabel(txt.upper())
            lbl.setStyleSheet(
                "color: #8A96B0; font-size: 10px; font-weight: bold; "
                "letter-spacing: 0.4px; border: none; padding: 0; margin-top: 8px;"
            )
            grid_cliente.addWidget(lbl, 5, col)

        # fila 6: combos
        self.combo_tipo_comprobante = QComboBox()
        self.combo_tipo_comprobante.addItems(["Factura Electrónica", "Boleta de Venta"])
        
        self.combo_forma_pago = QComboBox()
        self.combo_forma_pago.addItems(["Contado", "Crédito"])
        
        self.combo_metodo_pago = QComboBox()
        self.combo_metodo_pago.addItems(["Efectivo", "Tarjeta", "Transferencia"])
        
        self.combo_moneda = QComboBox()
        self.combo_moneda.addItems(["PEN (S/)", "USD ($)"])

        grid_cliente.addWidget(self.combo_tipo_comprobante, 6, 0)
        grid_cliente.addWidget(self.combo_forma_pago, 6, 1)
        grid_cliente.addWidget(self.combo_metodo_pago, 6, 2)
        grid_cliente.addWidget(self.combo_moneda, 6, 3)

        # reactividad para deshabilitar metodo de pago en credito
        self.combo_forma_pago.currentTextChanged.connect(self._on_forma_pago_changed)

        grid_cliente.setColumnStretch(0, 3)
        grid_cliente.setColumnStretch(1, 2)
        grid_cliente.setColumnStretch(2, 2)
        grid_cliente.setColumnStretch(3, 2)

        contenido_layout.addWidget(cliente_frame)

        # seccion de agregar producto
        productos_frame = QFrame()
        productos_frame.setObjectName("SeccionFrame")
        grid_prod = QGridLayout(productos_frame)
        grid_prod.setContentsMargins(20, 15, 20, 15)
        grid_prod.setVerticalSpacing(8)
        grid_prod.setHorizontalSpacing(16)

        lbl_prods = QLabel("Agregar producto / servicio")
        lbl_prods.setStyleSheet("color: #1B2A4A; font-size: 15px; font-weight: bold;")
        grid_prod.addWidget(lbl_prods, 0, 0, 1, 4)

        self.btn_buscar_prod = QPushButton("Buscar producto")
        self.btn_buscar_prod.setFixedHeight(32)
        self.btn_buscar_prod.setStyleSheet("""
            QPushButton {
                background: #EEF2FA; color: #1B2A4A;
                border: 1.5px solid #C0CCEA; border-radius: 5px;
                padding: 0px 14px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #D8E2F5; }
        """)
        grid_prod.addWidget(self.btn_buscar_prod, 0, 4,
                            Qt.AlignmentFlag.AlignRight)

        # etiquetas fila de solo lectura
        for col, txt in enumerate(["Código", "Nombre / Descripción",
                                    "Stock disponible", "Precio unitario"]):
            lbl = QLabel(txt.upper())
            lbl.setStyleSheet(
                "color: #8A96B0; font-size: 10px; font-weight: bold; "
                "letter-spacing: 0.4px; border: none; padding: 0;"
            )
            grid_prod.addWidget(lbl, 1, col)

        self.lbl_prod_codigo = self._val_label()
        self.lbl_prod_nombre = self._val_label()
        self.lbl_prod_stock  = self._val_label()
        self.lbl_prod_precio = self._val_label()
        grid_prod.addWidget(self.lbl_prod_codigo, 2, 0)
        grid_prod.addWidget(self.lbl_prod_nombre, 2, 1)
        grid_prod.addWidget(self.lbl_prod_stock,  2, 2)
        grid_prod.addWidget(self.lbl_prod_precio, 2, 3)
        grid_prod.setColumnStretch(1, 3)

        # separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: none; border-top: 1px solid #E6E9ED; margin: 4px 0;")
        grid_prod.addWidget(sep, 3, 0, 1, 5)

        # etiquetas cantidad / descuento
        lbl_cant = QLabel("CANTIDAD")
        lbl_cant.setStyleSheet(
            "color: #8A96B0; font-size: 10px; font-weight: bold; "
            "letter-spacing: 0.4px; border: none; padding: 0;"
        )
        lbl_desc_pct = QLabel("DESCUENTO (%)")
        lbl_desc_pct.setStyleSheet(
            "color: #8A96B0; font-size: 10px; font-weight: bold; "
            "letter-spacing: 0.4px; border: none; padding: 0;"
        )
        grid_prod.addWidget(lbl_cant,     4, 0)
        grid_prod.addWidget(lbl_desc_pct, 4, 1)

        self.input_prod_cantidad = QLineEdit("1")
        self.input_prod_cantidad.setFixedWidth(90)
        self.input_prod_cantidad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_prod_cantidad.setValidator(QIntValidator(1, 99999))

        self.input_prod_descuento = QLineEdit("0")
        self.input_prod_descuento.setFixedWidth(110)
        self.input_prod_descuento.setPlaceholderText("0.00")
        self.input_prod_descuento.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_prod_descuento.setValidator(QDoubleValidator(0.0, 99.99, 2))

        grid_prod.addWidget(self.input_prod_cantidad,  5, 0)
        grid_prod.addWidget(self.input_prod_descuento, 5, 1)

        self.btn_agregar_item = QPushButton("Añadir a la lista")
        self.btn_agregar_item.setFixedSize(160, 36)
        self.btn_agregar_item.setStyleSheet("""
            QPushButton {
                background-color: #1B2A4A; color: white;
                font-weight: bold; border-radius: 5px; border: none;
            }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        grid_prod.addWidget(self.btn_agregar_item, 5, 4,
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        contenido_layout.addWidget(productos_frame)

        # detalles de la factura
        self.tabla_detalle = QTableWidget(0, 7)
        self.tabla_detalle.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Cant.", "P. Unit.", "Desc. %", "Total", ""]
        )
        self.tabla_detalle.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla_detalle.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tabla_detalle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_detalle.setAlternatingRowColors(True)
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.setMinimumHeight(160)
        self.tabla_detalle.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.tabla_detalle.verticalHeader().setDefaultSectionSize(38)
        self.tabla_detalle.setStyleSheet("""
            QHeaderView::section {
                background-color: #1B2A4A;
                color: white;
                padding: 9px 8px;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-right: 1px solid #2C3E6B;
            }
            QTableWidget::item {
                color: #1B2A4A;
                background-color: white;
                border-bottom: 1px solid #E6E9ED;
                padding: 7px 8px;
            }
            QTableWidget::item:selected { background-color: #D5E0F5; color: #1B2A4A; }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
        """)

        hdr = self.tabla_detalle.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla_detalle.setColumnWidth(0, 90)
        self.tabla_detalle.setColumnWidth(2, 60)
        self.tabla_detalle.setColumnWidth(3, 90)
        self.tabla_detalle.setColumnWidth(4, 75)
        self.tabla_detalle.setColumnWidth(5, 95)
        self.tabla_detalle.setColumnWidth(6, 40)

        contenido_layout.addWidget(self.tabla_detalle)

       # totales
        final_layout = QHBoxLayout()
        final_layout.addStretch()

        totales_frame = QFrame()
        totales_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #E6E9ED;
            }
        """)
        totales_frame.setFixedWidth(280)
        totales_layout = QGridLayout(totales_frame)
        totales_layout.setContentsMargins(18, 14, 18, 14)
        totales_layout.setVerticalSpacing(7)
        totales_layout.setHorizontalSpacing(20)

        def _tot_lbl(txt, bold=False, big=False, color="#555555"):
            l = QLabel(txt)
            fs = "15px" if big else "13px"
            fw = "bold" if bold else "normal"
            l.setStyleSheet(
                f"color:{color}; font-size:{fs}; font-weight:{fw}; border:none;"
            )
            return l

        lbl_sub = _tot_lbl("Subtotal:")
        self.lbl_val_subtotal = _tot_lbl("S/ 0.00", color="#000000")
        self.lbl_val_subtotal.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        lbl_desc = _tot_lbl("Descuento:")
        self.lbl_val_descuento = _tot_lbl("S/ 0.00", color="#B00000")
        self.lbl_val_descuento.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.lbl_igv = _tot_lbl("IGV:")
        self.lbl_val_igv = _tot_lbl("S/ 0.00", color="#000000")
        self.lbl_val_igv.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # separador
        sep_tot = QFrame()
        sep_tot.setFrameShape(QFrame.Shape.HLine)
        sep_tot.setStyleSheet("border:none; border-top:1px solid #E6E9ED;")

        lbl_total = _tot_lbl("Total a pagar:", bold=True, big=True, color="#1B2A4A")
        self.lbl_val_total = _tot_lbl("S/ 0.00", bold=True, big=True, color="#000000")
        self.lbl_val_total.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.simbolo_moneda = "S/"

        totales_layout.addWidget(lbl_sub,              0, 0)
        totales_layout.addWidget(self.lbl_val_subtotal,  0, 1)
        totales_layout.addWidget(lbl_desc,             1, 0)
        totales_layout.addWidget(self.lbl_val_descuento, 1, 1)
        totales_layout.addWidget(self.lbl_igv,          2, 0)
        totales_layout.addWidget(self.lbl_val_igv,       2, 1)
        totales_layout.addWidget(sep_tot,              3, 0, 1, 2)
        totales_layout.addWidget(lbl_total,            4, 0)
        totales_layout.addWidget(self.lbl_val_total,     4, 1)

        final_layout.addWidget(totales_frame)
        contenido_layout.addLayout(final_layout)
        contenido_layout.addStretch()

    # esto son helpers
    @staticmethod
    def _val_label(texto="—"):
        """etiqueta de solo lectura con fondo gris claro."""
        lbl = QLabel(texto)
        lbl.setStyleSheet("""
            color: #1B2A4A;
            font-size: 13px;
            font-weight: normal;
            background: #F4F6F9;
            border: 1px solid #CCD1D9;
            border-radius: 4px;
            padding: 6px 10px;
        """)
        lbl.setMinimumHeight(32)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return lbl

    def set_simbolo_moneda(self, simbolo):
        self.simbolo_moneda = simbolo

    # y esto esta relacionado a la api publica (usada por facturacontroller)
    def set_cliente(self, datos: dict):
        self.lbl_cli_nombre.setText(datos.get("nombre_razon_social") or "—")
        self.lbl_cli_doc.setText(datos.get("dni_ruc") or "—")
        self.lbl_cli_dir.setText(datos.get("direccion") or "—")
        self.lbl_cli_tel.setText(datos.get("telefono") or "—")
        self.lbl_cli_email.setText(datos.get("email") or "—")

    def set_producto(self, datos: dict):
        self.lbl_prod_codigo.setText(datos.get("codigo") or "—")
        self.lbl_prod_nombre.setText(datos.get("nombre") or "—")
        self.lbl_prod_stock.setText(str(datos.get("stock", "—")))
        precio = datos.get("precio_unitario", 0)
        self.lbl_prod_precio.setText(f"{self.simbolo_moneda} {float(precio):.2f}")
        self.input_prod_cantidad.setText("1")
        self.input_prod_descuento.setText("0")

    def agregar_fila_tabla(self, codigo, nombre, cantidad,
                           precio_uni, descuento_pct, subtotal):
        row = self.tabla_detalle.rowCount()
        self.tabla_detalle.insertRow(row)
        self.tabla_detalle.setRowHeight(row, 38)

        datos = [
            (codigo,                  Qt.AlignmentFlag.AlignLeft),
            (nombre,                  Qt.AlignmentFlag.AlignLeft),
            (str(cantidad),           Qt.AlignmentFlag.AlignCenter),
            (f"{self.simbolo_moneda} {precio_uni:.2f}",  Qt.AlignmentFlag.AlignRight),
            (f"{descuento_pct:.1f}%", Qt.AlignmentFlag.AlignCenter),
            (f"{self.simbolo_moneda} {subtotal:.2f}",    Qt.AlignmentFlag.AlignRight),
        ]
        for col, (val, alig) in enumerate(datos):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | alig)
            item.setForeground(QColor("#000000"))
            self.tabla_detalle.setItem(row, col, item)

        btn_del = QPushButton("X")
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent; color: #B00000;
                font-weight: bold; font-size: 13px;
                border: none; border-radius: 3px;
            }
            QPushButton:hover { background: #FDECEA; }
        """)
        btn_del.setToolTip("Eliminar este item")
        btn_del.clicked.connect(lambda _, r=row: self._eliminar_fila(r))
        self.tabla_detalle.setCellWidget(row, 6, btn_del)

    def _eliminar_fila(self, row):
        self.fila_eliminada_index.emit(row)
        self.tabla_detalle.removeRow(row)
        for r in range(self.tabla_detalle.rowCount()):
            btn = self.tabla_detalle.cellWidget(r, 6)
            if btn:
                try:
                    btn.clicked.disconnect()
                except Exception:
                     pass
                btn.clicked.connect(lambda _, r_=r: self._eliminar_fila(r_))

    def actualizar_totales(self, subtotal, descuento, igv, total):
        self.lbl_val_subtotal.setText(f"{self.simbolo_moneda} {subtotal:.2f}")
        self.lbl_val_descuento.setText(f"- {self.simbolo_moneda} {descuento:.2f}")
        self.lbl_val_igv.setText(f"{self.simbolo_moneda} {igv:.2f}")
        self.lbl_val_total.setText(f"{self.simbolo_moneda} {total:.2f}")

    def limpiar_formulario(self):
        self.tabla_detalle.setRowCount(0)
        for attr in ("lbl_cli_nombre", "lbl_cli_doc", "lbl_cli_dir",
                     "lbl_cli_tel", "lbl_cli_email",
                     "lbl_prod_codigo", "lbl_prod_nombre",
                     "lbl_prod_stock", "lbl_prod_precio"):
            getattr(self, attr).setText("—")
        self.input_prod_cantidad.setText("1")
        self.input_prod_descuento.setText("0")
        self.combo_tipo_comprobante.setCurrentIndex(0)
        self.combo_forma_pago.setCurrentIndex(0)
        self.combo_metodo_pago.setCurrentIndex(0)
        self.combo_moneda.setCurrentIndex(0)
        self.combo_metodo_pago.setEnabled(True)
        self.actualizar_totales(0, 0, 0, 0)
        self.lbl_cli_fecha.setText(QDate.currentDate().toString("dd/MM/yyyy"))

    def _on_forma_pago_changed(self, texto):
        if texto == "Crédito":
            self.combo_metodo_pago.setEnabled(False)
            if self.combo_metodo_pago.findText("—") == -1:
                self.combo_metodo_pago.addItem("—")
            self.combo_metodo_pago.setCurrentText("—")
        else:
            self.combo_metodo_pago.setEnabled(True)
            idx = self.combo_metodo_pago.findText("—")
            if idx != -1:
                self.combo_metodo_pago.removeItem(idx)
            self.combo_metodo_pago.setCurrentIndex(0)