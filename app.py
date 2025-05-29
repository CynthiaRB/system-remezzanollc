from flask import Flask, render_template, request, redirect, session
app = Flask(__name__)
app.secret_key = "una_clave_super_secreta"
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta"

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        correo = request.form["correo"]
        contrasena = request.form["contrasena"]

        if correo == "andres@remezzano.com" and contrasena == "Andres2025!":
            session["admin"] = True
            return redirect("/admin")

        try:
            with open("empleados.csv", newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 7:
                        nombre, pais, tipo, costo_hora, pago_mensual, correo_emp, contrasena_emp = row
                        if correo == correo_emp and contrasena == contrasena_emp:
                            session["usuario"] = nombre
                            return redirect("/usuario")
        except FileNotFoundError:
            error = "Archivo de empleados no encontrado."

        error = "Correo o contraseña incorrectos."

    return render_template("login.html", error=error)




@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        fecha = request.form["fecha"]
        fecha_entrega = request.form["fecha_entrega"]
        cliente = request.form["cliente"]
        proyecto = request.form["proyecto"]
        precio = request.form["precio"]
        quien_trajo = request.form["quien_trajo"]
        pais = request.form["pais"]
        socios = ", ".join(request.form.getlist("socios"))
        gastos = ""  # no hay campo en el formulario, lo dejamos vacío
        empleados_seleccionados = ", ".join(request.form.getlist("empleados"))

        with open("proyectos.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([fecha, fecha_entrega, cliente, proyecto, precio, pais, socios, empleados_seleccionados, gastos,quien_trajo])

        return redirect("/admin")

    # Parte GET
    proyectos = []
    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                proyectos.append(row)

    
    empleados = []
    socios = []
    costos_por_usuario = {}

    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                empleados.append(row)
                if len(row) >= 3 and row[2].lower() == "socio":
                    socios.append(row[0])
                if len(row) >= 4:
                    try:
                        costos_por_usuario[row[0]] = float(row[3])
                    except:
                        costos_por_usuario[row[0]] = 0.0


    # Leer horas por proyecto y empleado (AQUÍ DEBE IR)
    horas_proyecto_empleado = {}
    if os.path.exists("horas.csv"):
        with open("horas.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    fecha, proyecto, usuario, descripcion, hora_inicio, hora_fin = row
                    formato = "%H:%M"
                    try:
                        inicio = datetime.strptime(hora_inicio, formato)
                        fin = datetime.strptime(hora_fin, formato)
                        diferencia = (fin - inicio).total_seconds() / 3600
                        if diferencia < 0:
                            diferencia += 24
                    except:
                        diferencia = 0

                    if proyecto not in horas_proyecto_empleado:
                        horas_proyecto_empleado[proyecto] = {}
                    if usuario not in horas_proyecto_empleado[proyecto]:
                        horas_proyecto_empleado[proyecto][usuario] = {"total": 0.0, "tareas": []}

                    horas_proyecto_empleado[proyecto][usuario]["tareas"].append([fecha, descripcion, hora_inicio, hora_fin])
                    horas_proyecto_empleado[proyecto][usuario]["total"] += diferencia

    # Cálculo de total de gastos por proyecto
    totales_gastos = {}
    for p in proyectos:
        total = 0.0
        for gasto in p[8].split(';'):
            try:
                partes = gasto.strip().rsplit(' ', 1)
                if len(partes) == 2:
                    monto = float(partes[1].replace('$', '').replace(',', '').strip())
                    total += monto
            except:
                continue
        totales_gastos[p[3]] = total

    # Finalmente el return
    return render_template("admin.html",
    proyectos=proyectos,
    socios=socios,
    empleados=empleados,
    horas_empleado=horas_proyecto_empleado,
    totales_gastos=totales_gastos,
    costos_usuarios=costos_por_usuario)




            
@app.route("/agregar_gasto", methods=["POST"])
def agregar_gasto():
    nombre_proyecto = request.form.get("proyecto_gasto")
    concepto = request.form.get("concepto_gasto", "").strip()
    monto = request.form.get("monto_gasto", "").strip()

    if not concepto or not monto:
        return redirect("/admin")

    nuevo_gasto = f"{concepto} ${monto}"
    proyectos_actualizados = []
    with open("proyectos.csv", newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[3] == nombre_proyecto:
                if row[8].strip():
                    row[8] = f"{row[8]}; {nuevo_gasto}"
                else:
                    row[8] = nuevo_gasto
            proyectos_actualizados.append(row)

    with open("proyectos.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(proyectos_actualizados)

    return redirect("/admin")



    # Leer proyectos
    proyectos = []
    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                proyectos.append(row)

    # Leer empleados
    empleados = []
    socios = []
    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                empleados.append(row)
                if len(row) >= 3 and row[2].lower() == "socio":
                    socios.append(row[0])  # nombre del socio

    return render_template("admin.html", proyectos=proyectos, socios=socios, empleados=empleados)
    
@app.route("/alta_empleado", methods=["POST"])
def alta_empleado():
    nombre = request.form["nombre"]
    pais = request.form["pais"]
    tipo = request.form["tipo"]
    costo_hora = request.form["costo_hora"]
    pago_mensual = request.form["pago_mensual"]
    correo = request.form["correo"]
    contrasena = request.form["contrasena"]

    with open("empleados.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([nombre, pais, tipo, costo_hora, pago_mensual, correo, contrasena])


    return redirect("/admin")
    
@app.route("/modificar_empleado", methods=["POST"])
def modificar_empleado():
    def normalizar(nombre):
        return nombre.strip().lower()

    original_correo = request.form["original_correo"]
    nuevo_nombre = request.form["nombre"]
    nuevos_datos = [
        nuevo_nombre,
        request.form["pais"],
        request.form["tipo"],
        request.form["costo_hora"],
        request.form["pago_mensual"],
        request.form["correo"],
        request.form["contrasena"]
    ]

    empleados_actualizados = []
    nombre_anterior = None

    # Buscar nombre anterior
    with open("empleados.csv", newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[5] == original_correo:
                nombre_anterior = row[0]
                fila_editada = nuevos_datos
                empleados_actualizados.append(fila_editada)
            else:
                empleados_actualizados.append(row)

    with open("empleados.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(empleados_actualizados)

    # Actualizar nombre en proyectos.csv
    if nombre_anterior and os.path.exists("proyectos.csv"):
        proyectos_actualizados = []
        with open("proyectos.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    empleados_lista = [e.strip() for e in row[7].split(",")]
                    empleados_nuevos = [
                        nuevo_nombre if normalizar(e) == normalizar(nombre_anterior) else e
                        for e in empleados_lista
                    ]
                    row[7] = ", ".join(empleados_nuevos)
                proyectos_actualizados.append(row)
        with open("proyectos.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(proyectos_actualizados)

    # Actualizar nombre en horas.csv
    if nombre_anterior and os.path.exists("horas.csv"):
        horas_actualizadas = []
        with open("horas.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6 and normalizar(row[2]) == normalizar(nombre_anterior):
                    row[2] = nuevo_nombre
                horas_actualizadas.append(row)
        with open("horas.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(horas_actualizadas)

    # Si es el usuario en sesión, actualiza su nombre
    if session.get("usuario", "").strip().lower() == nombre_anterior.strip().lower():
        session["usuario"] = nuevo_nombre

    return redirect("/admin")




@app.route("/eliminar_empleado", methods=["POST"])
def eliminar_empleado():
    correo = request.form["correo"]

    empleados_filtrados = []
    with open("empleados.csv", newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[5] != correo:
                empleados_filtrados.append(row)

    with open("empleados.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(empleados_filtrados)

    return redirect("/admin")

    
@app.route("/usuario")
def usuario():
    if "usuario" not in session:
        return redirect("/")

    def normalizar(nombre):
        return nombre.strip().lower()

    usuario_actual = session["usuario"]
    proyectos_usuario = []
    horas_por_proyecto = {}

    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    empleados_lista = [e.strip() for e in row[7].split(",")]
                    if any(normalizar(e) == normalizar(usuario_actual) for e in empleados_lista):
                        proyectos_usuario.append(row)
                        horas_por_proyecto[row[3]] = {
                            "tareas": [],
                            "total_horas": 0.0
                        }

    if os.path.exists("horas.csv"):
        with open("horas.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    fecha, proyecto, usuario, descripcion, hora_inicio, hora_fin = row
                    if normalizar(usuario) == normalizar(usuario_actual) and proyecto in horas_por_proyecto:
                        try:
                            inicio = datetime.strptime(hora_inicio, "%H:%M")
                            fin = datetime.strptime(hora_fin, "%H:%M")
                            diferencia = (fin - inicio).total_seconds() / 3600
                            if diferencia < 0:
                                diferencia += 24
                        except:
                            diferencia = 0

                        horas_por_proyecto[proyecto]["tareas"].append([fecha, descripcion, hora_inicio, hora_fin])
                        horas_por_proyecto[proyecto]["total_horas"] += diferencia

    return render_template("usuario.html", proyectos=proyectos_usuario, horas=horas_por_proyecto)

@app.route("/cargar_horas", methods=["POST"])
def cargar_horas():
    if "usuario" not in session:
        return redirect("/")

    usuario = session["usuario"]
    proyecto = request.form["proyecto"]
    descripcion = request.form["descripcion"]
    hora_inicio = request.form["hora_inicio"]
    hora_fin = request.form["hora_fin"]
    fecha = request.form["fecha"]

    with open("horas.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([fecha, proyecto, usuario, descripcion, hora_inicio, hora_fin])

    return redirect("/usuario")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")

@app.route("/actualizar_fecha", methods=["POST"])
def actualizar_fecha():
    proyecto_nombre = request.form["proyecto_nombre"]
    nueva_fecha = request.form["nueva_fecha"]

    proyectos_actualizados = []
    with open("proyectos.csv", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[3] == proyecto_nombre:
                row[1] = nueva_fecha  # actualiza fecha de entrega
            proyectos_actualizados.append(row)

    with open("proyectos.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(proyectos_actualizados)

    return redirect("/admin")

@app.route("/resumen_financiero")
def resumen_financiero():
    if "admin" not in session:
        return redirect("/")

    proyectos = []
    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline="") as f:
            reader = csv.reader(f)
            proyectos = list(reader)

    costos_usuarios = {}
    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4:
                    try:
                        costos_usuarios[row[0]] = float(row[3])
                    except:
                        costos_usuarios[row[0]] = 0.0

    horas_empleado = {}
    if os.path.exists("horas.csv"):
        with open("horas.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    fecha, proyecto, usuario, descripcion, hora_inicio, hora_fin = row
                    formato = "%H:%M"
                    try:
                        inicio = datetime.strptime(hora_inicio, formato)
                        fin = datetime.strptime(hora_fin, formato)
                        diferencia = (fin - inicio).total_seconds() / 3600
                        if diferencia < 0:
                            diferencia += 24
                    except:
                        diferencia = 0

                    if proyecto not in horas_empleado:
                        horas_empleado[proyecto] = {}
                    if usuario not in horas_empleado[proyecto]:
                        horas_empleado[proyecto][usuario] = 0.0
                    horas_empleado[proyecto][usuario] += diferencia

    totales = []
    for p in proyectos:
        nombre = p[3]
        precio = float(p[4])
        quien_trajo = p[9].strip()
        gastos = 0.0
        if len(p) >= 9:
            for gasto in p[8].split(";"):
                try:
                    partes = gasto.strip().rsplit(" ", 1)
                    if len(partes) == 2:
                        gastos += float(partes[1].replace("$", "").replace(",", "").strip())
                except:
                    continue

        costo_horas = 0.0
        for usuario, horas in horas_empleado.get(nombre, {}).items():
            costo_unitario = costos_usuarios.get(usuario, 0.0)
            costo_horas += horas * costo_unitario

               # Obtener tipo del usuario que trajo el proyecto
        tipo_quien_trajo = ""
        if os.path.exists("empleados.csv"):
            with open("empleados.csv", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0].strip() == quien_trajo:
                        tipo_quien_trajo = row[2].lower().strip()
                        break

        # Calcular comisión 1
        comision1 = 0.0
        comision1_texto = "Sin asignar"
        if tipo_quien_trajo == "business":
            comision1 = 0.15 * precio
            comision1_texto = f"{quien_trajo}: ${comision1:.2f}"
        elif tipo_quien_trajo == "empleado":
            comision1 = 0.15 * precio
            comision1_texto = f"{quien_trajo}: ${comision1:.2f}"
        elif tipo_quien_trajo == "socio":
            comision1 = (1/3) * precio
            comision1_texto = f"{quien_trajo}: ${comision1:.2f}"
        
      
        # Obtener socios participantes
        socios_lista = p[6].split(",") if len(p) > 6 else []
        socios_participantes = [s.strip() for s in socios_lista if s.strip()]
        num_socios = len(socios_participantes)

        # Calcular Comisión 2
        #comision2 = (precio / 3) / num_socios if num_socios > 0 else 0.0
        comision2_texto = "Sin socios"
        if num_socios > 0:
            monto_por_socio = (precio / 3) / num_socios
            comision2_texto = "; ".join([f"{s}: ${monto_por_socio:.2f}" for s in socios_participantes])
            comision2 = monto_por_socio * num_socios # aún usamos para rentabilidad
        else:
            comision2 = 0.0




        rentabilidad = precio - comision1 - comision2 - gastos - costo_horas

                # Obtener país del proyecto
        pais_proyecto = p[5].strip().lower()

        # Mapas de reparto por país
        participaciones = {
            "méxico": {"Javier Adaya": 0.15, "Andres Remezzano": 0.85},
            "usa": {"Andres Remezzano": 1.0},
            "perú": {"Andres Remezzano": 0.6, "Martin Zuñiga": 0.2, "Daniel Barra": 0.2},
            "argentina": {
                "Andres Remezzano": 0.55,
                "Ornella Bilo": 0.15,
                "Lucas Iturriaga": 0.15,
                "Lilen Acosta": 0.15
            }
        }

        # Calcular comisión 3 por socio
        comision3_detalle = []
        if pais_proyecto in participaciones:
            for socio, porcentaje in participaciones[pais_proyecto].items():
                monto = rentabilidad * porcentaje
                comision3_detalle.append(f"{socio}: ${monto:.2f}")
        else:
            comision3_detalle.append("Sin reparto definido")

        # Convertir a texto
        comision3_texto = "; ".join(comision3_detalle)

        cliente = p[2]  # nuevo campo
        totales.append([
            cliente,
            nombre,
            f"${precio:.2f}",
            comision1_texto,    # r[3]
            comision2_texto,    # r[4]
            f"${gastos:.2f}",
            f"${costo_horas:.2f}",
            f"${rentabilidad:.2f}",
            comision3_texto
        ])

    return render_template("resumen_financiero.html", resumen=totales)

@app.route("/resumen_usuarios")
def resumen_usuarios():
    if "admin" not in session:
        return redirect("/")

    empleados = {}
    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4:
                    try:
                        costo = float(row[3])
                    except:
                        costo = 0.0
                    empleados[row[0]] = {
                        "nombre": row[0],
                        "costo_hora": costo,
                       "proyectos": {},
                        "total_horas": 0.0,
                        "total_pago": 0.0
                    }

        # Mapear empleados a proyectos
    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    proyecto = row[3]
                    usuarios = [e.strip() for e in row[7].split(",") if e.strip()]
                    for u in usuarios:
                        if u in empleados:
                            cliente = row[2]
                            if proyecto not in empleados[u]["proyectos"]:
                                empleados[u]["proyectos"][proyecto] = {"cliente": cliente, "horas": 0.0, "pago": 0.0}



    if os.path.exists("horas.csv"):
        with open("horas.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    fecha, proyecto, usuario, desc, inicio, fin = row
                    try:
                        h1 = datetime.strptime(inicio, "%H:%M")
                        h2 = datetime.strptime(fin, "%H:%M")
                        horas = (h2 - h1).total_seconds() / 3600
                        if horas < 0:
                            horas += 24
                    except:
                        horas = 0
                    if usuario in empleados:
                        emp = empleados[usuario]
                        emp["total_horas"] += horas
                        emp["total_pago"] += horas * emp["costo_hora"]
                        if proyecto not in emp["proyectos"]:
                            emp["proyectos"][proyecto] = {"cliente": "", "horas": 0.0, "pago": 0.0}

                    emp["proyectos"][proyecto]["horas"] += horas
                    emp["proyectos"][proyecto]["pago"] += horas * emp["costo_hora"]

    return render_template("resumen_usuarios.html", empleados=list(empleados.values()))

@app.route("/performance")
def performance():
    if "admin" not in session:
        return redirect("/")

    proyectos_por_pais = {}
    utilidad_por_pais = {}
    horas_por_empleado = {}
    gastos_total = 0
    costos_total = 0

    # Leer costos por usuario
    if os.path.exists("empleados.csv"):
        costos = {r[0]: float(r[3]) if r[3] else 0 for r in csv.reader(open("empleados.csv")) if len(r) >= 4}
    else:
        costos = {}

    # Leer horas y sumar por usuario
    horas_por_proyecto_usuario = {}
    if os.path.exists("horas.csv"):
        with open("horas.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 6:
                    _, proyecto, usuario, _, h_inicio, h_fin = row
                    try:
                        h1 = datetime.strptime(h_inicio, "%H:%M")
                        h2 = datetime.strptime(h_fin, "%H:%M")
                        horas = (h2 - h1).total_seconds() / 3600
                        if horas < 0: horas += 24
                    except:
                        horas = 0

                    horas_por_empleado[usuario] = horas_por_empleado.get(usuario, 0) + horas
                    costos_total += horas * costos.get(usuario, 0)

                    if proyecto not in horas_por_proyecto_usuario:
                        horas_por_proyecto_usuario[proyecto] = {}
                    horas_por_proyecto_usuario[proyecto][usuario] = horas_por_proyecto_usuario[proyecto].get(usuario, 0) + horas

    # Leer proyectos y calcular rentabilidad por país
    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) < 10:
                    continue
                _, _, _, nombre, precio_str, pais, _, _, gastos_str, quien_trajo = row
                pais = pais.strip()
                proyectos_por_pais[pais] = proyectos_por_pais.get(pais, 0) + 1
                precio = float(precio_str)
                gastos = 0.0
                for g in gastos_str.split(";"):
                    try:
                        gastos += float(g.strip().rsplit(" ", 1)[-1].replace("$", ""))
                    except:
                        continue

                costo_horas = 0.0
                for usuario, horas in horas_por_proyecto_usuario.get(nombre, {}).items():
                    costo_horas += horas * costos.get(usuario, 0)

                # Comisión 1 y 2 simplificada: asumimos 15% + 15% (30%)
                comisiones = 0.30 * precio

                utilidad = precio - comisiones - gastos - costo_horas
                utilidad_por_pais[pais] = utilidad_por_pais.get(pais, 0) + utilidad

    proyectos_por_tipo_usuario = {}

    # Crear mapa de tipo por usuario
    tipo_por_usuario = {}
    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 3:
                    tipo_por_usuario[row[0].strip()] = row[2].strip().capitalize()

    # Contar proyectos por tipo
    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 10:
                    quien = row[9].strip()
                    tipo = tipo_por_usuario.get(quien, "Desconocido")
                    proyectos_por_tipo_usuario[tipo] = proyectos_por_tipo_usuario.get(tipo, 0) + 1

    precios_por_pais = {}

    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 6:
                    pais = row[5].strip()
                    try:
                        precio = float(row[4])
                        precios_por_pais[pais] = precios_por_pais.get(pais, 0) + precio
                    except:
                        continue

    horas_por_pais = {}

    # Mapear país por empleado
    pais_por_usuario = {}
    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    pais_por_usuario[row[0].strip()] = row[1].strip()

    # Sumar horas por país
    for usuario, horas in horas_por_empleado.items():
        pais = pais_por_usuario.get(usuario, "Desconocido")
        horas_por_pais[pais] = horas_por_pais.get(pais, 0) + horas


    comisiones_por_tipo = {"Socio": 0, "Empleado": 0, "Business": 0, "Desconocido": 0}

    if os.path.exists("proyectos.csv") and os.path.exists("empleados.csv"):
        tipo_por_usuario = {}
        with open("empleados.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 3:
                    tipo_por_usuario[row[0].strip()] = row[2].strip().capitalize()

        with open("proyectos.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 10:
                    precio = float(row[4])
                    quien = row[9].strip()
                    tipo = tipo_por_usuario.get(quien, "Desconocido")

                    if tipo == "Socio":
                        comision = precio / 3
                    elif tipo in ["Empleado", "Business"]:
                        comision = 0.15 * precio
                    else:
                        comision = 0

                    comisiones_por_tipo[tipo] = comisiones_por_tipo.get(tipo, 0) + comision


    rentabilidad_por_cliente = {}

    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline='') as f:
            for row in csv.reader(f):
                if len(row) < 10:
                    continue
                cliente = row[2].strip()
                precio = float(row[4])
                gastos_str = row[8]
                nombre_proyecto = row[3]
                quien_trajo = row[9].strip()

                # Cálculo de gastos
                gastos = 0.0
                for g in gastos_str.split(";"):
                    try:
                        gastos += float(g.strip().rsplit(" ", 1)[-1].replace("$", ""))
                    except:
                        continue

                # Costo por horas trabajadas
                costo_horas = 0.0
                for usuario, horas in horas_por_proyecto_usuario.get(nombre_proyecto, {}).items():
                    costo_horas += horas * costos.get(usuario, 0)

                # Comisiones simplificadas: 15% + 15%
                comisiones = 0.30 * precio
                utilidad = precio - comisiones - gastos - costo_horas

                rentabilidad_por_cliente[cliente] = rentabilidad_por_cliente.get(cliente, 0) + utilidad



    return render_template("performance.html",
        proyectos_por_pais=proyectos_por_pais,
        horas_por_empleado=horas_por_empleado,
        gastos=gastos_total,
        costos=costos_total,
        utilidad_por_pais=utilidad_por_pais,
        proyectos_por_tipo_usuario=proyectos_por_tipo_usuario,
        precios_por_pais=precios_por_pais,
        horas_por_pais=horas_por_pais,
        comisiones_por_tipo=comisiones_por_tipo,
        rentabilidad_por_cliente=rentabilidad_por_cliente
    )

@app.route("/descargar_resumen_financiero")
def descargar_resumen_financiero():
    import io
    import pandas as pd
    from flask import send_file

    columnas = [
        "Cliente", "Proyecto", "Precio", "Comisión 1", "Comisión 2",
        "Total Gastos", "Costo de Horas", "Rentabilidad Neta", "Comisión 3"
    ]

    resumen = []

    if os.path.exists("proyectos.csv") and os.path.exists("empleados.csv") and os.path.exists("horas.csv"):
        costos_usuarios = {}
        with open("empleados.csv", newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 4:
                    try:
                        costos_usuarios[row[0]] = float(row[3])
                    except:
                        costos_usuarios[row[0]] = 0.0

        horas_empleado = {}
        with open("horas.csv", newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 6:
                    fecha, proyecto, usuario, desc, h1, h2 = row
                    try:
                        t1 = datetime.strptime(h1, "%H:%M")
                        t2 = datetime.strptime(h2, "%H:%M")
                        horas = (t2 - t1).total_seconds() / 3600
                        if horas < 0:
                            horas += 24
                    except:
                        horas = 0

                    if proyecto not in horas_empleado:
                        horas_empleado[proyecto] = {}
                    if usuario not in horas_empleado[proyecto]:
                        horas_empleado[proyecto][usuario] = 0.0
                    horas_empleado[proyecto][usuario] += horas

        with open("proyectos.csv", newline="") as f:
            for row in csv.reader(f):
                if len(row) < 10:
                    continue
                cliente = row[2]
                nombre = row[3]
                try:
                    precio = float(row[4])
                except:
                    continue
                pais = row[5].strip().lower()
                socios_txt = row[6]
                gastos_txt = row[8]
                quien_trajo = row[9].strip()

                # Calcular gastos
                gastos = 0.0
                for g in gastos_txt.split(";"):
                    try:
                        gastos += float(g.strip().rsplit(" ", 1)[-1].replace("$", ""))
                    except:
                        continue

                # Costo por horas
                costo_horas = 0.0
                for usuario, horas in horas_empleado.get(nombre, {}).items():
                    costo_unitario = costos_usuarios.get(usuario, 0.0)
                    costo_horas += horas * costo_unitario

                # Comisión 1
                tipo_quien = ""
                with open("empleados.csv", newline="") as f2:
                    for r in csv.reader(f2):
                        if r[0].strip() == quien_trajo and len(r) >= 3:
                            tipo_quien = r[2].strip().lower()
                            break

                if tipo_quien == "socio":
                    comision1 = (1/3) * precio
                elif tipo_quien in ["empleado", "business"]:
                    comision1 = 0.15 * precio
                else:
                    comision1 = 0.0
                com1_txt = f"{quien_trajo}: ${comision1:.2f}" if comision1 else "Sin asignar"

                # Comisión 2
                socios = [s.strip() for s in socios_txt.split(",") if s.strip()]
                comision2 = 0.0
                if socios:
                    monto = (precio / 3) / len(socios)
                    com2_txt = "; ".join([f"{s}: ${monto:.2f}" for s in socios])
                    comision2 = monto * len(socios)
                else:
                    com2_txt = "Sin socios"

                # Rentabilidad neta
                rentabilidad = precio - comision1 - comision2 - gastos - costo_horas

                # Comisión 3 por país
                participaciones = {
                    "méxico": {"Javier Adaya": 0.15, "Andres Remezzano": 0.85},
                    "usa": {"Andres Remezzano": 1.0},
                    "perú": {"Andres Remezzano": 0.6, "Martin Zuñiga": 0.2, "Daniel Barra": 0.2},
                    "argentina": {
                        "Andres Remezzano": 0.55,
                        "Ornella Bilo": 0.15,
                        "Lucas Iturriaga": 0.15,
                        "Lilen Acosta": 0.15
                    }
                }

                com3 = []
                if pais in participaciones:
                    for socio, pct in participaciones[pais].items():
                        com3.append(f"{socio}: ${rentabilidad * pct:.2f}")
                else:
                    com3.append("Sin reparto definido")

                resumen.append([
                    cliente, nombre, f"${precio:.2f}", com1_txt, com2_txt,
                    f"${gastos:.2f}", f"${costo_horas:.2f}", f"${rentabilidad:.2f}", "; ".join(com3)
                ])

    if not resumen:
        return "No hay datos para exportar."

    df = pd.DataFrame(resumen, columns=columnas)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resumen")

    output.seek(0)
    return send_file(output, as_attachment=True, download_name="resumen_financiero.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/alta_empleado", methods=["POST"])
def alta_empleado():
    nombre = request.form["nombre"]
    pais = request.form["pais"]
    tipo = request.form["tipo"]
    costo_hora = request.form["costo_hora"]
    salario_mensual = request.form["salario_mensual"]
    correo = request.form["correo"]
    password = request.form["password"]

    with open("empleados.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([nombre, pais, tipo, costo_hora, salario_mensual, correo, password])

    return redirect("/admin")


@app.route("/descargar_resumen_usuarios")
def descargar_resumen_usuarios():
    import io
    import pandas as pd
    from flask import send_file

    empleados = []

    if os.path.exists("empleados.csv"):
        with open("empleados.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4:
                    try:
                        costo = float(row[3])
                    except:
                        costo = 0.0
                    empleados.append({
                        "nombre": row[0],
                        "costo_hora": costo,
                        "proyectos": {},
                        "total_horas": 0.0,
                        "total_pago": 0.0
                    })

    empleados_dict = {e["nombre"]: e for e in empleados}

    if os.path.exists("proyectos.csv"):
        with open("proyectos.csv", newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 8:
                    cliente = row[2]
                    proyecto = row[3]
                    usuarios = [e.strip() for e in row[7].split(",") if e.strip()]
                    for u in usuarios:
                        if u in empleados_dict:
                            if proyecto not in empleados_dict[u]["proyectos"]:
                                empleados_dict[u]["proyectos"][proyecto] = {"cliente": cliente, "horas": 0.0, "pago": 0.0}

    if os.path.exists("horas.csv"):
        with open("horas.csv", newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 6:
                    fecha, proyecto, usuario, desc, inicio, fin = row
                    try:
                        h1 = datetime.strptime(inicio, "%H:%M")
                        h2 = datetime.strptime(fin, "%H:%M")
                        horas = (h2 - h1).total_seconds() / 3600
                        if horas < 0:
                            horas += 24
                    except:
                        horas = 0

                    if usuario in empleados_dict:
                        emp = empleados_dict[usuario]
                        emp["total_horas"] += horas
                        emp["total_pago"] += horas * emp["costo_hora"]
                        if proyecto not in emp["proyectos"]:
                            emp["proyectos"][proyecto] = {"cliente": "", "horas": 0.0, "pago": 0.0}
                        emp["proyectos"][proyecto]["horas"] += horas
                        emp["proyectos"][proyecto]["pago"] += horas * emp["costo_hora"]

    # Crear DataFrame
    filas = []
    for emp in empleados_dict.values():
        for proyecto, data in emp["proyectos"].items():
            filas.append([
                emp["nombre"],
                proyecto,
                data["cliente"],
                round(data["horas"], 2),
                round(data["pago"], 2)
            ])
        # Fila total
        filas.append([
            emp["nombre"],
            "TOTAL",
            "",
            round(emp["total_horas"], 2),
            round(emp["total_pago"], 2)
        ])

    df = pd.DataFrame(filas, columns=["Usuario", "Proyecto", "Cliente", "Horas", "Pago"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resumen Usuarios")
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="resumen_usuarios.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/alta_proyecto", methods=["POST"])
def alta_proyecto():
    fecha = request.form["fecha"]
    fecha_entrega = request.form["fecha_entrega"]
    cliente = request.form["cliente"]
    proyecto = request.form["proyecto"]
    precio = request.form["precio"]
    quien_trajo = request.form["quien_trajo"]
    pais = request.form["pais"]
    socios = ", ".join(request.form.getlist("socios"))
    gastos = ""  # Placeholder
    empleados_seleccionados = ", ".join(request.form.getlist("empleados"))

    with open("proyectos.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([fecha, fecha_entrega, cliente, proyecto, precio, pais, socios, empleados_seleccionados, gastos, quien_trajo])

    return redirect("/admin")

@app.route("/eliminar_proyecto", methods=["POST"])
def eliminar_proyecto():
    nombre_proyecto = request.form.get("proyecto")

    # 1. Eliminar del archivo proyectos.csv
    proyectos_filtrados = []
    with open("proyectos.csv", newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[3] != nombre_proyecto:
                proyectos_filtrados.append(row)

    with open("proyectos.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(proyectos_filtrados)

    # 2. Eliminar horas asociadas al proyecto
    if os.path.exists("horas.csv"):
        horas_filtradas = []
        with open("horas.csv", newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[1] != nombre_proyecto:
                    horas_filtradas.append(row)

        with open("horas.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(horas_filtradas)

    return redirect("/admin")



if __name__ == "__main__":
    app.run()

