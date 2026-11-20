from flask import Flask, render_template, request, redirect, jsonify, send_file
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import os

load_dotenv()

app = Flask(__name__)


def conectar_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT", 3306))
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/test_db")
def test_db():
    try:
        conexion = conectar_db()
        conexion.close()
        return "Conexion a MySQL correcta"
    except Error as e:
        return f"Error de conexion: {e}"


@app.route("/estudiantes")
@app.route("/alumnos")
def estudiantes():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_estudiante, nombre, apellido, paralelo, estado_alumno
        FROM estudiantes
        WHERE estado_alumno = 1
        ORDER BY paralelo ASC, apellido ASC, nombre ASC
    """)

    estudiantes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("alumnos.html", alumnos=estudiantes)


@app.route("/registrar_alumno", methods=["GET", "POST"])
def registrar_alumno():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        paralelo = request.form["paralelo"].upper().strip()

        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO estudiantes (nombre, apellido, paralelo, estado_alumno)
            VALUES (%s, %s, %s, 1)
        """, (nombre, apellido, paralelo))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect("/alumnos")

    return render_template("registrar_alumno.html")

@app.route("/editar_estudiante/<int:id_estudiante>", methods=["GET", "POST"])
def editar_estudiante(id_estudiante):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        paralelo = request.form["paralelo"].upper().strip()

        cursor.execute("""
            UPDATE estudiantes
            SET nombre = %s, apellido = %s, paralelo = %s
            WHERE id_estudiante = %s
        """, (nombre, apellido, paralelo, id_estudiante))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect("/alumnos")

    cursor.execute("""
        SELECT id_estudiante, nombre, apellido, paralelo
        FROM estudiantes
        WHERE id_estudiante = %s
    """, (id_estudiante,))

    estudiante = cursor.fetchone()

    cursor.close()
    conexion.close()

    return render_template("editar_estudiante.html", estudiante=estudiante)


@app.route("/eliminar_estudiante/<int:id_estudiante>", methods=["POST"])
def eliminar_estudiante(id_estudiante):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE estudiantes
        SET estado_alumno = 0
        WHERE id_estudiante = %s
    """, (id_estudiante,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect("/alumnos")

@app.route("/marcar_asistencia/<int:id_estudiante>")
def marcar_asistencia(id_estudiante):
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    hora_actual = datetime.now().strftime("%H:%M:%S")

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_asistencia
        FROM asistencia
        WHERE id_estudiante = %s AND fecha = %s
    """, (id_estudiante, fecha_actual))

    asistencia_existente = cursor.fetchone()

    if asistencia_existente:
        cursor.close()
        conexion.close()
        return "La asistencia de este estudiante ya fue registrada hoy."

    cursor.execute("""
        INSERT INTO asistencia (id_estudiante, fecha, hora_entrada, estado_asistencia)
        VALUES (%s, %s, %s, 1)
    """, (id_estudiante, fecha_actual, hora_actual))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect("/reporte")


@app.route("/api/reconocimiento", methods=["POST"])
def recibir_reconocimiento():
    datos = request.get_json()

    id_estudiante = datos.get("id_estudiante")

    if not id_estudiante:
        return jsonify({
            "error": "Debe enviar id_estudiante"
        }), 400

    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    hora_actual = datetime.now().strftime("%H:%M:%S")

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_estudiante, nombre, apellido
        FROM estudiantes
        WHERE id_estudiante = %s AND estado_alumno = 1
    """, (id_estudiante,))

    estudiante = cursor.fetchone()

    if not estudiante:
        cursor.close()
        conexion.close()
        return jsonify({
            "error": "Estudiante no encontrado"
        }), 404

    cursor.execute("""
        SELECT id_asistencia
        FROM asistencia
        WHERE id_estudiante = %s AND fecha = %s
    """, (id_estudiante, fecha_actual))

    asistencia_existente = cursor.fetchone()

    if asistencia_existente:
        cursor.close()
        conexion.close()
        return jsonify({
            "mensaje": "Asistencia ya registrada",
            "estudiante": f"{estudiante['nombre']} {estudiante['apellido']}"
        }), 200

    cursor.execute("""
        INSERT INTO asistencia (id_estudiante, fecha, hora_entrada, estado_asistencia)
        VALUES (%s, %s, %s, 1)
    """, (id_estudiante, fecha_actual, hora_actual))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "mensaje": "Asistencia registrada correctamente",
        "id_estudiante": id_estudiante,
        "estudiante": f"{estudiante['nombre']} {estudiante['apellido']}",
        "fecha": fecha_actual,
        "hora": hora_actual
    }), 201


@app.route("/reporte")
def reporte():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            estudiantes.nombre,
            estudiantes.apellido,
            estudiantes.paralelo,
            asistencia.fecha,
            asistencia.hora_entrada,
            asistencia.estado_asistencia
        FROM asistencia
        INNER JOIN estudiantes 
            ON asistencia.id_estudiante = estudiantes.id_estudiante
        WHERE estudiantes.estado_alumno = 1
        ORDER BY 
            estudiantes.paralelo ASC,
            estudiantes.apellido ASC,
            estudiantes.nombre ASC,
            asistencia.fecha DESC,
            asistencia.hora_entrada DESC
    """)

    asistencias = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("reporte.html", asistencias=asistencias)


@app.route("/exportar_excel")
def exportar_excel():
    conexion = conectar_db()

    consulta = """
        SELECT 
             estudiantes.paralelo AS Paralelo,
        estudiantes.apellido AS Apellido,
        estudiantes.nombre AS Nombre,
        asistencia.fecha AS Fecha,
        asistencia.hora_entrada AS Hora,
        CASE 
            WHEN asistencia.estado_asistencia = 1 THEN 'Presente'
            ELSE 'Falta'
        END AS Estado
    FROM asistencia
    INNER JOIN estudiantes 
        ON asistencia.id_estudiante = estudiantes.id_estudiante
    WHERE estudiantes.estado_alumno = 1
    ORDER BY 
        estudiantes.paralelo ASC,
        estudiantes.apellido ASC,
        estudiantes.nombre ASC,
        asistencia.fecha DESC,
        asistencia.hora_entrada DESC  
    """

    df = pd.read_sql(consulta, conexion)

    conexion.close()

    if not os.path.exists("reportes"):
        os.makedirs("reportes")

    ruta_archivo = "reportes/reporte_asistencia.xlsx"
    df.to_excel(ruta_archivo, index=False)

    return send_file(ruta_archivo, as_attachment=True)


@app.route("/reporte_mensual")
def reporte_mensual():
    hoy = datetime.now()
    anio_actual = hoy.year
    mes_actual = hoy.month

    dias_mes = list(range(1, 32))

    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    # Obtener estudiantes activos ordenados por paralelo, apellido y nombre
    cursor.execute("""
        SELECT 
            id_estudiante,
            nombre,
            apellido,
            paralelo,
            estado_alumno
        FROM estudiantes
        WHERE estado_alumno = 1
        ORDER BY paralelo ASC, apellido ASC, nombre ASC
    """)

    estudiantes = cursor.fetchall()

    # Obtener asistencias del mes actual
    cursor.execute("""
        SELECT 
            id_estudiante,
            DAY(fecha) AS dia,
            estado_asistencia
        FROM asistencia
        WHERE YEAR(fecha) = %s
        AND MONTH(fecha) = %s
    """, (anio_actual, mes_actual))

    asistencias = cursor.fetchall()

    cursor.close()
    conexion.close()

    # Crear un diccionario para buscar asistencia rápido
    mapa_asistencia = {}

    for asistencia in asistencias:
        id_estudiante = asistencia["id_estudiante"]
        dia = asistencia["dia"]
        estado = asistencia["estado_asistencia"]

        mapa_asistencia[(id_estudiante, dia)] = estado

    # Armar estructura final para la tabla
    reporte = []

    for estudiante in estudiantes:
        fila = {
            "id_estudiante": estudiante["id_estudiante"],
            "nombre": estudiante["nombre"],
            "apellido": estudiante["apellido"],
            "paralelo": estudiante["paralelo"],
            "dias": []
        }

        for dia in dias_mes:
            clave = (estudiante["id_estudiante"], dia)

            if clave in mapa_asistencia and mapa_asistencia[clave] == 1:
                fila["dias"].append("presente")
            else:
                fila["dias"].append("falta")

        reporte.append(fila)

    return render_template(
        "reporte_mensual.html",
        reporte=reporte,
        dias_mes=dias_mes,
        mes_actual=mes_actual,
        anio_actual=anio_actual
    )

if __name__ == "__main__":
    app.run(debug=True)