import tkinter as tk
from tkinter import scrolledtext

from shell import Shell


class App:
    def __init__(self, vfs_path="", prompt_text="", script_path=""):
        self.shell = Shell(vfs_path, prompt_text)
        self.root = tk.Tk()
        self.root.title("Эмулятор оболочки - VFS: " + self.shell.vfs_name)
        self.root.geometry("800x500")
        self.output = scrolledtext.ScrolledText(self.root, state="disabled")
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(self.root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()
        self.show_parameters(vfs_path, prompt_text, script_path)
        if self.shell.vfs_error:
            self.write(self.shell.vfs_error)
        if script_path:
            self.run_script(script_path)

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.configure(state="disabled")
        self.output.see(tk.END)

    def show_parameters(self, vfs_path, prompt_text, script_path):
        self.write("parameters:")
        self.write("  vfs = " + (vfs_path or "-"))
        self.write("  prompt = " + (prompt_text or "-"))
        self.write("  script = " + (script_path or "-"))
        self.write("")

    def run_line(self, line, number=0):
        self.write(self.shell.prompt() + line)
        result = self.shell.execute(line)
        if self.shell.clear_screen:
            self.output.configure(state="normal")
            self.output.delete("1.0", tk.END)
            self.output.configure(state="disabled")
            self.shell.clear_screen = False
            return
        if result and self.shell.error and number:
            result = f"line {number}: {result}"
        if result:
            self.write(result)

    def run_script(self, path):
        try:
            with open(path, encoding="utf-8") as script:
                lines = script.read().splitlines()
        except OSError as err:
            self.write(f"script error: {err}")
            return
        for number, line in enumerate(lines, 1):
            self.run_line(line, number)
            if not self.shell.running:
                break
        if not self.shell.running:
            self.root.destroy()

    def on_enter(self, event):
        self.run_line(self.entry.get())
        self.entry.delete(0, tk.END)
        if not self.shell.running:
            self.root.destroy()
