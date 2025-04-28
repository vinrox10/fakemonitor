#!/usr/bin/env python3
import os, subprocess, numpy as np
import gradio as gr
from mss import mss

# 1️⃣ Point GUI calls to your headless Xvfb display
os.environ["DISPLAY"] = ":99"

# 2️⃣ Function to grab a screenshot from virtual desktop
def capture_screen():
    with mss() as sct:
        return np.array(sct.grab(sct.monitors[1]))

# 3️⃣ Function to simulate a mouse click at the screen center
def click_center():
    subprocess.run(
        ["xdotool", "mousemove", "512", "384", "click", "1"],
        check=True
    )
    return "Clicked at center"

with gr.Blocks() as demo:                                                # Initialize Blocks :contentReference[oaicite:5]{index=5}
    # 4️⃣ Invisible timer that ticks every 2 seconds
    timer = gr.Timer(2.0, active=True)                                   # gr.Timer(interval, active) :contentReference[oaicite:6]{index=6}

    # 5️⃣ Image component to show the latest screenshot
    img = gr.Image(type="numpy", label="Virtual Desktop", height=480)     # height via constructor :contentReference[oaicite:7]{index=7}

    # 6️⃣ Wire timer ticks to capture_screen → update `img`
    timer.tick(fn=capture_screen, inputs=None, outputs=img)               # On each tick, grab and render :contentReference[oaicite:8]{index=8}

    # 7️⃣ Optional control: a button to click the center
    btn = gr.Button("Click Center")
    btn.click(fn=click_center, inputs=None, outputs=None)                # Normal click event :contentReference[oaicite:9]{index=9}

    demo.queue()                                                         # Enable background event processing :contentReference[oaicite:10]{index=10}
    demo.launch(share=True)                                              # Public link via gradio.live :contentReference[oaicite:11]{index=11}
