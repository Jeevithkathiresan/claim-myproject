import re
import fitz
import pymysql
import sys
import os
import shutil


print("CLAIM.PY VERSION 2026-06-01")
# =========================================================
# CONFIG
# =========================================================

# pdf_path = r"C:\Users\Aarthi Priya\Downloads\CLAIMPROJECT\cms1500.pdf"




pdf_path = sys.argv[1]

shutil.copy(
    pdf_path,
    r"C:\Users\Aarthi Priya\Downloads\projectfiles\LAST_UPLOADED_CLAIM.pdf"
)

print("BACKUP CREATED")

print("\n================ DEBUG =================")
print("ARGUMENT PDF :", pdf_path)

with open(pdf_path, "rb") as f:
    print("FIRST 100 BYTES:")
    print(f.read(100))

print("========================================")

print("\n======================")
print("PDF PATH :", pdf_path)

#========
doc = fitz.open(pdf_path)
page = doc[0]

print("\n================ FILE DEBUG ================")
print("PDF PATH :", pdf_path)
print("TOTAL PAGES :", len(doc))

for i in range(min(3, len(doc))):
    print(f"\n----- PAGE {i+1} -----")
    print(doc[i].get_text()[:1000])

print("===========================================")


#======

if not os.path.exists(pdf_path):
    print("PDF NOT FOUND")
    sys.exit()

print("PDF FOUND")
print("FILE SIZE :", os.path.getsize(pdf_path))
print("======================")

print("CLAIM PDF :", pdf_path)

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
page = doc[0]
print("TOTAL PAGES :", len(doc))

text = doc[0].get_text()

print("\n===== FIRST 500 CHARS =====")
print(text[:500])
print("===========================")

# =========================================================
# RAW TEXT
# =========================================================

raw_text = page.get_text()

print("\n================ RAW TEXT ================\n")
print(raw_text)

# =========================================================
# PDF FORM FIELDS
# =========================================================

fields = {}

for w in page.widgets() or []:

    if w.field_name:

        key = w.field_name.strip().lower()

        value = ""

        if w.field_value:
            value = str(w.field_value).strip()

        fields[key] = value

print("\n================ PDF FIELDS ================\n")

for k, v in fields.items():
    print(f"{k} : {v}")

# =========================================================
# SAFE FIELD GETTER
# =========================================================

def get_field(name, default=""):

    return str(fields.get(name.lower(), default)).strip()

# =========================================================
# PATIENT NAME
# =========================================================

patient_name = get_field("pt_name")

patient_last_name = ""
patient_first_name = ""

if "," in patient_name:

    parts = patient_name.split(",")

    patient_last_name = parts[0].strip()

    if len(parts) > 1:
        patient_first_name = parts[1].strip()

# =========================================================
# INSURED NAME
# =========================================================

insured_name = get_field("ins_name")

insured_last_name = ""
insured_first_name = ""

if "," in insured_name:

    parts = insured_name.split(",")

    insured_last_name = parts[0].strip()

    if len(parts) > 1:
        insured_first_name = parts[1].strip()

# =========================================================
# DOB
# =========================================================

patient_dob = None


if (
    get_field("birth_yy")
    and get_field("birth_mm")
    and get_field("birth_dd")
):

    patient_dob = (
        f"{get_field('birth_yy')}-"
        f"{get_field('birth_mm').zfill(2)}-"
        f"{get_field('birth_dd').zfill(2)}"
    )

insured_dob = None

if (
    get_field("ins_dob_yy")
    and get_field("ins_dob_mm")
    and get_field("ins_dob_dd")
):

    insured_dob = (
        f"{get_field('ins_dob_yy')}-"
        f"{get_field('ins_dob_mm').zfill(2)}-"
        f"{get_field('ins_dob_dd').zfill(2)}"
    )

# =========================================================
# DATE OF SERVICE
# =========================================================

date_of_service = None

if (
    get_field("sv1_yy_from")
    and get_field("sv1_mm_from")
    and get_field("sv1_dd_from")
):

    date_of_service = (
        f"20{get_field('sv1_yy_from').zfill(2)}-"
        f"{get_field('sv1_mm_from').zfill(2)}-"
        f"{get_field('sv1_dd_from').zfill(2)}"
    )

# =========================================================
# SAFE BILLING PROVIDER
# =========================================================

billing_provider = " ".join(filter(None, [

    get_field("doc_name"),
    get_field("doc_street"),
    get_field("doc_location")

])).strip()

billing_provider = re.sub(r"\s+", " ", billing_provider)

billing_provider = billing_provider[:500]

# =========================================================
# HCPCS
# =========================================================

hcpcs_found = []

for i in range(1, 7):

    code = get_field(f"cpt{i}").upper()

    if re.fullmatch(r"[A-Z][0-9]{4}", code):

        hcpcs_found.append(code)

hcpcs_found = list(set(hcpcs_found))

# =========================================================
# MODIFIERS
# =========================================================

modifier_pairs = {}

all_modifiers = []

for i in range(1, 7):

    hcpc = get_field(f"cpt{i}").upper()

    if not hcpc:
        continue

    mods = []

    for m in [

        get_field(f"mod{i}"),
        get_field(f"mod{i}a"),
        get_field(f"mod{i}b"),
        get_field(f"mod{i}c")

    ]:

        m = m.upper().strip()

        if re.fullmatch(r"[A-Z0-9]{2}", m):

            mods.append(m)
            all_modifiers.append(m)

    modifier_pairs[hcpc] = list(set(mods))

all_modifiers = list(set(all_modifiers))

# =========================================================
# DIAGNOSIS
# =========================================================

diagnosis_codes = []

for i in range(1, 13):

    d = get_field(f"diagnosis{i}").upper()

    if d:
        diagnosis_codes.append(d)

diagnosis_codes = list(set(diagnosis_codes))

# =========================================================
# DEBUG
# =========================================================

print("\n================ HCPCS FOUND ================\n")
print(hcpcs_found)

print("\n================ MODIFIERS FOUND ================\n")
print(all_modifiers)

print("\n================ DIAGNOSIS FOUND ================\n")
print(diagnosis_codes)

print("\n================ HCPCS -> MODIFIERS ================\n")

for k, v in modifier_pairs.items():

    print(k, "=>", v)

# =========================================================
# INSERT CLAIM
# =========================================================

cursor.execute("""

INSERT INTO claims(

INSURANCE_TYPE,
PATIENT_LAST_NAME,
PATIENT_FIRST_NAME,
PATIENT_FULL_NAME,
INSURED_ID,
PATIENT_DOB,

INSURED_LAST_NAME,
INSURED_FIRST_NAME,
INSURED_FULL_NAME,

OTHER_INSURED_NAME,

PATIENT_ADDRESS,
INSURED_ADDRESS,

INSURED_POLICY_GROUP_OR_FECA_NUMBER,

DIAGNOSIS_OR_NATURE_OF_ILLNESS_OR_INJUIRY,
HCPC,

TOTAL_CHARGES,
AMOUNT_PAID,

PATIENT_SIGNATURE,

DATE_OF_SERVICE,

NAME_OF_REFERRING_PROVIDER_OR_OTHER_SERVICE,
NAME_OF_REFERRING_PROVIDER_OR_OTHER_SERVICE_17b_NPI,

FEDERAL_TAX_ID_NO,
PATIENT_ACCOUNT_NO,
ACCEPT_ASSIGNMENT,

SIGNER_OF_PHYSICIAN_OR_PROVIDER,

BILLING_PROVIDER_INFO_AND_PH_nO,
BILLING_PROVIDER_NUM,
PROVIDER_ID

)

VALUES(

%s,%s,%s,%s,%s,%s,
%s,%s,%s,
%s,
%s,%s,
%s,
%s,%s,
%s,%s,
%s,
%s,
%s,%s,
%s,%s,%s,
%s,
%s,%s,%s

)

""", (

get_field("insurance_type"),

patient_last_name,
patient_first_name,
patient_name,

get_field("insurance_id"),

patient_dob,

insured_last_name,
insured_first_name,
insured_name,

get_field("other_ins_name"),

get_field("pt_street"),
get_field("ins_street"),

get_field("other_ins_policy"),

",".join(diagnosis_codes),
",".join(hcpcs_found),

get_field("t_charge"),
get_field("amt_paid"),

get_field("pt_signature"),

date_of_service,

get_field("ref_physician"),
get_field("id_physician"),

get_field("tax_id"),
get_field("pt_account"),
get_field("assignment"),

get_field("physician_signature"),

billing_provider,

get_field("pin"),

get_field("grp")

))

patient_id = cursor.lastrowid

print(f"\nCLAIM INSERTED : {patient_id}")

# =========================================================
# PATIENTS TABLE
# =========================================================

cursor.execute("""

INSERT INTO patients(

patient_id,
patient_name,
dob,
insurance_id,
phone,
address,
city,
state,
zip_code,
provider_name,
npi,
total_charge,
amount_paid

)

VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

""", (

patient_id,

patient_name,

patient_dob,

get_field("insurance_id"),

f"{get_field('pt_areacode')}-{get_field('pt_phone')}",

get_field("pt_street"),

get_field("pt_city"),

get_field("pt_state"),

get_field("pt_zip"),

get_field("ref_physician"),

get_field("id_physician"),

get_field("t_charge") or 0,

get_field("amt_paid") or 0

))

# =========================================================
# PATIENT ADDRESS DETAILS
# =========================================================

cursor.execute("""

INSERT INTO patient_address_details(

patient_id,
patient_address,
city,
state,
zip_code,
telephone_number

)

VALUES(%s,%s,%s,%s,%s,%s)

""", (

patient_id,

get_field("pt_street"),

get_field("pt_city"),

get_field("pt_state"),

get_field("pt_zip"),

f"{get_field('pt_areacode')}-{get_field('pt_phone')}"

))

# =========================================================
# INSURED ADDRESS DETAILS
# =========================================================

cursor.execute("""

INSERT INTO insured_address_details(

patient_id,
insured_address,
city,
state,
zip_code,
telephone_number

)

VALUES(%s,%s,%s,%s,%s,%s)

""", (

patient_id,

get_field("ins_street"),

get_field("ins_city"),

get_field("ins_state"),

get_field("ins_zip"),

f"{get_field('ins_phone area')}-{get_field('ins_phone')}"

))

# =========================================================
# INSURED POLICY DETAILS
# =========================================================

cursor.execute("""

INSERT INTO insured_policy_details(

patient_id,
insured_date_of_birth,
sex,
other_claim_id,
insurance_plan_name,
another_health_plan

)

VALUES(%s,%s,%s,%s,%s,%s)

""", (

patient_id,

insured_dob,

get_field("ins_sex"),

get_field("other_ins_policy"),

get_field("ins_plan_name"),

get_field("ins_benefit_plan")

))

# =========================================================
# OTHER INSURED DETAILS
# =========================================================

cursor.execute("""

INSERT INTO other_insured_details(

patient_id,
other_insured_name,
other_insured_policy_number,
preserved_for_nucc_use,
insured_plan_name_or_program_name

)

VALUES(%s,%s,%s,%s,%s)

""", (

patient_id,

get_field("other_ins_name"),

get_field("other_ins_policy"),

get_field("nucc use"),

get_field("other_ins_plan_name")

))

# =========================================================
# HCPCS CODES
# =========================================================

for hcpc in hcpcs_found:

    cursor.execute("""

    INSERT INTO hcpcs_codes(

    patient_id,
    hcpcs_code

    )

    VALUES(%s,%s)

    """, (

    patient_id,
    hcpc

    ))

# =========================================================
# MODIFIER CODES
# =========================================================

# =========================================================
# MODIFIER CODES
# =========================================================

for i in range(1, 7):

    hcpc = get_field(f"cpt{i}").upper().strip()

    if not hcpc:
        continue

    modifiers = [

        get_field(f"mod{i}"),
        get_field(f"mod{i}a"),
        get_field(f"mod{i}b"),
        get_field(f"mod{i}c")

    ]

    for mod in modifiers:

        mod = mod.upper().strip()

        if re.fullmatch(r"[A-Z0-9]{2}", mod):

            cursor.execute("""

            INSERT INTO modifier_codes(

            patient_id,
            hcpc_code,
            modifier_code

            )

            VALUES(%s,%s,%s)

            """, (

            patient_id,
            hcpc,
            mod

            ))
# =========================================================
# DIAGNOSIS DETAILS
# =========================================================

for d in diagnosis_codes:

    cursor.execute("""

    INSERT INTO diagnosis_details(

    patient_id,
    diagnosis_code

    )

    VALUES(%s,%s)

    """, (

    patient_id,
    d

    ))

# =========================================================
# HCPC DETAILS
# =========================================================

for i in range(1, 7):

    hcpc = get_field(f"cpt{i}")

    if not hcpc:
        continue

    from_date = ""
    to_date = ""

    if get_field(f"sv{i}_yy_from"):

        from_date = (
            f"20{get_field(f'sv{i}_yy_from')}-"
            f"{get_field(f'sv{i}_mm_from').zfill(2)}-"
            f"{get_field(f'sv{i}_dd_from').zfill(2)}"
        )

    if get_field(f"sv{i}_yy_end"):

        to_date = (
            f"20{get_field(f'sv{i}_yy_end')}-"
            f"{get_field(f'sv{i}_mm_end').zfill(2)}-"
            f"{get_field(f'sv{i}_dd_end').zfill(2)}"
        )

    cursor.execute("""

    INSERT INTO hcpc_details(

    patient_id,
    date_of_service_from,
    date_of_service_to,
    place_of_service,
    emg,
    hcpc,
    modifier1,
    modifier2,
    modifier3,
    modifier4,
    dx_pointer,
    charges,
    units,
    epsdt_family_plan,
    id_qual,
    rendering_provider_id

    )

    VALUES(

    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s

    )

    """, (

    patient_id,

    from_date,
    to_date,

    get_field(f"place{i}"),

    get_field(f"emg{i}"),

    hcpc,

    get_field(f"mod{i}"),
    get_field(f"mod{i}a"),
    get_field(f"mod{i}b"),
    get_field(f"mod{i}c"),

    get_field(f"diag{i}"),

    get_field(f"ch{i}") or 0,

    get_field(f"day{i}"),

    get_field(f"epsdt{i}"),

    get_field(f"local{i}"),

    get_field(f"local{i}a")

    ))

# =========================================================
# CLOSE
# =========================================================

cursor.close()
conn.close()

print("\n========================================")
print("CMS1500 EXTRACTION COMPLETED")
print("========================================")