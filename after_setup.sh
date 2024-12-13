#!/bin/bash

if ! command -v bat &> /dev/null; then
  echo "Error: bat is not installed. Please install it to use this script."
  exit 1
fi

bat cache --build

echo "bat cache rebuilt successfully."

exit 0
