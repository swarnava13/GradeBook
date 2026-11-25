"""
data_structures.py  -  Component 3: Data structures
Owner: Aditiya Sahrawat (25BTRDC003)
Students are kept in a dictionary with nested subject -> mark dictionaries:

students = {
    "25BTRDS001": {"name": "Asha Rao",
                   "marks": {"Maths": 86, "Python": 91, ...}}
}
"""


def add_student(students, usn, name, subjects):
    """Add a student with every subject mark set to None (not entered yet)."""
    if usn in students:
        raise KeyError(f"Student {usn} already exists.")
    students[usn] = {"name": name, "marks": {s: None for s in subjects}}   # dict comprehension


def set_mark(students, usn, subject, mark):
    if usn not in students:
        raise KeyError(f"No student with USN {usn}.")
    students[usn]["marks"][subject] = mark


def delete_student(students, usn):
    if usn not in students:
        raise KeyError(f"No student with USN {usn}.")
    return students.pop(usn)


def search(students, query):
    """Search by exact USN or by part of the name (case-insensitive)."""
    query = query.strip()
    if query.upper() in students:
        return [query.upper()]
    q = query.lower()
    return [usn for usn, info in students.items() if q in info["name"].lower()]   # list comprehension


def missing_marks(students):
    """Set of USNs that still have at least one subject without marks."""
    return {usn for usn, info in students.items() if None in info["marks"].values()}


def to_rows(students):
    """Flatten the nested dictionary into a list of tuples for saving."""
    rows = []
    for usn, info in students.items():
        for subject, mark in info["marks"].items():
            rows.append((usn, info["name"], subject, mark))
    return rows


def from_rows(rows):
    """Build the nested dictionary back from (usn, name, subject, mark) rows."""
    students = {}
    for usn, name, subject, mark in rows:
        students.setdefault(usn, {"name": name, "marks": {}})
        students[usn]["marks"][subject] = mark
    return students
