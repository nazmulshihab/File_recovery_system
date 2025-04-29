import os
import pytsk3
from recovery_utils import recover_by_signature

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
        size = self._fd.tell()
        self._fd.seek(cur)
        return size

def recursive_scan(fs_info, directory, progress_callback, recover_names):
    """
    Walk every entry in 'directory'.  Skip NTFS system files,
    but for each other entry:
      - report "Scanning file: name"
      - append name to recover_names
      - recurse if it's a subdirectory
    """
    for file in directory:
        try:
            raw  = file.info.name.name or b""
            name = raw.decode('latin1', errors='ignore') or "<unknown>"

            # Terminal + GUI update:
            print(f"Scanning file: {name}")
            if progress_callback:
                progress_callback(None, name)

            # Skip system metadata files
            if name.startswith("$"):
                continue

            # Always record it as a candidate
            recover_names.append(name)

            # Recurse into subdirs
            if (file.info.meta and
                file.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR and
                name not in (".","..")):
                try:
                    sub = file.as_directory()
                    recursive_scan(fs_info, sub, progress_callback, recover_names)
                except Exception:
                    pass

        except Exception as e:
            print(f"Error processing {name}: {e}")

def list_deleted_files(disk_path, progress_callback=None):
    """
    Metadata phase: walk every file and collect names.
    Returns list of filenames.
    """
    names = []
    try:
        img = RawImg(disk_path)
        fs  = pytsk3.FS_Info(img)
        root= fs.open_dir("/")

        if progress_callback:
            progress_callback(None, "Metadata-based scan started")
        recursive_scan(fs, root, progress_callback, names)
        if progress_callback:
            progress_callback(None, "Metadata-based scan done")

        img.close()
    except Exception as e:
        print(f"Metadata scan failed: {e}")

    return names

def recover_metadata(disk_path, names, output_dir=TEMP_REC_DIR):
    """
    Given a list of filenames, dump their full contents to disk
    named meta_1.ext, meta_2.ext, ... in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    recovered = []

    try:
        img = RawImg(disk_path)
        fs  = pytsk3.FS_Info(img)

        for idx, name in enumerate(names, start=1):
            try:
                fobj = fs.open(name)
                size = fobj.info.meta.size
                data = fobj.read_random(0, size)

                ext = os.path.splitext(name)[1] or ""
                out = os.path.join(output_dir, f"meta_{idx}{ext}")

                with open(out, "wb") as w:
                    w.write(data)

                recovered.append(out)
                print(f"Metadata recovered: {out}")
            except Exception as ex:
                print(f"Failed metadata recover {name}: {ex}")

        img.close()
    except Exception as e:
        print(f"Metadata recovery setup failed: {e}")

    return recovered

def unified_scan(disk_path, progress_callback=None):
    """
    1) Metadata-based walking & recovery
    2) Signature-based carving
    Returns full paths of everything dumped under ./recovered_files
    """
    all_paths = []

    # Phase 1: metadata
    names    = list_deleted_files(disk_path, progress_callback)
    md_paths = recover_metadata(disk_path, names, TEMP_REC_DIR)
    all_paths.extend(md_paths)

    # Report each metadata file
    for p in md_paths:
        if progress_callback:
            progress_callback(None, f"Meta recov: {os.path.basename(p)}")

    # Phase 2: carving
    if progress_callback:
        progress_callback(None, "Signature-based scan started")
    carve_paths = recover_by_signature(disk_path, TEMP_REC_DIR)
    all_paths.extend(carve_paths)

    for p in carve_paths:
        if progress_callback:
            progress_callback(None, f"Carved: {os.path.basename(p)}")
    if progress_callback:
        progress_callback(None, "Signature-based scan done")

    return all_paths
