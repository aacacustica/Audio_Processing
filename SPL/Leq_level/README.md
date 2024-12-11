# Resolving `sosfilt.so` Wrong ELF Class Error on Raspberry Pi

This guide provides step-by-step instructions to resolve the `sosfilt.so` "Wrong ELF Class: ELFCLASS64" error when working with the `pyfilterbank` library on a 32-bit Raspberry Pi system.

## Problem

When running a Python script that uses `pyfilterbank`, you might encounter the following error:


`OSError: cannot load library 'sosfilt.so': wrong ELF class: ELFCLASS64.`

## Solution

### Prerequisites

Ensure the following tools and dependencies are installed:

```bash
sudo apt update
sudo apt install build-essential python3-dev
```

Steps to Fix

    Clone the pyfilterbank Repository: Clone the library's source code:

git clone https://github.com/SiggiGue/pyfilterbank.git
cd pyfilterbank

Remove the Incompatible sosfilt.so: Delete the 64-bit version of sosfilt.so:

rm pyfilterbank/sosfilt.so

Recompile sosfilt.so for 32-bit: Use gcc to compile the sosfilt.so file for your Raspberry Pi:

gcc -shared -fPIC -o pyfilterbank/sosfilt.so pyfilterbank/sosfilt.c

Install the Corrected Library: Install the library using setup.py:

sudo python3 setup.py install

Verify the Installation: Test if pyfilterbank is working:

python3 -c "from pyfilterbank.splweighting import a_weighting_coeffs_design; print('pyfilterbank installed successfully')"

Run Your Script: Execute your script:

    python3 leq_level.py -p "/path/to/your/directory"

Notes

    Always ensure that your system matches the architecture of any compiled libraries.
    If you need to redo the process, make sure to clear any cached or precompiled versions of the library.

Troubleshooting
Missing gcc

If you encounter issues with gcc not being available, install it:

sudo apt install gcc

Permission Denied During Installation

Run the installation command with sudo:

sudo python3 setup.py install