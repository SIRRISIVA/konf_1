from datetime import datetime, timezone
import hashlib
import os
import shlex

VFS_NAME = "vfs"
MAX_ARGS = 1


def parse(line):
    """Split command line into command name and argument list."""
    words = shlex.split(line)
    if not words:
        return None, []
    return words[0], words[1:]


def vfs_name_from_path(path):
    """Extract VFS name from filesystem path."""
    name = os.path.basename(path.rstrip("/\\"))
    if not name:
        return VFS_NAME
    return name


def relative_path(full, start):
    """Return relative path with forward slashes."""
    return os.path.relpath(full, start).replace("\\", "/")


def load_vfs(path):
    """Load directory structure and file contents into memory."""
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
    """Calculate SHA-256 digest of VFS structure and file contents."""
    digest = hashlib.sha256()
    for name in sorted(dirs):
        digest.update(name.encode())
    for name in sorted(files):
        digest.update(name.encode())
        digest.update(files[name])
    return digest.hexdigest()


def resolve_path(cwd, path):
    """Resolve relative or absolute VFS path."""
    if not path or path == ".":
        return cwd
    if path == "~":
        return ""
    if path.startswith("/"):
        parts = []
    else:
        parts = cwd.split("/") if cwd else []
    for part in path.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


class Shell:
    """UNIX shell emulator working with in-memory VFS."""

    def __init__(self, vfs_path="", prompt_text=""):
        self.vfs_path = vfs_path
        self.vfs_name = vfs_name_from_path(vfs_path)
        self.prompt_text = prompt_text
        self.running = True
        self.error = False
        self.clear_screen = False
        self.cwd = ""
        self.vfs_dirs = []
        self.vfs_files = {}
        self.vfs_error = ""
        self.commands = {
            "ls": self.do_ls,
            "cd": self.do_cd,
            "clear": self.do_clear,
            "date": self.do_date,
            "mkdir": self.do_mkdir,
            "rmdir": self.do_rmdir,
            "vfs-info": self.do_vfs_info,
            "exit": self.do_exit,
        }
        if vfs_path:
            self.load_vfs(vfs_path)

    def load_vfs(self, path):
        """Load VFS from specified physical path."""
        if not os.path.isdir(path):
            self.vfs_error = f"vfs error: {path}: no such directory"
            return
        try:
            self.vfs_dirs, self.vfs_files = load_vfs(path)
        except OSError as err:
            self.vfs_error = f"vfs error: {err}"

    def prompt(self):
        """Return prompt string for REPL."""
        if self.prompt_text:
            return self.prompt_text + " "
        return self.vfs_name + ":~$ "

    def fail(self, message):
        """Set error state and return error message."""
        self.error = True
        return message

    def is_dir(self, path):
        """Check if path is a directory in VFS."""
        return path == "" or path in self.vfs_dirs

    def is_file(self, path):
        """Check if path is a file in VFS."""
        return path in self.vfs_files

    def list_dir_entries(self, dir_path):
        """Return direct child directory and file names for dir_path."""
        prefix = f"{dir_path}/" if dir_path else ""
        prefix_len = len(prefix)
        dirs = set()
        files = set()
        for d in self.vfs_dirs:
            if not prefix or d.startswith(prefix):
                rest = d[prefix_len:]
                if rest and "/" not in rest:
                    dirs.add(rest)
        for f in self.vfs_files:
            if not prefix or f.startswith(prefix):
                rest = f[prefix_len:]
                if rest and "/" not in rest:
                    files.add(rest)
        return sorted(dirs | files)

    def execute(self, line):
        """Parse and execute a shell command line."""
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

    def _format_ls_entries(self, target, entries, flags):
        """Format directory entries according to flags."""
        if "-a" in flags:
            entries = [".", ".."] + entries
        if "-l" in flags:
            lines = []
            for item in entries:
                full = f"{target}/{item}" if target else item
                if self.is_dir(full):
                    lines.append(f"drwxr-xr-x 1 vfs vfs 4096 {item}")
                else:
                    size = len(self.vfs_files.get(full, b""))
                    lines.append(f"-rw-r--r-- 1 vfs vfs {size:>4} {item}")
            return "\n".join(lines)
        return "\n".join(entries)

    def do_ls(self, args):
        """List directory contents or file info."""
        flags = [a for a in args if a.startswith("-")]
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            paths = [""]
        results = []
        for p in paths:
            target = resolve_path(self.cwd, p)
            if self.is_file(target):
                results.append(os.path.basename(target))
            elif self.is_dir(target):
                entries = self.list_dir_entries(target)
                results.append(self._format_ls_entries(target, entries, flags))
            else:
                return self.fail(
                    f"ls: cannot access '{p}': No such file or directory"
                )
        if len(paths) > 1:
            sections = [
                f"{p}:\n{out}" if out else f"{p}:"
                for p, out in zip(paths, results)
            ]
            return "\n\n".join(sections)
        return results[0] if results else ""

    def do_cd(self, args):
        """Change current working directory."""
        if len(args) > MAX_ARGS:
            return self.fail("cd: too many arguments")
        target = args[0] if args else ""
        if not target or target == "~":
            self.cwd = ""
            return ""
        resolved = resolve_path(self.cwd, target)
        if self.is_dir(resolved):
            self.cwd = resolved
            return ""
        if self.is_file(resolved):
            return self.fail(f"cd: {target}: Not a directory")
        return self.fail(f"cd: {target}: No such file or directory")

    def do_clear(self, args):
        """Request screen clear."""
        if args:
            return self.fail("clear: too many arguments")
        self.clear_screen = True
        return ""

    def do_date(self, args):
        """Display current date and time."""
        if len(args) > MAX_ARGS:
            return self.fail("date: too many arguments")
        now = datetime.now()
        if not args:
            return now.strftime("%a %b %d %H:%M:%S %Y")
        arg = args[0]
        if arg.startswith("+"):
            fmt = arg[1:]
            try:
                return now.strftime(fmt)
            except ValueError as err:
                return self.fail(f"date: invalid format '{fmt}': {err}")
        if arg in ("-u", "--utc"):
            return datetime.now(timezone.utc).strftime(
                "%a %b %d %H:%M:%S UTC %Y"
            )
        return self.fail(f"date: invalid option -- '{arg}'")

    def do_mkdir(self, args):
        """Create new directory/directories in memory VFS."""
        if not args:
            return self.fail("mkdir: missing operand")
        for arg in args:
            if arg.startswith("-"):
                continue
            target = resolve_path(self.cwd, arg)
            if self.is_dir(target) or self.is_file(target):
                return self.fail(
                    f"mkdir: cannot create directory '{arg}': File exists"
                )
            parent = resolve_path(target, "..")
            if parent and not self.is_dir(parent):
                return self.fail(
                    f"mkdir: cannot create directory '{arg}': "
                    "No such file or directory"
                )
            self.vfs_dirs.append(target)
        return ""

    def do_rmdir(self, args):
        """Remove empty directory/directories from in-memory VFS."""
        if not args:
            return self.fail("rmdir: missing operand")
        for arg in args:
            if arg.startswith("-"):
                continue
            target = resolve_path(self.cwd, arg)
            if not target:
                return self.fail(
                    f"rmdir: failed to remove '{arg}': Invalid argument"
                )
            if self.is_file(target):
                return self.fail(
                    f"rmdir: failed to remove '{arg}': Not a directory"
                )
            if not self.is_dir(target):
                return self.fail(
                    f"rmdir: failed to remove '{arg}': "
                    "No such file or directory"
                )
            if target == self.cwd or self.cwd.startswith(f"{target}/"):
                return self.fail(
                    f"rmdir: failed to remove '{arg}': Invalid argument"
                )
            entries = self.list_dir_entries(target)
            if entries:
                return self.fail(
                    f"rmdir: failed to remove '{arg}': Directory not empty"
                )
            self.vfs_dirs.remove(target)
        return ""

    def do_vfs_info(self, args):
        """Display VFS name and SHA-256 digest."""
        if args:
            return self.fail("vfs-info: too many arguments")
        if not self.vfs_path:
            return self.fail("vfs-info: vfs is not loaded")
        if self.vfs_error:
            return self.fail(self.vfs_error)
        digest = vfs_hash(self.vfs_dirs, self.vfs_files)
        return f"name: {self.vfs_name}\nsha256: {digest}"

    def do_exit(self, args):
        """Terminate the shell."""
        if len(args) > MAX_ARGS:
            return self.fail("exit: too many arguments")
        if args and not args[0].isdigit():
            return self.fail(f"exit: {args[0]}: numeric argument required")
        self.running = False
        return ""
