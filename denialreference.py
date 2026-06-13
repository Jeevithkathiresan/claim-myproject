import fitz
import re
import pymysql

# =====================================================
# PDF PATH
# =====================================================

pdf_path = r"C:\Users\Aarthi Priya\Downloads\Adjustment_Codes_CARC_and_RARC.pdf"

# =====================================================
# MYSQL
# =====================================================

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Jeevi@59",
    database="claims_project",
    autocommit=True
)

cursor = conn.cursor()

print("MYSQL CONNECTED")

# =====================================================
# CLEAR TABLES
# =====================================================

cursor.execute("TRUNCATE TABLE denial_master")
cursor.execute("TRUNCATE TABLE denial_reference")

# =====================================================
# REGEX
# =====================================================

carc_pattern = re.compile(r'^\d{1,4}$')
rarc_pattern = re.compile(r'^(M\d+|MA\d+|N\d+)$')

# =====================================================
# OPEN PDF
# =====================================================

doc = fitz.open(pdf_path)

master_inserted = set()
rarc_inserted = set()

master_count = 0
rarc_count = 0

# =====================================================
# PROCESS PDF
# =====================================================

for page_num in range(len(doc)):

    page = doc[page_num]

    text = page.get_text()

    print("\n" + "=" * 80)
    print(f"PAGE {page_num + 1}")
    print("=" * 80)
    print(text)
    print("=" * 80)

    lines = []

    for line in text.split("\n"):

        line = re.sub(r"\s+", " ", line.strip())

        if line:
            lines.append(line)

    i = 0

    while i < len(lines):

        line = lines[i]

        # =================================================
        # CARC
        # =================================================

        if carc_pattern.match(line):

            carc_code = line

            desc_lines = []

            j = i + 1

            while j < len(lines):

                nxt = lines[j]

                if carc_pattern.match(nxt):
                    break

                if rarc_pattern.match(nxt):
                    break

                desc_lines.append(nxt)

                j += 1

            carc_desc = " ".join(desc_lines).strip()

            if not carc_desc:
                carc_desc = "NO VALUES"

            key = (carc_code, carc_desc)

            if key not in master_inserted:

                cursor.execute("""
                    INSERT INTO denial_master
                    (
                        carc_code,
                        carc_description
                    )
                    VALUES
                    (
                        %s,
                        %s
                    )
                """, (
                    carc_code,
                    carc_desc
                ))

                master_inserted.add(key)

                master_count += 1

                print(
                    f"CARC INSERTED -> "
                    f"{carc_code} | {carc_desc[:100]}"
                )

            i = j
            continue

        # =================================================
        # RARC
        # =================================================

        if rarc_pattern.match(line):

            rarc_code = line

            desc_lines = []

            j = i + 1

            while j < len(lines):

                nxt = lines[j]

                if rarc_pattern.match(nxt):
                    break

                if carc_pattern.match(nxt):
                    break

                desc_lines.append(nxt)

                j += 1

            rarc_desc = " ".join(desc_lines).strip()

            if not rarc_desc:
                rarc_desc = "NO VALUES"

            key = (rarc_code, rarc_desc)

            if key not in rarc_inserted:

                cursor.execute("""
                    INSERT INTO denial_reference
                    (
                        rarc_code,
                        rarc_description
                    )
                    VALUES
                    (
                        %s,
                        %s
                    )
                """, (
                    rarc_code,
                    rarc_desc
                ))

                rarc_inserted.add(key)

                rarc_count += 1

                print(
                    f"RARC INSERTED -> "
                    f"{rarc_code} | {rarc_desc[:100]}"
                )

            i = j
            continue

        i += 1

# =====================================================
# SUMMARY
# =====================================================

print("\n")
print("=" * 80)
print("CARC RECORDS :", master_count)
print("RARC RECORDS :", rarc_count)
print("=" * 80)

cursor.close()
conn.close()

print("IMPORT COMPLETED")