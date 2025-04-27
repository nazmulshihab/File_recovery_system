# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# import customtkinter as ctk
# import threading
# import subprocess
# from scanner import unified_scan  # Our new unified scanning function
# from logger import log_recovery  # (Assuming you have a simple logger)

# ctk.set_appearance_mode("dark")
# ctk.set_default_color_theme("blue")

# class RecoveryApp(ctk.CTk):
#     def __init__(self):
#         super().__init__()
#         self.title("File System Recovery Tool")
#         self.geometry("600x600")

#         # Partition selection label and dropdown.
#         self.label = ctk.CTkLabel(self, text="Select Partition:")
#         self.label.pack(pady=10)

#         self.drive_var = ctk.StringVar()
#         self.drive_dropdown = ctk.CTkComboBox(self, variable=self.drive_var, values=self.get_drives())
#         self.drive_dropdown.pack(pady=10)

#         # Single scan button that performs unified scanning.
#         self.scan_button = ctk.CTkButton(self, text="Scan for Deleted Files", command=self.start_unified_scan)
#         self.scan_button.pack(pady=10)

#         # Label and textbox for showing recovered/deleted file names.
#         self.deleted_files_label = ctk.CTkLabel(self, text="Recovered/Deleted Files:")
#         self.deleted_files_label.pack(pady=10)

#         self.deleted_files_textbox = ctk.CTkTextbox(self, height=100, width=200)
#         self.deleted_files_textbox.pack(pady=10)
        
#         # Progress bar and percentage label.
#         self.progress_bar = ctk.CTkProgressBar(self)
#         self.progress_bar.pack(pady=10)
#         self.progress_bar.set(0)
#         self.progress_bar.configure(fg_color="blue")

#         self.progress_percentage_label = ctk.CTkLabel(self, text="0%")
#         self.progress_percentage_label.pack(pady=5)

#         # Label for current file being scanned (for debugging).
#         self.current_file_label = ctk.CTkLabel(self, text="Currently scanning: None")
#         self.current_file_label.pack(pady=5)

#         self.result_label = ctk.CTkLabel(self, text="")
#         self.result_label.pack(pady=10)

#     def get_drives(self):
#         """
#         Uses lsblk to list partitions with their sizes.
#         Returns a list of strings formatted as:
#           /dev/sda1 (500M)
#         """
#         result = subprocess.run(['lsblk', '-l', '-o', 'NAME,SIZE,TYPE', '-n'], capture_output=True, text=True)
#         partitions = []
#         for line in result.stdout.splitlines():
#             parts = line.split()
#             if len(parts) >= 3 and parts[2].strip() == "part":
#                 partition_name = parts[0]
#                 partition_size = parts[1]
#                 partitions.append(f"/dev/{partition_name} ({partition_size})")
#         return partitions

#     def start_unified_scan(self):
#         """
#         Starts the unified scan in a separate thread.
#         This scan will run metadata-based recovery first and,
#         if no results are found, will perform signature-based recovery.
#         """
#         selected = self.drive_var.get()
#         if selected:
#             device = selected.split()[0]  # Extract the device path (e.g., /dev/sda1)
#             self.deleted_files_textbox.delete(1.0, ctk.END)
#             self.progress_bar.set(0)
#             self.progress_percentage_label.configure(text="0%")
#             self.progress_bar.configure(fg_color="yellow")
#             threading.Thread(target=self.unified_scan_thread, args=(device,), daemon=True).start()
#         else:
#             self.result_label.configure(text="Please select a partition.")

#     def unified_scan_thread(self, device):
#         def update_progress(progress, current_file):
#             if progress is not None:
#                 self.progress_bar.set(progress)
#                 self.progress_percentage_label.configure(text=f"{int(progress * 100)}%")
#             self.current_file_label.configure(text=f"Currently scanning: {current_file}")
#             print(f"Progress update: {current_file}")
#         # Call the unified_scan function
#         results = unified_scan(device, progress_callback=update_progress)
#         # If results is a list (from metadata or carving), display recovered file names.
#         if isinstance(results, list) and results:
#             self.deleted_files_textbox.insert(ctk.END, "\n".join(results))
#         else:
#             self.deleted_files_textbox.insert(ctk.END, "No deleted files found.")
#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")
#         # Log recovery attempt if desired.
#         log_recovery(device, results)

# if __name__ == "__main__":
#     app = RecoveryApp()
#     app.mainloop()

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# import customtkinter as ctk
# import threading
# import subprocess
# import shutil
# import os
# from tkinter import Listbox, MULTIPLE, END, Scrollbar, RIGHT, Y
# from scanner import unified_scan  # Our unified scanning function
# from logger import log_recovery   # Your logger module (if any)
# from preview import get_preview   # Preview function from preview.py

# ctk.set_appearance_mode("dark")
# ctk.set_default_color_theme("blue")

# FINAL_RECOVERY_DIR = "./final_recovered_files"

# class RecoveryApp(ctk.CTk):
#     def __init__(self):
#         super().__init__()
#         self.title("File System Recovery Tool")
#         self.geometry("700x750")

#         # --- Partition Selection ---
#         self.label = ctk.CTkLabel(self, text="Select Partition:")
#         self.label.pack(pady=10)
#         self.drive_var = ctk.StringVar()
#         self.drive_dropdown = ctk.CTkComboBox(self, variable=self.drive_var, values=self.get_drives())
#         self.drive_dropdown.pack(pady=10)

#         # --- Scan Button ---
#         self.scan_button = ctk.CTkButton(self, text="Scan for Deleted Files", command=self.start_unified_scan)
#         self.scan_button.pack(pady=10)

#         # --- Candidate Files Display ---
#         self.files_label = ctk.CTkLabel(self, text="Candidate Recovered Files:")
#         self.files_label.pack(pady=10)
#         self.file_listbox = Listbox(self, selectmode=MULTIPLE, width=80, height=10, bg="#333333", fg="white")
#         self.file_listbox.pack(pady=5)
#         self.scrollbar = Scrollbar(self)
#         self.scrollbar.pack(side=RIGHT, fill=Y)
#         self.file_listbox.config(yscrollcommand=self.scrollbar.set)
#         self.scrollbar.config(command=self.file_listbox.yview)

#         # --- Progress Bar & Status for Scanning / Recovery ---
#         self.progress_bar = ctk.CTkProgressBar(self)
#         self.progress_bar.pack(pady=10)
#         self.progress_bar.set(0)
#         self.progress_bar.configure(fg_color="blue")
#         self.progress_percentage_label = ctk.CTkLabel(self, text="0%")
#         self.progress_percentage_label.pack(pady=5)
#         self.current_status_label = ctk.CTkLabel(self, text="Current status: None")
#         self.current_status_label.pack(pady=5)

#         # --- Preview Area ---
#         self.preview_label = ctk.CTkLabel(self, text="Preview Area")
#         self.preview_label.pack(pady=5)

#         # --- Recover Button ---
#         self.recover_button = ctk.CTkButton(self, text="Recover Selected Files", command=self.recover_selected_files)
#         self.recover_button.pack(pady=10)

#         self.result_label = ctk.CTkLabel(self, text="")
#         self.result_label.pack(pady=10)

#         # Store candidate file paths (full paths) once scanning finishes.
#         self.candidate_files = []

#     def get_drives(self):
#         """Uses lsblk to list partitions with sizes."""
#         result = subprocess.run(['lsblk', '-l', '-o', 'NAME,SIZE,TYPE', '-n'],
#                                   capture_output=True, text=True)
#         partitions = []
#         for line in result.stdout.splitlines():
#             parts = line.split()
#             if len(parts) >= 3 and parts[2].strip() == "part":
#                 partition_name = parts[0]
#                 partition_size = parts[1]
#                 partitions.append(f"/dev/{partition_name} ({partition_size})")
#         return partitions

#     def start_unified_scan(self):
#         """Starts the unified scan in a separate thread."""
#         selected = self.drive_var.get()
#         if selected:
#             device = selected.split()[0]  # e.g. /dev/sda1
#             self.file_listbox.delete(0, END)
#             self.candidate_files = []  # Reset candidate list
#             # Reset scanning progress
#             self.progress_bar.set(0)
#             self.progress_percentage_label.configure(text="0%")
#             self.progress_bar.configure(fg_color="yellow")
#             threading.Thread(target=self.unified_scan_thread, args=(device,), daemon=True).start()
#         else:
#             self.result_label.configure(text="Please select a partition.")

#     def unified_scan_thread(self, device):
#         def update_progress(progress, status):
#             if progress is not None:
#                 self.progress_bar.set(progress)
#                 self.progress_percentage_label.configure(text=f"{int(progress * 100)}%")
#             self.current_status_label.configure(text=f"Current status: {status}")
#             print(f"Progress update: {status}")
#         # Call unified_scan function (which returns a list of candidate file paths)
#         results = unified_scan(device, progress_callback=update_progress)
#         if isinstance(results, list) and results:
#             self.candidate_files = results
#             for file_path in results:
#                 self.file_listbox.insert(END, file_path)
#             self.result_label.configure(text=f"Found {len(results)} candidate files.")
#         else:
#             self.file_listbox.insert(END, "No recoverable files found.")
#             self.result_label.configure(text="No recoverable files found.")
#         # End scan phase progress
#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")
#         log_recovery(device, results)

#     def recover_selected_files(self):
#         """
#         In the recovery phase:
#          - Reset the progress bar to 0 for the recovery process.
#          - For each selected candidate file, copy it to the final folder.
#          - Update the progress bar and current status with the file being recovered.
#          - Update the preview area by calling get_preview() (from preview.py) to display a thumbnail (for images)
#            or text (for PDFs) beside the progress bar.
#         """
#         from preview import get_preview  # Import here so that we can use get_preview()
#         os.makedirs(FINAL_RECOVERY_DIR, exist_ok=True)
#         selected_indices = self.file_listbox.curselection()
#         if not selected_indices:
#             self.result_label.configure(text="No files selected for recovery.")
#             return

#         total = len(selected_indices)
#         recovered = []
#         # Reset recovery progress (start at 0%)
#         self.progress_bar.set(0)
#         self.progress_percentage_label.configure(text="0%")
#         for idx, i in enumerate(selected_indices, start=1):
#             candidate = self.file_listbox.get(i)
#             source_path = candidate  # Full path to the candidate file.
#             file_name = os.path.basename(candidate)
#             self.current_status_label.configure(text=f"Recovering: {file_name}")
#             # Update preview: try to get an image preview or text preview.
#             photo, preview_text = get_preview(candidate)
#             if photo is not None:
#                 self.preview_label.configure(image=photo, text="")
#                 self.preview_label.image = photo  # Prevent garbage collection.
#             else:
#                 self.preview_label.configure(text=preview_text if preview_text else "No preview available", image="")
#             if os.path.exists(source_path):
#                 dest_path = os.path.join(FINAL_RECOVERY_DIR, file_name)
#                 try:
#                     shutil.copy(source_path, dest_path)
#                     recovered.append(dest_path)
#                     print(f"Recovered file copied: {dest_path}")
#                 except Exception as e:
#                     print(f"Error copying {source_path}: {e}")
#             else:
#                 print(f"Candidate file does not exist: {source_path}")
#             # Update recovery progress based on the number of files processed.
#             progress_val = idx / total
#             self.progress_bar.set(progress_val)
#             self.progress_percentage_label.configure(text=f"{int(progress_val * 100)}%")
#         if recovered:
#             self.result_label.configure(text=f"Recovered {len(recovered)} files.")
#         else:
#             self.result_label.configure(text="No files were recovered.")
#         self.current_status_label.configure(text="Recovery complete")
#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")

# if __name__ == "__main__":
#     app = RecoveryApp()
#     app.mainloop()

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# import customtkinter as ctk
# import threading
# import subprocess
# import shutil
# import os
# from tkinter import Listbox, MULTIPLE, END, Scrollbar, RIGHT, Y, LEFT, BOTH, Frame
# from scanner import unified_scan
# from logger import log_recovery
# from preview import get_preview

# ctk.set_appearance_mode("dark")
# ctk.set_default_color_theme("blue")

# FINAL_RECOVERY_DIR = "./final_recovered_files"

# class RecoveryApp(ctk.CTk):
#     def __init__(self):
#         super().__init__()
#         self.title("File Recovery Tool")
#         self.geometry("700x750")

#         # --- Partition Selection ---
#         self.label = ctk.CTkLabel(self, text="Select Partition:")
#         self.label.pack(pady=10)

#         self.drive_var = ctk.StringVar()
#         self.drive_dropdown = ctk.CTkComboBox(self, variable=self.drive_var, values=self.get_drives())
#         self.drive_dropdown.pack(pady=10)

#         # --- Scan Button ---
#         self.scan_button = ctk.CTkButton(self, text="Scan", command=self.start_unified_scan)
#         self.scan_button.pack(pady=10)

#         # --- Candidate Files Display with Scrollbar ---
#         self.files_label = ctk.CTkLabel(self, text="Recoverable Files:")
#         self.files_label.pack(pady=10)

#         self.listbox_frame = Frame(self)
#         self.listbox_frame.pack(pady=5, fill=BOTH, expand=False)

#         self.file_listbox = Listbox(self.listbox_frame, selectmode=MULTIPLE, width=50, height=10, bg="#333333", fg="white")
#         self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)

#         self.scrollbar = Scrollbar(self.listbox_frame, orient="vertical", command=self.file_listbox.yview)
#         self.scrollbar.pack(side=RIGHT, fill=Y)

#         self.file_listbox.config(yscrollcommand=self.scrollbar.set)

#         # --- Progress & Status ---
#         self.progress_bar = ctk.CTkProgressBar(self)
#         self.progress_bar.pack(pady=10)
#         self.progress_bar.set(0)
#         self.progress_bar.configure(fg_color="blue")

#         self.progress_percentage_label = ctk.CTkLabel(self, text="0%")
#         self.progress_percentage_label.pack(pady=5)

#         self.current_status_label = ctk.CTkLabel(self, text="Current status: None")
#         self.current_status_label.pack(pady=5)

#         # --- Preview Area ---
#         # self.preview_label = ctk.CTkLabel(self, text="Preview Area")
#         # self.preview_label.pack(pady=5)

#         # --- Recover Button ---
#         self.recover_button = ctk.CTkButton(self, text="Recover Selected Files", command=self.recover_selected_files)
#         self.recover_button.pack(pady=10)

#         self.result_label = ctk.CTkLabel(self, text="")
#         self.result_label.pack(pady=10)

#         self.candidate_files = []

#     def get_drives(self):
#         result = subprocess.run(['lsblk', '-l', '-o', 'NAME,SIZE,TYPE', '-n'],
#                                 capture_output=True, text=True)
#         partitions = []
#         for line in result.stdout.splitlines():
#             parts = line.split()
#             if len(parts) >= 3 and parts[2].strip() == "part":
#                 partition_name = parts[0]
#                 partition_size = parts[1]
#                 partitions.append(f"/dev/{partition_name} ({partition_size})")
#         return partitions

#     def start_unified_scan(self):
#         selected = self.drive_var.get()
#         if selected:
#             device = selected.split()[0]
#             self.file_listbox.delete(0, END)
#             self.candidate_files = []
#             self.progress_bar.set(0)
#             self.progress_percentage_label.configure(text="0%")
#             self.progress_bar.configure(fg_color="yellow")
#             threading.Thread(target=self.unified_scan_thread, args=(device,), daemon=True).start()
#         else:
#             self.result_label.configure(text="Please select a partition.")

#     def unified_scan_thread(self, device):
#         def update_progress(progress, status):
#             self.after(0, lambda: self.update_progress_ui(progress, status))

#         results = unified_scan(device, progress_callback=update_progress)
#         self.after(0, lambda: self.finish_scan(device, results))

#     def update_progress_ui(self, progress, status):
#         if progress is not None:
#             self.progress_bar.set(progress)
#             self.progress_percentage_label.configure(text=f"{int(progress * 100)}%")
#         self.current_status_label.configure(text=f"Current status: {status}")

#     def finish_scan(self, device, results):
#         if isinstance(results, list) and results:
#             self.candidate_files = results
#             for file_path in results:
#                 self.file_listbox.insert(END, file_path)
#             self.result_label.configure(text=f"Found {len(results)} candidate files.")
#         else:
#             self.file_listbox.insert(END, "No recoverable files found.")
#             self.result_label.configure(text="No recoverable files found.")

#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")
#         log_recovery(device, results)

#     def recover_selected_files(self):
#         os.makedirs(FINAL_RECOVERY_DIR, exist_ok=True)
#         selected_indices = self.file_listbox.curselection()
#         if not selected_indices:
#             self.result_label.configure(text="No files selected for recovery.")
#             return

#         total = len(selected_indices)
#         recovered = []

#         self.progress_bar.set(0)
#         self.progress_percentage_label.configure(text="0%")

#         for idx, i in enumerate(selected_indices, start=1):
#             candidate = self.file_listbox.get(i)
#             file_name = os.path.basename(candidate)
#             self.current_status_label.configure(text=f"Recovering: {file_name}")

#             photo, preview_text = get_preview(candidate)
#             if photo is not None:
#                 self.preview_label.configure(image=photo, text="")
#                 self.preview_label.image = photo
#             else:
#                 self.preview_label.configure(text=preview_text if preview_text else "No preview available", image="")

#             if os.path.exists(candidate):
#                 dest_path = os.path.join(FINAL_RECOVERY_DIR, file_name)
#                 try:
#                     shutil.copy(candidate, dest_path)
#                     recovered.append(dest_path)
#                     print(f"Recovered file copied: {dest_path}")
#                 except Exception as e:
#                     print(f"Error copying {candidate}: {e}")
#             else:
#                 print(f"Candidate file does not exist: {candidate}")

#             progress_val = idx / total
#             self.progress_bar.set(progress_val)
#             self.progress_percentage_label.configure(text=f"{int(progress_val * 100)}%")

#         if recovered:
#             self.result_label.configure(text=f"Recovered {len(recovered)} files.")
#         else:
#             self.result_label.configure(text="No files were recovered.")
#         self.current_status_label.configure(text="Recovery completed")
#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")

# if __name__ == "__main__":
#     app = RecoveryApp()
#     app.mainloop()

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# import customtkinter as ctk
# import threading
# import subprocess
# import shutil
# import os
# from tkinter import Listbox, MULTIPLE, END, Scrollbar, RIGHT, Y, LEFT, BOTH, Frame
# from scanner import unified_scan
# from logger import log_recovery
# from preview import get_preview

# ctk.set_appearance_mode("dark")
# ctk.set_default_color_theme("blue")

# FINAL_RECOVERY_DIR = "./final_recovered_files"

# class RecoveryApp(ctk.CTk):
#     def __init__(self):
#         super().__init__()
#         self.title("File Recovery Tool")
#         self.geometry("700x750")

#         # --- Partition Selection ---
#         self.label = ctk.CTkLabel(self, text="Select Partition:")
#         self.label.pack(pady=10)

#         self.drive_var = ctk.StringVar()
#         # Make dropdown read-only to prevent typing
#         self.drive_dropdown = ctk.CTkComboBox(self, variable=self.drive_var,
#                                               values=self.get_drives(), state="readonly")
#         self.drive_dropdown.pack(pady=10)

#         # --- Scan Button ---
#         self.scan_button = ctk.CTkButton(self, text="Scan", command=self.start_unified_scan)
#         self.scan_button.pack(pady=10)

#         # --- Candidate Files Display with Scrollbar ---
#         self.files_label = ctk.CTkLabel(self, text="Recoverable Files:")
#         self.files_label.pack(pady=10)

#         self.listbox_frame = Frame(self)
#         self.listbox_frame.pack(pady=5, fill=BOTH, expand=False)

        
#         self.file_listbox = Listbox(self.listbox_frame, selectmode=MULTIPLE,
#                                      width=50, height=5, bg="#333333", fg="white")
#         self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)

#         self.scrollbar = Scrollbar(self.listbox_frame, orient="vertical", command=self.file_listbox.yview)
#         self.scrollbar.pack(side=RIGHT, fill=Y)
#         self.file_listbox.config(yscrollcommand=self.scrollbar.set)

#         # Enable Ctrl+A to select all files
#         self.file_listbox.bind('<Control-a>', self.select_all)
#         self.file_listbox.bind('<Control-A>', self.select_all)

#         # --- Progress & Status ---
#         self.progress_bar = ctk.CTkProgressBar(self)
#         self.progress_bar.pack(pady=10)
#         self.progress_bar.set(0)
#         self.progress_bar.configure(fg_color="blue")

#         self.progress_percentage_label = ctk.CTkLabel(self, text="0%")
#         self.progress_percentage_label.pack(pady=5)

#         self.current_status_label = ctk.CTkLabel(self, text="Current status: None")
#         self.current_status_label.pack(pady=5)

#         # --- Recover Button ---
#         self.recover_button = ctk.CTkButton(self, text="Recover Selected Files",
#                                            command=self.recover_selected_files)
#         self.recover_button.pack(pady=10)

#         self.result_label = ctk.CTkLabel(self, text="")
#         self.result_label.pack(pady=10)

#         self.candidate_files = []

#     def select_all(self, event):
#         """Select all items in the listbox."""
#         self.file_listbox.select_set(0, END)
#         return 'break'  # Prevent default behavior

#     def get_drives(self):
#         result = subprocess.run(['lsblk', '-l', '-o', 'NAME,SIZE,TYPE', '-n'],
#                                 capture_output=True, text=True)
#         partitions = []
#         for line in result.stdout.splitlines():
#             parts = line.split()
#             if len(parts) >= 3 and parts[2].strip() == "part":
#                 partition_name = parts[0]
#                 partition_size = parts[1]
#                 partitions.append(f"/dev/{partition_name} ({partition_size})")
#         return partitions

#     def start_unified_scan(self):
#         selected = self.drive_var.get()
#         if selected:
#             device = selected.split()[0]
#             self.file_listbox.delete(0, END)
#             self.candidate_files = []
#             self.progress_bar.set(0)
#             self.progress_percentage_label.configure(text="0%")
#             self.progress_bar.configure(fg_color="yellow")
#             threading.Thread(target=self.unified_scan_thread, args=(device,), daemon=True).start()
#         else:
#             self.result_label.configure(text="Please select a partition.")

#     def unified_scan_thread(self, device):
#         def update_progress(progress, status):
#             self.after(0, lambda: self.update_progress_ui(progress, status))

#         results = unified_scan(device, progress_callback=update_progress)
#         self.after(0, lambda: self.finish_scan(device, results))

#     def update_progress_ui(self, progress, status):
#         if progress is not None:
#             self.progress_bar.set(progress)
#             self.progress_percentage_label.configure(text=f"{int(progress * 100)}%")
#         self.current_status_label.configure(text=f"Current status: {status}")

#     def finish_scan(self, device, results):
#         if isinstance(results, list) and results:
#             self.candidate_files = results
#             for file_path in results:
#                 self.file_listbox.insert(END, file_path)
#             self.result_label.configure(text=f"Found {len(results)} candidate files.")
#         else:
#             self.file_listbox.insert(END, "No recoverable files found.")
#             self.result_label.configure(text="No recoverable files found.")

#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")
#         log_recovery(device, results)

#     def recover_selected_files(self):
#         os.makedirs(FINAL_RECOVERY_DIR, exist_ok=True)
#         selected_indices = self.file_listbox.curselection()
#         if not selected_indices:
#             self.result_label.configure(text="No files selected for recovery.")
#             return

#         total = len(selected_indices)
#         recovered = []

#         self.progress_bar.set(0)
#         self.progress_percentage_label.configure(text="0%")

#         for idx, i in enumerate(selected_indices, start=1):
#             candidate = self.file_listbox.get(i)
#             file_name = os.path.basename(candidate)
#             self.current_status_label.configure(text=f"Recovering: {file_name}")

#             if os.path.exists(candidate):
#                 dest_path = os.path.join(FINAL_RECOVERY_DIR, file_name)
#                 try:
#                     shutil.copy(candidate, dest_path)
#                     recovered.append(dest_path)
#                     print(f"Recovered file copied: {dest_path}")
#                 except Exception as e:
#                     print(f"Error copying {candidate}: {e}")
#             else:
#                 print(f"Candidate file does not exist: {candidate}")

#             progress_val = idx / total
#             self.progress_bar.set(progress_val)
#             self.progress_percentage_label.configure(text=f"{int(progress_val * 100)}%")

#         if recovered:
#             self.result_label.configure(text=f"Recovered {len(recovered)} files.")
#         else:
#             self.result_label.configure(text="No files were recovered.")
#         self.current_status_label.configure(text="Recovery completed")
#         self.progress_bar.set(1.0)
#         self.progress_percentage_label.configure(text="100%")

#         # Clear candidate list for next scan
#         self.candidate_files = []
#         self.file_listbox.delete(0, END)

# if __name__ == "__main__":
#     app = RecoveryApp()
#     app.mainloop()

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import customtkinter as ctk
import threading, subprocess, shutil, os
from tkinter import Listbox, MULTIPLE, END, Scrollbar, RIGHT, Y, LEFT, BOTH, Frame
from scanner import unified_scan
from logger import log_recovery
from preview import get_preview

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Make sure this is defined
FINAL_RECOVERY_DIR = "./final_recovered_files"

class RecoveryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("File Recovery Tool")
        self.geometry("700x750")

        # Partition dropdown (read‑only)
        ctk.CTkLabel(self, text="Select Partition:").pack(pady=10)
        self.drive_var = ctk.StringVar()
        self.drive_dropdown = ctk.CTkComboBox(
            self, variable=self.drive_var,
            values=self.get_drives(), state="readonly"
        )
        self.drive_dropdown.pack(pady=10)

        # Scan button
        ctk.CTkButton(self, text="Scan", command=self.start_scan).pack(pady=10)

        # Candidate list
        ctk.CTkLabel(self, text="Recoverable Files:").pack(pady=10)
        frame = Frame(self); frame.pack(pady=5, fill=BOTH)
        self.file_listbox = Listbox(
            frame, selectmode=MULTIPLE,
            width=35, height=8,
            bg="#333333", fg="white"
        )
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        sb = Scrollbar(frame, orient="vertical", command=self.file_listbox.yview)
        sb.pack(side=RIGHT, fill=Y)
        self.file_listbox.config(yscrollcommand=sb.set)
        # Ctrl+A for select all
        self.file_listbox.bind("<Control-a>", lambda e: self.file_listbox.select_set(0, END))

        # Progress & status
        self.progress_bar   = ctk.CTkProgressBar(self); self.progress_bar.pack(pady=10)
        self.progress_label = ctk.CTkLabel(self, text="0%");       self.progress_label.pack(pady=5)
        self.status_label   = ctk.CTkLabel(self, text="Status: None"); self.status_label.pack(pady=5)

        # Recover button
        ctk.CTkButton(self, text="Recover Selected", command=self.recover_selected).pack(pady=10)
        self.result_label = ctk.CTkLabel(self, text=""); self.result_label.pack(pady=10)

        self.candidate_paths = []

    def get_drives(self):
        out = subprocess.run(
            ['lsblk','-l','-o','NAME,SIZE,TYPE','-n'],
            capture_output=True, text=True
        ).stdout
        parts = []
        for line in out.splitlines():
            n,s,t = line.split()
            if t=="part":
                parts.append(f"/dev/{n} ({s})")
        return parts

    def start_scan(self):
        sel = self.drive_var.get().split()[0]
        if not sel:
            self.result_label.configure(text="Select a partition first")
            return
        self.file_listbox.delete(0, END)
        self.candidate_paths = []
        self.progress_bar.set(0); self.progress_label.configure(text="0%")
        self.status_label.configure(text="Scanning...")
        threading.Thread(target=self._scan_thread, args=(sel,), daemon=True).start()

    def _scan_thread(self, device):
        def cb(pct, name):
            self.after(0, lambda: self._update_progress(pct, name))
        paths = unified_scan(device, progress_callback=cb)
        self.after(0, lambda: self._finish_scan(device, paths))

    def _update_progress(self, pct, name):
        if pct is not None:
            self.progress_bar.set(pct)
            self.progress_label.configure(text=f"{int(pct*100)}%")
        self.status_label.configure(text=f"Scanning: {name}")

    def _finish_scan(self, device, paths):
        self.candidate_paths = paths
        if paths:
            for p in paths:
                self.file_listbox.insert(END, os.path.basename(p))
            self.result_label.configure(text=f"Found {len(paths)} files")
        else:
            self.file_listbox.insert(END, "No files")
            self.result_label.configure(text="No recoverable files")

        # Final status
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")
        self.status_label.configure(text="Scan finished — select your files")
        log_recovery(device, paths)

    def recover_selected(self):
        os.makedirs(FINAL_RECOVERY_DIR, exist_ok=True)
        os.chmod(FINAL_RECOVERY_DIR, 0o777)

        idxs = self.file_listbox.curselection()
        if not idxs:
            self.result_label.configure(text="Select files first")
            return

        total = len(idxs); done = 0
        for i in idxs:
            src = self.candidate_paths[i]
            dst = os.path.join(FINAL_RECOVERY_DIR, os.path.basename(src))
            try:
                shutil.copy(src, dst)
                os.chmod(dst, 0o666)
            except Exception as e:
                print("Copy error:", e)
            done += 1
            pct = done/total
            self.progress_bar.set(pct)
            self.progress_label.configure(text=f"{int(pct*100)}%")

        self.result_label.configure(text=f"Recovered {done} files")
        # Clear list for next scan
        self.file_listbox.delete(0, END)
        self.candidate_paths.clear()
        self.status_label.configure(text="Recovery completed")
        self.progress_bar.set(1.0); self.progress_label.configure(text="100%")

if __name__=="__main__":
    RecoveryApp().mainloop()






