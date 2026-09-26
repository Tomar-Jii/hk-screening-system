import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# ICAO 9303 Character Weights: 7, 3, 1 repeating
ICAO_WEIGHTS = [7, 3, 1]

def mrz_char_value(char: str) -> int:
    """
    Computes the numeric value of an MRZ character according to ICAO 9303 Part 3.
    0-9 -> 0-9
    A-Z -> 10-35
    < -> 0
    """
    char = char.upper()
    if '0' <= char <= '9':
        return int(char)
    elif 'A' <= char <= 'Z':
        return ord(char) - ord('A') + 10
    elif char == '<':
        return 0
    return 0

def calculate_check_digit(data_str: str) -> int:
    """
    Calculates the ICAO 9303 check digit using weights [7, 3, 1].
    """
    total = 0
    for i, char in enumerate(data_str):
        weight = ICAO_WEIGHTS[i % 3]
        val = mrz_char_value(char)
        total += val * weight
    return total % 10

def verify_check_digit(data_str: str, check_digit_char: str) -> bool:
    """
    Verifies if check_digit_char matches the calculated check digit for data_str.
    """
    try:
        expected = calculate_check_digit(data_str)
        actual = int(check_digit_char)
        return expected == actual
    except (ValueError, TypeError):
        return False

def parse_mrz_date(date_str: str, is_expiry: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses YYMMDD into YYYY-MM-DD format.
    Pivot logic:
    - For DOB: YY > (current_year % 100) -> 19YY, else 20YY
    - For Expiry: always assumes current century / future unless expired
    """
    if len(date_str) != 6 or not date_str.isdigit():
        return None, "Invalid date format in MRZ (must be 6 digits YYMMDD)"
    
    yy = int(date_str[0:2])
    mm = int(date_str[2:4])
    dd = int(date_str[4:6])

    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return None, f"Invalid month ({mm}) or day ({dd}) in MRZ date."

    current_year = datetime.now().year
    current_yy = current_year % 100

    if is_expiry:
        # Expiry is almost always 20YY in modern passports
        full_year = 2000 + yy
    else:
        # DOB
        if yy > current_yy:
            full_year = 1900 + yy
        else:
            full_year = 2000 + yy

    try:
        formatted = f"{full_year:04d}-{mm:02d}-{dd:02d}"
        # Validate calendar validity (leap year etc.)
        datetime.strptime(formatted, "%Y-%m-%d")
        return formatted, None
    except ValueError as ve:
        return None, str(ve)

class MRZParser:
    """
    Parser for ICAO 9303 TD3 (Passports - 2 lines x 44 chars) and TD1/TD2 formats.
    """

    @staticmethod
    def clean_mrz_text(raw_text: str) -> list[str]:
        """
        Extracts and sanitizes 44-character (TD3) or 30/36-character MRZ lines.
        """
        lines = []
        for raw_line in raw_text.splitlines():
            # Keep only A-Z, 0-9, and <
            cleaned = re.sub(r'[^A-Z0-9<]', '', raw_line.upper())
            if len(cleaned) >= 30: # Potential MRZ line
                lines.append(cleaned)
        return lines

    @staticmethod
    def parse_td3(line1: str, line2: str) -> Dict[str, Any]:
        """
        Parses official ICAO Doc 9303 TD3 standard (Passport format - 2 lines of 44 characters):
        Line 1:
          P<[Country 3][Surname]<<[Given Names]... (44 chars)
        Line 2:
          [Doc# 9][Chk 1][Nationality 3][DOB 6][Chk 1][Sex 1][Expiry 6][Chk 1][Optional 14][Chk 1][Composite Chk 1]
        """
        line1 = line1.ljust(44, '<')[:44]
        line2 = line2.ljust(44, '<')[:44]

        # Line 1 parsing
        doc_type = line1[0:2].replace('<', '')
        issuing_country = line1[2:5].replace('<', '')
        names_part = line1[5:44]
        name_split = names_part.split('<<')
        surname = name_split[0].replace('<', ' ').strip()
        given_names = " ".join([part.replace('<', ' ').strip() for part in name_split[1:]]).strip() if len(name_split) > 1 else ""

        # Line 2 parsing
        doc_number_raw = line2[0:9]
        doc_number = doc_number_raw.replace('<', '')
        doc_num_chk = line2[9]
        
        nationality = line2[10:13].replace('<', '')
        
        dob_raw = line2[13:19]
        dob_chk = line2[19]
        
        sex = line2[20]
        if sex not in ['M', 'F', 'X', '<']:
            sex = 'U'
        else:
            sex = 'Unspecified' if sex in ['X', '<'] else ('Male' if sex == 'M' else 'Female')
            
        expiry_raw = line2[21:27]
        expiry_chk = line2[27]
        
        optional_data = line2[28:42]
        optional_chk = line2[42]
        composite_chk = line2[43]

        # Validation Checks
        doc_num_valid = verify_check_digit(doc_number_raw, doc_num_chk)
        dob_valid = verify_check_digit(dob_raw, dob_chk)
        expiry_valid = verify_check_digit(expiry_raw, expiry_chk)

        # Composite check digit data in TD3:
        # doc_number + doc_num_chk + dob + dob_chk + expiry + expiry_chk + optional_data + optional_chk
        composite_data = line2[0:10] + line2[13:20] + line2[21:43]
        composite_valid = verify_check_digit(composite_data, composite_chk)

        dob_formatted, dob_err = parse_mrz_date(dob_raw, is_expiry=False)
        expiry_formatted, expiry_err = parse_mrz_date(expiry_raw, is_expiry=True)

        checksum_failures = []
        if not doc_num_valid:
            checksum_failures.append("Document number check digit mismatch (ICAO 9303 checksum failed).")
        if not dob_valid:
            checksum_failures.append("Date of Birth check digit mismatch.")
        if not expiry_valid:
            checksum_failures.append("Expiration date check digit mismatch.")
        if not composite_valid:
            checksum_failures.append("Composite/Overall MRZ check digit mismatch.")
        if dob_err:
            checksum_failures.append(f"DOB format error: {dob_err}")
        if expiry_err:
            checksum_failures.append(f"Expiry format error: {expiry_err}")

        all_valid = len(checksum_failures) == 0

        return {
            "mrz_type": "TD3",
            "is_valid": all_valid,
            "document_type": doc_type or "Passport",
            "issuing_country": issuing_country,
            "surname": surname,
            "given_names": given_names,
            "full_name": f"{given_names} {surname}".strip(),
            "document_number": doc_number,
            "nationality": nationality,
            "date_of_birth": dob_formatted,
            "date_of_birth_raw": dob_raw,
            "sex": sex,
            "expiry_date": expiry_formatted,
            "expiry_date_raw": expiry_raw,
            "optional_data": optional_data.replace('<', ''),
            "checksums": {
                "document_number_valid": doc_num_valid,
                "dob_valid": dob_valid,
                "expiry_valid": expiry_valid,
                "composite_valid": composite_valid
            },
            "checksum_failures": checksum_failures,
            "raw_mrz_lines": [line1, line2]
        }
