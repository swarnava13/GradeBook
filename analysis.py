"""
analysis.py  -  Component 5: Data analysis with pandas and NumPy
Owner: Shivani M (25BTRDC046)
Subject averages, toppers, pass percentage and students with missing marks.
"""
import numpy as np
import pandas as pd

from core_logic import grade


def build_dataframe(rows, credits):
    """Long table: one row per (student, subject)."""
    df = pd.DataFrame(rows, columns=["usn", "name", "subject", "mark"])
    df["mark"] = pd.to_numeric(df["mark"], errors="coerce")
    credit_table = pd.DataFrame(list(credits.items()), columns=["subject", "credits"])
    df = df.merge(credit_table, on="subject", how="left")          # merge
    df["grade"] = df["mark"].apply(lambda m: grade(None if pd.isna(m) else m)[0])
    df["grade_point"] = df["mark"].apply(lambda m: grade(None if pd.isna(m) else m)[1])
    return df


def student_summary(df, pass_mark=40):
    """One row per student: total, percentage, SGPA, result and rank."""
    df = df.copy()
    df["weighted"] = df["credits"] * df["grade_point"]
    g = df.groupby(["usn", "name"])
    summary = pd.DataFrame({
        "total": g["mark"].sum(),
        "subjects_entered": g["mark"].count(),
        "sgpa": (g["weighted"].sum() / g["credits"].sum()).round(2),
        "lowest": g["mark"].min(),
    }).reset_index()
    summary["lowest"] = summary["lowest"].fillna(0)                   # fillna
    summary["percentage"] = (summary["total"] / (summary["subjects_entered"] * 100) * 100).round(2)
    missing = df[df["mark"].isna()]["usn"].unique()
    summary["result"] = np.where(summary["usn"].isin(missing), "INCOMPLETE",
                                 np.where(summary["lowest"] >= pass_mark, "PASS", "FAIL"))
    summary = summary.sort_values("sgpa", ascending=False).reset_index(drop=True)
    summary["rank"] = summary.index + 1
    return summary


def subject_averages(df):
    return df.groupby("subject")["mark"].mean().round(2).sort_values()


def subject_pass_rate(df, pass_mark=40):
    entered = df.dropna(subset=["mark"])
    return (entered.groupby("subject")["mark"]
            .apply(lambda s: (s >= pass_mark).mean() * 100).round(1))


def toppers(summary, n=5):
    return summary.head(n)[["rank", "usn", "name", "sgpa", "percentage"]]


def subject_toppers(df):
    idx = df.dropna(subset=["mark"]).groupby("subject")["mark"].idxmax()
    return df.loc[idx, ["subject", "usn", "name", "mark"]]


def pass_percentage(summary):
    complete = summary[summary["result"] != "INCOMPLETE"]
    return round((complete["result"] == "PASS").mean() * 100, 1) if len(complete) else 0.0


def missing_marks_list(df):
    return df[df["mark"].isna()][["usn", "name", "subject"]]


def grade_distribution(df):
    order = ["O", "A+", "A", "B+", "B", "C", "F"]
    return df.dropna(subset=["mark"])["grade"].value_counts().reindex(order, fill_value=0)


def print_report(df, pass_mark=40):
    """Print the full class analysis to the screen."""
    summary = student_summary(df, pass_mark)
    marks = df["mark"].dropna().to_numpy()            # NumPy array of all marks
    print("\n----------- CLASS ANALYSIS -----------")
    print(f"Students: {summary.shape[0]}   Records: {df.shape[0]}")
    print(f"Class mean mark: {np.mean(marks):.2f}   Std dev: {np.std(marks):.2f}")
    print(f"Average SGPA: {summary['sgpa'].mean():.2f}")
    print(f"Pass percentage: {pass_percentage(summary)}%")
    print("\nSubject averages (lowest first):")
    print(subject_averages(df).to_string())
    print("\nPass rate by subject (%):")
    print(subject_pass_rate(df, pass_mark).to_string())
    print("\nTop 5 students:")
    print(toppers(summary).to_string(index=False))
    print("\nSubject toppers:")
    print(subject_toppers(df).to_string(index=False))
    miss = missing_marks_list(df)
    print(f"\nStudents with missing marks: {miss['usn'].nunique()}")
    if not miss.empty:
        print(miss.to_string(index=False))
    print("--------------------------------------")
    return summary
