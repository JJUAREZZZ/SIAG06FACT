import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFrame, QLabel, QDialog, QAbstractItemView, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPixmap

class FormularioClienteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir nuevo cliente")
        self.setFixedSize(400, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_title = QLabel("Registrar Cliente")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2A4A; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        self.input_dni = QLineEdit()
        self.input_dni.setPlaceholderText("DNI / RUC (Obligatorio)")
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre o Razón Social (Obligatorio)")
        self.input_direccion = QLineEdit()
        self.input_direccion.setPlaceholderText("Dirección fiscal")
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Correo electrónico")
        self.input_telefono = QLineEdit()
        self.input_telefono.setPlaceholderText("Número de teléfono")

        style_input = "QLineEdit { padding: 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: #F4F6F9; color: black; font-size: 13px; min-height: 28px; }"
        for inp in [self.input_dni, self.input_nombre, self.input_direccion, self.input_email, self.input_telefono]:
            inp.setStyleSheet(style_input)
            layout.addWidget(inp)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("QPushButton { background-color: #C00000; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar_form = QPushButton("Guardar")
        self.btn_guardar_form.setStyleSheet("QPushButton { background-color: #70AD47; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }")
        self.btn_guardar_form.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar_form)
        layout.addLayout(btn_layout)

    def obtener_datos(self):
        return (
            self.input_dni.text().strip(),
            self.input_nombre.text().strip(),
            self.input_direccion.text().strip(),
            self.input_email.text().strip(),
            self.input_telefono.text().strip()
        )

    def precompletar(self, datos):
        self.setWindowTitle("Modificar cliente")
        self.input_dni.setText(datos.get("dni_ruc", ""))
        self.input_dni.setReadOnly(True)
        self.input_dni.setStyleSheet("QLineEdit { padding: 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: #E2EAF8; color: #555555; font-size: 13px; min-height: 28px; }")
        self.input_nombre.setText(datos.get("nombre_razon_social", ""))
        self.input_direccion.setText(datos.get("direccion", "") or "")
        self.input_email.setText(datos.get("email", "") or "")
        self.input_telefono.setText(datos.get("telefono", "") or "")

class ClienteView(QWidget):
    def __init__(self):
        super().__init__()
        
        falso_layout = QHBoxLayout(self)
        falso_layout.setContentsMargins(0, 0, 0, 0)

        # sidebar lateral compartido
        self.sidebar = QFrame()
        self.sidebar.setStyleSheet("background-color: #1B2A4A;")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        # cargar logo
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_logo = os.path.join(directorio_actual, "Logosistema.png")
        
        self.lbl_logo_img = QLabel()
        pixmap_logo = QPixmap(ruta_logo)
        if not pixmap_logo.isNull():
            pixmap_escalado = pixmap_logo.scaledToWidth(160, Qt.TransformationMode.SmoothTransformation)
            self.lbl_logo_img.setPixmap(pixmap_escalado)
        else:
            self.lbl_logo_img.setText("[Logo no encontrado]")
            self.lbl_logo_img.setStyleSheet("color: #CCD1D9; font-weight: bold; font-size: 14px;")
            
        self.lbl_logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.lbl_logo_img)
        sidebar_layout.addSpacing(30)
        
        # estilo de botones
        style_botones = "QPushButton { color: white; background-color: transparent; text-align: left; padding: 10px; font-size: 13px; border: none; } QPushButton:hover { background-color: #2C3E6B; border-radius: 4px; }"
        
        # se instancian los botones como atributos de la clase
        self.btn_menu_dashboard = QPushButton("Dashboard")
        self.btn_menu_nueva_factura = QPushButton("Nueva Factura")
        self.btn_menu_historial = QPushButton("Historial de Facturas")
        self.btn_menu_productos = QPushButton("Productos/Servicios")
        self.btn_menu_clientes = QPushButton("Clientes")
        self.btn_menu_config = QPushButton("Configuración")
        
        # aca se aplican estilos y se añaden al layout
        for btn in [self.btn_menu_dashboard, self.btn_menu_nueva_factura, self.btn_menu_historial, self.btn_menu_productos, self.btn_menu_clientes, self.btn_menu_config]:
            btn.setStyleSheet(style_botones)
            sidebar_layout.addWidget(btn)
            
        # se resalta el modulo inicial por defecto
        self.btn_menu_clientes.setStyleSheet(style_botones + "background-color: #2C3E6B; border-radius: 4px; font-weight: bold;")
        
        sidebar_layout.addStretch()

        # contenido principal
        self.contenido_widget = QWidget()
        self.contenido_widget.setStyleSheet("background-color: #F4F6F9;")
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        
        lbl_titulo = QLabel("Gestión de clientes")
        lbl_titulo.setStyleSheet("color: #1B2A4A; font-size: 20px; font-weight: bold;")
        contenido_layout.addWidget(lbl_titulo)

        # kpissss (resumen)
        kpi_layout = QHBoxLayout()
        
        card_total = QFrame()
        card_total.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 10px;")
        layout_t = QVBoxLayout(card_total)
        lbl_t_title = QLabel("Total clientes registrados")
        lbl_t_title.setStyleSheet("color: #7c7c7c; font-size: 11px; font-weight: bold;")
        layout_t.addWidget(lbl_t_title)
        self.lbl_val_total = QLabel("0")
        self.lbl_val_total.setStyleSheet("color: #1B2A4A; font-size: 18px; font-weight: bold;")
        self.lbl_val_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_t.addWidget(self.lbl_val_total)
        kpi_layout.addWidget(card_total)

        card_activos = QFrame()
        card_activos.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 10px;")
        layout_a = QVBoxLayout(card_activos)
        lbl_a_title = QLabel("Clientes activos")
        lbl_a_title.setStyleSheet("color: #7c7c7c; font-size: 11px; font-weight: bold;")
        layout_a.addWidget(lbl_a_title)
        self.lbl_val_activos = QLabel("0")
        self.lbl_val_activos.setStyleSheet("color: #70AD47; font-size: 18px; font-weight: bold;")
        self.lbl_val_activos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_a.addWidget(self.lbl_val_activos)
        kpi_layout.addWidget(card_activos)

        card_inactivos = QFrame()
        card_inactivos.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 10px;")
        layout_i = QVBoxLayout(card_inactivos)
        lbl_i_title = QLabel("Clientes inactivos")
        lbl_i_title.setStyleSheet("color: #7c7c7c; font-size: 11px; font-weight: bold;")
        layout_i.addWidget(lbl_i_title)
        self.lbl_val_inactivos = QLabel("0")
        self.lbl_val_inactivos.setStyleSheet("color: #C00000; font-size: 18px; font-weight: bold;")
        self.lbl_val_inactivos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_i.addWidget(self.lbl_val_inactivos)
        kpi_layout.addWidget(card_inactivos)

        contenido_layout.addLayout(kpi_layout)
        contenido_layout.addSpacing(10)

        # actionbar
        acc_layout = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Buscar por dni, ruc o nombre...")
        self.input_buscar.setStyleSheet("QLineEdit { padding: 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: white; color: black; min-height: 28px; }")
        
        # filtrar por categoría
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
        self.combo_categoria.addItems(["Ver todas", "General", "Empresa", "Particular"])

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

        # tabla (se añade columna para 'tipo doc' requerida por los lineamientos de auditoría)
        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(["DNI/RUC", "Tipo Doc", "Nombre / Razón Social", "Dirección", "Email", "Teléfono", "Estado", "Fecha Registro"])
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

        # paginación y resumen de clientes
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

        self.lbl_info_clientes = QLabel("Total items(clientes): 9  |  Clientes activos: 7  |  Clientes inactivos: 2")
        self.lbl_info_clientes.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        bottom_layout.addWidget(self.lbl_info_clientes)

        contenido_layout.addLayout(bottom_layout)
        
        falso_layout.addWidget(self.contenido_widget)

    def obtener_cliente_seleccionado(self):
        fila_actual = self.tabla.currentRow()
        if fila_actual != -1:
            # ahora el estado se encuentra indexado en la columna 6 debido a la nueva inserción de tipo doc
            return self.tabla.item(fila_actual, 0).text(), self.tabla.item(fila_actual, 6).text()
        return None

    def actualizar_kpis(self, total, activos, inactivos):
        self.lbl_val_total.setText(str(total))
        self.lbl_val_activos.setText(str(activos))
        self.lbl_val_inactivos.setText(str(inactivos))

    def cargar_tabla(self, clientes):
        self.tabla.setRowCount(0)
        fuente_estado = QFont()
        fuente_estado.setBold(True)

        for cliente in clientes:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            item_dni = QTableWidgetItem(str(cliente.get("dni_ruc", "")))
            item_tdoc = QTableWidgetItem(str(cliente.get("tipo_documento", "DNI")))
            item_nom = QTableWidgetItem(str(cliente.get("nombre_razon_social", "")))
            item_dir = QTableWidgetItem(str(cliente.get("direccion", "")))
            item_ema = QTableWidgetItem(str(cliente.get("email", "")))
            item_tel = QTableWidgetItem(str(cliente.get("telefono", "")))
            item_est = QTableWidgetItem(str(cliente.get("estado", "Activo")))
            item_fec = QTableWidgetItem(str(cliente.get("fecha_registro", "")))
            
            item_est.setFont(fuente_estado)
            if cliente.get("estado") == "Inactivo":
                item_est.setForeground(QColor("#C00000"))
            else:
                item_est.setForeground(QColor("#70AD47"))

            for item in (item_dni, item_tdoc, item_nom, item_dir, item_ema, item_tel, item_fec):
                item.setForeground(QColor("#1B2A4A"))

            self.tabla.setItem(row, 0, item_dni)
            self.tabla.setItem(row, 1, item_tdoc)
            self.tabla.setItem(row, 2, item_nom)
            self.tabla.setItem(row, 3, item_dir)
            self.tabla.setItem(row, 4, item_ema)
            self.tabla.setItem(row, 5, item_tel)
            self.tabla.setItem(row, 6, item_est)
            self.tabla.setItem(row, 7, item_fec)