import tkinter as tk
import customtkinter as ctk
import sqlite3


# ---------------- DATABASE ---------------- #
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("todo.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_name TEXT,
                task TEXT
            )
        """)
        self.conn.commit()

    # LISTS
    def add_list(self, name):
        self.cursor.execute(
            "INSERT OR IGNORE INTO lists (name) VALUES (?)",
            (name,)
        )
        self.conn.commit()

    def get_lists(self):
        self.cursor.execute("SELECT name FROM lists")
        return [r[0] for r in self.cursor.fetchall()]

    # TASKS
    def add_task(self, list_name, task):
        self.cursor.execute(
            "INSERT INTO tasks (list_name, task) VALUES (?, ?)",
            (list_name, task)
        )
        self.conn.commit()

    def get_tasks(self, list_name):
        self.cursor.execute(
            "SELECT task FROM tasks WHERE list_name=?",
            (list_name,)
        )
        return [r[0] for r in self.cursor.fetchall()]

    def delete_task(self, list_name, task):
        self.cursor.execute(
            "DELETE FROM tasks WHERE list_name=? AND task=?",
            (list_name, task)
        )
        self.conn.commit()


# ---------------- APP ---------------- #
class ToDoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = Database()

        self.title("To-Do list")

        # ---- YOUR ORIGINAL SIZING ---- #
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        min_width = int(screen_width * 0.8)
        min_height = int(screen_height * 0.8)

        self.minsize(min_width // 2, min_height // 2)
        self.geometry(f"{min_width}x{min_height}")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew")

        self.container.columnconfigure(0, weight=0)
        self.container.columnconfigure(1, weight=1)
        self.container.rowconfigure(0, weight=1)

        self.display_area = DisplayArea(self.container, self)
        self.display_area.grid(row=0, column=1, sticky="nsew")

        self.sidebar = SideBar(self.container, self)
        self.sidebar.grid(row=0, column=0, sticky="ns")


# ---------------- SIDEBAR ---------------- #
class SideBar(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.list_buttons = {}

        self.columnconfigure(0, weight=1)

        self.add_btn = ctk.CTkButton(self, text="+ Add List", command=self.add_list)
        self.add_btn.grid(row=0, column=0, pady=10, padx=10)

        self.load_lists()

    def load_lists(self):
        for name in self.controller.db.get_lists():
            self.create_list_button(name)

    def add_list(self):
        self.entry = ctk.CTkEntry(self)
        self.entry.grid(row=len(self.list_buttons) + 1, column=0, pady=5, padx=10)
        self.entry.bind("<Return>", self.save_list)
        self.entry.focus()

    def save_list(self, event=None):
        name = self.entry.get()
        if not name:
            return

        self.controller.db.add_list(name)
        self.create_list_button(name)

        self.entry.destroy()

    def create_list_button(self, name):
        btn = ctk.CTkButton(
            self,
            text=name,
            command=lambda n=name: self.controller.display_area.switch_list(n)
        )

        btn.grid(row=len(self.list_buttons) + 1, column=0, pady=5, padx=10)

        self.list_buttons[name] = btn

        btn.bind("<Double-Button-1>", self.delete_list)

    def delete_list(self, event=None):
        btn = event.widget.master
        name = btn.cget("text")

        btn.destroy()
        self.list_buttons.pop(name, None)


# ---------------- DISPLAY AREA ---------------- #
class DisplayArea(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.frames = {}  # list_name → frame

        self.current_list = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self.head_label = ctk.CTkLabel(
            self,
            text="Get Started! Great things are waiting for you to do them!",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.head_label.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.add_task_btn = ctk.CTkButton(self, text="+ Add Task", command=self.add_task)
        self.add_task_btn.grid(row=2, column=0, pady=10, padx=10, sticky="ew")

    # ---------------- SWITCH LIST ---------------- #
    def switch_list(self, list_name):
        self.current_list = list_name

        # create frame if doesn't exist
        if list_name not in self.frames:
            frame = ctk.CTkFrame(self, fg_color="grey")
            frame.grid(row=1, column=0, pady=80, padx=80, sticky="nsew")
            frame.columnconfigure(0, weight=1)

            self.frames[list_name] = frame

            # LOAD TASKS INTO CORRECT FRAME
            tasks = self.controller.db.get_tasks(list_name)
            for task in tasks:
                self.create_task_button(list_name, task, frame)

        self.frames[list_name].tkraise()

    # ---------------- ADD TASK ENTRY ---------------- #
    def add_task(self):
        if not self.current_list:
            return

        frame = self.frames[self.current_list]

        self.task_entry = ctk.CTkEntry(frame)
        self.task_entry.grid(
            row=len(frame.winfo_children()),
            column=0,
            pady=5,
            padx=10,
            sticky="ew"
        )

        self.task_entry.bind("<Return>", self.save_task)
        self.task_entry.focus()

    # ---------------- SAVE TASK ---------------- #
    def save_task(self, event=None):
        task_name = self.task_entry.get()

        if not task_name:
            return

        list_name = self.current_list
        frame = self.frames[list_name]

        self.controller.db.add_task(list_name, task_name)

        self.create_task_button(list_name, task_name, frame)

        self.task_entry.destroy()

    # ---------------- CREATE TASK BUTTON (FIXED CORE) ---------------- #
    def create_task_button(self, list_name, task_name, frame):
        btn = ctk.CTkButton(frame, text=task_name)

        btn.grid(
            row=len(frame.winfo_children()),
            column=0,
            pady=5,
            padx=10,
            sticky="ew"
        )

        btn.bind(
            "<Double-Button-1>",
            lambda e: self.delete_task(list_name, task_name, btn)
        )

    # ---------------- DELETE TASK ---------------- #
    def delete_task(self, list_name, task_name, btn):
        self.controller.db.delete_task(list_name, task_name)
        btn.destroy()


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    
    # import os

    # if os.path.exists("todo.db"):
    #     os.remove("todo.db")
    app = ToDoApp()
    app.mainloop()