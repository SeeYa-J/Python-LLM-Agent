# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
import unittest
from ui.url import HaivenUrl


class TestPath(unittest.TestCase):
    def setUp(self):
        self.path = HaivenUrl()

    def test_path_about(self):
        self.assertEqual(self.path.PATH_ABOUT, "about")

    def test_path_analysis(self):
        self.assertEqual(self.path.PATH_ANALYSIS, "analysis")

    def test_path_auth(self):
        self.assertEqual(self.path.PATH_AUTH, "auth")

    def test_path_chat(self):
        self.assertEqual(self.path.PATH_CHAT, "chat")

    def test_path_coding(self):
        self.assertEqual(self.path.PATH_CODING, "coding")

    def test_path_general(self):
        self.assertEqual(self.path.PATH_GENERAL_DEPRECATED, "teamai")

    def test_path_knowledge(self):
        self.assertEqual(self.path.PATH_KNOWLEDGE, "knowledge")

    def test_path_login(self):
        self.assertEqual(self.path.PATH_LOGIN, "login")

    def test_path_logout(self):
        self.assertEqual(self.path.PATH_LOGOUT, "logout")

    def test_path_testing(self):
        self.assertEqual(self.path.PATH_TESTING, "testing")


if __name__ == "__main__":
    unittest.main()
