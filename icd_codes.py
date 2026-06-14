import re
import fitz
import pymysql

# =====================================================
# MYSQL CONNECTION
# =====================================================

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Jeevi@59",
    database="claims_project",
    charset="utf8mb4"
)

cursor = conn.cursor()

# =====================================================
# CLEAR TABLE
# =====================================================

cursor.execute("TRUNCATE TABLE icd_codes")

# =====================================================
# PDF PATH
# =====================================================

pdf_path = r"C:\Users\Aarthi Priya\Downloads\icdcodes.pdf"

# =====================================================
# ICD REGEX
# Examples:
# A000 Cholera due to ...
# B1711 Acute hepatitis ...
# C4A10 Merkel cell ...
# =====================================================

pattern = re.compile(
    r'^([A-Z][A-Z0-9]{2,9})\s+(.+)$'
)

# =====================================================
# COUNTERS
# =====================================================

inserted_count = 0
skipped_count = 0

# =====================================================
# OPEN PDF
# =====================================================

doc = fitz.open(pdf_path)

for page_num in range(len(doc)):

    page = doc[page_num]

    text = page.get_text()

    lines = text.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Skip page headers/footers
        if line.startswith("ICD"):
            continue

        if line.startswith("Chapter"):
            continue

        if line.startswith("Page"):
            continue

        match = pattern.match(line)

        if not match:
            continue

        icd_code = match.group(1).strip()
        description = match.group(2).strip()

        # Remove weird spaces/newlines
        description = re.sub(r"\s+", " ", description)

        try:

            cursor.execute(
                """
                INSERT INTO icd_codes
                (icd_code, description)
                VALUES (%s, %s)
                """,
                (icd_code, description)
            )

            inserted_count += 1

        except pymysql.err.IntegrityError:
            skipped_count += 1

# =====================================================
# SAVE
# =====================================================

conn.commit()

print("\n===================================")
print("ICD IMPORT COMPLETED")
print("===================================")
print(f"Inserted : {inserted_count}")
print(f"Skipped  : {skipped_count}")

# =====================================================
# VERIFY DATA
# =====================================================

cursor.execute("""
SELECT icd_code, description
FROM icd_codes
LIMIT 20
""")

rows = cursor.fetchall()

print("\nSAMPLE DATA\n")

for row in rows:
    print(f"{row[0]} --> {row[1]}")

# =====================================================
# CLOSE
# =====================================================

cursor.close()
conn.close()
doc.close()

print("\nDatabase connection closed.")