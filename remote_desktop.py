#!/usr/bin/env python3
import os, io, base64, subprocess, numpy as np
from PIL import Image
import gradio as gr
from mss import mss

# 1. Tell Linux to use the virtual display
os.environ["DISPLAY"] = ":99"

# 2. Screenshot function that returns an <img> HTML tag
def capture_screen_as_html():
    with mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        img = Image.fromarray(np.array(screenshot))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        html = f'<img src="data:image/png;base64,{img_b64}" style="width:100%;height:auto;">'
        return html

# 3. Function to simulate clicking the center of the screen
def click_center():
    subprocess.run(["xdotool", "mousemove", "512", "384", "click", "1"], check=True)
    return "Clicked at center"

# 4. Build the Gradio Blocks UI
with gr.Blocks() as demo:
    gr.Markdown("# Virtual Desktop Remote View")
    
    # auto-refreshing screen
    screen = gr.HTML(capture_screen_as_html, every=2, label="Live Screen")
    
    # button to click center
    click_btn = gr.Button("Click Center")
    click_btn.click(click_center, outputs=None)

    demo.queue()
    demo.launch(share=True)
