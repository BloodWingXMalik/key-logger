# Malik the Cracker

Interactive CLI password cracking suite for **fcrackzip** (ZIP) and **John the Ripper** (hashes).

## Prerequisites

- Python 3.8+
- `fcrackzip` for cracking ZIP passwords
- `john` (John the Ripper) for cracking password hashes
- On Windows: tools must be available via WSL

## Quick Start

```bash
make install   # installs colorama
make run       # starts the interactive app
```

## Features

- **Choose tool**: fcrackzip (ZIP files) or John the Ripper (hash files)
- **Choose mode**: Wordlist (dictionary) or Brute Force
- **Custom charset**: Select lowercase, uppercase, digits, special symbols individually
- **Password length**: Set exact min/max length for brute force
- **Live output**: See cracking progress in real time
- **Found password**: Displayed prominently when discovered

## Usage

```
╔══════════════════════════════════════════╗
║        MALIK THE CRACKER v1.0            ║
║    ZIP & Hash Password Cracking Suite    ║
╚══════════════════════════════════════════╝

  1. fcrackzip - ZIP Password Cracker
  2. John the Ripper - Hash Password Cracker
```
