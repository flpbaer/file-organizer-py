# file-organizer

Um organizador de arquivos: varre uma pasta e move cada arquivo para uma subpasta
de acordo com a extensão (`Images`, `Compressed`, `Installers`, `Documents`).

Escrito em Python, sem dependências externas — só a biblioteca padrão.
É a reescrita de um projeto de estudo que originalmente eu fiz em JavaScript.

```
file_organizer/
├── config.py                  # pastas, extensões e diretório alvo
├── organizer.py               # regra central (extensão -> pasta)
├── cli.py                     # interface de linha de comando
└── services/
    ├── get_local_files.py     # lista os arquivos do diretório
    ├── create_folder.py       # cria a pasta de destino
    └── move_file.py           # move o arquivo
```

## Uso

Não é preciso trocar path nenhum dentro do código: a pasta vem por argumento,
pela variável de ambiente `FILE_ORGANIZER_TARGET` ou, por padrão, `~/Downloads`.

```bash
# ver o que seria movido, sem mexer em nada
python3 -m file_organizer ~/Downloads --dry-run

# organizar de verdade
python3 -m file_organizer ~/Downloads

# usando o padrão (~/Downloads) ou a variável de ambiente
python3 -m file_organizer
FILE_ORGANIZER_TARGET=~/Desktop python3 -m file_organizer
```

Instalando como comando:

```bash
pip install -e .
file-organizer ~/Downloads --dry-run
```

Opções: `-n/--dry-run` (simula), `-q/--quiet` (só o resumo).

Para mudar as pastas ou adicionar extensões, edite o dicionário `FOLDERS` em
[`file_organizer/config.py`](file_organizer/config.py).

## Testes

```bash
python3 -m unittest discover -s tests
```

## Detalhes de comportamento

- A extensão é comparada pelo **final** do nome, não por substring: `meu-png-favorito.txt`
  não é tratado como imagem, e cada arquivo é movido uma única vez.
- Extensões compostas (`tar.gz`, `tar.xz`) casam antes das curtas.
- Nada é sobrescrito no destino: se `foto.png` já existir lá, o novo vira `foto (1).png`.
- Subpastas são ignoradas na varredura, então rodar duas vezes é seguro.
- Arquivos com extensão desconhecida ficam onde estão.
- Erros de disco/permissão são reportados por arquivo, sem abortar o resto.
