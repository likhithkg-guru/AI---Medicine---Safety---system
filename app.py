from flask import Flask, render_template, request
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
from medicine_db import medicines
from datetime import datetime
import sqlite3

app = Flask(__name__)

# --------------------------------
# DATABASE
# --------------------------------
conn = sqlite3.connect("complaints.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop TEXT,
    location TEXT,
    medicine TEXT,
    complaint TEXT
)
""")

conn.commit()
conn.close()

# --------------------------------
# TESSERACT PATH
# --------------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --------------------------------
# HOME PAGE
# --------------------------------
@app.route("/")
def home():
    return render_template("home.html")

# --------------------------------
# SCANNER PAGE
# --------------------------------
@app.route("/scanner", methods=["GET", "POST"])
def scanner():

    medicine_name = ""
    composition = ""
    uses = ""
    side_effects = ""
    mfg = ""
    exp = ""
    status = ""
    fake_status = ""

    if request.method == "POST":

        file = request.files["image"]

        if file:

            file_path = "medicine.jpg"
            file.save(file_path)

            # Open image
            img = Image.open(file_path)

            # Improve OCR
            img = img.resize((img.width * 3, img.height * 3))
            img = img.convert("L")

            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(3)

            img = img.filter(ImageFilter.SHARPEN)

            # OCR TEXT
            text = pytesseract.image_to_string(img)

            print("\nExtracted Text:\n")
            print(text)

            # EXTRACT DATES
            dates = re.findall(r'\d{2}/\d{4}', text)

            if len(dates) >= 2:
                mfg = dates[0]
                exp = dates[1]

            # CLEAN TEXT
            clean_text = text.lower()
            clean_text = clean_text.replace(" ", "")
            clean_text = clean_text.replace("\n", "")

            # MEDICINE DETECTION
            found = False

            for med in medicines:

                med_clean = med.lower().replace(" ", "")

                if med_clean in clean_text:

                    found = True
                    composition = medicines[med]
                    ["composition"]
                    medicine_name = med
                    uses = medicines[med]["uses"]
                    side_effects = medicines[med]["side_effects"]

                    fake_status = "REAL MEDICINE"

                    # EXPIRY CHECK
                    try:

                        expiry_date = datetime.strptime(exp, "%m/%Y")

                        if expiry_date < datetime.now():
                            status = "Expired Medicine"
                        else:
                            status = "Safe Medicine"

                    except:
                        status = "Unknown"

                    break

            # IF NOT FOUND
            if not found:

                medicine_name = "Unknown Medicine"
                uses = "Not Available"
                side_effects = "Not Available"

                fake_status = "POSSIBLE FAKE MEDICINE"
                status = "Unsafe"

    return render_template(
        "index.html",
        medicine=medicine_name,
        composition = composition,
        uses=uses,
        side_effects=side_effects,
        mfg=mfg,
        exp=exp,
        status=status,
        fake_status=fake_status
    )

# --------------------------------
# MEDICINE INFO PAGE
# --------------------------------
@app.route("/medicine_info", methods=["GET", "POST"])
def medicine_info():

    result = None
    searched = False
    medicine_text = ""

    medicines = {

        "dolo 650": {
            "composition":"Paracetamol",
            "uses":"Fever and body pain",
            "side_effects":"Nausea"
        },

        "paracetamol": {
            "composition":"Paracetamol",
            "uses":"Fever and pain relief",
            "side_effects":"Liver damage if overdosed"
        },

        "crocin": {
            "composition":"Paracetamol",
            "uses":"Cold and fever",
            "side_effects":"Vomiting"
        },

        "cetirizine": {
            "composition":"Cetirizine",
            "uses":"Cold and allergy",
            "side_effects":"Sleepiness"
        }

    }

    if request.method == "POST":

        searched = True

        medicine_text = request.form["medicine"].lower()

        for med in medicines:

            if med in medicine_text:

                result = medicines[med]

                result["name"] = med.upper()

                break

    return render_template(
        "medicine_info.html",
        result=result,
        searched=searched,
        medicine_text=medicine_text
    )

# --------------------------------
# AI ASSISTANT
# --------------------------------
@app.route("/assistant", methods=["GET", "POST"])
def assistant():

    answer = ""
    question = ""

    if request.method == "POST":

        question = request.form["question"].lower()

        # FEVER
        if (
            "fever" in question
            or "temperature" in question
            or "body pain" in question
        ):

            answer = """
            You may have fever symptoms.

            Common medicines:
            • Dolo 650
            • Paracetamol

            Advice:
            • Drink plenty of water
            • Take proper rest
            • Eat healthy food
            """

        # HEADACHE
        elif (
            "headache" in question
            or "head pain" in question
            or "migraine" in question
        ):

            answer = """
            You may have headache symptoms.

            Common medicine:
            • Paracetamol

            Advice:
            • Sleep properly
            • Stay hydrated
            • Avoid stress
            """

        # COLD / NOSE BLOCK
        elif (
            "cold" in question
            or "nose blocked" in question
            or "blocked nose" in question
            or "runny nose" in question
            or "sneezing" in question
            or "nose" in question
        ):

            answer = """
            It may be common cold or allergy symptoms.

            Common medicines:
            • Cetirizine
            • Cold tablets

            Advice:
            • Drink warm water
            • Take steam inhalation
            • Take rest
            """

        # COUGH
        elif (
            "cough" in question
            or "throat pain" in question
            or "sore throat" in question
        ):

            answer = """
            You may have cough symptoms.

            Suggestions:
            • Cough syrup
            • Warm water
            • Steam inhalation

            Avoid cold drinks.
            """

        # STOMACH PAIN
        elif (
            "stomach" in question
            or "gas" in question
            or "acidity" in question
            or "vomit" in question
        ):

            answer = """
            You may have stomach irritation.

            Advice:
            • Avoid oily food
            • Drink water
            • Eat simple food

            Consult doctor if pain continues.
            """

        # BREATHING / ASTHMA
        elif (
            "asthma" in question
            or "breathing" in question
            or "breath problem" in question
            or "wheezing" in question
        ):

            answer = """
            Breathing problems may require medical attention.

            Common medicine:
            • Doxofylline Tablets IP

            Please consult a doctor before taking asthma medicines.
            """

        # SIDE EFFECTS
        elif (
            "side effect" in question
            or "reaction" in question
        ):

            answer = """
            Some medicines may cause:
            • Nausea
            • Headache
            • Dizziness
            • Sleepiness
            """

        # EXPIRED MEDICINE
        elif (
            "expired" in question
            or "expiry" in question
        ):

            answer = """
            Expired medicines should NOT be used.

            Always check expiry date before consuming medicines.
            """

        # FAKE MEDICINE
        elif (
            "fake medicine" in question
            or "duplicate medicine" in question
        ):

            answer = """
            Fake medicines can be dangerous.

            Always buy medicines from trusted pharmacies.
            """

        # DOLO
        elif (
            "dolo" in question
            or "dolo 650" in question
        ):

            answer = """
            Dolo 650 is commonly used for:
            • Fever
            • Body pain
            • Mild headache

            Usually taken after food.
            """

        # PARACETAMOL
        elif "paracetamol" in question:

            answer = """
            Paracetamol helps reduce:
            • Fever
            • Headache
            • Mild body pain
            """

        # DEFAULT
        else:

            answer = """
            Sorry, I could not fully understand.

            Try questions like:
            • I have fever
            • My nose is blocked
            • I have cough
            • Tell me about Dolo 650
            """

    return render_template(
        "assistant.html",
        answer=answer,
        question = question
    )

# --------------------------------
# COMPLAINT PAGE
# --------------------------------
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    success = False

    if request.method == "POST":

        shop = request.form["shop"]
        location = request.form["location"]
        medicine = request.form["medicine"]
        complaint_text = request.form["complaint"]

        conn = sqlite3.connect("complaints.db")

        cursor = conn.cursor()


        cursor.execute(
            "INSERT INTO complaints(shop, location, medicine, complaint) VALUES(?,?,?,?)",
            (shop, location, medicine, complaint_text)
        )

        conn.commit()

        conn.close()

        success = True

    return render_template(
        "complaint.html",
        success=success
    )

# --------------------------------
# VIEW COMPLAINTS
# --------------------------------
@app.route("/view_complaints")
def view_complaints():

    conn = sqlite3.connect("complaints.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM complaints")

    complaints = cursor.fetchall()

    conn.close()

    return render_template(
        "view_complaints.html",
        complaints=complaints
    )

# --------------------------------
# ABOUT PAGE
# --------------------------------
@app.route("/about")
def about():
    return render_template("about.html")

# --------------------------------
# RUN FLASK
# --------------------------------
if __name__ == "__main__":
    app.run(debug=True)