import tkinter as tk
from tkinter import scrolledtext

from shell import Shell


class App:
    def __init__(self):
        self.shell = Shell()
        self.root = tk.Tk()
        self.root.title("Эмулятор оболочки - VFS: " + self.shell.vfs_name)
        self.root.geometry("800x500")
        self.output = scrolledtext.ScrolledText(self.root, state="disabled")
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(self.root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.configure(state="disabled")
        self.output.see(tk.END)

    def on_enter(self, event):
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.write(self.shell.prompt() + line)
        result = self.shell.execute(line)
        if result:
            self.write(result)
        if not self.shell.running:
            self.root.destroy()
