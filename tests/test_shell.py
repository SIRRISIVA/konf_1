import unittest

from shell import Shell, parse


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
    def setUp(self):
        self.shell = Shell()

    def test_ls(self):
        self.assertEqual(self.shell.execute("ls -l"), "ls ['-l']")

    def test_cd(self):
        self.assertEqual(self.shell.execute("cd \"my dir\""), "cd ['my dir']")

    def test_cd_too_many_args(self):
        self.assertEqual(self.shell.execute("cd a b"),
                         "cd: too many arguments")

    def test_unknown_command(self):
        self.assertEqual(self.shell.execute("abc"), "abc: command not found")

    def test_syntax_error(self):
        self.assertIn("syntax error", self.shell.execute("ls \"abc"))

    def test_exit(self):
        self.shell.execute("exit")
        self.assertFalse(self.shell.running)

    def test_exit_too_many_args(self):
        self.assertEqual(self.shell.execute("exit 1 2"),
                         "exit: too many arguments")
        self.assertTrue(self.shell.running)

    def test_exit_not_number(self):
        self.assertEqual(self.shell.execute("exit abc"),
                         "exit: abc: numeric argument required")
        self.assertTrue(self.shell.running)


if __name__ == "__main__":
    unittest.main()
