import pytest
from services.ocr_mrz.mrz_parser import calculate_check_digit, verify_check_digit, MRZParser

def test_mrz_char_weights():
    # Test ICAO 9303 standard check digit calculations
    # 'HA672242<6' -> Check digit 6
    doc_raw = "HA672242<"
    assert calculate_check_digit(doc_raw) == 6
    assert verify_check_digit(doc_raw, "6") is True
    assert verify_check_digit(doc_raw, "5") is False

def test_mrz_td3_parsing():
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

    parsed = MRZParser.parse_td3(line1, line2)
    assert parsed["mrz_type"] == "TD3"
    assert parsed["issuing_country"] == "UTO"
    assert parsed["surname"] == "ERIKSSON"
    assert parsed["given_names"] == "ANNA MARIA"
    assert parsed["document_number"] == "L898902C3"
    assert parsed["nationality"] == "UTO"
    assert parsed["sex"] == "Female"
    assert parsed["date_of_birth"] == "1974-08-12"
    assert parsed["expiry_date"] == "2012-04-15"

def test_mrz_checksum_tamper_detection():
    # Alter DOB by 1 digit without adjusting check digit
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408132F1204159ZE184226B<<<<<10" # 740812 modified to 740813

    parsed = MRZParser.parse_td3(line1, line2)
    assert parsed["checksums"]["dob_valid"] is False
    assert parsed["is_valid"] is False
    assert any("Date of Birth check digit mismatch" in fail for fail in parsed["checksum_failures"])
