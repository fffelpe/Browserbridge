#!/usr/bin/env python3

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_FILES = [
    ROOT
    / "native-host"
    / "site.felipeleal.browserbridge.json"
]


FORBIDDEN_DIRECTORY_NAMES = {
    "__pycache__",
}


FORBIDDEN_EXTENSIONS = {
    ".pyc",
    ".pyo",
}


SENSITIVE_PATTERNS = [

    # Windows home directories
    re.compile(
        r"C:\\Users\\[^\\]+",
        re.IGNORECASE
    ),

    # Unix home directories
    re.compile(
        r"/home/[^/\s]+",
        re.IGNORECASE
    ),

    # macOS home directories
    re.compile(
        r"/Users/[^/\s]+",
        re.IGNORECASE
    ),

]


TEXT_EXTENSIONS = {

    ".py",
    ".js",
    ".json",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".ps1",
    ".sh",
    ".bat",
    ".yml",
    ".yaml",
    ".toml",

}


errors = []


def check_forbidden_files():

    for path in FORBIDDEN_FILES:

        if path.exists():

            errors.append(
                f"Arquivo local versionavel encontrado: "
                f"{path.relative_to(ROOT)}"
            )


def check_generated_files():

    for path in ROOT.rglob("*"):

        if any(
            part in FORBIDDEN_DIRECTORY_NAMES
            for part in path.parts
        ):

            errors.append(
                f"Diretorio Python gerado encontrado: "
                f"{path.relative_to(ROOT)}"
            )

        if (
            path.is_file()
            and path.suffix.lower()
            in FORBIDDEN_EXTENSIONS
        ):

            errors.append(
                f"Bytecode Python encontrado: "
                f"{path.relative_to(ROOT)}"
            )


def check_text_files():

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:

            text = path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:

            continue

        for pattern in SENSITIVE_PATTERNS:

            for match in pattern.finditer(text):

                errors.append(
                    "Possivel caminho pessoal em "
                    f"{path.relative_to(ROOT)}: "
                    f"{match.group(0)}"
                )


def main():

    check_forbidden_files()

    check_generated_files()

    check_text_files()

    if errors:

        print("")
        print(
            "BrowserBridge privacy check: FALHOU"
        )
        print("")

        for error in errors:

            print(
                f"[ERRO] {error}"
            )

        print("")

        sys.exit(1)

    print("")
    print(
        "BrowserBridge privacy check: OK"
    )
    print(
        "Nenhum artefato local ou caminho "
        "pessoal foi encontrado."
    )
    print("")


if __name__ == "__main__":

    main()
