import fitz
import re
import pymysql

pdf_path = r"C:\Users\Aarthi Priya\Downloads\Adjustment_Codes_CARC_and_RARC.pdf"

doc = fitz.open(pdf_path)

text = ""

for page in doc:
    text += page.get_text() + "\n"

lines = text.split("\n")

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Jeevi@59",
    database="claims_project",
    autocommit=True
)

cursor = conn.cursor()

current_carc = None
current_carc_desc = None

insert_count = 0

for line in lines:

    line = re.sub(r"\s+", " ", line.strip())

    if not line:
        continue

    # CARC line

    carc_match = re.match(
        r'^(\d+)\s+(.*)',
        line
    )

    if carc_match:

        code = carc_match.group(1)

        desc = carc_match.group(2)

        if len(code) <= 3:

            current_carc = f"CO-{code}"

            current_carc_desc = desc

        continue

    # RARC line

    rarc_match = re.match(
        r'^(N\d+|MA\d+|M\d+)\s+(.*)',
        line
    )

    if rarc_match and current_carc:

        rarc_code = rarc_match.group(1)

        rarc_desc = rarc_match.group(2)

        cursor.execute("""
        INSERT INTO denial_reference
        (
            carc_code,
            carc_description,
            rarc_code,
            rarc_description
        )
        VALUES
        (
            %s,%s,%s,%s
        )
        """,
        (
            current_carc,
            current_carc_desc,
            rarc_code,
            rarc_desc
        ))

        insert_count += 1

print("TOTAL INSERTED =", insert_count)

cursor.close()
conn.close()
print("TOTAL INSERTS =", insert_count)

for line in lines[:500]:
    print(line)