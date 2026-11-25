"""
menu_input.py  -  Component 1: Menu, input and validation
Owner: Amulya (25BTRDC008)
Shows the menu and safely reads every value the user types.
"""

MENU = """
==============================================
        GRADEBOOK - Student Result Analyzer
==============================================
 1. Add a new student
 2. Enter / update marks
 3. View result of a student
 4. View class results (ranked)
 5. Search student by USN or name
 6. Delete a student
 7. Show class analysis (pandas)
 8. Generate charts (matplotlib)
 9. Save data to file
 0. Save and exit
=============================================="""


def show_menu():
    print(MENU)


def get_choice(valid=("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
    """Keep asking until the user types a valid menu option."""
    while True:
        choice = input("Enter your choice: ").strip()
        if choice in valid:
            return choice
        print("  Invalid choice. Please enter a number from the menu.")


def get_text(prompt, allow_empty=False):
    """Read non-empty text, using string methods to clean it."""
    while True:
        text = input(prompt).strip()
        if text or allow_empty:
            return text
        print("  This field cannot be empty.")


def get_usn(prompt="Enter USN: "):
    """USN must be letters and digits only; stored in upper case."""
    while True:
        usn = input(prompt).strip().upper()
        if usn.isalnum() and 5 <= len(usn) <= 12:
            return usn
        print("  Invalid USN. Use 5-12 letters/digits, e.g. 25BTRDS001.")


def get_name(prompt="Enter student name: "):
    while True:
        name = input(prompt).strip().title()
        if name and name.replace(" ", "").isalpha():
            return name
        print("  Name must contain only letters and spaces.")


def get_mark(subject):
    """Mark must be a whole number between 0 and 100."""
    while True:
        raw = input(f"  Marks in {subject} (0-100): ").strip()
        try:
            mark = int(raw)
        except ValueError:
            print("  Error: please enter a whole number.")
            continue
        if 0 <= mark <= 100:
            return mark
        print("  Error: marks must be between 0 and 100.")


def confirm(prompt):
    return input(prompt + " (y/n): ").strip().lower() == "y"
