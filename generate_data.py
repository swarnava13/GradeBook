"""
generate_data.py
Creates realistic sample data for GradeBook using the random module.
Writes data/marks.csv (120 students x 5 subjects = 600 records)
and data/settings.json (subjects, credits, pass mark).
Run once:  python generate_data.py
"""
import csv
import json
import os
import random

random.seed(42)

SUBJECTS = {"Maths": 4, "Python": 4, "Physics": 3, "English": 2, "Electronics": 3}
FIRST = ["Asha", "Ravi", "Priya", "Arjun", "Sneha", "Kiran", "Meera", "Rahul", "Divya", "Vikram",
         "Ananya", "Rohan", "Kavya", "Aditya", "Pooja", "Nikhil", "Isha", "Varun", "Neha", "Suresh",
         "Lakshmi", "Manoj", "Deepa", "Harsh", "Shreya", "Akash", "Tanvi", "Yash", "Ritu", "Gaurav"]
LAST = ["Sharma", "Rao", "Iyer", "Patel", "Reddy", "Nair", "Gupta", "Kumar", "Singh", "Menon",
        "Shetty", "Joshi", "Das", "Verma", "Hegde"]

# Each subject has its own difficulty so the analysis shows a "weak subject"
SUBJECT_MEAN = {"Maths": 62, "Python": 74, "Physics": 58, "English": 78, "Electronics": 66}


def make_mark(subject, ability):
    """Mark = subject difficulty + student ability + noise, kept in 0-100."""
    mark = random.gauss(SUBJECT_MEAN[subject] + ability, 10)
    return max(0, min(100, round(mark)))


def main():
    os.makedirs("data", exist_ok=True)
    rows = []
    for i in range(1, 121):
        usn = f"25BTRDS{i:03d}"
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        ability = random.gauss(0, 12)          # strong / average / weak students
        for subject in SUBJECTS:
            # About 2% marks are left blank to simulate "missing marks"
            mark = "" if random.random() < 0.02 else make_mark(subject, ability)
            rows.append({"usn": usn, "name": name, "subject": subject, "mark": mark})

    with open("data/marks.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["usn", "name", "subject", "mark"])
        writer.writeheader()
        writer.writerows(rows)

    settings = {"class_name": "B.Tech CSE (Data Science) - Sem III",
                "subjects": SUBJECTS, "pass_mark": 40}
    with open("data/settings.json", "w") as f:
        json.dump(settings, f, indent=4)

    print(f"Created {len(rows)} records for {len(rows) // len(SUBJECTS)} students.")


if __name__ == "__main__":
    main()
