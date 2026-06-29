from datetime import datetime
import sqlite3

DB_PATH = "sistema_facturacion.db"

class DashboardController:
    def __init__(self, model, view, cliente_model):
        self.model = model
        self.view = view
        self.cliente_model = cliente_model
        
        self.actualizar_modulo()

    def actualizar_modulo(self):
        try:
            # 1. obtener todas las facturas del modelo
            facturas = self.model.obtener_todas()
            clientes = self.cliente_model.obtener_todos()

            # determinar el periodo activo (mes/ano de la factura mas reciente o el mes/ano actual)
            if facturas:
                fechas = [datetime.strptime(f["fecha"], "%Y-%m-%d") for f in facturas]
                mas_reciente = max(fechas)
                mes_activo = mas_reciente.month
                anio_activo = mas_reciente.year
            else:
                mes_activo = datetime.now().month
                anio_activo = datetime.now().year

            nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            nombre_mes = nombres_meses[mes_activo - 1]
            self.view.lbl_periodo.setText(f"Dashboard general  |  {nombre_mes} {anio_activo}")

            # 2. calcular kpis reales del periodo activo
            # filtrar facturas del mes activo que no esten anuladas
            facturas_mes = []
            for f in facturas:
                f_date = datetime.strptime(f["fecha"], "%Y-%m-%d")
                if f_date.month == mes_activo and f_date.year == anio_activo:
                    facturas_mes.append(f)

            total_ventas = sum(float(f["total"]) for f in facturas_mes if f.get("estado") != "Anulada")

            # calcular el mes anterior para la tendencia (trend)
            if mes_activo == 1:
                mes_prev = 12
                anio_prev = anio_activo - 1
            else:
                mes_prev = mes_activo - 1
                anio_prev = anio_activo

            facturas_mes_prev = []
            for f in facturas:
                f_date = datetime.strptime(f["fecha"], "%Y-%m-%d")
                if f_date.month == mes_prev and f_date.year == anio_prev:
                    facturas_mes_prev.append(f)

            total_ventas_prev = sum(float(f["total"]) for f in facturas_mes_prev if f.get("estado") != "Anulada")

            # tendencia de ventas ()
            if total_ventas_prev > 0:
                diff_ventas_pct = ((total_ventas - total_ventas_prev) / total_ventas_prev) * 100.0
                trend_ventas = f"{'+' if diff_ventas_pct >= 0 else ''}{diff_ventas_pct:.1f}%"
            else:
                trend_ventas = "+0.0%" if total_ventas == 0 else "+100.0%"

            # contar clientes nuevos en este periodo
            clientes_nuevos = 0
            for c in clientes:
                try:
                    c_date = datetime.strptime(c["fecha_registro"].split()[0], "%Y-%m-%d")
                    if c_date.month == mes_activo and c_date.year == anio_activo:
                        clientes_nuevos += 1
                except Exception:
                    pass

            # clientes nuevos en el mes anterior para la tendencia
            clientes_nuevos_prev = 0
            for c in clientes:
                try:
                    c_date = datetime.strptime(c["fecha_registro"].split()[0], "%Y-%m-%d")
                    if c_date.month == mes_prev and c_date.year == anio_prev:
                        clientes_nuevos_prev += 1
                except Exception:
                    pass

            diff_cli = clientes_nuevos - clientes_nuevos_prev
            trend_clientes = f"{'+' if diff_cli >= 0 else ''}{diff_cli}"

            self.view.actualizar_kpis(total_ventas, clientes_nuevos, trend_ventas, trend_clientes)

            # 3. cargar la tabla de ultimas facturas emitidas (las ultimas 5)
            ultimas = facturas[:5]
            self.view.cargar_ultimas_facturas(ultimas)

            # 4. generar datos del grafico de ventas semanales de forma dinamica (ultimas 12 semanas)
            if facturas:
                fechas = [datetime.strptime(f["fecha"], "%Y-%m-%d") for f in facturas]
                fecha_max = max(fechas)
            else:
                fecha_max = datetime.now()

            # generar las ultimas 12 semanas cronologicamente
            semanas_keys = []   # lista de tuplas (year week)
            semanas_labels = [] # lista de etiquetas "sem x"
            
            from datetime import timedelta
            # retrocedemos 11 semanas hasta llegar a la actual (12 semanas en total)
            for i in range(11, -1, -1):
                dt = fecha_max - timedelta(weeks=i)
                y, w, _ = dt.isocalendar()
                if (y, w) not in semanas_keys:
                    semanas_keys.append((y, w))
                    semanas_labels.append(f"Sem {w}")

            ventas = [0.0] * len(semanas_keys)

            for f in facturas:
                try:
                    f_date = datetime.strptime(f["fecha"], "%Y-%m-%d")
                    if f.get("estado") != "Anulada":
                        y, w, _ = f_date.isocalendar()
                        if (y, w) in semanas_keys:
                            idx = semanas_keys.index((y, w))
                            ventas[idx] += float(f["total"])
                except Exception:
                    pass

            self.view.canvas.dibujar_grafico(semanas_labels, ventas)

        except Exception as e:
            print(f"[DEBUG ERROR] No se pudo actualizar el Dashboard: {e}")
