import pytest
import io
import csv
from fastapi import UploadFile, HTTPException
from src.lumber_estimator.web.server import validate_csv_headers

def create_upload_file(content: str, filename: str = "test.csv"):
    f = io.BytesIO(content.encode('utf-8'))
    return UploadFile(file=f, filename=filename)

def test_validate_csv_headers_success():
    content = "Description,Length,Width,Quantity,Material Type,Material\nPart A,10,5,1,Lumber,Oak"
    file = create_upload_file(content)
    expected = ['Description', 'Length', 'Width', 'Quantity', 'Material Type', 'Material']
    # Should not raise any exception
    validate_csv_headers(file, expected)

def test_validate_csv_headers_empty_file():
    file = create_upload_file("")
    with pytest.raises(HTTPException) as exc:
        validate_csv_headers(file, ['any'])
    assert exc.value.status_code == 400
    assert "Uploaded file is empty" in str(exc.value.detail)

def test_validate_csv_headers_mismatched_headers():
    content = "Wrong,Header,Row\nPart A,10,5"
    file = create_upload_file(content)
    with pytest.raises(HTTPException) as exc:
        validate_csv_headers(file, ['Description', 'Length', 'Width'])
    assert exc.value.status_code == 400
    assert "Invalid CSV headers" in str(exc.value.detail)

def test_validate_csv_headers_mismatched_columns():
    content = "Description,Length,Width\nPart A,10\nPart B,20,30"
    file = create_upload_file(content)
    with pytest.raises(HTTPException) as exc:
        validate_csv_headers(file, ['Description', 'Length', 'Width'])
    assert exc.value.status_code == 400
    assert "Row 2 in CSV has mismatched column count" in str(exc.value.detail)

def test_validate_csv_headers_inventory_success():
    # Label,Length,Width,Quantity,Material Type,Material
    content = "Label,Length,Width,Quantity,Material Type,Material\nBoard A,96,6,2,Lumber,Walnut"
    file = create_upload_file(content)
    expected = ['Label', 'Length', 'Width', 'Quantity', 'Material Type', 'Material']
    validate_csv_headers(file, expected)
