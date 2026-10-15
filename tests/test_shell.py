import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "src"))

from shell import (  # noqa: E402
    Shell,
    load_vfs,
    parse,
    resolve_path,
    vfs_hash,
    vfs_name_from_path,
)

MIN_VFS = os.path.join(ROOT, "vfs_min")
DEEP_VFS = os.path.join(ROOT, "vfs_deep")


def make_shell(vfs_path="", prompt_text=""):
    return Shell(vfs_path, prompt_text)


class BaseTest(unittest.TestCase):
    def show_io(self, input_val, output_val):
        print(f"\n[{self._testMethodName}]")
        print(f"Input: {input_val}")
        print(f"Output: {output_val}")

    def run_cmd(self, shell, cmd):
        result = shell.execute(cmd)
        self.show_io(cmd, result if result else "(empty)")
        return result


class TestParse(BaseTest):
    def test_simple(self):
        res = parse("ls -l /home")
        self.show_io("ls -l /home", res)
        self.assertEqual(res, ("ls", ["-l", "/home"]))

    def test_quotes(self):
        cmd = "cd \"my dir\" 'a b'"
        res = parse(cmd)
        self.show_io(cmd, res)
        self.assertEqual(res, ("cd", ["my dir", "a b"]))

    def test_empty(self):
        res = parse("")
        self.show_io("''", res)
        self.assertEqual(res, (None, []))

    def test_unclosed_quote(self):
        self.show_io("ls \"abc", "ValueError raised")
        with self.assertRaises(ValueError):
            parse("ls \"abc")


class TestPathResolve(BaseTest):
    def test_resolve_root_and_relative(self):
        res = resolve_path("docs", "work")
        self.show_io("cwd='docs', path='work'", res)
        self.assertEqual(res, "docs/work")

    def test_resolve_parent(self):
        res = resolve_path("docs/work", "..")
        self.show_io("cwd='docs/work', path='..'", res)
        self.assertEqual(res, "docs")

    def test_resolve_absolute(self):
        res = resolve_path("docs/work", "/etc")
        self.show_io("cwd='docs/work', path='/etc'", res)
        self.assertEqual(res, "etc")


class TestShell(BaseTest):
    def test_unknown_command(self):
        shell = make_shell()
        res = self.run_cmd(shell, "abc")
        self.assertEqual(res, "abc: command not found")
        self.assertTrue(shell.error)

    def test_syntax_error(self):
        shell = make_shell()
        res = self.run_cmd(shell, 'ls "abc')
        self.assertIn("syntax error", res)
        self.assertTrue(shell.error)

    def test_error_flag_reset(self):
        shell = make_shell()
        self.run_cmd(shell, "abc")
        self.assertTrue(shell.error)
        self.run_cmd(shell, "clear")
        self.assertFalse(shell.error)

    def test_exit(self):
        shell = make_shell()
        self.run_cmd(shell, "exit")
        self.assertFalse(shell.running)

    def test_exit_too_many_args(self):
        shell = make_shell()
        res = self.run_cmd(shell, "exit 1 2")
        self.assertEqual(res, "exit: too many arguments")
        self.assertTrue(shell.running)

    def test_exit_not_number(self):
        shell = make_shell()
        res = self.run_cmd(shell, "exit abc")
        self.assertEqual(res, "exit: abc: numeric argument required")
        self.assertTrue(shell.running)


class TestCommands(BaseTest):
    def test_ls_root(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "ls")
        self.assertEqual(res, "docs\netc\nreadme.txt")

    def test_ls_subdir(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "ls docs")
        self.assertEqual(res, "notes.txt\nwork")

    def test_ls_file(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "ls readme.txt")
        self.assertEqual(res, "readme.txt")

    def test_ls_all_flag(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "ls -a docs")
        self.assertIn(".\n..\nnotes.txt\nwork", res)

    def test_ls_long_flag(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "ls -l")
        self.assertIn("drwxr-xr-x", res)
        self.assertIn("readme.txt", res)

    def test_ls_not_found(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "ls no_such_file")
        self.assertIn("No such file or directory", res)
        self.assertTrue(shell.error)

    def test_cd_success(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "cd docs")
        self.assertEqual(res, "")
        self.assertEqual(shell.cwd, "docs")

    def test_cd_nested_and_parent(self):
        shell = make_shell(DEEP_VFS)
        self.run_cmd(shell, "cd docs/work")
        self.assertEqual(shell.cwd, "docs/work")
        self.run_cmd(shell, "cd ..")
        self.assertEqual(shell.cwd, "docs")

    def test_cd_to_root(self):
        shell = make_shell(DEEP_VFS)
        self.run_cmd(shell, "cd docs")
        self.run_cmd(shell, "cd /")
        self.assertEqual(shell.cwd, "")

    def test_cd_not_directory(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "cd readme.txt")
        self.assertEqual(res, "cd: readme.txt: Not a directory")
        self.assertTrue(shell.error)

    def test_cd_not_found(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "cd no_such_dir")
        self.assertEqual(res, "cd: no_such_dir: No such file or directory")
        self.assertTrue(shell.error)

    def test_cd_too_many_args(self):
        shell = make_shell(DEEP_VFS)
        res = self.run_cmd(shell, "cd a b")
        self.assertEqual(res, "cd: too many arguments")
        self.assertTrue(shell.error)

    def test_clear(self):
        shell = make_shell()
        res = self.run_cmd(shell, "clear")
        self.assertEqual(res, "")
        self.assertTrue(shell.clear_screen)

    def test_clear_too_many_args(self):
        shell = make_shell()
        res = self.run_cmd(shell, "clear extra")
        self.assertEqual(res, "clear: too many arguments")
        self.assertTrue(shell.error)

    def test_date_default(self):
        shell = make_shell()
        res = self.run_cmd(shell, "date")
        self.assertTrue(len(res) > 0)
        self.assertFalse(shell.error)

    def test_date_format(self):
        shell = make_shell()
        res = self.run_cmd(shell, "date +%Y")
        self.assertTrue(res.isdigit())
        self.assertEqual(len(res), 4)

    def test_date_utc(self):
        shell = make_shell()
        res = self.run_cmd(shell, "date -u")
        self.assertIn("UTC", res)

    def test_date_invalid_option(self):
        shell = make_shell()
        res = self.run_cmd(shell, "date -x")
        self.assertEqual(res, "date: invalid option -- '-x'")
        self.assertTrue(shell.error)

    def test_date_too_many_args(self):
        shell = make_shell()
        res = self.run_cmd(shell, "date 1 2")
        self.assertEqual(res, "date: too many arguments")
        self.assertTrue(shell.error)


class TestParameters(BaseTest):
    def test_default_prompt(self):
        prompt = make_shell().prompt()
        self.show_io("make_shell().prompt()", prompt)
        self.assertEqual(prompt, "vfs:~$ ")

    def test_custom_prompt(self):
        prompt = make_shell(prompt_text="user>").prompt()
        self.show_io("make_shell(prompt_text='user>').prompt()", prompt)
        self.assertEqual(prompt, "user> ")

    def test_vfs_name_from_path(self):
        name = vfs_name_from_path("C:/data/my_vfs")
        self.show_io("C:/data/my_vfs", name)
        self.assertEqual(name, "my_vfs")

    def test_vfs_name_with_slash(self):
        name = vfs_name_from_path("/home/user/data/")
        self.show_io("/home/user/data/", name)
        self.assertEqual(name, "data")

    def test_vfs_name_empty(self):
        name = vfs_name_from_path("")
        self.show_io("''", name)
        self.assertEqual(name, "vfs")

    def test_vfs_name_in_shell(self):
        name = make_shell("C:/data/my_vfs").vfs_name
        self.show_io("make_shell('C:/data/my_vfs').vfs_name", name)
        self.assertEqual(name, "my_vfs")


class TestVfs(BaseTest):
    def test_load_min(self):
        dirs, files = load_vfs(MIN_VFS)
        self.show_io("load_vfs(MIN_VFS)", f"dirs={dirs}, files={list(files)}")
        self.assertEqual(dirs, [])
        self.assertEqual(list(files), ["readme.txt"])
        self.assertIn(b"hello", files["readme.txt"])

    def test_load_deep(self):
        dirs, files = load_vfs(DEEP_VFS)
        self.show_io(
            "load_vfs(DEEP_VFS)",
            f"dirs_count={len(dirs)}, files_count={len(files)}"
        )
        self.assertIn("docs/work", dirs)
        self.assertIn("docs/work/reports/year.txt", files)

    def test_hash_is_stable(self):
        first = vfs_hash(*load_vfs(MIN_VFS))
        second = vfs_hash(*load_vfs(MIN_VFS))
        self.show_io("vfs_hash comparison", f"{first} == {second}")
        self.assertEqual(first, second)

    def test_hash_differs(self):
        first = vfs_hash(*load_vfs(MIN_VFS))
        second = vfs_hash(*load_vfs(DEEP_VFS))
        self.show_io("vfs_hash distinct", f"{first} != {second}")
        self.assertNotEqual(first, second)

    def test_vfs_info(self):
        shell = make_shell(MIN_VFS)
        res = self.run_cmd(shell, "vfs-info")
        self.assertIn("name: vfs_min", res)
        self.assertIn("sha256: ", res)

    def test_vfs_info_without_vfs(self):
        shell = make_shell()
        res = self.run_cmd(shell, "vfs-info")
        self.assertEqual(res, "vfs-info: vfs is not loaded")

    def test_vfs_info_with_args(self):
        shell = make_shell(MIN_VFS)
        res = self.run_cmd(shell, "vfs-info extra")
        self.assertEqual(res, "vfs-info: too many arguments")

    def test_missing_vfs(self):
        shell = make_shell("no_such_vfs")
        self.show_io("make_shell('no_such_vfs')", shell.vfs_error)
        self.assertIn("no such directory", shell.vfs_error)


if __name__ == "__main__":
    unittest.main()
