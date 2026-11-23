import unittest

from wordmeter.core import count_text


class CountTextTest(unittest.TestCase):
    def test_empty(self):
        stats = count_text("")
        self.assertEqual((stats.lines, stats.words, stats.chars), (0, 0, 0))

    def test_mixed_text(self):
        stats = count_text("hello world\n你好\n")
        self.assertEqual(stats.lines, 2)
        self.assertEqual(stats.words, 4)
        self.assertEqual(stats.cjk, 2)

    def test_last_line_without_newline(self):
        stats = count_text("a\nb")
        self.assertEqual(stats.lines, 2)


if __name__ == "__main__":
    unittest.main()
