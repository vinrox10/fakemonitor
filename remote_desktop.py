#!/usr/bin/env python3
import os
import time
import threading
import subprocess
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
        # Convert raw BGRA → RGB
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save("/tmp/latest_screen.png")

def screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)

# Start in background
threading.Thread(target=screenshot_loop, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# 3. Gradio functions

def get_screenshot_pil():
    """Return the latest screenshot as a PIL Image, or a placeholder if missing."""
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        # blank dark placeholder
        return Image.new("RGB", (1024, 768), color=(30, 30, 30))
    return Image.open(path)

def on_click(evt: gr.SelectData):
    """
    Handle clicks on the Gradio Image.
    evt.index == (x, y) in pixels within the image.
    """
    x, y = evt.index
    # Move virtual mouse & click
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=True)
    # No return value needed

# ──────────────────────────────────────────────────────────────────────────────
# 4. Build & launch Gradio UI

with gr.Blocks() as demo:
    gr.Markdown("# Headless Remote Desktop Viewer\n\nClick anywhere on the image to move & click the mouse.")
    screen = gr.Image(
        value=get_screenshot_pil,
        every=2,            # refresh every 2 seconds
        label="Live Screen"
    )
    screen.select(on_click, inputs=None, outputs=None)
    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
