import os, subprocess, numpy as np
import gradio as gr
from mss import mss

os.environ["DISPLAY"] = ":99"

def capture_screen():
    with mss() as sct:
        monitor = sct.monitors[1]
        return np.array(sct.grab(monitor))   # grab the virtual desktop

def click_center():
    subprocess.run(["xdotool", "mousemove", "512", "384", "click", "1"], check=True)
    return "Clicked at center"

with gr.Blocks() as demo:
    img = gr.Image(type="numpy", label="Virtual Desktop", height=480)  
    btn = gr.Button("Click Center")
    btn.click(click_center, None, None)
    demo.load(capture_screen, None, img, every=2)
    demo.launch(share=True)
