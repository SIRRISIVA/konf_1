import hashlib
import os
import shlex

VFS_NAME = "vfs"
MAX_ARGS = 1


def parse(line):
    words = shlex.split(line)
    if not words:
        return None, []
    return words[0], words[1:]


def vfs_name_from_path(path):
    name = os.path.basename(path.rstrip("/\\"))
    if not name:
        return VFS_NAME
    return name


def relative_path(full, start):
    return os.path.relpath(full, start).replace("\\", "/")


def load_vfs(path):
    dirs = []
    files = {}
    for root, names, filenames in os.walk(path):
        for name in names:
            dirs.append(relative_path(os.path.join(root, name), path))
        for name in filenames:
            full = os.path.join(root, name)
            with open(full, "rb") as data:
                files[relative_path(full, path)] = data.read()
    return dirs, files


def vfs_hash(dirs, files):
    digest = hashlib.sha256()
    for name in sorted(dirs):
        digest.update(name.encode())
    for name in sorted(files):
        digest.update(name.encode())
        digest.update(files[name])
    return digest.hexdigest()


class Shell:
    def __init__(self, vfs_path="", prompt_text=""):
        self.vfs_path = vfs_path
        self.vfs_name = vfs_name_from_path(vfs_path)
        self.prompt_text = prompt_text
        self.running = True
        self.error = False
        self.vfs_dirs = []
        self.vfs_files = {}
        self.vfs_error = ""
        self.commands = {"ls": self.do_ls, "cd": self.do_cd,
                         "vfs-info": self.do_vfs_info, "exit": self.do_exit}
        if vfs_path:
            self.load_vfs(vfs_path)

    def load_vfs(self, path):
        if not os.path.isdir(path):
            self.vfs_error = f"vfs error: {path}: no such directory"
            return
        try:
            self.vfs_dirs, self.vfs_files = load_vfs(path)
        except OSError as err:
            self.vfs_error = f"vfs error: {err}"

    def prompt(self):
        if self.prompt_text:
            return self.prompt_text + " "
        return self.vfs_name + ":~$ "

    def fail(self, message):
        self.error = True
        return message

    def execute(self, line):
        self.error = False
        try:
            name, args = parse(line)
        except ValueError as err:
            return self.fail(f"syntax error: {err}")
        if name is None:
            return ""
        if name not in self.commands:
            return self.fail(name + ": command not found")
        return self.commands[name](args)

    def do_ls(self, args):
        return f"ls {args}"

    def do_cd(self, args):
        if len(args) > MAX_ARGS:
            return self.fail("cd: too many arguments")
        return f"cd {args}"

    def do_vfs_info(self, args):
        if args:
            return self.fail("vfs-info: too many arguments")
        if not self.vfs_path:
            return self.fail("vfs-info: vfs is not loaded")
        if self.vfs_error:
            return self.fail(self.vfs_error)
        digest = vfs_hash(self.vfs_dirs, self.vfs_files)
        return f"name: {self.vfs_name}\nsha256: {digest}"

    def do_exit(self, args):
        if len(args) > MAX_ARGS:
            return self.fail("exit: too many arguments")
        if args and not args[0].isdigit():
            return self.fail(f"exit: {args[0]}: numeric argument required")
        self.running = False
        return ""
