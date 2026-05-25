#!/bin/bash
# Install additional dependencies needed for development
# Run this inside the container: docker exec homeassistant-dev bash /usr/src/install-dev-deps.sh

echo "Installing additional Home Assistant development dependencies..."

uv pip install \
    home-assistant-frontend \
    go2rtc-client \
    pymodbus \
    pyudev \
    || echo "Some packages failed to install, continuing..."

echo "✓ Development dependencies installed!"
