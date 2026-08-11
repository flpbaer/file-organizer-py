import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from file_organizer.cli import main
from file_organizer.config import FOLDERS
from file_organizer.organizer import (
    build_extension_map,
    folder_for,
    organize,
    organize_others,
)


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


class TempDirectoryTest(unittest.TestCase):
    """Base com um diretório temporário para cada teste."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.directory = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def touch(self, name, content=""):
        path = self.directory / name
        path.write_text(content)
        return path


class OrganizeTest(TempDirectoryTest):
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


class OrganizeOthersTest(TempDirectoryTest):
    def test_moves_skipped_files_into_others(self):
        self.touch("script.sh")
        self.touch("notas.md")
        result = organize(target=self.directory)

        organize_others(result)

        self.assertEqual(result.skipped, [])
        self.assertEqual(len(result.moved), 2)
        self.assertTrue((self.directory / "Others" / "script.sh").is_file())
        self.assertTrue((self.directory / "Others" / "notas.md").is_file())

    def test_dry_run_does_not_touch_the_disk(self):
        self.touch("script.sh")
        result = organize(target=self.directory, dry_run=True)

        organize_others(result, dry_run=True)

        # target é o diretório já resolvido, que no macOS difere de self.directory.
        self.assertEqual(
            result.moved,
            [(result.target / "script.sh", result.target / "Others" / "script.sh")],
        )
        self.assertFalse((self.directory / "Others").exists())

    def test_others_is_not_organized_again(self):
        self.touch("script.sh")
        organize_others(organize(target=self.directory))

        result = organize(target=self.directory)

        self.assertEqual(result.moved, [])
        self.assertEqual(result.skipped, [])

    def test_does_not_overwrite_existing_destination(self):
        (self.directory / "Others").mkdir()
        (self.directory / "Others" / "script.sh").write_text("antigo")
        self.touch("script.sh", "novo")

        organize_others(organize(target=self.directory))

        self.assertEqual((self.directory / "Others" / "script.sh").read_text(), "antigo")
        self.assertEqual(
            (self.directory / "Others" / "script (1).sh").read_text(), "novo"
        )

    def test_custom_folder_name(self):
        self.touch("script.sh")

        organize_others(organize(target=self.directory), folder_name="Diversos")

        self.assertTrue((self.directory / "Diversos" / "script.sh").is_file())


class CliOthersTest(TempDirectoryTest):
    def run_cli(self, *extra, answers=()):
        """Roda a CLI num terminal simulado, respondendo à pergunta."""
        output = io.StringIO()
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", side_effect=list(answers) or EOFError),
            redirect_stdout(output),
        ):
            code = main([str(self.directory), *extra])
        return code, output.getvalue()

    def test_answering_yes_creates_others(self):
        self.touch("script.sh")

        code, output = self.run_cli(answers=["s"])

        self.assertEqual(code, 0)
        self.assertTrue((self.directory / "Others" / "script.sh").is_file())
        self.assertIn("1 arquivo(s) movido(s), 0 ignorado(s)", output)

    def test_answering_no_leaves_the_file_alone(self):
        self.touch("script.sh")

        code, output = self.run_cli(answers=["n"])

        self.assertEqual(code, 0)
        self.assertTrue((self.directory / "script.sh").is_file())
        self.assertFalse((self.directory / "Others").exists())
        self.assertIn("0 arquivo(s) movido(s), 1 ignorado(s)", output)

    def test_invalid_answer_asks_again(self):
        self.touch("script.sh")

        _, output = self.run_cli(answers=["talvez", "sim"])

        self.assertIn("Responda s (sim) ou n (não).", output)
        self.assertTrue((self.directory / "Others" / "script.sh").is_file())

    def test_does_not_ask_when_nothing_was_skipped(self):
        self.touch("foto.png")

        # input() levantaria EOFError se fosse chamado; a pergunta não deve sair.
        _, output = self.run_cli()

        self.assertNotIn("Others", output)

    def test_flag_skips_the_question(self):
        self.touch("script.sh")

        self.run_cli("--others")

        self.assertTrue((self.directory / "Others" / "script.sh").is_file())

    def test_no_others_flag_skips_the_question(self):
        self.touch("script.sh")

        self.run_cli("--no-others")

        self.assertTrue((self.directory / "script.sh").is_file())

    def test_does_not_ask_outside_a_terminal(self):
        self.touch("script.sh")

        with redirect_stdout(io.StringIO()), patch("sys.stdin.isatty", return_value=False):
            main([str(self.directory)])

        self.assertTrue((self.directory / "script.sh").is_file())


if __name__ == "__main__":
    unittest.main()
