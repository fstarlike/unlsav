"""Self-check: encrypt fake files the way MIUI does, run unlsa.py, compare. Run: python3 test_unlsa.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
ENC = ["openssl", "enc", "-aes-128-ctr", "-K", "3082046c30820354a003020102020900",
       "-iv", "11132123313341435153616667687172"]
SUFFIX = ".3e751332435bfad27569ca4efed1b602"

photo = b"\xff\xd8\xff\xe0" + os.urandom(5000)
video = b"\x00\x00\x00\x20ftypisom" + os.urandom(5000)

with tempfile.TemporaryDirectory() as tmp:
    src, out = Path(tmp, "in"), Path(tmp, "out")
    src.mkdir()
    enc = lambda data: subprocess.run(ENC, input=data, capture_output=True, check=True).stdout
    (src / f"IMG_1{SUFFIX}.lsa").write_bytes(enc(photo))              # photos: whole file
    (src / f"VID_1{SUFFIX}.lsav").write_bytes(enc(video[:1024]) + video[1024:])  # videos: header only
    subprocess.run([sys.executable, HERE / "unlsa.py", src, out], check=True)
    assert (out / "IMG_1.jpg").read_bytes() == photo
    assert (out / "VID_1.mp4").read_bytes() == video
print("ok")
