"""
core_logic.py  -  Component 2: Core logic and functions
Owner: Adithya Sapkal (25BTRDC043)
Total, percentage, grade rules, SGPA and rank calculation.
"""

# (minimum mark, grade letter, grade point) - checked from top to bottom
GRADE_RULES = [(90, "O", 10), (80, "A+", 9), (70, "A", 8), (60, "B+", 7),
               (50, "B", 6), (40, "C", 5), (0, "F", 0)]


def total(marks):
    """Sum of all available marks (missing marks are skipped)."""
    return sum(m for m in marks.values() if m is not None)


def percentage(marks):
    entered = [m for m in marks.values() if m is not None]
    if not entered:
        return 0.0
    return round(total(marks) / (len(entered) * 100) * 100, 2)


def grade(mark):
    """Return (grade letter, grade point) for one mark using if/elif logic."""
    if mark is None:
        return ("AB", 0)
    for minimum, letter, point in GRADE_RULES:
        if mark >= minimum:
            return (letter, point)
    return ("F", 0)


def sgpa(marks, credits):
    """SGPA = sum(credit x grade point) / sum(credits)."""
    earned = sum(credits[s] * grade(m)[1] for s, m in marks.items() if s in credits)
    total_credits = sum(credits[s] for s in marks if s in credits)
    return round(earned / total_credits, 2) if total_credits else 0.0


def result_status(marks, pass_mark=40):
    """PASS only if every subject has a mark >= pass mark."""
    for m in marks.values():
        if m is None:
            return "INCOMPLETE"
        if m < pass_mark:
            return "FAIL"
    return "PASS"


def rank_students(students, credits):
    """Return a list of (rank, usn, name, sgpa) sorted by SGPA using a lambda."""
    scored = [(usn, info["name"], sgpa(info["marks"], credits)) for usn, info in students.items()]
    scored.sort(key=lambda row: row[2], reverse=True)
    return [(i + 1, *row) for i, row in enumerate(scored)]


def count_backlogs(mark_list, pass_mark=40):
    """Recursive function: count subjects below the pass mark."""
    if not mark_list:
        return 0
    first = 1 if (mark_list[0] is not None and mark_list[0] < pass_mark) else 0
    return first + count_backlogs(mark_list[1:], pass_mark)


def class_average(*sgpas):
    """Uses *args: average of any number of SGPA values."""
    return round(sum(sgpas) / len(sgpas), 2) if sgpas else 0.0


def report_line(**fields):
    """Uses **kwargs: build one formatted line of a report."""
    return " | ".join(f"{key}: {value}" for key, value in fields.items())
