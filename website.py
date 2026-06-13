from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import subprocess
import sys
import time

import os

print("CURRENT FILE:", __file__)
print("CURRENT DIR :", os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# =====================================================
# UPLOAD FOLDER
# =====================================================

UPLOAD_FOLDER = r"C:\Users\Aarthi Priya\Downloads\projectfiles"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =====================================================
# CLEAN UP FUNCTION
# =====================================================

def clear_upload_folder():
    folder = app.config["UPLOAD_FOLDER"]

    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print("Deleted:", file_path)
            except Exception as e:
                print("Error deleting file:", e)


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# UPLOAD ROUTE
# =====================================================

@app.route("/upload", methods=["POST"])
def upload():

    claim_file = request.files.get("claim_pdf")
    eob_file = request.files.get("eob_pdf")

    if not claim_file:
        return "Claim PDF not selected"

    if not eob_file:
        return "EOB PDF not selected"

    # =================================================
    # SAVE CLAIM PDF
    # =================================================

    claim_filename = secure_filename(claim_file.filename)

    claim_path = os.path.join(app.config["UPLOAD_FOLDER"], claim_filename)
    claim_file.save(claim_path)
    
    
    print("\nCLAIM FILE NAME :", claim_file.filename)
    print("CLAIM FILE SIZE :", os.path.getsize(claim_path))

    # =================================================
    # SAVE EOB PDF
    # =================================================

    eob_filename = secure_filename(eob_file.filename)

    eob_path = os.path.join(app.config["UPLOAD_FOLDER"], eob_filename)
    eob_file.save(eob_path)
    
    print("EOB FILE NAME :", eob_file.filename)
    print("EOB FILE SIZE :", os.path.getsize(eob_path))

    # =================================================
    # FORCE ABSOLUTE PATH (IMPORTANT FIX)
    # =================================================

    claim_path = os.path.abspath(claim_path)
    eob_path = os.path.abspath(eob_path)

    print("\n==============================")
    print("CLAIM SAVED :", claim_path)
    print("EOB SAVED   :", eob_path)
    print("==============================")

    print("CLAIM EXISTS:", os.path.exists(claim_path))
    print("EOB EXISTS:", os.path.exists(eob_path))

    # =================================================
    # SMALL DELAY (WINDOWS FILE WRITE SAFETY)
    # =================================================

    time.sleep(1)

    # =================================================
    # RUN CLAIM.PY
    # =================================================

    print("\nRUNNING CLAIM.PY")

    subprocess.run(
        [
            sys.executable,
            r"C:\Users\Aarthi Priya\Downloads\CLAIMPROJECT\claim.py",
            claim_path
        ],
        check=True
    )

    print("CLAIM COMPLETED")

    # =================================================
    # SMALL DELAY
    # =================================================

    time.sleep(1)

    # =================================================
    # RUN EOB ANALYZER
    # =================================================

    print("\nRUNNING EOBANALYZER.PY")
    
    print("CLAIM SCRIPT EXISTS:",
      os.path.exists(
      r"C:\Users\Aarthi Priya\Downloads\CLAIMPROJECT\claim.py"
      ))

    print("SCRIPT SIZE:",
      os.path.getsize(
      r"C:\Users\Aarthi Priya\Downloads\CLAIMPROJECT\claim.py"
      ))

    subprocess.run(
        [
            sys.executable,
            r"C:\Users\Aarthi Priya\Downloads\CLAIMPROJECT\eobanalyzer.py",
            eob_path
        ],
        check=True
    )

    print("EOB COMPLETED")

    # =================================================
    # CLEAN UP FILES
    # =================================================

    clear_upload_folder()

    print("UPLOAD FOLDER CLEANED")

    # =================================================
    # RESPONSE
    # =================================================

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Success</title>
<style>
body {{
    font-family: Arial;
    background: #f4f7fa;
    text-align: center;
    padding: 50px;
}}

.card {{
    background: white;
    padding: 30px;
    border-radius: 10px;
    width: 600px;
    margin: auto;
    box-shadow: 0 0 20px rgba(0,0,0,.1);
}}

.success {{
    color: green;
    font-size: 30px;
}}

.btn {{
    display:inline-block;
    padding:10px 20px;
    background:#2563eb;
    color:white;
    text-decoration:none;
    border-radius:5px;
}}
</style>
</head>

<body>

<div class="card">

<h1 class="success">✅ Analysis Completed</h1>

<p><b>Claim PDF:</b> {claim_filename}</p>

<p><b>EOB PDF:</b> {eob_filename}</p>

<p>Claim Extraction Completed Successfully</p>

<p>EOB Analysis Completed Successfully</p>

<p>Temporary Files Deleted Successfully</p>

<br>

<a href="/" class="btn">Upload Another File</a>

</div>

</body>
</html>
"""
# =====================================================
# START APP
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)