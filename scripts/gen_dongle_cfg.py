import subprocess
import time
import re
from pathlib import Path

def run_asterisk_cmd(cmd):
    """Run an asterisk -rx or -rvvvx command and return stdout."""
    try:
        result = subprocess.run(
            ["asterisk", "-rx" if "-rx" in cmd else "-rvvvx"] + cmd.split()[1:],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    except Exception:
        return ""

def get_latest_response_from_log(dongle_name):
    """Equivalent to tail/grep logic on /var/log/asterisk/messages.log"""
    log_path = Path("/var/log/asterisk/messages.log")
    if not log_path.exists():
        return ""
    
    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        # Look for lines containing the dongle name and "Got Response" from the tail
        pattern = re.compile(rf".*{dongle_name}.*Got Response")
        matching_lines = [line for line in lines if pattern.search(line)]
        
        if matching_lines:
            # Check the last 2 lines like tail -n2
            for line in matching_lines[-2:]:
                match = re.search(r"\b[0-9]{15}\b", line)
                if match:
                    return match.group(0)
    except Exception:
        pass
    return ""

def main():
    dongle_profiles = []

    # 1. Find dongle names from dongle.conf (equivalent to grep -o dongle-[0-9]* dongle.conf)
    conf_path = Path("/etc/asterisk/dongle.conf")
    dongles = []
    if conf_path.exists():
        content = conf_path.read_text(encoding="utf-8", errors="ignore")
        dongles = re.findall(r"dongle-[0-9]+", content)
        # Remove duplicates while preserving order
        dongles = list(dict.fromkeys(dongles))

    if not dongles:
        print("No dongles found in dongle.conf")
        return

    # 2. Start asterisk in background
    print("Starting Asterisk...")
    asterisk_proc = subprocess.Popen(["asterisk"])
    time.sleep(3)  # Give asterisk a moment to initialize

    try:
        for d in dongles:
            imei = ""
            imsi = ""

            # Query IMEI (AT+CGSN)
            res_cgsn = run_asterisk_cmd(f"asterisk -rvvvx 'dongle cmd {d} AT+CGSN'")
            if "AT command queued" in res_cgsn:
                time.sleep(1)
                imei = get_latest_response_from_log(d)

            # Query IMSI (AT+CIMI)
            res_cimi = run_asterisk_cmd(f"asterisk -rvvvx 'dongle cmd {d} AT+CIMI'")
            if "AT command queued" in res_cimi:
                time.sleep(1)
                imsi = get_latest_response_from_log(d)

            if imei and imsi:
                dongle_profiles.append((d, imei, imsi))
                print(f"Collected profile for {d}: IMEI={imei}, IMSI={imsi}")
            else:
                print(f"Warning: Could not fetch IMEI/IMSI for {d}")

    finally:
        # 3. Stop asterisk gracefully (equivalent to asterisk -rx "core stop now")
        print("Stopping Asterisk...")
        subprocess.run(["asterisk", "-rx", "core stop now"])
        asterisk_proc.wait()

    # 4. Process dongle.conf.sample (equivalent to sed 's#^exten=#;exten=#; /^.dongle0./,$d')
    sample_path = Path("/etc/asterisk/dongle.conf.sample")
    new_conf_lines = []
    
    if sample_path.exists():
        sample_content = sample_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in sample_content:
            # Stop if line matches /^\[dongle0/ or similar pattern
            if re.match(r"^\[dongle0", line):
                break
            # Comment out lines starting with exten=
            if line.startswith("exten="):
                line = ";" + line
            new_conf_lines.append(line)

    # 5. Append collected profiles to configuration lines
    for d, imei, imsi in dongle_profiles:
        new_conf_lines.append(f"\n[{d}]")
        new_conf_lines.append(f"imei={imei}")
        new_conf_lines.append(f"imsi={imsi}")

    # Write out to dongle.conf
    conf_path.write_text("\n".join(new_conf_lines) + "\n", encoding="utf-8")
    print("Successfully updated dongle.conf with queried dongle profiles.")

if __name__ == "__main__":
    main()
