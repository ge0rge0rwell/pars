import os
import tarfile


def create_backup(file_paths: list, output_path: str) -> None:
    with tarfile.open(output_path, "w:gz") as tar:
        for path in file_paths:
            tar.add(path, arcname=os.path.basename(path))


def restore_backup(archive_path: str, target_dir: str) -> None:
    os.makedirs(target_dir, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = os.path.realpath(os.path.join(target_dir, member.name))
            if not member_path.startswith(os.path.realpath(target_dir) + os.sep):
                raise ValueError(f"unsafe archive member path: {member.name!r}")
        tar.extractall(target_dir)
