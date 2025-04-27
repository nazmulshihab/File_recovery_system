import os
import parted

def recover_partition(disk_path):
    device = parted.Device(disk_path)
    disk = parted.Disk(device)
    
    try:
        partition = disk.getFreeSpaceRegions()[0]  # Get unallocated space
        new_partition = parted.Partition(disk, type=parted.PARTITION_NORMAL, geometry=partition)
        disk.addPartition(new_partition, constraint=device.optimalAlignedConstraint)
        disk.commit()
        return f"Partition recovered successfully on {disk_path}"
    except Exception as e:
        return f"Partition recovery failed: {str(e)}"

if __name__ == "__main__":
    print(recover_partition("/dev/sda"))

