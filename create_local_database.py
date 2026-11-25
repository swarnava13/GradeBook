"""Import marks.csv into SQLite and export the same records to Excel and charts."""
import csv
import json
import math
import sqlite3
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import analysis
from core_logic import grade
import visualisation

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "gradebook.sqlite3"
WORKBOOK = ROOT / "GradeBook_Data.xlsx"
SOURCE_CSV = ROOT / "marks.csv"
SETTINGS_FILE = ROOT / "settings.json"
PASS_MARK = 40
SUBJECTS = {}


def build_database():
    global PASS_MARK, SUBJECTS

    with SETTINGS_FILE.open(encoding="utf-8") as settings_file:
        settings = json.load(settings_file)
    PASS_MARK = int(settings["pass_mark"])
    SUBJECTS = settings["subjects"]
    if not SUBJECTS:
        raise ValueError(f"No subjects configured in {SETTINGS_FILE}.")

    with SOURCE_CSV.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        required_columns = {"usn", "name", "subject", "mark"}
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{SOURCE_CSV} must contain columns: "
                f"{', '.join(sorted(required_columns))}."
            )
        students_by_usn = {}
        marks = []
        seen_records = set()
        for line_number, row in enumerate(reader, 2):
            try:
                usn = row["usn"].strip()
                name = row["name"].strip()
                subject = row["subject"].strip()
                raw_mark = row["mark"].strip()
                if not usn or not name or subject not in SUBJECTS:
                    raise ValueError("missing student details or unknown subject")
                mark = int(raw_mark) if raw_mark else None
                if mark is not None and not 0 <= mark <= 100:
                    raise ValueError("mark must be between 0 and 100")
                if usn in students_by_usn and students_by_usn[usn] != name:
                    raise ValueError(f"USN {usn} has inconsistent student names")
                key = (usn, subject)
                if key in seen_records:
                    raise ValueError(f"duplicate record for {usn} / {subject}")
            except (AttributeError, TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid record in {SOURCE_CSV}, line {line_number}: {error}"
                ) from error
            students_by_usn[usn] = name
            seen_records.add(key)
            marks.append((usn, subject, mark))

    expected_count = len(students_by_usn) * len(SUBJECTS)
    if len(marks) != expected_count:
        raise ValueError(
            f"{SOURCE_CSV} has {len(marks)} mark rows; expected "
            f"{expected_count} ({len(students_by_usn)} students × "
            f"{len(SUBJECTS)} subjects)."
        )

    with sqlite3.connect(DATABASE) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS students (
                usn TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS subjects (
                subject TEXT PRIMARY KEY,
                credits INTEGER NOT NULL CHECK (credits > 0),
                pass_mark INTEGER NOT NULL CHECK (pass_mark BETWEEN 0 AND 100)
            );
            CREATE TABLE IF NOT EXISTS marks (
                usn TEXT NOT NULL REFERENCES students(usn) ON DELETE CASCADE,
                subject TEXT NOT NULL REFERENCES subjects(subject),
                mark INTEGER CHECK (mark BETWEEN 0 AND 100),
                PRIMARY KEY (usn, subject)
            );
            """
        )
        db.execute("DELETE FROM marks")
        db.execute("DELETE FROM students")
        db.execute("DELETE FROM subjects")
        db.execute("DELETE FROM settings")
        db.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            [
                ("class_name", settings["class_name"]),
                ("pass_mark", str(PASS_MARK)),
                ("source_file", SOURCE_CSV.name),
            ],
        )
        db.executemany(
            "INSERT INTO subjects (subject, credits, pass_mark) VALUES (?, ?, ?)",
            [(name, credits, PASS_MARK) for name, credits in SUBJECTS.items()],
        )
        db.executemany(
            "INSERT INTO students (usn, name) VALUES (?, ?)",
            list(students_by_usn.items()),
        )
        db.executemany(
            "INSERT INTO marks (usn, subject, mark) VALUES (?, ?, ?)", marks
        )
        db.commit()
    return len(students_by_usn), len(marks)


def excel_column(number):
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xml_cell(reference, value, header=False):
    style = ' s="1"' if header else ""
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            return ""
        return f'<c r="{reference}"{style}><v>{value}</v></c>'
    text = escape(str(value))
    preserve = ' xml:space="preserve"' if text != text.strip() else ""
    return (
        f'<c r="{reference}" t="inlineStr"{style}>'
        f"<is><t{preserve}>{text}</t></is></c>"
    )


def worksheet_xml(rows, widths, filter_last_row):
    last_col = excel_column(len(widths))
    columns = "".join(
        f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>'
        for i, width in enumerate(widths, 1)
    )
    row_xml = []
    for row_index, row in enumerate(rows, 1):
        cells = "".join(
            xml_cell(f"{excel_column(col_index)}{row_index}", value, row_index == 1)
            for col_index, value in enumerate(row, 1)
        )
        row_xml.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        f'<cols>{columns}</cols><sheetData>{"".join(row_xml)}</sheetData>'
        f'<autoFilter ref="A1:{last_col}{filter_last_row}"/>'
        '</worksheet>'
    )


def build_workbook():
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        mark_rows = db.execute(
            """
            SELECT s.usn, s.name, m.subject, sub.credits, m.mark
            FROM marks AS m
            JOIN students AS s USING (usn)
            JOIN subjects AS sub USING (subject)
            ORDER BY s.usn, sub.rowid
            """
        ).fetchall()
        student_rows = db.execute(
            """
            SELECT s.usn, s.name, m.subject, sub.credits, m.mark, sub.pass_mark
            FROM marks AS m
            JOIN students AS s USING (usn)
            JOIN subjects AS sub USING (subject)
            ORDER BY s.usn, sub.rowid
            """
        ).fetchall()

    marks_sheet = [[
        "USN", "Student Name", "Subject", "Credits", "Marks",
        "Grade", "Grade Point",
    ]]
    summary_sheet = [[
        "USN", "Student Name", "Total Marks", "Marks Entered",
        "Percentage", "SGPA", "Backlogs", "Result",
    ]]
    by_student = {}
    for row in student_rows:
        marks_sheet.append([
            row["usn"], row["name"], row["subject"], row["credits"],
            row["mark"], grade(row["mark"])[0], grade(row["mark"])[1],
        ])
        entry = by_student.setdefault(
            row["usn"],
            {"name": row["name"], "total": 0, "entered": 0, "weighted": 0,
             "credits": 0, "backlogs": 0, "missing": False},
        )
        if row["mark"] is None:
            entry["missing"] = True
            continue
        point = grade(row["mark"])[1]
        entry["total"] += row["mark"]
        entry["entered"] += 1
        entry["weighted"] += row["credits"] * point
        entry["credits"] += row["credits"]
        if row["mark"] < row["pass_mark"]:
            entry["backlogs"] += 1

    for usn, entry in by_student.items():
        percentage = (
            round(entry["total"] / (entry["entered"] * 100) * 100, 2)
            if entry["entered"] else 0
        )
        sgpa = (
            round(entry["weighted"] / entry["credits"], 2)
            if entry["credits"] else 0
        )
        result = (
            "INCOMPLETE" if entry["missing"]
            else "FAIL" if entry["backlogs"]
            else "PASS"
        )
        summary_sheet.append([
            usn, entry["name"], entry["total"], entry["entered"],
            percentage, sgpa, entry["backlogs"], result,
        ])

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    package_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Marks" sheetId="1" r:id="rId1"/>'
        '<sheet name="Student Summary" sheetId="2" r:id="rId2"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF164E63"/>'
        '<bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )
    with zipfile.ZipFile(WORKBOOK, "w", zipfile.ZIP_DEFLATED) as workbook_zip:
        workbook_zip.writestr("[Content_Types].xml", content_types)
        workbook_zip.writestr("_rels/.rels", package_rels)
        workbook_zip.writestr("xl/workbook.xml", workbook)
        workbook_zip.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        workbook_zip.writestr("xl/styles.xml", styles)
        workbook_zip.writestr(
            "xl/worksheets/sheet1.xml",
            worksheet_xml(marks_sheet, [16, 24, 18, 12, 12, 12, 14], len(marks_sheet)),
        )
        workbook_zip.writestr(
            "xl/worksheets/sheet2.xml",
            worksheet_xml(summary_sheet, [16, 24, 15, 15, 14, 12, 12, 16], len(summary_sheet)),
        )
    return len(mark_rows), len(by_student)


def build_charts():
    with sqlite3.connect(DATABASE) as db:
        rows = db.execute(
            "SELECT usn, name, subject, mark FROM marks "
            "JOIN students USING (usn) ORDER BY usn, subject"
        ).fetchall()
    frame = analysis.build_dataframe(rows, SUBJECTS)
    paths = visualisation.generate_all(frame, PASS_MARK)
    summary = analysis.student_summary(frame, PASS_MARK)
    print(f"Average SGPA: {summary['sgpa'].mean():.2f}")
    print(f"Complete-pass percentage: {analysis.pass_percentage(summary):.1f}%")
    print(f"Students with missing marks: {analysis.missing_marks_list(frame)['usn'].nunique()}")
    return paths


if __name__ == "__main__":
    student_count, record_count = build_database()
    mark_count, summary_count = build_workbook()
    build_charts()
    print(f"Source CSV: {SOURCE_CSV}")
    print(f"SQLite database: {DATABASE}")
    print(f"Students: {student_count}; subjects: {len(SUBJECTS)}; records: {record_count}")
    print(f"Excel workbook: {WORKBOOK} ({mark_count} marks rows, {summary_count} student summaries)")
