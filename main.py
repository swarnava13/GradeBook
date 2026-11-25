"""
main.py  -  GradeBook: Student Result Analyzer
Group 01 | Python Programming Group Project | B.Tech CSE (Data Science) Sem III

Integrates all six components into one menu-driven program.
Run:  python main.py
"""
import analysis
import core_logic
import data_structures as ds
import file_handler
import menu_input as ui
import visualisation


def print_student(usn, info, credits, pass_mark):
    marks = info["marks"]
    print(f"\nUSN: {usn}    Name: {info['name']}")
    print(f"{'Subject':<14}{'Marks':>6}{'Grade':>7}")
    for subject, mark in marks.items():
        letter, _ = core_logic.grade(mark)
        print(f"{subject:<14}{'--' if mark is None else mark:>6}{letter:>7}")
    print(core_logic.report_line(Total=core_logic.total(marks),
                                 Percentage=f"{core_logic.percentage(marks)}%",
                                 SGPA=core_logic.sgpa(marks, credits),
                                 Result=core_logic.result_status(marks, pass_mark),
                                 Backlogs=core_logic.count_backlogs(list(marks.values()), pass_mark)))


def main():
    settings = file_handler.load_settings()
    credits = settings["subjects"]
    pass_mark = settings["pass_mark"]
    students = ds.from_rows(file_handler.load_marks())
    print(f"\nLoaded {len(students)} students for {settings['class_name']}.")

    while True:
        ui.show_menu()
        try:
            choice = ui.get_choice()
        except (KeyboardInterrupt, EOFError):
            choice = "0"                      # Ctrl+C on the menu = save and exit

        try:
            if choice == "1":
                usn = ui.get_usn()
                name = ui.get_name()
                ds.add_student(students, usn, name, credits)
                print(f"  Student {name} added. Use option 2 to enter marks.")

            elif choice == "2":
                usn = ui.get_usn()
                if usn not in students:
                    raise KeyError(f"No student with USN {usn}.")
                for subject in credits:
                    ds.set_mark(students, usn, subject, ui.get_mark(subject))
                print("  Marks saved in memory.")
                print_student(usn, students[usn], credits, pass_mark)

            elif choice == "3":
                usn = ui.get_usn()
                if usn not in students:
                    raise KeyError(f"No student with USN {usn}.")
                print_student(usn, students[usn], credits, pass_mark)

            elif choice == "4":
                ranked = core_logic.rank_students(students, credits)
                print(f"\n{'Rank':<6}{'USN':<13}{'Name':<22}{'SGPA':>6}")
                for rank, usn, name, sg in ranked[:20]:
                    print(f"{rank:<6}{usn:<13}{name:<22}{sg:>6}")
                if len(ranked) > 20:
                    print(f"... and {len(ranked) - 20} more students")
                print("Class average SGPA:", core_logic.class_average(*[r[3] for r in ranked]))

            elif choice == "5":
                found = ds.search(students, ui.get_text("Enter USN or part of name: "))
                if not found:
                    print("  No matching student found.")
                for usn in found[:10]:
                    print(f"  {usn}  {students[usn]['name']}")

            elif choice == "6":
                usn = ui.get_usn()
                if ui.confirm(f"Delete {usn}?"):
                    removed = ds.delete_student(students, usn)
                    print(f"  Deleted {removed['name']}.")

            elif choice == "7":
                df = analysis.build_dataframe(ds.to_rows(students), credits)
                analysis.print_report(df, pass_mark)

            elif choice == "8":
                df = analysis.build_dataframe(ds.to_rows(students), credits)
                visualisation.generate_all(df, pass_mark)

            elif choice == "9":
                file_handler.save_marks(ds.to_rows(students))

            elif choice == "0":
                file_handler.save_marks(ds.to_rows(students))
                print("Goodbye!")
                break

        except KeyError as e:
            print("  Error:", e.args[0])
        except (KeyboardInterrupt, EOFError):
            print("\n  Input cancelled. Returning to menu.")
            continue


if __name__ == "__main__":
    main()
