import shlex

VFS_NAME = "vfs"
MAX_ARGS = 1


def parse(line):
    words = shlex.split(line)
    if not words:
        return None, []
    return words[0], words[1:]


class Shell:
    def __init__(self):
        self.vfs_name = VFS_NAME
        self.running = True
        self.commands = {"ls": self.do_ls, "cd": self.do_cd,
                         "exit": self.do_exit}

    def prompt(self):
        return self.vfs_name + ":~$ "

    def execute(self, line):
        try:
            name, args = parse(line)
        except ValueError as err:
            return f"syntax error: {err}"
        if name is None:
            return ""
        if name not in self.commands:
            return name + ": command not found"
        return self.commands[name](args)

    def do_ls(self, args):
        return f"ls {args}"

    def do_cd(self, args):
        if len(args) > MAX_ARGS:
            return "cd: too many arguments"
        return f"cd {args}"

    def do_exit(self, args):
        if len(args) > MAX_ARGS:
            return "exit: too many arguments"
        if args and not args[0].isdigit():
            return f"exit: {args[0]}: numeric argument required"
        self.running = False
        return ""
