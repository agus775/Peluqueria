from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__, template_folder="Templates")

app.secret_key = "clave_secreta_barberia"


# ==========================
# CONEXIÓN A MYSQL
# ==========================

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin12345",
        database="pelu",
        port=3307
    )


# ==========================
# PÁGINA PRINCIPAL
# ==========================

# Esta es la página PÚBLICA.
# No necesita usuario ni contraseña.

@app.route("/")
def inicio():
    return redirect(url_for("reservar"))


# ==========================
# LOGIN DEL BARBERO
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE usuario = %s
            AND password = %s
        """, (usuario, password))

        usuario_db = cursor.fetchone()

        cursor.close()
        conexion.close()

        if usuario_db:

            session["usuario"] = usuario_db["usuario"]

            return redirect(url_for("index"))

        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos"
        )

    return render_template("login.html")


# ==========================
# CERRAR SESIÓN
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("reservar"))


# ==========================
# PANEL DEL BARBERO
# ==========================

@app.route("/panel")
def index():

    # SOLO EL BARBERO PUEDE ENTRAR
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.id_turno,
            c.nombre,
            c.apellido,
            e.nombre AS empleado,
            s.nombre AS servicio,
            s.precio,
            t.fecha,
            t.hora,
            t.estado
        FROM turnos t
        JOIN clientes c
            ON t.id_cliente = c.id_cliente
        JOIN empleados e
            ON t.id_empleado = e.id_empleado
        JOIN servicios s
            ON t.id_servicio = s.id_servicio
        ORDER BY t.fecha, t.hora
    """)

    turnos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "index.html",
        turnos=turnos
    )


# ==========================
# NUEVO TURNO - BARBERO
# ==========================

@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():

    # SOLO puede entrar el barbero
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        dni = request.form["dni"]
        telefono = request.form["telefono"]

        empleado = request.form["empleado"]
        servicio = request.form["servicio"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]

        # ==========================
        # BUSCAR CLIENTE
        # ==========================

        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE dni = %s
        """, (dni,))

        cliente = cursor.fetchone()

        # ==========================
        # CREAR CLIENTE SI NO EXISTE
        # ==========================

        if cliente is None:

            cursor.execute("""
                INSERT INTO clientes
                (nombre, apellido, dni, telefono)
                VALUES (%s, %s, %s, %s)
            """, (
                nombre,
                apellido,
                dni,
                telefono
            ))

            conexion.commit()

            id_cliente = cursor.lastrowid

        else:

            id_cliente = cliente["id_cliente"]

        # ==========================
        # CREAR TURNO
        # ==========================

        cursor.execute("""
            INSERT INTO turnos
            (id_cliente, id_empleado, id_servicio, fecha, hora)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            id_cliente,
            empleado,
            servicio,
            fecha,
            hora
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        # IMPORTANTE:
        # Después de reservar como BARBERO
        # va a la confirmación del BARBERO

        return redirect(url_for(
            "turno_confirmado_barber",
            nombre=nombre,
            apellido=apellido,
            empleado=empleado,
            servicio=servicio,
            fecha=fecha,
            hora=hora
        ))

    # ==========================
    # EMPLEADOS
    # ==========================

    cursor.execute("SELECT * FROM empleados")
    empleados = cursor.fetchall()

    # ==========================
    # SERVICIOS
    # ==========================

    cursor.execute("SELECT * FROM servicios")
    servicios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "reservar_barber.html",
        empleados=empleados,
        servicios=servicios
    )


# ==========================
# TURNO CONFIRMADO - BARBERO
# ==========================

@app.route("/turno-confirmado-barber")
def turno_confirmado_barber():

    # SOLO puede verla el barbero
    if "usuario" not in session:
        return redirect(url_for("login"))

    nombre = request.args.get("nombre")
    apellido = request.args.get("apellido")

    empleado_id = request.args.get("empleado")
    servicio_id = request.args.get("servicio")

    fecha = request.args.get("fecha")
    hora = request.args.get("hora")

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # ==========================
    # BUSCAR EMPLEADO
    # ==========================

    cursor.execute("""
        SELECT nombre
        FROM empleados
        WHERE id_empleado = %s
    """, (empleado_id,))

    empleado_db = cursor.fetchone()

    # ==========================
    # BUSCAR SERVICIO
    # ==========================

    cursor.execute("""
        SELECT nombre, precio
        FROM servicios
        WHERE id_servicio = %s
    """, (servicio_id,))

    servicio_db = cursor.fetchone()

    cursor.close()
    conexion.close()

    if empleado_db:
        empleado_nombre = empleado_db["nombre"]
    else:
        empleado_nombre = "No encontrado"

    if servicio_db:
        servicio_nombre = servicio_db["nombre"]
        precio = servicio_db["precio"]
    else:
        servicio_nombre = "No encontrado"
        precio = 0

    return render_template(
        "turno_confirmado_barber.html",
        nombre=nombre,
        apellido=apellido,
        empleado=empleado_nombre,
        servicio=servicio_nombre,
        precio=precio,
        fecha=fecha,
        hora=hora
    )


# ==========================
# RESERVAR TURNO - CLIENTE
# ==========================

# ESTA RUTA ES PÚBLICA.
# NO TIENE LOGIN.
# NO TIENE SESSION.

@app.route("/reservar", methods=["GET", "POST"])
def reservar():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        dni = request.form["dni"]
        telefono = request.form["telefono"]

        empleado = request.form["empleado"]
        servicio = request.form["servicio"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]

        # ==========================
        # BUSCAR CLIENTE
        # ==========================

        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE dni = %s
        """, (dni,))

        cliente = cursor.fetchone()

        # ==========================
        # CREAR CLIENTE
        # ==========================

        if cliente is None:

            cursor.execute("""
                INSERT INTO clientes
                (nombre, apellido, dni, telefono)
                VALUES (%s, %s, %s, %s)
            """, (
                nombre,
                apellido,
                dni,
                telefono
            ))

            conexion.commit()

            id_cliente = cursor.lastrowid

        else:

            id_cliente = cliente["id_cliente"]

        # ==========================
        # CREAR TURNO
        # ==========================

        cursor.execute("""
            INSERT INTO turnos
            (id_cliente, id_empleado, id_servicio, fecha, hora)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            id_cliente,
            empleado,
            servicio,
            fecha,
            hora
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        # Mandar al turno confirmado
        return redirect(url_for(
            "turno_confirmado",
            nombre=nombre,
            apellido=apellido,
            empleado=empleado,
            servicio=servicio,
            fecha=fecha,
            hora=hora
        ))

    # ==========================
    # MOSTRAR EMPLEADOS
    # ==========================

    cursor.execute("SELECT * FROM empleados")
    empleados = cursor.fetchall()

    # ==========================
    # MOSTRAR SERVICIOS
    # ==========================

    cursor.execute("SELECT * FROM servicios")
    servicios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "reservar.html",
        empleados=empleados,
        servicios=servicios
    )


# ==========================
# TURNO CONFIRMADO
# ==========================

@app.route("/turno-confirmado")
def turno_confirmado():

    nombre = request.args.get("nombre")
    apellido = request.args.get("apellido")

    empleado_id = request.args.get("empleado")
    servicio_id = request.args.get("servicio")

    fecha = request.args.get("fecha")
    hora = request.args.get("hora")

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Buscar empleado
    cursor.execute("""
        SELECT nombre
        FROM empleados
        WHERE id_empleado = %s
    """, (empleado_id,))

    empleado_db = cursor.fetchone()

    # Buscar servicio
    cursor.execute("""
        SELECT nombre, precio
        FROM servicios
        WHERE id_servicio = %s
    """, (servicio_id,))

    servicio_db = cursor.fetchone()

    cursor.close()
    conexion.close()

    if empleado_db:
        empleado_nombre = empleado_db["nombre"]
    else:
        empleado_nombre = "No encontrado"

    if servicio_db:
        servicio_nombre = servicio_db["nombre"]
        precio = servicio_db["precio"]
    else:
        servicio_nombre = "No encontrado"
        precio = 0

    return render_template(
        "turno_confirmado.html",
        nombre=nombre,
        apellido=apellido,
        empleado=empleado_nombre,
        servicio=servicio_nombre,
        precio=precio,
        fecha=fecha,
        hora=hora
    )


# ==========================
# ELIMINAR
# ==========================

@app.route("/eliminar/<int:id>")
def eliminar(id):

    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM turnos WHERE id_turno = %s",
        (id,)
    )

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(url_for("index"))


# ==========================
# EDITAR
# ==========================

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        empleado = request.form["empleado"]
        servicio = request.form["servicio"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        estado = request.form["estado"]

        cursor.execute("""
            UPDATE turnos
            SET
                id_empleado = %s,
                id_servicio = %s,
                fecha = %s,
                hora = %s,
                estado = %s
            WHERE id_turno = %s
        """, (
            empleado,
            servicio,
            fecha,
            hora,
            estado,
            id
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for("index"))

    # Buscar turno
    cursor.execute("""
        SELECT *
        FROM turnos
        WHERE id_turno = %s
    """, (id,))

    turno = cursor.fetchone()

    # Empleados
    cursor.execute("SELECT * FROM empleados")
    empleados = cursor.fetchall()

    # Servicios
    cursor.execute("SELECT * FROM servicios")
    servicios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "editar_turno.html",
        turno=turno,
        empleados=empleados,
        servicios=servicios
    )


# ==========================
# BUSCAR
# ==========================

@app.route("/buscar", methods=["POST"])
def buscar():

    if "usuario" not in session:
        return redirect(url_for("login"))

    texto = request.form["buscar"]

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.id_turno,
            c.nombre,
            c.apellido,
            e.nombre AS empleado,
            s.nombre AS servicio,
            s.precio,
            t.fecha,
            t.hora,
            t.estado
        FROM turnos t
        JOIN clientes c
            ON t.id_cliente = c.id_cliente
        JOIN empleados e
            ON t.id_empleado = e.id_empleado
        JOIN servicios s
            ON t.id_servicio = s.id_servicio
        WHERE
            c.nombre LIKE %s
            OR c.apellido LIKE %s
    """, (
        "%" + texto + "%",
        "%" + texto + "%"
    ))

    turnos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "index.html",
        turnos=turnos
    )


# ==========================
# EJECUTAR
# ==========================

if __name__ == "__main__":
    app.run(debug=True)