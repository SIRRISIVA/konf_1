import unittest

from shell import Shell, parse, vfs_name_from_path


def make_shell(vfs_path="", prompt_text=""):
    return Shell(vfs_path, prompt_text)


class TestParse(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse("ls -l /home"), ("ls", ["-l", "/home"]))

    def test_quotes(self):
        self.assertEqual(parse("cd \"my dir\" 'a b'"),
                         ("cd", ["my dir", "a b"]))

    def test_empty(self):
        self.assertEqual(parse(""), (None, []))

    def test_unclosed_quote(self):
        with self.assertRaises(ValueError):
            parse("ls \"abc")


class TestShell(unittest.TestCase):
    def test_ls(self):
        self.assertEqual(make_shell().execute("ls -l"), "ls ['-l']")

    def test_cd(self):
        self.assertEqual(make_shell().execute("cd \"my dir\""),
                         "cd ['my dir']")

    def test_cd_too_many_args(self):
        self.assertEqual(make_shell().execute("cd a b"),
                         "cd: too many arguments")

    def test_unknown_command(self):
        self.assertEqual(make_shell().execute("abc"),
                         "abc: command not found")

    def test_syntax_error(self):
        self.assertIn("syntax error", make_shell().execute("ls \"abc"))

    def test_error_flag(self):
        shell = make_shell()
        shell.execute("abc")
        self.assertTrue(shell.error)
        shell.execute("ls")
        self.assertFalse(shell.error)

    def test_exit(self):
        shell = make_shell()
        shell.execute("exit")
        self.assertFalse(shell.running)

    def test_exit_too_many_args(self):
        shell = make_shell()
        self.assertEqual(shell.execute("exit 1 2"),
                         "exit: too many arguments")
        self.assertTrue(shell.running)

    def test_exit_not_number(self):
        shell = make_shell()
        self.assertEqual(shell.execute("exit abc"),
                         "exit: abc: numeric argument required")
        self.assertTrue(shell.running)


class TestParameters(unittest.TestCase):
    def test_default_prompt(self):
        self.assertEqual(make_shell().prompt(), "vfs:~$ ")

    def test_custom_prompt(self):
        self.assertEqual(make_shell(prompt_text="user>").prompt(), "user> ")

    def test_vfs_name_from_path(self):
        self.assertEqual(vfs_name_from_path("C:/data/my_vfs"), "my_vfs")

    def test_vfs_name_with_slash(self):
        self.assertEqual(vfs_name_from_path("/home/user/data/"), "data")

    def test_vfs_name_empty(self):
        self.assertEqual(vfs_name_from_path(""), "vfs")

    def test_vfs_name_in_shell(self):
        self.assertEqual(make_shell("C:/data/my_vfs").vfs_name, "my_vfs")


if __name__ == "__main__":
    unittest.main()
