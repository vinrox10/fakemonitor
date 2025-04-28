#!/usr/bin/env python3
import os, io, base64, subprocess, time
import gradio as gr
from mss import mss
from PIL import Image

# 1. Set up environment
os.environ["DISPLAY"] = ":99"

# 2. Screenshot function that saves to file
def save_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = Image.fromarray(sct_img.rgb)
        img.save("/tmp/latest_screen.png")  # Save to tmp folder
    return

# 3. Gradio function that loads the latest screenshot
def load_screenshot_as_html():
    if not os.path.exists("/tmp/latest_screen.png"):
        return "<p>No screenshot available yet.</p>"
    
    with open("/tmp/latest_screen.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        html = f'<img src="data:image/png;base64,{img_b64}" style="width:100%; height:auto;">'
        return html

# 4. Background task to keep saving screenshots
def background_screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)  # Save every 2 seconds

# 5. Start background screenshot loop in a separate thread
import threading
threading.Thread(target=background_screenshot_loop, daemon=True).start()

# 6. Build Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# Virtual Desktop Viewer (Updated Method)")
    screen = gr.HTML(load_screenshot_as_html, every=2, label="Live Screenshot")
    demo.queue()
    demo.launch(share=True)
