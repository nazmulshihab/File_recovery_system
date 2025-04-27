import pytsk3

image_path = "./disk_images/devsdb.img"  # Modify to match the partition image
try:
    img_info = pytsk3.Img_Info(image_path)
    fs_info = pytsk3.FS_Info(img_info)
    print("Filesystem detected:", fs_info.info)
except Exception as e:
    print(f"Error accessing the filesystem: {e}")
