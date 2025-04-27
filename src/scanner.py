import os
import pytsk3
from recovery_utils import recover_by_signature 

# Helper class to read the raw device in read-only mode
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
        current = self._fd.tell()
        self._fd.seek(0, os.SEEK_END)
        size = self._fd.tell()
        self._fd.seek(current)
        return size

def recursive_scan(fs_info, directory, progress_callback, deleted_files):
    """
    Recursively scan the given directory object.
    For each file, update the progress callback with the file name.
    If a file is marked as deleted—either by:
      - having the unallocated flag (TSK_FS_META_FLAG_UNALLOC),
      - having a FAT deletion marker (first byte == 0xE5), or
      - having a '.trashinfo' extension (used by Linux trash systems)
    —then add its name to deleted_files.
    """
    for file in directory:
        try:
            # Safely obtain the raw file name bytes.
            raw_name = b""
            if file.info and file.info.name and file.info.name.name:
                raw_name = file.info.name.name

            # Decode file name using latin1 (often works for FAT)
            try:
                decoded_name = raw_name.decode('latin1', errors='ignore')
            except Exception:
                decoded_name = "<unknown>"

            # Print current file to terminal for debugging
            print(f"Scanning file: {decoded_name}")

            # Skip system files that start with '$'
            if decoded_name.startswith("$"):
                print(f"Skipping system file: {decoded_name}")
                if progress_callback:
                    progress_callback(None, decoded_name)
                continue

            is_deleted = False

            # Check metadata flag (for NTFS/EXT4)
            try:
                if file.info.meta is not None and hasattr(file.info.meta, 'flags'):
                    flags = file.info.meta.flags
                    if flags is not None and flags == pytsk3.TSK_FS_META_FLAG_UNALLOC:
                        is_deleted = True
            except Exception as e:
                print(f"Error checking meta.flags for {decoded_name}: {e}")

            # Check FAT deletion marker: first byte equals 0xE5.
            try:
                if raw_name and raw_name[0] == 0xE5:
                    is_deleted = True
            except Exception as e:
                print(f"Error checking FAT marker for {decoded_name}: {e}")

            # Check if file has a .trashinfo extension (common in Linux trash systems)
            if decoded_name.lower().endswith(".trashinfo"):
                is_deleted = True

            if is_deleted:
                deleted_files.append(decoded_name)

            if progress_callback:
                progress_callback(None, decoded_name)

            # If the entry is a directory and not '.' or '..', recursively scan.
            try:
                if file.info.meta is not None and hasattr(file.info.meta, 'type'):
                    if file.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                        if decoded_name not in [".", ".."]:
                            try:
                                sub_directory = file.as_directory()
                                recursive_scan(fs_info, sub_directory, progress_callback, deleted_files)
                            except Exception as sub_e:
                                print(f"Error accessing subdirectory {decoded_name}: {sub_e}")
            except Exception as e:
                print(f"Error checking if {decoded_name} is a directory: {e}")

        except Exception as e:
            print(f"Unexpected error processing file: {e}")

def list_deleted_files(disk_path, progress_callback=None):
    """
    Recursively scans the selected partition for deleted files without creating a disk image.
    Updates progress by printing each file name.
    """
    deleted_files = []
    try:
        # Open the partition in read-only mode.
        img_info = RawImg(disk_path)
        # Open the file system on the partition (assuming offset 0)
        fs_info = pytsk3.FS_Info(img_info)
        
        # Open the root directory and recursively scan.
        root_directory = fs_info.open_dir("/")
        recursive_scan(fs_info, root_directory, progress_callback, deleted_files)
        
        # Final progress callback update.
        if progress_callback:
            progress_callback(1.0, "Done")
        
        img_info.close()
        return deleted_files

    except Exception as e:
        print(f"Error scanning partition {disk_path}: {e}")
        return []

def unified_scan(disk_path, progress_callback=None):
    """
    Performs a unified scan of the selected partition for deleted files.
    
    Steps:
      1. Detects the file system type.
      2. Runs a metadata-based scan via list_deleted_files().
         (Filters out trash-related entries such as those ending in ".trashinfo".)
      3. If metadata scanning finds results, returns them.
      4. Otherwise, runs a signature-based (carving) scan using recover_by_signature()
         and returns the list of recovered files.
    """
    # Detect file system type (for logging purposes)
    fs_type = "unknown"
    try:
        img_info = RawImg(disk_path)
        fs_info = pytsk3.FS_Info(img_info)
        fs_type = fs_info.info.ftype
        print(f"Detected FS type: {fs_type}")
        img_info.close()
    except Exception as e:
        print(f"Error detecting FS type: {e}")

    # Step 2: Metadata-based scan
    metadata_results = list_deleted_files(disk_path, progress_callback)
    # Filter out trash-related files (we don’t want to recover files in trash)
    metadata_results = [f for f in metadata_results if not f.lower().endswith(".trashinfo")]
    carving_results = recover_by_signature(disk_path, "./recovered_files")

    if metadata_results:
        if carving_results:
             print("Signature-based scan found deleted files.")
             return metadata_results
             return carving_results
        else:
            return metadata_results

    elif carving_results:
        print("Signature-based scan found deleted files.")
        return carving_results

    else:
        print("No files found to recover.")

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------




























