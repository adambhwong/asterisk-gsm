from pathlib import Path

def main():
    dongle_id = 1001
    base_dir = Path("/sys/bus/usb/devices")
    
    if not base_dir.exists():
        print("Error: /sys/bus/usb/devices not found. (Are you running this on Linux?)")
        return

    conf_lines = []

    # Find all 'product' files up to depth 2 (equivalent to find -L ... -maxdepth 2 -name product)
    product_files = list(base_dir.glob("*/product")) + list(base_dir.glob("*/*/product"))

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
        if id_product in ("140c", "141b"):
            conf_lines.append(f"\n[dongle-{dongle_id}]")
            
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
                            conf_lines.append(f"audio=/dev/{field8}")
                        elif field7.endswith("3"):
                            conf_lines.append(f"data=/dev/{field8}")
                    elif id_product == "141b":
                        if field7.endswith("1"):
                            conf_lines.append(f"audio=/dev/{field8}")
                        elif field7.endswith("0"):
                            conf_lines.append(f"data=/dev/{field8}")

            dongle_id += 1

    # Append results to dongle.conf (equivalent to >> dongle.conf)
    if conf_lines:
        output_content = "\n".join(conf_lines).strip() + "\n"
        with open("dongle.conf", "a", encoding="utf-8") as f:
            f.write(output_content)
        print("Successfully updated dongle.conf")
    else:
        print("No matching Huawei dongles found.")

if __name__ == "__main__":
    main()
