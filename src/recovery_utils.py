import os
from io import BytesIO
from PIL import Image
import PyPDF2

# Extended signature list
FILE_SIGNATURES = {
    "jpg":  ("jpg",  b"\xFF\xD8\xFF",            b"\xFF\xD9"),
    "jpeg": ("jpeg", b"\xFF\xD8\xFF",            b"\xFF\xD9"),
    "png":  ("png",  b"\x89PNG\r\n\x1a\n",       b"IEND\xaeB`\x82"),
    "pdf":  ("pdf",  b"%PDF",                    b"%%EOF"),
    "mp3":  ("mp3",  b"ID3",                     None),
    "mp4":  ("mp4",  b"\x00\x00\x00\x18ftyp",    None),
    "mkv":  ("mkv",  b"\x1A\x45\xDF\xA3",        None),
    "xlsx": ("xlsx", b"PK\x03\x04",              None),
    # "txt":  ("txt",  b"\n",                      None),
}

def is_valid_image(data: bytes) -> bool:
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        return True
    except:
        return False

def is_valid_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF") and b"%%EOF" in data

def recover_by_signature(
    disk_path: str,
    output_dir: str,
    chunk_size: int = 4096,
    progress_callback = None
) -> list[str]:
    """
    Carve files by signature, validate only real images/PDFs, write as carved_i.ext,
    and report each “Scanning for file: carved_i.ext” and “Recovered file: carved_i.ext”.
    """
    os.makedirs(output_dir, exist_ok=True)
    recovered = []
    file_index = 1

    # Safely get size for progress
    try:
        total_size = os.path.getsize(disk_path)
    except OSError:
        total_size = 0

    with open(disk_path, "rb") as disk:
        buffer = b""
        read_so_far = 0

        while True:
            chunk = disk.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            read_so_far += len(chunk)

            # Carving per signature
            for key, (extension, header, footer) in FILE_SIGNATURES.items():
                start = buffer.find(header)
                while start != -1:
                    # Filename to carve
                    fname = f"carved_{file_index}.{extension}"
                    msg = f"Scanning currently: {fname}"
                    print(msg)
                    if progress_callback:
                        progress_callback(None, msg)

                    # Determine carve end
                    if footer:
                        end = buffer.find(footer, start)
                        if end != -1:
                            end += len(footer)
                            data = buffer[start:end]
                            buffer = buffer[end:]
                        else:
                            buffer = buffer[start:]
                            break
                    else:
                        MAX = 5 * 1024 * 1024
                        end = min(start + MAX, len(buffer))
                        data = buffer[start:end]
                        buffer = buffer[end:]

                    # Validate before writing
                    valid = True
                    if extension in ("jpg", "jpeg", "png"):
                        valid = is_valid_image(data)
                    elif extension == "pdf":
                        valid = is_valid_pdf(data)
                    # else: assume audio/video/txt/xlsx is OK

                    if valid:
                        out = os.path.join(output_dir, fname)
                        try:
                            with open(out, "wb") as w:
                                w.write(data)
                            recovered.append(out)
                            done_msg = f"Recovered file: {fname}"
                            print(done_msg)
                            if progress_callback:
                                progress_callback(None, done_msg)
                        except Exception as e:
                            print(f"Error writing {out}: {e}")
                        file_index += 1

                    start = buffer.find(header)

            # Trim buffer to avoid runaway memory
            if len(buffer) > chunk_size * 10:
                buffer = buffer[-chunk_size * 10:]

            # Optionally report carve-phase progress
            if total_size and progress_callback:
                pct = read_so_far / total_size
                progress_callback(pct, f"Carving disk: {int(pct*100)}%")

    return recovered
