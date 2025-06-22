import io
import pytest
from fastapi.testclient import TestClient
from interfaces.rest_api import app

client = TestClient(app)

def test_txt_file_upload():
    txt_content = b"This is a test file."
    response = client.post(
        "/analyze",
        files={"file": ("test.txt", io.BytesIO(txt_content), "text/plain")},
        data={"text": "Analyze this text file."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "analysis" in data["result"]


def test_csv_file_upload():
    csv_content = b"col1,col2\n1,2\n3,4"
    response = client.post(
        "/analyze",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
        data={"text": "Analyze this CSV file."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "analysis" in data["result"]


def test_proactive_analysis_on_file_only():
    csv_content = b"col1,col2\n1,2\n3,4"
    response = client.post(
        "/analyze",
        files={"file": ("matches.csv", io.BytesIO(csv_content), "text/csv")},
        data={}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    analysis = data["result"].get("analysis", "").lower()
    assert "analysis complete" in analysis
    assert not any(
        phrase in analysis for phrase in ["which data", "please provide the file content", "can you be more specific"]
    )


def test_pdf_file_upload():
    pdf_content = b"%PDF-1.4 test pdf content"
    response = client.post(
        "/analyze",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
        data={"text": "Analyze this PDF file."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "analysis" in data["result"]


def test_unsupported_file_type():
    xlsx_content = b"PK\x03\x04 test xlsx content"
    response = client.post(
        "/analyze",
        files={"file": ("test.xlsx", io.BytesIO(xlsx_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"text": "Analyze this Excel file."}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert "unsupported file type" in data["message"].lower()
