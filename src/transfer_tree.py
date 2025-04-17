import shutil
import subprocess
from pathlib import Path

from tqdm import tqdm

from trope_paths import browser_root, doc_root


def has_file_changed(filepath: Path) -> bool:
    file_str = str(filepath)

    try:
        # Check if the file is different from HEAD~1
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD~1", file_str],
            check=True,
            capture_output=True,
        )
        return False  # No changes found, exit code is 0
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return True  # Changes found, exit code is 1
        else:
            raise RuntimeError(f"Git command failed: {e.stderr.decode()}")


def transfer_tree(target_dir=doc_root, browser_root=browser_root):
    transfers = []
    for image in browser_root.glob("**/*.png"):
        target = target_dir / image.relative_to(browser_root)
        if not target.exists():
            transfers.append((image, target))

    for doc in browser_root.glob("**/*.md"):
        target = target_dir / doc.relative_to(browser_root).with_suffix(
            ".docx"
        )
        if not target.exists():
            transfers.append((doc, target))
        elif has_file_changed(doc):
            transfers.append((doc, target))

    for src, target in tqdm(transfers, desc="Transferring documents"):
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix == ".png":
            shutil.copy2(src, target)
        elif src.suffix == ".md":
            subprocess.run(["pandoc", str(src), "-o", str(target)], check=True)


if __name__ == "__main__":
    transfer_tree()
