import os
import pytsk3
from recovery_utils import recover_by_signature

# Where both metadata and carved files go, before final copy
TEMP_REC_DIR = "./recovered_files"

class RawImg(pytsk3.Img_Info):
    def __init__(self, path):
        self._fd = open(path, "rb")
        super(RawImg, self).__init__()
    def close(self):
        self._fd.close()
    def read(self, offset, size):
        self._fd.seek(offset)
        return self._fd.read(size)
    def get_size(self):
        cur = self._fd.tell()
        self._fd.seek(0, os.SEEK_END)
        sz = self._fd.tell()
        self._fd.seek(cur)
        return sz

def recursive_scan(fs_info, directory, progress_callback, idx, total, names):
    """Walk the FS tree, report each filename, collect all deleted names."""
    for f in directory:
        try:
            raw  = f.info.name.name or b""
            name = raw.decode("latin1", errors="ignore") or "<unknown>"

            idx[0] += 1
            pct = idx[0] / total
            if progress_callback:
                progress_callback(pct, name)
            print(f"Scanning file: {name}")

            # Skip system entries
            if name.startswith("$"):
                continue

            names.append(name)

            # Recurse into directories
            if (f.info.meta and
                f.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR and
                name not in (".","..")):
                try:
                    sub = f.as_directory()
                    recursive_scan(fs_info, sub, progress_callback, idx, total, names)
                except Exception:
                    pass

        except Exception as e:
            print(f"Error processing {name}: {e}")

def count_entries(fs_info, directory):
    """Count all non-system entries (for progress estimation)."""
    cnt = 0
    for f in directory:
        try:
            raw  = f.info.name.name or b""
            name = raw.decode("latin1", errors="ignore") or "<unknown>"
            if name.startswith("$"):
                continue
            cnt += 1
            if (f.info.meta and
                f.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR and
                name not in (".","..")):
                cnt += count_entries(fs_info, f.as_directory())
        except Exception:
            pass
    return cnt

def list_deleted_files(disk_path, progress_callback=None):
    """
    Metadata‐only pass: finds deleted filenames via unallocated flags or FAT markers.
    Returns list of original names.
    """
    names = []
    try:
        img  = RawImg(disk_path)
        fs   = pytsk3.FS_Info(img)
        root = fs.open_dir("/")

        # Step 1: count total entries
        if progress_callback:
            progress_callback(0, "Counting files…")
        total = count_entries(fs, root)

        # Step 2: recursive scan
        if progress_callback:
            progress_callback(0, "Metadata scanning started")
        idx = [0]
        recursive_scan(fs, root, progress_callback, idx, total, names)
        if progress_callback:
            progress_callback(1.0, "Metadata scanning done")

        img.close()

    except Exception as e:
        print(f"Metadata scan failed: {e}")

    return names

def recover_metadata(disk_path, names, output_dir=TEMP_REC_DIR):
    """
    Dump each metadata‐found file under its ORIGINAL name into output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    recovered = []
    try:
        img = RawImg(disk_path)
        fs  = pytsk3.FS_Info(img)

        for name in names:
            try:
                # Read the file’s full data
                fobj = fs.open(name)
                size = fobj.info.meta.size or 0
                if size <= 0:
                    print(f"Skipping zero‐length file: {name}")
                    continue

                data = fobj.read_random(0, size)

                # Build a safe path: strip leading slash, create subdirs
                clean = name.lstrip(os.sep)
                out_path = os.path.join(output_dir, clean)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, "wb") as w:
                    w.write(data)
                recovered.append(out_path)
                print(f"Metadata recovered: {out_path}")

            except Exception as ex:
                print(f"Metadata dump failed for {name}: {ex}")

        img.close()

    except Exception as e:
        print(f"Metadata recovery error: {e}")

    return recovered

def unified_scan(disk_path, progress_callback=None):
    """
    1) Metadata pass → list & dump originals
    2) Signature carving → carve new files
    Returns combined list of file‐paths in TEMP_REC_DIR.
    """
    all_paths = []

    # Metadata phase
    names    = list_deleted_files(disk_path, progress_callback)
    md_paths = recover_metadata(disk_path, names, TEMP_REC_DIR)
    all_paths.extend(md_paths)
    for p in md_paths:
        if progress_callback:
            progress_callback(None, f"Meta recov: {os.path.basename(p)}")

    # Carving phase
    if progress_callback:
        progress_callback(None, "Signature scanning started")
    carve_paths = recover_by_signature(
        disk_path,
        TEMP_REC_DIR,
        progress_callback=progress_callback
    )
    all_paths.extend(carve_paths)

    if progress_callback:
        progress_callback(1.0, "Signature scanning done")

    return all_paths
