#!/bin/bash
echo "Building Linux Installer..."
pyinstaller --onefile --noconsole --name File_System_Recovery src/main.py
echo "Moving output to installers directory..."
mkdir -p installers
mv dist/File_System_Recovery installers/FileSystemRecovery.AppImage
echo "Linux Installer Ready!"

