# file-organizer

A file organizer: it scans a folder and moves each file into a subfolder based on
its extension (`Images`, `Compressed`, `Installers`, `Documents`).

Written in Python, with no external dependencies — standard library only.
It is a rewrite of a study project I originally wrote in JavaScript.

Files that no rule recognizes are left alone by default — at the end of the run
the application asks whether you want to gather them into an `Others` folder.

```
file_organizer/
├── config.py                  # folders, extensions and target directory
├── organizer.py               # core rule (extension -> folder) + Others folder
├── cli.py                     # command line interface
└── services/
    ├── get_local_files.py     # lists the files in the directory
    ├── create_folder.py       # creates the destination folder
    └── move_file.py           # moves the file
```

## Usage

There is no path to change inside the code: the folder comes from an argument,
from the `FILE_ORGANIZER_TARGET` environment variable or, by default,
`~/Downloads`.

```bash
# see what would be moved, without touching anything
python3 -m file_organizer ~/Downloads --dry-run

# actually organize
python3 -m file_organizer ~/Downloads

# using the default (~/Downloads) or the environment variable
python3 -m file_organizer
FILE_ORGANIZER_TARGET=~/Desktop python3 -m file_organizer
```

Installing as a command:

```bash
pip install -e .
file-organizer ~/Downloads --dry-run
```

Options: `-n/--dry-run` (simulates), `-q/--quiet` (summary only),
`--others/--no-others` (answers the `Others` folder question up front).

To change the folders or add extensions, edit the `FOLDERS` dictionary in
[`file_organizer/config.py`](file_organizer/config.py). The folder name for
unrecognized files is `OTHERS_FOLDER`, in the same file.

## The `Others` folder

Once the organizing is done, if any file was left without a folder, the
application lists what is left over and asks:

```
3 arquivo(s) não foram organizados:
  Makefile
  notas.md
  script.sh
Criar Others/ e mover esse(s) 3 arquivo(s) para lá? [s/N]
```

The CLI itself speaks Portuguese — the block above is its actual output, asking
whether to create `Others/` and move those 3 files there.

`s`/`sim`/`y` moves them; `n`/Enter/Ctrl+C leaves everything as it is. To avoid
depending on the question — in a script, cron job or pipe — use `--others`
(always moves) or `--no-others` (never moves). Outside a terminal, with no flag,
nothing is moved.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Behavior details

- The extension is matched against the **end** of the name, not as a substring:
  `my-png-favorite.txt` is not treated as an image, and each file is moved once.
- Compound extensions (`tar.gz`, `tar.xz`) match before the short ones.
- Nothing is overwritten at the destination: if `photo.png` is already there, the
  new one becomes `photo (1).png`.
- Subfolders are ignored during the scan, so running twice is safe.
- Files with an unknown extension stay where they are, unless you accept the
  `Others` folder — which follows the same rules (no overwriting, ignored on
  subsequent runs).
- Disk/permission errors are reported per file, without aborting the rest.
