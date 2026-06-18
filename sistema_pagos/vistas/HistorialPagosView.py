import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFrame, QLabel, QComboBox, QAbstractItemView, QSizePolicy,
                             QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

class HistorialPagosView(QWidget):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        falso_layout = QHBoxLayout(self)
        falso_layout.setContentsMargins(0, 0, 0, 0)
        falso_layout.setSpacing(0)

        self.contenido_widget = QWidget()
        self.contenido_widget.setObjectName("ContenidoWidget")
        self.contenido_widget.setStyleSheet("""
            QWidget#ContenidoWidget { background-color: #F4F6F9; }
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: #1B2A4A; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: bold; }
            QLineEdit {
                padding: 5px 8px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 28px;
            }
            QLineEdit:focus { border: 1.5px solid #1B2A4A; }
            QComboBox {
                padding: 5px;
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
            }
            QTableWidget::item { color: black; background-color: white; }
            QTableWidget::item:selected { background-color: #E6E9ED; color: #1B2A4A; }
            QHeaderView::section {
                background-color: #1B2A4A;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
        
        self.contenido_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        contenido_layout.setSpacing(14)
        falso_layout.addWidget(self.contenido_widget)

        # 1. cabecera
        self.lbl_titulo = QLabel("Historial de Recibos de Caja (Cobros)")
        self.lbl_titulo.setStyleSheet("color: #1B2A4A; font-size: 20px; font-weight: bold;")
        contenido_layout.addWidget(self.lbl_titulo)

        # 2. barra de filtros
        filters_frame = QFrame()
        filters_frame.setObjectName("SeccionFrame")
        filters_lay = QHBoxLayout(filters_frame)
        filters_lay.setContentsMargins(15, 10, 15, 10)
        filters_lay.setSpacing(15)

        # buscar
        bus_lay = QVBoxLayout()
        bus_lay.addWidget(QLabel("Búsqueda por recibo, factura o cliente:"))
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Ej: R001-00001, F001-00001 o Juan...")
        bus_lay.addWidget(self.input_buscar)
        filters_lay.addLayout(bus_lay, 5)

        # filtro fecha
        fec_lay = QVBoxLayout()
        fec_lay.addWidget(QLabel("Rango de fechas:"))
        self.combo_fecha = QComboBox()
        self.combo_fecha.addItems(["Todos", "Hoy", "Esta Semana", "Este Mes"])
        fec_lay.addWidget(self.combo_fecha)
        filters_lay.addLayout(fec_lay, 2)

        # acciones
        act_lay = QVBoxLayout()
        act_lay.addWidget(QLabel("Acciones:"))
        
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(8)
        
        self.btn_ver_asiento = QPushButton("Ver Asiento")
        self.btn_ver_asiento.setStyleSheet("QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2C3E6B; }")
        
        self.btn_anular = QPushButton("Anular Recibo")
        self.btn_anular.setStyleSheet("QPushButton { background-color: #C00000; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #A00000; }")
        
        btn_lay.addWidget(self.btn_ver_asiento)
        btn_lay.addWidget(self.btn_anular)
        act_lay.addLayout(btn_lay)
        filters_lay.addLayout(act_lay, 4)

        contenido_layout.addWidget(filters_frame)

        # 3. tabla principal
        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(["N° Recibo", "Factura Ref.", "Cliente", "DNI/RUC", "Fecha Cobro", "Método Pago", "Monto Cobrado", "Estado"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setStyleSheet("""
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
        
        hdr = self.tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        
        self.tabla.setColumnWidth(0, 95)
        self.tabla.setColumnWidth(1, 95)
        self.tabla.setColumnWidth(3, 95)
        self.tabla.setColumnWidth(4, 95)
        self.tabla.setColumnWidth(5, 120)
        self.tabla.setColumnWidth(6, 110)
        self.tabla.setColumnWidth(7, 85)

        contenido_layout.addWidget(self.tabla)

        # 4. fila inferior
        bottom_layout = QHBoxLayout()
        
        # paginación
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

        # resumen
        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 15px;")
        resumen_lay = QVBoxLayout(resumen_frame)
        resumen_lay.setSpacing(6)
        
        self.lbl_resumen_total = QLabel("Total Recaudado: S/ 0.00")
        self.lbl_resumen_total.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        self.lbl_resumen_recibos = QLabel("Recibos Emitidos: 0")
        self.lbl_resumen_recibos.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        
        resumen_lay.addWidget(self.lbl_resumen_total)
        resumen_lay.addWidget(self.lbl_resumen_recibos)
        
        bottom_layout.addWidget(resumen_frame)
        contenido_layout.addLayout(bottom_layout)

    def cargar_tabla(self, pagos):
        self.tabla.setRowCount(0)
        font_estado = QFont("Segoe UI", 9, QFont.Weight.Bold)
        
        for p in pagos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            num_rec = QTableWidgetItem(str(p["num_pago"]))
            num_fac = QTableWidgetItem(str(p["num_factura"]))
            cli_nom = QTableWidgetItem(str(p["cliente_nombre"]))
            doc_cli = QTableWidgetItem(str(p["dni_ruc"]))
            fec_pag = QTableWidgetItem(str(p["fecha"]))
            met_pag = QTableWidgetItem(str(p["metodo_pago"]))
            
            monto_val = float(p["monto"])
            mon_item = QTableWidgetItem(f"S/ {monto_val:,.2f}")
            mon_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            est_val = str(p.get("estado", "Emitido"))
            est_item = QTableWidgetItem(est_val)
            est_item.setFont(font_estado)
            est_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if est_val == "Anulado":
                est_item.setForeground(QColor("#C00000"))
            else:
                est_item.setForeground(QColor("#70AD47"))
            
            for item in (num_rec, num_fac, cli_nom, doc_cli, fec_pag, met_pag, mon_item):
                item.setForeground(QColor("#1B2A4A"))
                
            self.tabla.setItem(row, 0, num_rec)
            self.tabla.setItem(row, 1, num_fac)
            self.tabla.setItem(row, 2, cli_nom)
            self.tabla.setItem(row, 3, doc_cli)
            self.tabla.setItem(row, 4, fec_pag)
            self.tabla.setItem(row, 5, met_pag)
            self.tabla.setItem(row, 6, mon_item)
            self.tabla.setItem(row, 7, est_item)

    def obtener_pago_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila != -1:
            # retorna num_pago, num_factura
            return self.tabla.item(fila, 0).text(), self.tabla.item(fila, 1).text()
        return None

    def actualizar_resumen(self, total_recaudado, cantidad_recibos):
        self.lbl_resumen_total.setText(f"Total Recaudado: S/ {total_recaudado:,.2f}")
        self.lbl_resumen_recibos.setText(f"Recibos Emitidos: {cantidad_recibos}")
