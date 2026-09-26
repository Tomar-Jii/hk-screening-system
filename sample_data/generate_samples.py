import numpy as np
import cv2
import os

def create_sample_passport(
    filename: str,
    country: str,
    holder_name: str,
    doc_number: str,
    dob: str,
    expiry: str,
    sex: str,
    mrz_line1: str,
    mrz_line2: str,
    tamper_type: str = "none"
):
    # Canvas size: 800 x 540 (Standard ID-3 / Passport page aspect ratio)
    img = np.ones((540, 800, 3), dtype=np.uint8) * 245
    
    # Background security pattern / gradient
    for y in range(540):
        img[y, :, 0] = int(240 - (y * 0.05))
        img[y, :, 1] = int(245 - (y * 0.03))
        img[y, :, 2] = int(250 - (y * 0.02))

    # Passport Header
    cv2.putText(img, f"REPUBLIC OF {country} / PASSPORT", (40, 45), cv2.FONT_HERSHEY_DUPLEX, 0.75, (20, 20, 60), 2)
    cv2.putText(img, "TYPE: P   CODE: " + country + "   PASSPORT NO: " + doc_number, (40, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 50, 50), 1)

    # Document Photo Box (Passport holder photo)
    cv2.rectangle(img, (40, 100), (220, 330), (180, 180, 180), 2)
    # Draw simple avatar face
    cv2.circle(img, (130, 190), 45, (160, 140, 130), -1) # Head
    cv2.ellipse(img, (130, 290), (60, 45), 0, 0, 180, (50, 70, 120), -1) # Shoulders
    cv2.circle(img, (115, 180), 5, (40, 40, 40), -1) # Left eye
    cv2.circle(img, (145, 180), 5, (40, 40, 40), -1) # Right eye
    cv2.putText(img, "[PHOTO]", (100, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Primary Data Fields
    fields = [
        ("SURNAME / NOM", holder_name.split()[1] if len(holder_name.split()) > 1 else holder_name),
        ("GIVEN NAMES / PRENOMS", holder_name.split()[0]),
        ("NATIONALITY / NATIONALITE", country),
        ("DATE OF BIRTH / DATE DE NAISSANCE", dob),
        ("SEX / SEXE", sex),
        ("DATE OF EXPIRY / DATE D'EXPIRATION", expiry),
        ("AUTHORITY / AUTORITE", "PASSPORT ISSUING OFFICE")
    ]

    y_pos = 115
    for label, val in fields:
        cv2.putText(img, label, (250, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)
        
        # Apply tampering artifact if specified
        if tamper_type == "font_mismatch" and label.startswith("DATE OF BIRTH"):
            # Spliced font
            cv2.putText(img, val, (250, y_pos + 18), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.65, (0, 0, 0), 2)
        elif tamper_type == "spliced_dob" and label.startswith("DATE OF BIRTH"):
            # Mismatched digital patch
            cv2.rectangle(img, (245, y_pos + 2), (450, y_pos + 24), (255, 255, 200), -1)
            cv2.putText(img, "1999-12-31", (250, y_pos + 18), cv2.FONT_HERSHEY_DUPLEX, 0.6, (10, 10, 10), 2)
        else:
            cv2.putText(img, val, (250, y_pos + 18), cv2.FONT_HERSHEY_DUPLEX, 0.55, (20, 20, 20), 1)
            
        y_pos += 33

    # MRZ Area (White / Monospace Box at bottom)
    cv2.rectangle(img, (20, 390), (780, 510), (255, 255, 255), -1)
    cv2.rectangle(img, (20, 390), (780, 510), (200, 200, 200), 1)
    
    cv2.putText(img, mrz_line1, (35, 435), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (10, 10, 10), 2)
    cv2.putText(img, mrz_line2, (35, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (10, 10, 10), 2)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    cv2.imwrite(filename, img)
    return filename

def generate_all_samples():
    base_dir = r"C:\Users\amit\.gemini\antigravity\scratch\fake-doc-screening\sample_data"
    
    # 1. Genuine Active Passport
    create_sample_passport(
        os.path.join(base_dir, "sample_1_genuine.png"),
        country="IND",
        holder_name="VIKRAM SHARMA",
        doc_number="J82947192",
        dob="14 AUG 1994",
        expiry="20 NOV 2031",
        sex="M",
        mrz_line1="P<INDSHARMA<<VIKRAM<<<<<<<<<<<<<<<<<<<<<<<<<",
        mrz_line2="J829471927IND9408144M3111204<<<<<<<<<<<<<<04",
        tamper_type="none"
    )

    # 2. Expired Passport
    create_sample_passport(
        os.path.join(base_dir, "sample_2_expired.png"),
        country="RUS",
        holder_name="ELENA ROSTOVA",
        doc_number="E10293847",
        dob="22 MAR 1988",
        expiry="10 MAY 2021",
        sex="F",
        mrz_line1="P<RUSROSTOVA<<ELENA<<<<<<<<<<<<<<<<<<<<<<<<<",
        mrz_line2="E102938472RUS8803225F2105108<<<<<<<<<<<<<<02",
        tamper_type="none"
    )

    # 3. Blacklisted Document (Interpol Red Notice)
    create_sample_passport(
        os.path.join(base_dir, "sample_3_blacklisted.png"),
        country="GBR",
        holder_name="MARCUS VANCE",
        doc_number="X99887766",
        dob="05 DEC 1975",
        expiry="18 AUG 2029",
        sex="M",
        mrz_line1="P<GBRVANCE<<MARCUS<<<<<<<<<<<<<<<<<<<<<<<<<<",
        mrz_line2="X998877664GBR7512053M2908182<<<<<<<<<<<<<<08",
        tamper_type="none"
    )

    # 4. Deliberately Tampered Document (DOB & Font Splice)
    create_sample_passport(
        os.path.join(base_dir, "sample_4_tampered_dob.png"),
        country="IND",
        holder_name="VIKRAM SHARMA",
        doc_number="J82947192",
        dob="31 DEC 1999", # Tampered visual DOB
        expiry="20 NOV 2031",
        sex="M",
        mrz_line1="P<INDSHARMA<<VIKRAM<<<<<<<<<<<<<<<<<<<<<<<<<",
        mrz_line2="J829471927IND9912314M3111204<<<<<<<<<<<<<<04", # Tampered MRZ check digit mismatch
        tamper_type="spliced_dob"
    )

    # 5. Matching Live Selfie sample
    selfie_img = np.ones((400, 400, 3), dtype=np.uint8) * 230
    cv2.circle(selfie_img, (200, 170), 75, (160, 140, 130), -1)
    cv2.ellipse(selfie_img, (200, 350), (110, 80), 0, 0, 180, (50, 70, 120), -1)
    cv2.circle(selfie_img, (175, 155), 8, (40, 40, 40), -1)
    cv2.circle(selfie_img, (225, 155), 8, (40, 40, 40), -1)
    cv2.putText(selfie_img, "TRAVELER LIVE WEBCAM CAPTURE", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.imwrite(os.path.join(base_dir, "sample_selfie_matching.png"), selfie_img)

if __name__ == "__main__":
    generate_all_samples()
    print("All synthetic demo datasets generated successfully in sample_data/")
