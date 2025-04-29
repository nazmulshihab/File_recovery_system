import os
from PIL import Image
from io import BytesIO

# Define file signatures for multiple file types.
FILE_SIGNATURES = {
    "jpg": ("jpg", b"\xff\xd8", b"\xff\xd9"),
    "jpeg": ("jpeg", b"\xff\xd8", b"\xff\xd9"),
    "png": ("png", b"\x89PNG\r\n\x1a\n", b"IEND\xaeB`\x82"),
    "pdf": ("pdf", b"%PDF", b"%%EOF"),
    "mp3": ("mp3", b"\x49\x44\x33", None),  
    "mp4": ("mp4", b"\x00\x00\x00\x18ftyp", None), 
    "mkv": ("mkv", b"\x1A\x45\xDF\xA3", None),  
}

def is_valid_image(data):
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        return True
    except Exception:
        return False

def recover_by_signature(disk_path, output_dir, chunk_size=4096):
    os.makedirs(output_dir, exist_ok=True)
    recovered_files = []
    file_index = 1

    with open(disk_path, "rb") as disk:
        buffer = b""
        while True:
            chunk = disk.read(chunk_size)
            if not chunk:
                break
            buffer += chunk

            for key, (extension, header, footer) in FILE_SIGNATURES.items():
                start = buffer.find(header)
                while start != -1:
                    if footer is not None:
                        end = buffer.find(footer, start)
                        if end != -1:
                            end += len(footer)
                            file_data = buffer[start:end]
                            buffer = buffer[end:]
                        else:
                            # Footer not found, retain partial buffer
                            buffer = buffer[start:]
                            break
                    else:
                        # No footer; carve up to MAX_SIZE or end of buffer
                        MAX_SIZE = 2 * 1024 * 1024  # 2MB (tweak if needed)
                        end = min(start + MAX_SIZE, len(buffer))
                        file_data = buffer[start:end]
                        buffer = buffer[end:]

                    filename = os.path.join(output_dir, f"carved_{file_index}.{extension}")
                    try:
                        with open(filename, "wb") as f:
                            f.write(file_data)
                        recovered_files.append(filename)
                        print(f"Recovered file: {filename}")
                    except Exception as e:
                        print(f"Error writing {filename}: {e}")
                    file_index += 1
                    start = buffer.find(header)


            # Keep the buffer small
            if len(buffer) > chunk_size * 10:
                buffer = buffer[-chunk_size * 10:]
    
    return recovered_files





