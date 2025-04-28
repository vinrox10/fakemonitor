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
        # Convert raw BGRA → RGB
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save("/tmp/latest_screen.png")

def screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)

threading.Thread(target=screenshot_loop, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# 3. Gradio functions

def get_screenshot_pil():
    """Return the latest screenshot as a PIL Image (for gr.Image)."""
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        # Return a blank placeholder if no screenshot yet
        return Image.new("RGB", (1024, 768), color=(30, 30, 30))
    return Image.open(path)

def on_click(evt: gr.SelectData):
    """
    evt.index gives (x, y) clicked in the displayed image.
    We send a mousemove+click to Xvfb at those coords.
    """
    click_x, click_y = evt.index
    # Move + click
    subprocess.run(["xdotool", "mousemove", str(click_x), str(click_y), "click", "1"])
    return None  # no value to update

# ──────────────────────────────────────────────────────────────────────────────
# 4. Build & launch Gradio UI

with gr.Blocks() as demo:
    gr.Markdown("# Headless Remote Desktop Viewer")
    # Use gr.Image so we can capture clicks
    screen = gr.Image(
        value=get_screenshot_pil,
        every=2,
        label="Live Screen"
    )
    # Bind clicks on the image to our handler
    screen.select(on_click, inputs=None, outputs=None)
    demo.launch(server_name="0.0.0.0", share=True)
