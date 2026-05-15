from flask import Flask, render_template, request
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
from medicine_db import medicines
from datetime import datetime
import sqlite3

app = Flask(__name__)

# -----------------------------
# CREATE DATABASE
# -----------------------------
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

# -----------------------------
# Tesseract Path
# -----------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -----------------------------
# SCANNER PAGE
# -----------------------------
@app.route("/scanner", methods=["GET", "POST"])
def scanner():

    medicine_name = ""
    uses = ""
    side_effects = ""
    mfg = ""
    exp = ""
    status = ""
    fake_status = ""

    if request.method == "POST":

        file = request.files["image"]

        if file:

            # Save uploaded image
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

            # OCR Text
            text = pytesseract.image_to_string(img)

            print("\nExtracted Text:\n")
            print(text)

            # Extract Dates
            dates = re.findall(r'\d{2}/\d{4}', text)

            if len(dates) >= 2:
                mfg = dates[0]
                exp = dates[1]

            # Clean OCR Text
            clean_text = text.lower()
            clean_text = clean_text.replace(" ", "")
            clean_text = clean_text.replace("\n", "")

            # -----------------------------
            # Medicine Detection
            # -----------------------------
            found = False

            for med in medicines:

                med_clean = med.lower().replace(" ", "")

                if med_clean in clean_text:

                    found = True

                    medicine_name = med
                    uses = medicines[med]["uses"]
                    side_effects = medicines[med]["side_effects"]

                    fake_status = "REAL MEDICINE"

                    # Expiry Check
                    try:

                        expiry_date = datetime.strptime(exp, "%m/%Y")

                        if expiry_date < datetime.now():
                            status = "Expired"
                        else:
                            status = "Safe"

                    except:
                        status = "Unknown"

                    break

            # -----------------------------
            # Fake Detection
            # -----------------------------
            if not found:

                medicine_name = "Unknown Medicine"

                uses = "Not Available"

                side_effects = "Not Available"

                fake_status = "POSSIBLE FAKE MEDICINE"

                status = "Unsafe"

    return render_template(
        "index.html",
        medicine=medicine_name,
        uses=uses,
        side_effects=side_effects,
        mfg=mfg,
        exp=exp,
        status=status,
        fake_status=fake_status
    )


# -----------------------------
# MEDICINE INFO PAGE
# -----------------------------
@app.route("/medicine_info", methods=["GET", "POST"])
def medicine_info():

    result = None
    searched = False

    if request.method == "POST":

        searched = True

        medicine_name = request.form["medicine"]

        for med in medicines:

            if medicine_name.lower() == med.lower():

                result = medicines[med]

                result["name"] = med

                break

    return render_template(
        "medicine_info.html",
        result=result,
        searched=searched
    )


# -----------------------------
# COMPLAINT PAGE
# -----------------------------
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    success = False

    if request.method == "POST":

        shop = request.form["shop"]
        location = request.form["location"]
        medicine = request.form["medicine"]
        complaint_text = request.form["complaint"]

        # Save Complaint
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


# -----------------------------
# VIEW COMPLAINTS PAGE
# -----------------------------
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


# -----------------------------
# ABOUT PAGE
# -----------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# -----------------------------
# RUN FLASK
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)