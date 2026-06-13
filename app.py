from flask import Flask
import pymysql

app = Flask(__name__)


# =========================================================
# DATABASE CONNECTION FUNCTION
# =========================================================
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Jeevi@59",
        database="claims_project",
        autocommit=True
    )


# =========================================================
# HOME PAGE - SHOW ALL TABLES
# =========================================================
@app.route("/")
def home():

    html = """
    <html>
    <head>
        <title>Claims Dashboard</title>

        <style>
            body{
                font-family: Arial;
                padding: 20px;
                background:#f5f5f5;
            }

            h1{
                background:black;
                color:white;
                padding:10px;
                text-align:center;
            }

            h2{
                background:#1d4ed8;
                color:white;
                padding:10px;
                margin-top:40px;
            }

            table{
                width:100%;
                border-collapse:collapse;
                background:white;
                margin-bottom:40px;
            }

            th,td{
                border:1px solid #ccc;
                padding:8px;
                text-align:left;
            }

            th{
                background:#e5e7eb;
            }

            .container{
                max-width:1200px;
                margin:auto;
            }
        </style>
    </head>

    <body>
    <div class="container">

    <h1>CMS1500 CLAIMS DASHBOARD</h1>
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ======================================
        # GET ALL TABLES
        # ======================================
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        if not tables:
            html += "<p>No tables found.</p>"

        # ======================================
        # LOOP TABLES
        # ======================================
        for table in tables:
            table_name = table[0]

            html += f"<h2>{table_name}</h2>"

            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()

            if not rows:
                html += "<p>No data available</p>"
                continue

            column_names = [desc[0] for desc in cursor.description]

            html += "<table><tr>"

            # headers
            for col in column_names:
                html += f"<th>{col}</th>"

            html += "</tr>"

            # rows
            for row in rows:
                html += "<tr>"
                for val in row:
                    html += f"<td>{val}</td>"
                html += "</tr>"

            html += "</table>"

        cursor.close()
        conn.close()

    except Exception as e:
        html += f"<h3 style='color:red'>ERROR: {e}</h3>"

    html += """
    </div>
    </body>
    </html>
    """

    return html


# =========================================================
# RUN FLASK
# =========================================================
if __name__ == "__main__":
    app.run(debug=True, port=8000)