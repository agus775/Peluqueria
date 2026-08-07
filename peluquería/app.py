from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# ==========================
# CONEXIÓN A MYSQL
# ==========================

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="pelu"
    )

# ==========================
# INICIO
# ==========================

@app.route("/")
def index():

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
        ON t.id_cliente=c.id_cliente
    JOIN empleados e
        ON t.id_empleado=e.id_empleado
    JOIN servicios s
        ON t.id_servicio=s.id_servicio
    ORDER BY t.fecha,t.hora
    """)

    turnos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("index.html",turnos=turnos)

# ==========================
# NUEVO TURNO
# ==========================

@app.route("/nuevo",methods=["GET","POST"])
def nuevo():

    conexion=conectar()
    cursor=conexion.cursor(dictionary=True)

    if request.method=="POST":

        nombre=request.form["nombre"]
        apellido=request.form["apellido"]
        dni=request.form["dni"]
        telefono=request.form["telefono"]

        empleado=request.form["empleado"]
        servicio=request.form["servicio"]
        fecha=request.form["fecha"]
        hora=request.form["hora"]

        cursor.execute(
            """
            SELECT id_cliente
            FROM clientes
            WHERE dni=%s
            """,
            (dni,)
        )

        cliente=cursor.fetchone()

        if cliente is None:

            cursor.execute(
                """
                INSERT INTO clientes
                (nombre,apellido,dni,telefono)
                VALUES(%s,%s,%s,%s)
                """,
                (nombre,apellido,dni,telefono)
            )

            conexion.commit()

            id_cliente=cursor.lastrowid

        else:

            id_cliente=cliente["id_cliente"]

        cursor.execute(
            """
            INSERT INTO turnos
            (id_cliente,id_empleado,id_servicio,fecha,hora)
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                id_cliente,
                empleado,
                servicio,
                fecha,
                hora
            )
        )

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM empleados")
    empleados=cursor.fetchall()

    cursor.execute("SELECT * FROM servicios")
    servicios=cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "nuevo_turno.html",
        empleados=empleados,
        servicios=servicios
    )

# ==========================
# ELIMINAR
# ==========================

@app.route("/eliminar/<int:id>")
def eliminar(id):

    conexion=conectar()
    cursor=conexion.cursor()

    cursor.execute(
        "DELETE FROM turnos WHERE id_turno=%s",
        (id,)
    )

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(url_for("index"))

# ==========================
# EDITAR
# ==========================

@app.route("/editar/<int:id>",methods=["GET","POST"])
def editar(id):

    conexion=conectar()
    cursor=conexion.cursor(dictionary=True)

    if request.method=="POST":

        empleado=request.form["empleado"]
        servicio=request.form["servicio"]
        fecha=request.form["fecha"]
        hora=request.form["hora"]
        estado=request.form["estado"]

        cursor.execute("""
        UPDATE turnos
        SET
        id_empleado=%s,
        id_servicio=%s,
        fecha=%s,
        hora=%s,
        estado=%s
        WHERE id_turno=%s
        """,
        (
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

    cursor.execute("""
    SELECT *
    FROM turnos
    WHERE id_turno=%s
    """,(id,))

    turno=cursor.fetchone()

    cursor.execute("SELECT * FROM empleados")
    empleados=cursor.fetchall()

    cursor.execute("SELECT * FROM servicios")
    servicios=cursor.fetchall()

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

@app.route("/buscar",methods=["POST"])
def buscar():

    texto=request.form["buscar"]

    conexion=conectar()
    cursor=conexion.cursor(dictionary=True)

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
    ON t.id_cliente=c.id_cliente
    JOIN empleados e
    ON t.id_empleado=e.id_empleado
    JOIN servicios s
    ON t.id_servicio=s.id_servicio
    WHERE
    c.nombre LIKE %s
    OR
    c.apellido LIKE %s
    """,
    (
        "%"+texto+"%",
        "%"+texto+"%"
    ))

    turnos=cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "index.html",
        turnos=turnos
    )

if __name__=="__main__":
    app.run(debug=True)