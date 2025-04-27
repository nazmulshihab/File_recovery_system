import logging

logging.basicConfig(filename="recovery.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def log_recovery(drive, result):
    logging.info(f"Drive: {drive} - {result}")

if __name__ == "__main__":
    log_recovery("/dev/sda", "Recovered file.jpg")

