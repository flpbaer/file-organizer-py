import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from file_organizer.config import FOLDERS
from file_organizer.organizer import build_extension_map, folder_for, organize


class ExtensionMatchingTest(unittest.TestCase):
    def setUp(self):
        self.extension_map = build_extension_map(FOLDERS)

    def match(self, name):
        return folder_for(Path(name), self.extension_map)

    def test_matches_by_extension(self):
        self.assertEqual(self.match("foto.png"), "Images")
        self.assertEqual(self.match("backup.zip"), "Compressed")
        self.assertEqual(self.match("nota.pdf"), "Documents")

    def test_extension_is_case_insensitive(self):
        self.assertEqual(self.match("FOTO.JPG"), "Images")

    def test_compound_extension_wins_over_short_one(self):
        self.assertEqual(self.match("pacote.tar.gz"), "Installers")

    def test_unknown_extension_is_skipped(self):
        self.assertIsNone(self.match("script.sh"))

    def test_extension_in_the_middle_of_the_name_does_not_match(self):
        # No original em JS, "meu-png-favorito.txt" casava por substring.
        self.assertIsNone(self.match("meu-png-favorito.txt"))


class OrganizeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.directory = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def touch(self, name, content=""):
        path = self.directory / name
        path.write_text(content)
        return path

    def test_moves_files_into_folders(self):
        self.touch("foto.png")
        self.touch("nota.pdf")

        result = organize(target=self.directory)

        self.assertEqual(len(result.moved), 2)
        self.assertTrue((self.directory / "Images" / "foto.png").is_file())
        self.assertTrue((self.directory / "Documents" / "nota.pdf").is_file())

    def test_dry_run_does_not_touch_the_disk(self):
        self.touch("foto.png")

        result = organize(target=self.directory, dry_run=True)

        self.assertEqual(len(result.moved), 1)
        self.assertTrue((self.directory / "foto.png").is_file())
        self.assertFalse((self.directory / "Images").exists())

    def test_unknown_files_stay_where_they_are(self):
        self.touch("script.sh")

        result = organize(target=self.directory)

        self.assertEqual([p.name for p in result.skipped], ["script.sh"])
        self.assertTrue((self.directory / "script.sh").is_file())

    def test_does_not_overwrite_existing_destination(self):
        (self.directory / "Images").mkdir()
        (self.directory / "Images" / "foto.png").write_text("antigo")
        self.touch("foto.png", "novo")

        organize(target=self.directory)

        self.assertEqual((self.directory / "Images" / "foto.png").read_text(), "antigo")
        self.assertEqual(
            (self.directory / "Images" / "foto (1).png").read_text(), "novo"
        )

    def test_created_folders_are_not_organized_again(self):
        self.touch("foto.png")
        organize(target=self.directory)

        result = organize(target=self.directory)

        self.assertEqual(result.moved, [])
        self.assertEqual(result.skipped, [])

    def test_missing_directory_raises(self):
        with self.assertRaises(NotADirectoryError):
            organize(target=self.directory / "nao-existe")


if __name__ == "__main__":
    unittest.main()
