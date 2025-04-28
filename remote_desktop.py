import os, subprocess, numpy as np
import gradio as gr
from mss import mss

# point all GUI calls to our virtual display
os.environ["DISPLAY"] = ":99"

def capture_screen():
    with mss() as sct:
        monitor = sct.monitors[1]
        return np.array(sct.grab(monitor))   # grab the virtual desktop :contentReference[oaicite:2]{index=2}

def click_center():
    # simulate a mouse click at the center of 1024×768
    subprocess.run(["xdotool", "mousemove", "512", "384", "click", "1"], check=True)
    return "Clicked at center"             # triggers xdotool in the :99 display :contentReference[oaicite:3]{index=3}

with gr.Blocks() as demo:
    img = gr.Image(type="numpy", label="Virtual Desktop").style(height=480)
    btn = gr.Button("Click Center")
    btn.click(click_center, None, None)
    # auto-refresh screenshot every 2 seconds
    demo.load(capture_screen, None, img, every=2)
    demo.launch(share=True)                # exposes a public gradio.live URL :contentReference[oaicite:4]{index=4}
