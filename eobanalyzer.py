import re
import fitz
import pytesseract
import pymysql
import sys
import os

from PIL import Image

# =========================================================
# TESSERACT
# =========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# =========================================================
# PDF PATH
# =========================================================
pdf_path = sys.argv[1]

print("\n======================")
print("PDF PATH :", pdf_path)

if not os.path.exists(pdf_path):
    print("PDF NOT FOUND")
    sys.exit()

print("PDF FOUND")
print("FILE SIZE :", os.path.getsize(pdf_path))
print("======================")

print("EOB PDF :", pdf_path)

# =========================================================
# DEFAULT VALUE
# =========================================================

NO_VALUE = "NO VALUE"

# =========================================================
# MYSQL CONNECTION
# =========================================================

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Jeevi@59",
    database="claims_project",
    autocommit=True
)

cursor = conn.cursor()

# =========================================================
# OPEN PDF
# =========================================================

doc = fitz.open(pdf_path)

raw_text = ""

# =========================================================
# OCR + PDF TEXT
# =========================================================

for page in doc:

    page_text = page.get_text().strip()

    raw_text += "\n" + page_text

    if not page_text:

        pix = page.get_pixmap(dpi=300)

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        raw_text += "\n" + pytesseract.image_to_string(img)

# =========================================================
# CLEAN TEXT
# =========================================================

raw_text = raw_text.replace("|", " ")
raw_text = raw_text.replace("_", " ")

lines = []

for line in raw_text.split("\n"):

    line = re.sub(r"\s+", " ", line.strip())

    if line:
        lines.append(line)

full_text = " ".join(lines)

if not full_text.strip():

    print("NO TEXT FOUND IN PDF")

    full_text = NO_VALUE

# =========================================================
# DEBUG RAW TEXT
# =========================================================

print("\n================ RAW TEXT ================\n")

for line in lines:
    print(line)

# =========================================================
# SAFE FUNCTIONS
# =========================================================

def safe_text(value):

    if value and str(value).strip():
        return str(value).strip()

    return NO_VALUE


def safe_float(value):

    try:

        value = str(value)

        value = value.replace("$", "")
        value = value.replace(",", "")

        return float(value)

    except:
        return 0.00


def safe_date(value):

    if not value:
        return NO_VALUE

    value = str(value).strip()

    try:

        if "/" in value:

            mm, dd, yy = value.split("/")

            if len(yy) == 2:
                yy = "20" + yy

            return f"{yy}-{mm.zfill(2)}-{dd.zfill(2)}"

        if re.match(r"^\d{6}$", value):

            mm = value[:2]
            dd = value[2:4]
            yy = value[4:]

            return f"20{yy}-{mm}-{dd}"

        if re.match(r"^\d{8}$", value):

            mm = value[:2]
            dd = value[2:4]
            yyyy = value[4:]

            return f"{yyyy}-{mm}-{dd}"

    except:
        pass

    return None

# =========================================================
# FIND FUNCTION
# =========================================================

def find(patterns):

    try:

        for pattern in patterns:

            match = re.search(
                pattern,
                full_text,
                re.IGNORECASE
            )

            if match:

                value = match.group(1).strip()

                if value:
                    return value

    except Exception as e:
        print("FIND ERROR :", e)

    return NO_VALUE
# =========================================================
# PAYER NAME
# =========================================================

payer_name = NO_VALUE

for line in lines[:10]:

    if re.search(
        r'cigna|aetna|uhc|medicare|medicaid|humana',
        line,
        re.IGNORECASE
    ):

        payer_name = line.strip()
        break

# =========================================================
# PAYER ADDRESS
# =========================================================

if payer_name != NO_VALUE:

    for i, line in enumerate(lines):

        if payer_name.lower() in line.lower():

            temp = []

            for j in range(i + 1, len(lines)):

                if re.search(
                    r'TIN|NPI|EFT|Patient Name',
                    lines[j],
                    re.IGNORECASE
                ):
                    break

                temp.append(lines[j])

            payer_address = " ".join(temp)

            break

# =========================================================
# PROVIDER NAME
# =========================================================

provider_name = NO_VALUE

for line in lines:

    if re.search(
        r'healthcare|medical|hospital|clinic|group|facility',
        line,
        re.IGNORECASE
    ):

        if "EFT" in line:

            provider_name = line.split("EFT")[0].strip()

        else:
            provider_name = line.strip()

        break

# =========================================================
# PROVIDER ADDRESS
# =========================================================

provider_address = NO_VALUE

if provider_name != NO_VALUE:

    for i, line in enumerate(lines):

        if provider_name.lower() in line.lower():

            temp = []

            for j in range(i + 1, min(i + 4, len(lines))):

                if (
                    "check date" in lines[j].lower()
                    or "processed" in lines[j].lower()
                    or "patient" in lines[j].lower()
                ):
                    break

                temp.append(lines[j])

            if temp:
                provider_address = " ".join(temp)

            break

# =========================================================
# HEADER EXTRACTION
# =========================================================



tax_id_number = find([
    r'TIN\s*[:\-]?\s*(\d{9})',
    r'tax\s*id\s*[:\-]?\s*(\d{9})'
])

npi_number = find([
    r'NPI\s*[:\-]?\s*(\d{10})',
    r'NP1I\s*[:\-]?\s*(\d{10})'
])

eft_or_cheque_number = find([

    r'EFT\/?Check\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)',

    r'EFT\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)',

    r'check\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)',

    r'check\s*number\s*[:\-]?\s*([A-Z0-9\-]+)',

    r'payment\s*number\s*[:\-]?\s*([A-Z0-9\-]+)'

])

check_date = safe_date(find([
    r'check\s*date\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})',
    r'payment\s*date\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})'
]))

processed_date = safe_date(find([

    r'processed\s*date\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})',

    r'production\s*date\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})'

]))

patient_name = NO_VALUE

for line in lines:

    if "PATIENT NAME" in line.upper():

        match = re.search(
            r'Patient\s*Name\s*:?\s*(.*?)\s*MBR\s*ID',
            line,
            re.IGNORECASE
        )

        if match:

            patient_name = match.group(1).strip()

            patient_name = re.sub(
                r'\s*,\s*',
                ', ',
                patient_name
            )

            break

member_id = find([
    r'MBR\s*ID\s*:\s*([A-Z0-9]+)',
    r'member\s*id\s*:\s*([A-Z0-9]+)'
])

claim_number = find([
    r'Claim\s*#\s*:\s*([A-Z0-9]+)'
])

# =========================================================
# PATIENT ID
# =========================================================

cursor.execute("""
SELECT patient_id
FROM claims
ORDER BY patient_id DESC
LIMIT 1
""")

row = cursor.fetchone()

if row:
    patient_id = row[0]
else:
    patient_id = 0

# =========================================================
# SERVICE LINE EXTRACTION
# =========================================================

parsed_lines = []

total_paid_amount = 0
total_patient_responsibility = 0
total_coinsurance = 0
total_copay = 0
total_deductible = 0

print("\n================ SERVICE LINES ================\n")

# =====================================================
# SERVICE LINE LOOP
# =====================================================

for idx, line in enumerate(lines):

    # Skip non-service lines
    if not re.match(
         r'^\d+\s*\.?\s*\d{2}\s+\d{6,8}',
        line
    ):
        continue

    print(line)

    amounts = re.findall(
        r'\$?([\d,]+\.\d{2})',
        line
    )

    dates = re.findall(
        r'\d{6,8}',
        line
    )

    # =====================================================
    # SI.NO
    # =====================================================

    si_match = re.search(
        r'^(\d+)',
        line
    )

    si_no = (
        si_match.group(1)
        if si_match else NO_VALUE
    )

    # =====================================================
    # POS
    # =====================================================

    pos_match = re.search(
        r'^\d+\s+(\d{2})',
        line
    )

    pos = (
        pos_match.group(1)
        if pos_match else NO_VALUE
    )

    # =====================================================
    # HCPC
    # =====================================================

    hcpc_match = re.search(
        r'\b([A-Z][A-Z0-9]{4})\b',
        line
    )

    hcpc = (
        hcpc_match.group(1)
        if hcpc_match else NO_VALUE
    )

    # =====================================================
    # MODIFIER
    # =====================================================

    modifier = NO_VALUE

    tokens = line.split()

    for i, token in enumerate(tokens):

        if re.match(r'^[A-Z][A-Z0-9]{4}$', token):

            if i + 1 < len(tokens):

                possible_modifier = tokens[i + 1].strip()

                possible_modifier = (
                    possible_modifier.upper()
                    .replace("I", "1")
                    .replace("L", "1")
                )

                if re.match(r'^[A-Z0-9]{2}$', possible_modifier):

                    modifier = possible_modifier

            break

    # =====================================================
    # ALL DENIAL CODES
    # =====================================================

    denial_codes = re.findall(
        r'((?:CO|PR|OA|PI|CR)-\d+)',
        line,
        re.IGNORECASE
    )

    denial_codes = [
        x.upper()
        for x in denial_codes
    ]

    # =====================================================
    # NEXT LINE DENIALS
    # =====================================================

    next_line = ""

    if idx + 1 < len(lines):
        next_line = lines[idx + 1]

    next_denials = re.findall(
        r'((?:CO|PR|OA|PI|CR)-\d+)',
        next_line,
        re.IGNORECASE
    )

    for nd in next_denials:

        nd = nd.upper()

        if nd not in denial_codes:
            denial_codes.append(nd)

    # =====================================================
    # DENIAL AMOUNT MAP
    # =====================================================

    denial_amount_map = {}

    denial_amounts = re.findall(
        r'((?:CO|PR|OA|PI|CR)-\d+)\s+\$?([\d,]+\.\d{2})',
        line,
        re.IGNORECASE
    )

    for dc, amt in denial_amounts:

        denial_amount_map[
            dc.upper()
        ] = safe_float(amt)

    next_denial_amounts = re.findall(
        r'((?:CO|PR|OA|PI|CR)-\d+)\s+\$?([\d,]+\.\d{2})',
        next_line,
        re.IGNORECASE
    )

    for dc, amt in next_denial_amounts:

        denial_amount_map[
            dc.upper()
        ] = safe_float(amt)

    # =====================================================
    # RARC
    # =====================================================

    rarc_match = re.search(
        r'\b([MN][0-9]{2,3})\b',
        line,
        re.IGNORECASE
    )

    rarc_code = (
        rarc_match.group(1).upper()
        if rarc_match else NO_VALUE
    )

    # =====================================================
    # DOS
    # =====================================================

    dos_from = (
        safe_date(dates[0])
        if len(dates) > 0 else None
    )

    dos_to = (
        safe_date(dates[1])
        if len(dates) > 1 else None
    )

    # =====================================================
    # AMOUNTS
    # =====================================================

    billed = (
        safe_float(amounts[0])
        if len(amounts) > 0 else 0
    )

    allowed = (
        safe_float(amounts[1])
        if len(amounts) > 1 else 0
    )

    deductible = (
        safe_float(amounts[2])
        if len(amounts) > 2 else 0
    )

    copay = (
        safe_float(amounts[3])
        if len(amounts) > 3 else 0
    )

    coinsurance = (
        safe_float(amounts[4])
        if len(amounts) > 4 else 0
    )

    paid_amount = (
        safe_float(amounts[-1])
        if len(amounts) > 0 else 0
    )

    # =====================================================
    # PATIENT RESPONSIBILITY
    # =====================================================

    patient_responsibility = (
        deductible +
        copay +
        coinsurance
    )

    # =====================================================
    # TOTALS
    # =====================================================

    total_paid_amount += paid_amount

    total_patient_responsibility += (
        patient_responsibility
    )

    total_coinsurance += coinsurance

    total_copay += copay

    total_deductible += deductible

    # =====================================================
    # STORE EACH DENIAL SEPARATELY
    # =====================================================

    if denial_codes:

        for single_denial in denial_codes:

            single_denied_amount = (
                denial_amount_map.get(
                    single_denial,
                    0.00
                )
            )

            parsed_lines.append({

                "si_no": si_no,

                "dos_from": dos_from,
                "dos_to": dos_to,

                "pos": pos,

                "hcpc": hcpc,

                "modifier": modifier,

                "billed": billed,

                "allowed": allowed,

                "deductible": deductible,

                "copay": copay,

                "coinsurance": coinsurance,

                "denial_code": single_denial,

                "rarc_code": rarc_code,

                "denied_amount": single_denied_amount,

                "paid_amount": paid_amount,

                "patient_responsibility": patient_responsibility

            })

    else:

        parsed_lines.append({

            "si_no": si_no,

            "dos_from": dos_from,
            "dos_to": dos_to,

            "pos": pos,

            "hcpc": hcpc,

            "modifier": modifier,

            "billed": billed,

            "allowed": allowed,

            "deductible": deductible,

            "copay": copay,

            "coinsurance": coinsurance,

            "denial_code": NO_VALUE,

            "rarc_code": rarc_code,

            "denied_amount": 0.00,

            "paid_amount": paid_amount,

            "patient_responsibility": patient_responsibility

        })
        
        # =========================================================
# FORCE DEFAULT VALUES
# =========================================================

payer_name = safe_text(payer_name)
payer_address = safe_text(payer_address)

provider_name = safe_text(provider_name)
provider_address = safe_text(provider_address)

tax_id_number = safe_text(tax_id_number)
npi_number = safe_text(npi_number)

eft_or_cheque_number = safe_text(eft_or_cheque_number)

patient_name = safe_text(patient_name)

member_id = safe_text(member_id)

claim_number = safe_text(claim_number)

# =========================================================
# IF NO SERVICE LINES FOUND
# =========================================================

if len(parsed_lines) == 0:

    print("NO SERVICE LINE FOUND")

    parsed_lines.append({

        "si_no": None,

        "dos_from": None,
        "dos_to": None,

        "pos": None,

        "hcpc": None,

        "modifier": None,

        "billed": 0.00,

        "allowed": 0.00,

        "deductible": 0.00,

        "copay": 0.00,

        "coinsurance": 0.00,

        "denial_code": None,

        "rarc_code": None,

        "denied_amount": 0.00,

        "paid_amount": 0.00,

        "patient_responsibility": 0.00

    })

# =========================================================
# DEBUG HEADER
# =========================================================

print("\n================ HEADER ================\n")

print("payer_name :", payer_name)
print("payer_address :", payer_address)

print("provider_name :", provider_name)
print("provider_address :", provider_address)

print("tax_id_number :", tax_id_number)
print("npi_number :", npi_number)

print("eft_or_cheque_number :", eft_or_cheque_number)

print("check_date :", check_date)
print("processed_date :", processed_date)

print("patient_name :", patient_name)

print("member_id :", member_id)

print("claim_number :", claim_number)

print("patient_id :", patient_id)

print("total_paid_amount :", total_paid_amount)

# =========================================================
# INSERT INTO EOB
# =========================================================

cursor.execute("""

INSERT INTO eob(

patient_id,
payer_name,
payer_address,
provider_name,
provider_address,
tax_id_number,
npi_number,
eft_or_cheque_number,
check_date,
processed_date,
patient_name,
member_id,
claim_number,
total_paid_amount,
total_patient_responsibility,
total_coinsurance,
total_copay,
total_deductible

)

VALUES(

%s,%s,%s,%s,%s,%s,%s,%s,
%s,%s,%s,%s,%s,%s,%s,%s,%s,%s

)

""", (

patient_id,



safe_text(payer_name),

safe_text(payer_address),

safe_text(provider_name),

safe_text(provider_address),

safe_text(tax_id_number),

safe_text(npi_number),

safe_text(eft_or_cheque_number),

check_date,

processed_date,

safe_text(patient_name),

safe_text(member_id),

safe_text(claim_number),

total_paid_amount,

total_patient_responsibility,

total_coinsurance,

total_copay,

total_deductible

))

eob_id = cursor.lastrowid

print("\nEOB INSERTED :", eob_id)

# =========================================================
# INSERT SERVICE LINES
# =========================================================

for line in parsed_lines:

    cursor.execute("""

    INSERT INTO eob_hcpc_details(

    eob_id,
    patient_id,

    date_of_service_from,
    date_of_service_to,

    place_of_service,

    hcpc_cpt_code,

    modifier_code,

    billed_amount,
    allowed_amount,

    deductible,
    copay,
    coinsurance,

    denial_code,
    rarc_code,

    denied_amount,
    paid_amount,

    patient_responsibility

    )

    VALUES(

    %s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s

    )

    """, (

    eob_id,
    patient_id,

    line["dos_from"],
    line["dos_to"],

    line["pos"],

    line["hcpc"],

    line["modifier"],

    line["billed"],
    line["allowed"],

    line["deductible"],
    line["copay"],
    line["coinsurance"],

    line["denial_code"],
    line["rarc_code"],

    line["denied_amount"],
    line["paid_amount"],

    line["patient_responsibility"]

    ))

# =========================================================
# CLOSE
# =========================================================

cursor.close()

conn.close()

print("\n===================================")
print("EOB ANALYSIS COMPLETED")
print("===================================")