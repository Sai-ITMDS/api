from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import csv
import os
from pathlib import Path

# Initialize app
app = FastAPI()

# Enable CORS for GET from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# Load CSV once at startup
CSV_PATH = Path(__file__).parent / "apiprac" / "q-fastapi.csv"

def load_students() -> List[dict]:
    students: List[dict] = []
    if not CSV_PATH.exists():
        return students

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Keep the same column names and order; convert studentId to int when possible
            student = {
                "studentId": int(row.get("studentId")) if row.get("studentId") and row.get("studentId").isdigit() else row.get("studentId"),
                "class": row.get("class"),
            }
            students.append(student)
    return students


STUDENTS = load_students()


@app.get("/api")
def get_students(class_: Optional[List[str]] = Query(None, alias="class")):
    """
    Return students in the same order as CSV. Optional repeated `class` query parameter filters results.
    Example: /api?class=1A&class=1B
    """
    if not class_:
        return {"students": STUDENTS}

    # Filter while preserving CSV order
    allowed = set(class_)
    filtered = [s for s in STUDENTS if s.get("class") in allowed]
    return {"students": filtered}


if __name__ == "__main__":
    # Run with: python3 students_api.py
    import uvicorn
    port = int(os.environ.get("PORT", 5002))
    uvicorn.run("students_api:app", host="127.0.0.1", port=port, reload=True)
