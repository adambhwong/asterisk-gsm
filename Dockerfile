FROM python:3.15-alpine

# Install Asterisk, sample configs, chan-dongle, and libusb
RUN apk add --no-cache \
    asterisk \
    asterisk-sample-config \
    asterisk-chan-dongle \
    libusb

# Upgrade vulnerable Python packages to fix CVEs (msgpack, setuptools, urllib3)
RUN pip install --no-cache-dir --upgrade \
    "msgpack>=1.2.3" \
    "setuptools>=78.1.1" \
    "urllib3>=2.8.0"

# Copy the entrypoint script into the container and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy your local scripts directory into the container and ensure ownership
COPY scripts/ /app/scripts/
RUN chown -R asterisk:asterisk /app/scripts

# Expose default Asterisk SIP/PJSIP port if needed
EXPOSE 5060/udp

# Switch to the non-root user
USER asterisk

# Use the script as the container entrypoint/CMD
CMD ["/entrypoint.sh"]
