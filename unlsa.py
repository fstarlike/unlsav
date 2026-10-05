#!/usr/bin/env python3
"""Decrypt MIUI Gallery secret-album files: unlsa.py <folder> [out_folder]

MIUI uses AES-128-CTR with a key taken from the Gallery APK certificate and a fixed IV.
.lsa (photos) are fully encrypted; .lsav (videos) only in the first 1024 bytes.
The middle part of the file name is md5(key); this key matches 3e751332435bfad27569ca4efed1b602.
Needs the openssl command.
"""
import shutil
import subprocess
import sys
from pathlib import Path

KEY = "3082046c30820354a003020102020900"
IV = "11132123313341435153616667687172"
OPENSSL = ["openssl", "enc", "-d", "-aes-128-ctr", "-K", KEY, "-iv", IV]

MAGIC = [(b"\xff\xd8\xff", ".jpg"), (b"\x89PNG", ".png"), (b"GIF8", ".gif"),
         (b"ftypheic", ".heic"), (b"ftyp", ".mp4"), (b"WEBP", ".webp")]


def ext_for(head):
    for sig, ext in MAGIC:
        if sig in head[:12]:
            return ext
    return None


def decrypt(f, tmp):
    if f.suffix.lower() == ".lsa":
        subprocess.run(OPENSSL + ["-in", f, "-out", tmp], check=True)
        return
    with open(f, "rb") as src, open(tmp, "wb") as dst:
        head = subprocess.run(OPENSSL, input=src.read(1024), capture_output=True, check=True).stdout
        dst.write(head)
        shutil.copyfileobj(src, dst)


if len(sys.argv) < 2 or not Path(sys.argv[1]).is_dir():
    sys.exit(__doc__)
if not shutil.which("openssl"):
    sys.exit("openssl not found. Install it first (see README).")

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.name + "_decrypted")
out.mkdir(parents=True, exist_ok=True)
tmp = out / ".unlsa.tmp"
ok = bad = 0
for f in sorted(src.iterdir()):
    if f.suffix.lower() not in (".lsa", ".lsav"):
        continue
    decrypt(f, tmp)
    with open(tmp, "rb") as t:
        ext = ext_for(t.read(16))
    if not ext:
        print(f"SKIP (different key or unknown format): {f.name}")
        bad += 1
        continue
    tmp.replace(out / (f.name.rsplit(".", 2)[0] + ext))  # drop .<md5>.lsa(v)
    ok += 1
tmp.unlink(missing_ok=True)
print(f"{ok} converted, {bad} skipped -> {out}")
