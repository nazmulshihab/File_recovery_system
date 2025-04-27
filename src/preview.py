# import os
# try:
#     from PIL import Image
#     # Try to import PhotoImage directly from PIL.ImageTk
#     from PIL.ImageTk import PhotoImage
#     preview_enabled = True
# except ImportError:
#     preview_enabled = False

# import PyPDF2

# def get_preview(file_path):
#     """
#     Returns a tuple (preview_obj, text_preview) for previewing the file:
#       - For image files (.jpg, .jpeg, .png), returns (PhotoImage, None) if preview is enabled.
#       - For PDF files, returns (None, extracted_text) from the first page.
#       - Otherwise returns (None, "Preview not available").
#     """
#     ext = os.path.splitext(file_path)[1].lower()
#     if preview_enabled and ext in [".jpg", ".jpeg", ".png"]:
#         try:
#             img = Image.open(file_path)
#             img.thumbnail((150, 150))
#             # Create a PhotoImage from the PIL Image
#             photo = PhotoImage(image=img)
#             return (photo, None)
#         except Exception as e:
#             return (None, f"Image preview error: {e}")
#     elif ext == ".pdf":
#         try:
#             with open(file_path, "rb") as f:
#                 reader = PyPDF2.PdfReader(f)
#                 text = reader.pages[0].extract_text()
#             return (None, text if text else "No text extracted")
#         except Exception as e:
#             return (None, f"PDF preview error: {e}")
#     else:
#         return (None, "Preview not available")

# if __name__ == "__main__":
#     # For testing, change the file path as needed.
#     preview = get_preview("recovered_files/recovered_1.jpg")
#     if preview_enabled and preview[0]:
#         print("Image preview is available.")
#     else:
#         print(preview[1])


import os

try:
    from PIL import Image
    from customtkinter import CTkImage
    preview_enabled = True
except ImportError:
    preview_enabled = False

try:
    import PyPDF2
    pdf_enabled = True
except ImportError:
    pdf_enabled = False

def get_preview(file_path):
    """
    Returns a tuple (preview_obj, text_preview) for previewing the file:
      - For image files (.jpg, .jpeg, .png), returns (CTkImage, None) if preview is enabled.
      - For PDF files, returns (None, extracted_text) from the first page.
      - For audio/video files, returns (None, "Media file - No preview")
      - Otherwise returns (None, "Preview not available")
    """
    ext = os.path.splitext(file_path)[1].lower()

    if preview_enabled and ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(file_path)
            img.thumbnail((150, 150))
            # Use CTkImage instead of PhotoImage
            photo = CTkImage(light_image=img, size=(150, 150))
            return (photo, None)
        except Exception as e:
            return (None, f"Image preview error: {e}")

    elif pdf_enabled and ext == ".pdf":
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = reader.pages[0].extract_text()
            return (None, text if text else "No text extracted")
        except Exception as e:
            return (None, f"PDF preview error: {e}")

    elif ext in [".mp3", ".mp4", ".mkv", ".wav"]:
        return (None, "Media file - No preview")

    else:
        return (None, "Preview not available")

if __name__ == "__main__":
    test_file = "recovered_files/recovered_1.jpg"  # Adjust path for testing

    preview = get_preview(test_file)
    if preview_enabled and preview[0]:
        print("Image preview is available.")
    else:
        print("ℹ️", preview[1])
