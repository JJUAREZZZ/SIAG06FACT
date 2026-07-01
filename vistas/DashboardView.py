import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QFrame, QLabel, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

#
# canvas de matplotlib incorporado con diseno premium
#
class VentasChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3.5, dpi=100):
        # crear la figura y el eje de dibujo
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = fig.add_subplot(111)
        
        # eliminar bordes para estetica limpia
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['left'].set_color('#E6E9ED')
        self.axes.spines['bottom'].set_color('#E6E9ED')
        
        # configurar colores y grid
        self.axes.tick_params(colors='#7c7c7c', labelsize=8)
        self.axes.grid(True, linestyle='--', alpha=0.4, color='#CCD1D9')
        
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()

    def dibujar_grafico(self, semanas, ventas):
        self.axes.clear()
        self.axes.grid(True, linestyle='--', alpha=0.4, color='#CCD1D9')
        
        # dibujar la linea de ventas en azul corporativo ucsm
        self.axes.plot(semanas, ventas, marker='o', color='#1B2A4A', linewidth=2, markersize=4, label="Ventas Semanales")
        
        # llenar el area debajo de la linea para un toque premium (glassmorphism/gradient effect)
        self.axes.fill_between(semanas, ventas, color='#1B2A4A', alpha=0.08)
        
        # formatear titulo y etiquetas
        self.axes.set_title("Ventas Semanales (S/.)", color='#1B2A4A', fontsize=10, fontweight='bold', pad=10)
        
        # ajustar los ejes de forma limpia
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['left'].set_color('#E6E9ED')
        self.axes.spines['bottom'].set_color('#E6E9ED')
        self.axes.tick_params(colors='#7c7c7c', labelsize=8)
        
        # rotar etiquetas del eje x si son muchas
        if len(semanas) > 10:
            self.axes.set_xticks(range(len(semanas)))
            self.axes.set_xticklabels(semanas, rotation=45, ha='right')
            
        self.draw()


#
# vista del dashboard general
#
class DashboardView(QWidget):
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
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: black; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: bold; }
            QFrame#SeccionFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #E6E9ED;
            }
            QFrame { color: black; }
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
            QPushButton { color: black; }
        """)
        self.contenido_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        contenido_layout.setSpacing(14)
        falso_layout.addWidget(self.contenido_widget)

        # 1. cabecera con nombre y periodo
        header_frame = QFrame()
        header_frame.setObjectName("SeccionFrame")
        header_frame.setStyleSheet("background-color: #E6EDF8; border: 1px solid #C0CCEA;")
        header_lay = QHBoxLayout(header_frame)
        header_lay.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_periodo = QLabel("Dashboard general  |  Mayo 2026")
        self.lbl_periodo.setStyleSheet("color: #1B2A4A; font-size: 18px; font-weight: bold;")
        header_lay.addWidget(self.lbl_periodo)
        contenido_layout.addWidget(header_frame)

        # 2. tarjetas kpis superiores (ventas del mes clientes nuevos)
        kpis_row = QHBoxLayout()
        kpis_row.setSpacing(20)

        # tarjeta ventas
        card_ventas = QFrame()
        card_ventas.setObjectName("SeccionFrame")
        ventas_lay = QVBoxLayout(card_ventas)
        ventas_lay.setContentsMargins(20, 15, 20, 15)
        
        lbl_v_title = QLabel("Total ventas del mes")
        lbl_v_title.setStyleSheet("color: #7c7c7c; font-size: 13px; font-weight: bold;")
        ventas_lay.addWidget(lbl_v_title)
        
        self.lbl_val_ventas = QLabel("S/. 0.00")
        self.lbl_val_ventas.setStyleSheet("color: #1B2A4A; font-size: 26px; font-weight: bold; margin-top: 5px;")
        ventas_lay.addWidget(self.lbl_val_ventas)
        
        self.lbl_trend_ventas = QLabel("+0.0%")
        self.lbl_trend_ventas.setStyleSheet("color: #70AD47; font-size: 14px; font-weight: bold; margin-top: 2px;")
        ventas_lay.addWidget(self.lbl_trend_ventas)
        
        kpis_row.addWidget(card_ventas)

        # tarjeta clientes
        card_clientes = QFrame()
        card_clientes.setObjectName("SeccionFrame")
        clientes_lay = QVBoxLayout(card_clientes)
        clientes_lay.setContentsMargins(20, 15, 20, 15)
        
        lbl_c_title = QLabel("Total clientes nuevos")
        lbl_c_title.setStyleSheet("color: #7c7c7c; font-size: 13px; font-weight: bold;")
        clientes_lay.addWidget(lbl_c_title)
        
        self.lbl_val_clientes = QLabel("0")
        self.lbl_val_clientes.setStyleSheet("color: #1B2A4A; font-size: 26px; font-weight: bold; margin-top: 5px;")
        clientes_lay.addWidget(self.lbl_val_clientes)
        
        self.lbl_trend_clientes = QLabel("+0")
        self.lbl_trend_clientes.setStyleSheet("color: #70AD47; font-size: 14px; font-weight: bold; margin-top: 2px;")
        clientes_lay.addWidget(self.lbl_trend_clientes)
        
        kpis_row.addWidget(card_clientes)

        contenido_layout.addLayout(kpis_row)

        # 3. tabla de ultimas facturas emitidas
        tabla_frame = QFrame()
        tabla_frame.setObjectName("SeccionFrame")
        tabla_lay = QVBoxLayout(tabla_frame)
        tabla_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_t_title = QLabel("Últimas Facturas Emitidas")
        lbl_t_title.setStyleSheet("color: #1B2A4A; font-size: 15px; font-weight: bold; margin-bottom: 5px;")
        tabla_lay.addWidget(lbl_t_title)

        self.tabla_ultimas = QTableWidget(0, 6)
        self.tabla_ultimas.setHorizontalHeaderLabels(["N° Factura", "Cliente", "Fecha", "Total", "Estado", "Notas"])
        self.tabla_ultimas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_ultimas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_ultimas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_ultimas.horizontalHeader().setStretchLastSection(True)
        self.tabla_ultimas.setFixedHeight(150)
        
        tabla_lay.addWidget(self.tabla_ultimas)
        contenido_layout.addWidget(tabla_frame)

        # 4. grafico contenedor
        grafico_frame = QFrame()
        grafico_frame.setObjectName("SeccionFrame")
        grafico_lay = QVBoxLayout(grafico_frame)
        grafico_lay.setContentsMargins(10, 10, 10, 10)
        
        self.canvas = VentasChartCanvas(grafico_frame)
        grafico_lay.addWidget(self.canvas)
        contenido_layout.addWidget(grafico_frame)
        
        contenido_layout.addStretch()

    def cargar_ultimas_facturas(self, facturas):
        self.tabla_ultimas.setRowCount(0)
        font_estado = QFont("Segoe UI", 9, QFont.Weight.Bold)
        for f in facturas:
            row = self.tabla_ultimas.rowCount()
            self.tabla_ultimas.insertRow(row)
            
            num_item = QTableWidgetItem(str(f["num_factura"]))
            cli_item = QTableWidgetItem(str(f["cliente_nombre"]))
            fec_item = QTableWidgetItem(str(f["fecha"]))
            tot_item = QTableWidgetItem(f"S/. {float(f['total']):,.2f}")
            est_item = QTableWidgetItem(str(f["estado"]))
            not_item = QTableWidgetItem(str(f.get("notas_anulacion") or ""))
            
            est_item.setFont(font_estado)
            if f["estado"] == "Anulada":
                est_item.setForeground(QColor("#C00000"))
            elif f["estado"] == "Pendiente":
                est_item.setForeground(QColor("#E67E22"))
            else:
                est_item.setForeground(QColor("#70AD47"))

            for item in (num_item, cli_item, fec_item, tot_item, not_item):
                item.setForeground(QColor("#1B2A4A"))

            self.tabla_ultimas.setItem(row, 0, num_item)
            self.tabla_ultimas.setItem(row, 1, cli_item)
            self.tabla_ultimas.setItem(row, 2, fec_item)
            self.tabla_ultimas.setItem(row, 3, tot_item)
            self.tabla_ultimas.setItem(row, 4, est_item)
            self.tabla_ultimas.setItem(row, 5, not_item)

    def actualizar_kpis(self, total_ventas, total_clientes, trend_ventas="+9.5%", trend_clientes="+3"):
        self.lbl_val_ventas.setText(f"S/. {total_ventas:,.2f}")
        self.lbl_val_clientes.setText(str(total_clientes))
        
        self.lbl_trend_ventas.setText(trend_ventas)
        self.lbl_trend_clientes.setText(trend_clientes)
        
        if '-' in trend_ventas:
            self.lbl_trend_ventas.setStyleSheet("color: #C00000; font-size: 14px; font-weight: bold;")
        else:
            self.lbl_trend_ventas.setStyleSheet("color: #70AD47; font-size: 14px; font-weight: bold;")
            
        if '-' in trend_clientes or trend_clientes == "+0":
            self.lbl_trend_clientes.setStyleSheet("color: #7c7c7c; font-size: 14px; font-weight: bold;")
        else:
            self.lbl_trend_clientes.setStyleSheet("color: #70AD47; font-size: 14px; font-weight: bold;")
