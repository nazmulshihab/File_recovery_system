import os
import shutil
import threading
import subprocess

import customtkinter as ctk
from tkinter import Listbox, MULTIPLE, END, Scrollbar, RIGHT, Y, LEFT, BOTH, Frame

from scanner import unified_scan, TEMP_REC_DIR
from logger import log_recovery

FINAL_REC_DIR = "./final_recovered_files"

class RecoveryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("File Recovery Tool")
        self.geometry("500x600")

        ctk.CTkLabel(self, text="Select Partition:").pack(pady=10)
        self.drive_var = ctk.StringVar()
        self.drive_dropdown = ctk.CTkComboBox(
            self, variable=self.drive_var,
            values=self.get_drives(), state="readonly"
        )
        self.drive_dropdown.pack(pady=10)

        ctk.CTkButton(self, text="Scan", command=self.start_scan).pack(pady=10)

        ctk.CTkLabel(self, text="Recoverable Files:").pack(pady=10)
        frm = Frame(self); frm.pack(pady=5, fill=BOTH)
        self.file_listbox = Listbox(frm, selectmode=MULTIPLE,
            width=35, height=8, bg="#333333", fg="white")
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        sb = Scrollbar(frm, orient="vertical", command=self.file_listbox.yview)
        sb.pack(side=RIGHT, fill=Y)
        self.file_listbox.config(yscrollcommand=sb.set)
        self.file_listbox.bind("<Control-a>", lambda e: self.file_listbox.select_set(0, END))

        self.progress_bar   = ctk.CTkProgressBar(self); self.progress_bar.pack(pady=10)
        self.progress_label = ctk.CTkLabel(self, text="0%"); self.progress_label.pack(pady=5)
        self.status_label   = ctk.CTkLabel(self, text="Status: None"); self.status_label.pack(pady=5)

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

        # clear prev
        self.file_listbox.delete(0, END)
        self.candidate_paths = []
        self.progress_bar.set(0); self.progress_label.configure(text="0%")
        self.status_label.configure(text="Scanning…")

        # clear only contents of TEMP_REC_DIR
        if os.path.isdir(TEMP_REC_DIR):
            for f in os.listdir(TEMP_REC_DIR):
                os.remove(os.path.join(TEMP_REC_DIR, f))
        else:
            os.makedirs(TEMP_REC_DIR, exist_ok=True)

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

        self.progress_bar.set(1.0); self.progress_label.configure(text="100%")
        self.status_label.configure(text="Scan finished — select files")
        log_recovery(device, paths)

    def recover_selected(self):
        os.makedirs(FINAL_REC_DIR, exist_ok=True)
        os.chmod(FINAL_REC_DIR, 0o777)

        idxs = self.file_listbox.curselection()
        if not idxs:
            self.result_label.configure(text="Select files first")
            return

        total = len(idxs)
        done  = 0

        for i in idxs:
            src = self.candidate_paths[i]
            dst = os.path.join(FINAL_REC_DIR, os.path.basename(src))
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

        # clear TEMP_REC_DIR contents post-recovery
        for f in os.listdir(TEMP_REC_DIR):
            os.remove(os.path.join(TEMP_REC_DIR, f))

        self.file_listbox.delete(0, END)
        self.candidate_paths.clear()
        self.status_label.configure(text="Recovery completed")
        self.progress_bar.set(1.0); self.progress_label.configure(text="100%")

if __name__=="__main__":
    RecoveryApp().mainloop()

