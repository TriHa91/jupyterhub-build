#!/bin/bash

# Check if the user has a requirements file
if [ -f "/home/jovyan/work/.user-requirements.txt" ]; then
    echo "Installing user packages from .user-requirements.txt"
    pip install --user -r /home/jovyan/work/.user-requirements.txt
fi

# Run the original command
exec "$@"
