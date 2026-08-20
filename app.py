#!/usr/bin/env python3
"""Malik the Cracker - Interactive CLI password cracking tool."""

import os
import sys
import re
import subprocess
import threading
import shutil
from pathlib import Path
from datetime import datetime

try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    clear_screen()
    print(Fore.CYAN + Style.BRIGHT)
    print("  ╔══════════════════════════════════════════╗")
    print("  ║        MALIK THE CRACKER v1.0            ║")
    print("  ║    ZIP & Hash Password Cracking Suite    ║")
    print("  ╚══════════════════════════════════════════╝")
    print(Style.RESET_ALL)


def print_header(title):
    print()
    print(Fore.YELLOW + "  ── " + title + " ──" + Style.RESET_ALL)
    print()


def get_choice(prompt, options):
    """Show a menu and get a choice."""
    print(Fore.CYAN + "  Options:" + Style.RESET_ALL)
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    print()
    while True:
        try:
            val = input(Fore.GREEN + "  └─> " + Style.RESET_ALL).strip()
            if not val:
                continue
            num = int(val)
            if 1 <= num <= len(options):
                return num
        except ValueError:
            pass
        print(Fore.RED + "  Invalid choice. Try again." + Style.RESET_ALL)


def get_input(prompt, default=None):
    """Get text input with optional default."""
    if default:
        val = input(Fore.GREEN + f"  └─> [{default}] " + Style.RESET_ALL).strip()
        return val if val else default
    else:
        val = input(Fore.GREEN + "  └─> " + Style.RESET_ALL).strip()
        return val if val else ""


def get_yes_no(prompt):
    """Get yes/no answer."""
    val = input(Fore.GREEN + f"  └─> {prompt} [y/n]: " + Style.RESET_ALL).strip().lower()
    return val.startswith("y")


def get_char_set():
    """Interactive character set selection."""
    print()
    print(Fore.YELLOW + "  Select character sets to include:" + Style.RESET_ALL)
    use_lower = get_yes_no("Lowercase letters (a-z)?")
    use_upper = get_yes_no("Uppercase letters (A-Z)?")
    use_digits = get_yes_no("Digits (0-9)?")
    use_special = get_yes_no("Special symbols (!@#$%^&*)?")
    use_custom = get_yes_no("Custom characters?")

    charset = ""
    if use_lower:
        charset += "a"
    if use_upper:
        charset += "A"
    if use_digits:
        charset += "1"
    if use_special:
        charset += "!"

    if use_custom:
        custom = get_input("Enter custom characters (e.g. @#$):")
        if custom:
            charset += custom

    if not charset:
        print(Fore.RED + "  No sets selected. Using defaults (all)." + Style.RESET_ALL)
        charset = "aA1!"

    # Build display string
    desc = []
    if use_lower:
        desc.append("a-z")
    if use_upper:
        desc.append("A-Z")
    if use_digits:
        desc.append("0-9")
    if use_special:
        desc.append("!@#$%^&*")
    if use_custom and custom:
        desc.append(f"'{custom}'")
    print(Fore.CYAN + f"  Charset: {', '.join(desc)}" + Style.RESET_ALL)

    return charset


def get_command_prefix():
    """Use WSL on Windows, direct on Linux."""
    if sys.platform == "win32":
        return ["wsl"]
    return []


def check_tool(tool_name):
    """Check if a CLI tool is available."""
    prefix = get_command_prefix()
    try:
        subprocess.run(
            [*prefix, "which", tool_name] if prefix else ["which", tool_name],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        try:
            subprocess.run(
                [*prefix, tool_name, "--help"] if (prefix or tool_name != "fcrackzip") else ["fcrackzip", "--help"],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception:
            return False


def parse_fcrackzip_password(line):
    """Extract password from fcrackzip output."""
    m = re.search(r"password\s+(?:is|found|==)\s*['\"]?([^'\"\n]+)['\"]?", line, re.I)
    if m:
        return m.group(1)
    m = re.search(r"pw\s*==\s*['\"]?([^'\"\n]+)['\"]?", line, re.I)
    if m:
        return m.group(1)
    m = re.search(r"PASSWORD\s+FOUND", line, re.I)
    if m:
        return True
    return None


def parse_john_password(line):
    """Extract password from John the Ripper output."""
    m = re.match(r"^(\S+):(\S+)", line)
    if m:
        user = m.group(1)
        pwd = m.group(2)
        if pwd and not pwd.startswith(":") and pwd != "?":
            return f"{user}:{pwd}"
    return None


def print_found_password(password, tool):
    """Display found password prominently."""
    print()
    print(Fore.GREEN + Style.BRIGHT)
    print("  ╔══════════════════════════════════════════╗")
    print("  ║         🔓  PASSWORD FOUND!  🔓          ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  Tool:  {tool:<32} ║")
    # Center the password
    pwd_display = f"  ║  Password:  {password}"
    padding = 42 - len(password) - len("  ║  Password:  ")
    pwd_display += " " * max(padding, 1) + "║"
    print(pwd_display)
    print("  ╚══════════════════════════════════════════╝")
    print(Style.RESET_ALL)


def run_fcrackzip(params):
    """Run fcrackzip with streaming output."""
    prefix = get_command_prefix()
    zip_file = params["target"]
    mode = params["mode"]
    wordlist = params.get("wordlist", "")
    min_len = params.get("min_length", 4)
    max_len = params.get("max_length", 8)
    charset = params.get("charset", "aA1!")

    cmd = [*prefix, "fcrackzip"]

    if mode == "wordlist" and wordlist:
        cmd.extend(["-D", "-p", wordlist])
    elif mode == "brute":
        cmd.extend(["-b", f"-l{min_len}-{max_len}", f"-c{charset}"])

    cmd.extend(["-v", "--use-unzip"])
    cmd.append(zip_file)

    print(Fore.CYAN + f"\n  Running: {' '.join(cmd)}\n" + Style.RESET_ALL)

    found_password = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(proc.stdout.readline, ""):
            line = line.rstrip()
            print(Fore.WHITE + f"  {line}" + Style.RESET_ALL)
            result = parse_fcrackzip_password(line)
            if result is True:
                pass
            elif result:
                found_password = result

        proc.wait()
        if proc.returncode == 0:
            print(Fore.GREEN + "\n  ✓ fcrackzip completed successfully." + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"\n  ⚠ fcrackzip finished (exit code: {proc.returncode})." + Style.RESET_ALL)
    except FileNotFoundError:
        print(Fore.RED + "\n  ✗ fcrackzip not found. Install it first." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"\n  ✗ Error: {e}" + Style.RESET_ALL)

    # Try to find password in output file too
    if not found_password:
        out_file = RESULTS_DIR / f"fcrackzip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.out"
        if out_file.exists():
            with open(out_file) as f:
                for line in f:
                    result = parse_fcrackzip_password(line)
                    if result and result is not True:
                        found_password = result
                        break

    return found_password


def run_john(params):
    """Run John the Ripper with streaming output."""
    prefix = get_command_prefix()
    hash_file = params["target"]
    mode = params["mode"]
    wordlist = params.get("wordlist", "")
    min_len = params.get("min_length", 4)
    max_len = params.get("max_length", 8)
    charset = params.get("charset", "")

    cmd = [*prefix, "john"]

    if mode == "wordlist":
        if wordlist:
            cmd.append(f"--wordlist={wordlist}")
    elif mode == "brute":
        cmd.append("--incremental")
        if charset:
            cmds = []
            if "a" in charset:
                cmds.append("LowerNum")
            if "A" in charset:
                cmds.append("UpperNum")
            if "1" in charset:
                cmds.append("All")
            if cmds:
                mode_name = cmds[-1]
                cmd.append(f"--incremental={mode_name}")
        cmd.append(f"--min-length={min_len}")
        cmd.append(f"--max-length={max_len}")

    cmd.append("--pot=/dev/null")
    cmd.append("--verbosity=6")
    cmd.append(hash_file)

    print(Fore.CYAN + f"\n  Running: {' '.join(cmd)}\n" + Style.RESET_ALL)

    found_password = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(proc.stdout.readline, ""):
            line = line.rstrip()
            print(Fore.WHITE + f"  {line}" + Style.RESET_ALL)
            result = parse_john_password(line)
            if result:
                found_password = result

        proc.wait()
        print(Fore.GREEN + f"\n  ✓ John the Ripper finished." + Style.RESET_ALL)

        # Also show cracked passwords from pot file or stdout
        if found_password:
            print_found_password(found_password, "John the Ripper")
    except FileNotFoundError:
        print(Fore.RED + "\n  ✗ John the Ripper not found. Install it first." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"\n  ✗ Error: {e}" + Style.RESET_ALL)

    return found_password


def fcrackzip_menu():
    """Interactive fcrackzip menu."""
    print_banner()
    print_header("fcrackzip - ZIP Password Cracker")

    # Step 1: Target file
    zip_file = get_input("Enter path to encrypted ZIP file:")
    if not zip_file or not Path(zip_file).exists():
        print(Fore.RED + "  ✗ File not found." + Style.RESET_ALL)
        input(Fore.YELLOW + "  Press Enter to continue..." + Style.RESET_ALL)
        return

    # Step 2: Mode
    print()
    mode_choice = get_choice("Select attack mode:", ["Wordlist (Dictionary)", "Brute Force"])
    mode = "wordlist" if mode_choice == 1 else "brute"

    params = {"target": zip_file, "mode": mode}

    if mode == "wordlist":
        wordlist = get_input("Enter path to wordlist:", "/usr/share/wordlists/rockyou.txt")
        params["wordlist"] = wordlist
    else:
        print()
        min_len = int(get_input("Minimum password length:", "4"))
        max_len = int(get_input("Maximum password length:", "8"))
        params["min_length"] = min_len
        params["max_length"] = max_len
        params["charset"] = get_char_set()

    # Confirm
    print()
    print(Fore.YELLOW + "  ── Summary ──" + Style.RESET_ALL)
    print(f"    Tool:     fcrackzip")
    print(f"    Target:   {zip_file}")
    print(f"    Mode:     {mode}")
    if mode == "wordlist":
        print(f"    Wordlist: {params['wordlist']}")
    else:
        print(f"    Length:   {min_len}-{max_len}")
        print(f"    Chars:    {params['charset']}")

    if not get_yes_no("\nStart cracking?"):
        print(Fore.YELLOW + "  Cancelled." + Style.RESET_ALL)
        input(Fore.YELLOW + "  Press Enter to continue..." + Style.RESET_ALL)
        return

    print()
    print(Fore.CYAN + Style.BRIGHT + "  🔨 Starting fcrackzip..." + Style.RESET_ALL)
    password = run_fcrackzip(params)

    if password:
        print_found_password(password, "fcrackzip")
    else:
        print()
        print(Fore.YELLOW + "  ⚠ No password found in output." + Style.RESET_ALL)
        print(Fore.YELLOW + "     Check the results folder for full logs." + Style.RESET_ALL)

    input(Fore.YELLOW + "\n  Press Enter to continue..." + Style.RESET_ALL)


def john_menu():
    """Interactive John the Ripper menu."""
    print_banner()
    print_header("John the Ripper - Password Hash Cracker")

    # Step 1: Target file
    hash_file = get_input("Enter path to hash file:")
    if not hash_file or not Path(hash_file).exists():
        print(Fore.RED + "  ✗ File not found." + Style.RESET_ALL)
        input(Fore.YELLOW + "  Press Enter to continue..." + Style.RESET_ALL)
        return

    # Step 2: Mode
    print()
    mode_choice = get_choice("Select attack mode:", ["Wordlist (Dictionary)", "Brute Force (Incremental)"])
    mode = "wordlist" if mode_choice == 1 else "brute"

    params = {"target": hash_file, "mode": mode}

    if mode == "wordlist":
        wordlist = get_input("Enter path to wordlist:", "/usr/share/wordlists/rockyou.txt")
        params["wordlist"] = wordlist
    else:
        print()
        min_len = int(get_input("Minimum password length:", "4"))
        max_len = int(get_input("Maximum password length:", "8"))
        params["min_length"] = min_len
        params["max_length"] = max_len
        params["charset"] = get_char_set()

    # Confirm
    print()
    print(Fore.YELLOW + "  ── Summary ──" + Style.RESET_ALL)
    print(f"    Tool:     John the Ripper")
    print(f"    Target:   {hash_file}")
    print(f"    Mode:     {mode}")
    if mode == "wordlist":
        print(f"    Wordlist: {params['wordlist']}")
    else:
        print(f"    Length:   {min_len}-{max_len}")
        print(f"    Chars:    {params['charset']}")

    if not get_yes_no("\nStart cracking?"):
        print(Fore.YELLOW + "  Cancelled." + Style.RESET_ALL)
        input(Fore.YELLOW + "  Press Enter to continue..." + Style.RESET_ALL)
        return

    print()
    print(Fore.CYAN + Style.BRIGHT + "  🔨 Starting John the Ripper..." + Style.RESET_ALL)
    password = run_john(params)

    if password:
        print_found_password(password, "John the Ripper")
    else:
        print()
        print(Fore.YELLOW + "  ⚠ No password found in output." + Style.RESET_ALL)

    input(Fore.YELLOW + "\n  Press Enter to continue..." + Style.RESET_ALL)


def check_dependencies():
    """Check that required tools are available."""
    print(Fore.YELLOW + "  Checking dependencies..." + Style.RESET_ALL)
    fcrackzip_ok = check_tool("fcrackzip")
    john_ok = check_tool("john")

    if fcrackzip_ok:
        print(Fore.GREEN + "    ✓ fcrackzip found" + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "    ⚠ fcrackzip not found (some features disabled)" + Style.RESET_ALL)

    if john_ok:
        print(Fore.GREEN + "    ✓ John the Ripper found" + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "    ⚠ John the Ripper not found (some features disabled)" + Style.RESET_ALL)

    return fcrackzip_ok, john_ok


def main():
    try:
        while True:
            print_banner()
            print_header("MAIN MENU")
            print(Fore.WHITE + "  Select a cracking tool:\n" + Style.RESET_ALL)

            fcrackzip_ok, john_ok = check_dependencies()
            print()

            options = ["fcrackzip - ZIP Password Cracker", "John the Ripper - Hash Password Cracker"]
            choice = get_choice("What would you like to use?", options)

            if choice == 1:
                if not fcrackzip_ok:
                    print(Fore.RED + "  ✗ fcrackzip is not installed. Install it first." + Style.RESET_ALL)
                    input(Fore.YELLOW + "  Press Enter to continue..." + Style.RESET_ALL)
                    continue
                fcrackzip_menu()
            elif choice == 2:
                if not john_ok:
                    print(Fore.RED + "  ✗ John the Ripper is not installed. Install it first." + Style.RESET_ALL)
                    input(Fore.YELLOW + "  Press Enter to continue..." + Style.RESET_ALL)
                    continue
                john_menu()

    except KeyboardInterrupt:
        print()
        print(Fore.YELLOW + "\n  Goodbye!" + Style.RESET_ALL)
        sys.exit(0)


if __name__ == "__main__":
    main()
