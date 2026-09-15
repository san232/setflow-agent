"""Create a source-only submission archive from Git's non-ignored file list."""

from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> None:
    """Exclude environments, runtime DBs, .env, and exports using the project ignore rules."""
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=root, check=True, capture_output=True)
    names = sorted(set(name for name in result.stdout.decode("utf-8").split("\0") if name))
    output = root.parent / "SetFlow-Agent-submission.zip"
    forbidden = {".env", ".venv", ".venv-verify", "__pycache__", ".git", "exports", "artifacts"}
    sources: list[tuple[Path, str]] = []
    for name in names:
        path = (root / name).resolve()
        path.relative_to(root)
        relative = Path(name)
        if any(part in forbidden for part in relative.parts) or path.suffix in (".db", ".pyc", ".sqlite"):
            raise ValueError(f"Excluded runtime or sensitive file appears in submission: {name}")
        if path.is_file():
            sources.append((path, f"setflow-agent/{relative.as_posix()}"))
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path, name in sources:
            archive.write(path, name)
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive integrity check failed.")
    print(f"Created {output.name}: {len(sources)} files, {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
