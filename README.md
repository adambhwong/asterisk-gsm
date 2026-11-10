# Asterisk GSM Gateway Container

A containerized Asterisk setup powered by `python:3.15-alpine` and `asterisk-chan-dongle` for managing USB Huawei GSM modems. It includes Python automation scripts to detect attached USB hardware, dynamically extract IMEI/IMSI identifiers, generate `dongle.conf` configurations, and handle graceful shutdowns during container lifecycles.

---

## Features

- **Lightweight Base:** Built on top of Python 3.15 Alpine Linux for minimal image footprint.
- **Dynamic Dongle Discovery:** Python scripts handle mapping USB physical buses (`idProduct` `140c`/`141b`) directly to channel configurations.
- **SIM Identification:** Automated AT-command querying (`AT+CGSN`, `AT+CIMI`) to extract modem IMEI and IMSI parameters into `dongle.conf`.
- **Graceful Lifecycle Management:** Traps OS signals (`SIGTERM`, `SIGINT`) to invoke Asterisk's native CLI command (`core stop gracefully`) to finish active calls before stopping.
- **Automated CI/CD:** GitHub Actions pipeline for automated semantic versioning and deployment to GitHub Container Registry (GHCR).

---

## Directory Structure

```text
.
├── Dockerfile              # Alpine-based Asterisk container definition
├── entrypoint.sh           # Signal-trapping container entrypoint
├── scripts/
│   ├── detect_dongles.py   # Maps /sys/bus/usb devices to dongle slots
│   └── setup_profiles.py   # Interrogates modems for IMEI/IMSI & updates dongle.conf
└── README.md
```

## Reference
https://www.linkedin.com/pulse/self-hosting-gsm-sip-bridge-service-adam-wong-iz2ee/
