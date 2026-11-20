# EduControl Express

School attendance system built for a freelance client (a school in Quito, Ecuador). Staff register students, mark attendance manually or through a facial-recognition client, and export daily and monthly reports to Excel.

## Features

- **Student management:** register, edit and deactivate students
- **Attendance:** manual check-in from the web panel, plus a REST endpoint (`POST /api/reconocimiento`) that a facial-recognition client calls with the recognized student's ID
- **Reports:** daily attendance report, monthly report per student and one-click **Excel export** (pandas + openpyxl)
- Database credentials kept out of the code in a `.env` file

## Stack

Python 3 · Flask · MySQL (`mysql-connector-python`) · pandas · openpyxl · Jinja2 templates · HTML/CSS

## Run locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
```

Create a `.env` file:

```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=educontrol
MYSQL_PORT=3306
```

```bash
python app.py
```

Then open http://localhost:5000.

## Main routes

| Route | Purpose |
|---|---|
| `/alumnos` | Student list |
| `/registrar_alumno` | Register a student |
| `/marcar_asistencia/<id>` | Manual check-in |
| `POST /api/reconocimiento` | Check-in from the facial-recognition client (`{"id_estudiante": 12}`) |
| `/reporte` · `/reporte_mensual` | Daily and monthly reports |
| `/exportar_excel` | Download the report as .xlsx |

## Author

**José Ignacio Pumagualli** · [GitHub](https://github.com/JoseIgnacio-Puma08) · pumaguallipro@gmail.com
