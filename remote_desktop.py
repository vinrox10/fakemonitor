#!/usr/bin/env python3
import os, io, base64, subprocess, time, threading
from PIL import Image
import gradio as gr
from mss import mss

# ──────────────────────────────────────────────────────────────────────────────
# 1. Point all GUI calls to the virtual display (:99 must already be running)
os.environ["DISPLAY"] = ":99"

# ──────────────────────────────────────────────────────────────────────────────
# 2. Capture + save a screenshot to disk every 2 seconds
def save_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        # Correctly convert raw BGRA bytes → RGB Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")  # :contentReference[oaicite:0]{index=0}
        img.save("/tmp/latest_screen.png")

def screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)

# Start background thread (daemon so it stops with the main process)
threading.Thread(target=screenshot_loop, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# 3. Gradio functions

def load_screenshot_html() -> str:
    """
    Load the last saved screenshot and return
    an <img> tag with base64-encoded PNG.
    """
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet...</p>"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'style="width:100%;height:auto;border:1px solid #444;" />'
    )

def click_center() -> str:
    """Simulate a mouse click at the center of the 1024×768 screen."""
    subprocess.run(
        ["xdotool", "mousemove", "512", "384", "click", "1"],
        check=True
    )
    return "Clicked at center"

# ──────────────────────────────────────────────────────────────────────────────
# 4. Build & launch Gradio UI

with gr.Blocks() as demo:
    gr.Markdown("# Headless Remote Desktop Viewer")
    # HTML component auto-refreshes every 2 s
    demo.HTML(load_screenshot_html, every=2, label="Live Screen")  # :contentReference[oaicite:1]{index=1}
    gr.Button("Click Center").click(click_center, outputs=None)
    demo.queue()
    demo.launch(share=True)
