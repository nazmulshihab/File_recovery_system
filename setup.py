from setuptools import setup
import sys
import os
import shutil

APP_NAME = "FileSystemRecovery"
VERSION = "1.0"

if sys.platform == "win32":
    # Windows Installer Setup
    import py2exe
    setup(
        name=APP_NAME,
        version=VERSION,
        description="A File System Recovery Tool",
        windows=["src/main.py"],  # Entry point
        options={"py2exe": {"includes": ["customtkinter"]}},
        zipfile=None,
    )
elif sys.platform == "linux":
    # Linux AppImage or .deb Setup
    os.system("pyinstaller --onefile --noconsole --name FileSystemRecovery src/main.py")

    # Move output file to installers folder
    if not os.path.exists("installers/"):
        os.makedirs("installers/")
    shutil.move("dist/FileSystemRecovery", "installers/FileSystemRecovery.AppImage")

