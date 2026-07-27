import argparse
import os
from datetime import datetime, timezone

from pars_admin.backup import create_backup

_BACKUP_FILENAMES = (
    "registry.sqlite3",
    "admin_instance_id",
    "trust_root.key",
    "trust_root.pub",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pars admin console backup")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    existing_paths = [
        os.path.join(args.data_dir, name)
        for name in _BACKUP_FILENAMES
        if os.path.exists(os.path.join(args.data_dir, name))
    ]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output_path = os.path.join(args.output_dir, f"pars-admin-backup-{timestamp}.tar.gz")
    create_backup(existing_paths, output_path)


if __name__ == "__main__":
    main()
