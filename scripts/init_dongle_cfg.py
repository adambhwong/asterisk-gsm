from pathlib import Path
import re

def main():
    dongle_id = 1001
    base_dir = Path("/sys/bus/usb/devices")
    dongle_conf_sample = "/etc/asterisk/dongle.conf.sample"
    dongle_conf_file = "/etc/asterisk/dongle.conf"
    dongles = []

    
    if not base_dir.exists():
        print("Error: /sys/bus/usb/devices not found. (Are you running this on Linux?)")
        return

    # Read the sample configuration file using an absolute path
    with open(dongle_conf_sample, "r") as f:
        content = f.read()
     
    # Perform the equivalent sed operations:
    #   - Replace lines starting with 'exten=' with ';exten='
    #   - Delete everything from the line starting with '.dongle0.' to the end of the file
    content = re.sub(r"^exten=", ";exten=", content, flags=re.MULTILINE)
    content = re.sub(r"^.dongle0..*", "", content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the processed content directly to dongle.conf using an absolute path
    with open(dongle_conf_file, "w") as f:
        f.write(content)

    product_files = list(base_dir.glob("*/product"))

    for product_file in product_files:
        # Case-insensitive check for "huawei" (equivalent to grep -li huawei)
        try:
            product_text = product_file.read_text(encoding="utf-8", errors="ignore").strip()
            if "huawei" not in product_text.lower():
                continue
        except (PermissionError, OSError):
            continue

        dev_dir = product_file.parent
        
        # Read idProduct
        id_product_file = dev_dir / "idProduct"
        try:
            id_product = id_product_file.read_text(encoding="utf-8", errors="ignore").strip()
        except (PermissionError, OSError):
            continue

        # Check product IDs and extract ttyUSB paths
        this_dongle = {}
        if id_product in ("140c", "141b"):
            this_dongle["name"] = f"dongle-{dongle_id}"
            
            # Find ttyUSB* directories under dev_dir/* (equivalent to find -L $dev/* -maxdepth 1 -type d -name "ttyUSB*")
            tty_dirs = []
            for sub_path in dev_dir.iterdir():
                if sub_path.is_dir():
                    for tty_path in sub_path.glob("ttyUSB*"):
                        if tty_path.is_dir():
                            tty_dirs.append(tty_path)

            # Process paths matching the awk logic
            for tty_path in tty_dirs:
                parts = tty_path.parts
                if len(parts) >= 8:
                    field7 = parts[6]  # Equivalent to awk $7
                    field8 = parts[7]  # Equivalent to awk $8
                    
                    if id_product == "140c":
                        if field7.endswith("2"):
                            this_dongle["audio"] = f"/dev/{field8}"
                        elif field7.endswith("3"):
                            this_dongle["data"] = f"/dev/{field8}"
                    elif id_product == "141b":
                        if field7.endswith("1"):
                            this_dongle["audio"] = f"/dev/{field8}"
                        elif field7.endswith("0"):
                            this_dongle["data"] = f"/dev/{field8}"

            dongles.append(this_dongle)
            dongle_id += 1

    # Append results to dongle.conf (equivalent to >> dongle.conf)
    output_content = ""
    for d in dongles:
        if "audio" in d and "data" in d:
            output_content += f"\n[{d['name']}]\n"
            output_content += f"audio={d['audio']}\n"
            output_content += f"data={d['data']}\n"
    if output_content:    
        with open(dongle_conf_file, "a", encoding="utf-8") as f:
            f.write(output_content)
        print("Successfully updated dongle.conf")
    else:
        print("No matching Huawei dongles found.")

if __name__ == "__main__":
    main()
