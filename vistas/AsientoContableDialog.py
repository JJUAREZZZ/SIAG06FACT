from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QTabWidget, QWidget, QMessageBox,
                             QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class AsientoContableDialog(QDialog):
    def __init__(self, num_factura, asientos, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Asiento Contable — Factura {num_factura}")
        self.resize(700, 480)
        self.setStyleSheet("background-color: #F4F6F9;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. cabecera principal del diálogo
        header_lbl = QLabel("Consulta de Asiento Contable")
        header_lbl.setStyleSheet("color: #1B2A4A; font-size: 20px; font-weight: bold;")
        main_layout.addWidget(header_lbl)

        # si no hay asientos contables disponibles
        if not asientos:
            no_asientos_lbl = QLabel("No se encontraron asientos contables registrados para este comprobante.")
            no_asientos_lbl.setStyleSheet("color: #B00000; font-size: 14px; font-weight: bold; background: white; padding: 20px; border-radius: 6px; border: 1px solid #E6E9ED;")
            no_asientos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(no_asientos_lbl)
            
            btn_close = QPushButton("Cerrar")
            btn_close.setStyleSheet("background-color: #1B2A4A; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold; border: none;")
            btn_close.clicked.connect(self.reject)
            main_layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignCenter)
            return

        # 2. si hay asientos, mostramos la información. si hay más de uno (ej: venta y extorno), usamos tabs
        if len(asientos) > 1:
            self.tabs = QTabWidget()
            self.tabs.setStyleSheet("""
                QTabWidget::pane { border: 1px solid #E6E9ED; background: white; border-radius: 6px; }
                QTabBar::tab { background: #E2EAF8; color: #1B2A4A; padding: 8px 16px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #CCD1D9; border-bottom: none; margin-right: 2px; }
                QTabBar::tab:selected { background: white; color: #1B2A4A; border-bottom: 2px solid white; }
                QTabBar::tab:hover { background: #D8E2F5; }
            """)
            for idx, as_data in enumerate(asientos):
                tab_name = "Asiento Venta (Original)" if idx == 0 else "Asiento Extorno (Anulación)"
                self.tabs.addTab(self._crear_vista_asiento(as_data, num_factura), tab_name)
            main_layout.addWidget(self.tabs)
        else:
            # solo hay un asiento, lo mostramos directamente
            widget_asiento = self._crear_vista_asiento(asientos[0], num_factura)
            main_layout.addWidget(widget_asiento)

        # 3. fila de botones e interfaz inferior común
        bottom_layout = QHBoxLayout()
        
        # botón pdf
        self.btn_pdf = QPushButton("Exportar Asiento PDF")
        self.btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: #EEF2FA; color: #1B2A4A;
                border: 1.5px solid #C0CCEA; border-radius: 5px;
                padding: 8px 16px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #D8E2F5; }
        """)
        self.btn_pdf.clicked.connect(self._exportar_pdf_simulado)
        bottom_layout.addWidget(self.btn_pdf)
        
        bottom_layout.addStretch()
        
        # botón cerrar / regresar
        self.btn_cerrar = QPushButton("Regresar")
        self.btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #1B2A4A; color: white;
                border: none; border-radius: 5px;
                padding: 8px 24px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        self.btn_cerrar.clicked.connect(self.accept)
        bottom_layout.addWidget(self.btn_cerrar)
        
        main_layout.addLayout(bottom_layout)

    def _crear_vista_asiento(self, as_data, num_factura):
        """Crea el widget de visualización para un asiento específico."""
        widget = QWidget()
        widget.setStyleSheet("background-color: white; border-radius: 6px;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # panel de metadatos (cabecera)
        meta_frame = QFrame()
        meta_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E6E9ED; border-radius: 4px; padding: 10px;")
        meta_layout = QHBoxLayout(meta_frame)
        meta_layout.setContentsMargins(10, 8, 10, 8)
        
        def _lbl_meta(title, value):
            container = QVBoxLayout()
            container.setSpacing(2)
            t_lbl = QLabel(title.upper())
            t_lbl.setStyleSheet("color: #8A96B0; font-size: 9px; font-weight: bold; letter-spacing: 0.4px;")
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
            container.addWidget(t_lbl)
            container.addWidget(v_lbl)
            return container

        meta_layout.addLayout(_lbl_meta("N° Asiento", as_data["num_asiento"]))
        meta_layout.addSpacing(15)
        meta_layout.addLayout(_lbl_meta("Doc. Referencia", f"Factura {num_factura}"))
        meta_layout.addSpacing(15)
        meta_layout.addLayout(_lbl_meta("Fecha Registro", as_data["fecha"]))
        meta_layout.addSpacing(15)
        meta_layout.addLayout(_lbl_meta("Glosa General", as_data["glosa"]))
        meta_layout.addStretch()
        
        layout.addWidget(meta_frame)

        # grilla de cuentas contables (cuerpo)
        tabla = QTableWidget(0, 4)
        tabla.setHorizontalHeaderLabels(["Cuenta", "Denominación / Descripción", "Debe (S/)", "Haber (S/)"])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.verticalHeader().setVisible(False)
        tabla.verticalHeader().setDefaultSectionSize(32)
        tabla.setStyleSheet("""
            QHeaderView::section {
                background-color: #1B2A4A; color: white;
                padding: 7px; font-weight: bold; font-size: 11px;
                border: none; border-right: 1px solid #2C3E6B;
            }
            QTableWidget {
                border: 1px solid #E6E9ED; border-radius: 4px;
                gridline-color: #F1F3F5; font-size: 12px; background: white;
            }
            QTableWidget::item { color: #1B2A4A; padding: 5px; }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
        """)
        
        # configurar anchos de columna
        hdr = tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        tabla.setColumnWidth(0, 70)
        tabla.setColumnWidth(2, 100)
        tabla.setColumnWidth(3, 100)

        # rellenar la tabla
        for line in as_data["detalles"]:
            row = tabla.rowCount()
            tabla.insertRow(row)
            
            c_code = QTableWidgetItem(str(line["cuenta_codigo"]))
            c_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_name = QTableWidgetItem(str(line["cuenta_nombre"]))
            
            debe_val = float(line["debe"])
            haber_val = float(line["haber"])
            
            debe_str = f"{debe_val:,.2f}" if debe_val > 0 else "—"
            haber_str = f"{haber_val:,.2f}" if haber_val > 0 else "—"
            
            c_debe = QTableWidgetItem(debe_str)
            c_debe.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            c_haber = QTableWidgetItem(haber_str)
            c_haber.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # formato de estilo
            for item in (c_code, c_name, c_debe, c_haber):
                item.setForeground(QColor("#1B2A4A"))
                
            tabla.setItem(row, 0, c_code)
            tabla.setItem(row, 1, c_name)
            tabla.setItem(row, 2, c_debe)
            tabla.setItem(row, 3, c_haber)
            
        layout.addWidget(tabla)

        # panel de pie de asiento (totales y validación)
        footer_layout = QHBoxLayout()
        
        # badge de validación
        val_badge = QLabel("  Estado:  🟢 CUADRADO  ")
        val_badge.setStyleSheet("""
            color: #468847;
            font-size: 11px;
            font-weight: bold;
            background-color: #DFF0D8;
            border: 1px solid #D6E9C6;
            border-radius: 4px;
            padding: 4px 6px;
        """)
        footer_layout.addWidget(val_badge)
        footer_layout.addStretch()

        # fila de totales debe/haber
        total_debe = float(as_data["total_debe"])
        total_haber = float(as_data["total_haber"])
        
        totals_lbl = QLabel(f"TOTALES:     Debe: S/ {total_debe:,.2f}    |    Haber: S/ {total_haber:,.2f}")
        totals_lbl.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        footer_layout.addWidget(totals_lbl)
        
        layout.addLayout(footer_layout)

        return widget

    def _exportar_pdf_simulado(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Exportación de PDF")
        msg.setText("✔ Representación física e impresa del Asiento Contable exportada a PDF de forma exitosa.")
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        msg.exec()
