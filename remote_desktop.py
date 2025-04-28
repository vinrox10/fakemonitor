import os, subprocess, numpy as np
import gradio as gr
from mss import mss

# point all GUI calls to our virtual display
os.environ["DISPLAY"] = ":99"

def capture_screen():
    with mss() as sct:
        monitor = sct.monitors[1]
        return np.array(sct.grab(monitor))   # grab the virtual desktop

def click_center():
    # simulate a mouse click at the center of 1024×768
    subprocess.run(["xdotool", "mousemove", "512", "384", "click", "1"], check=True)
    return "Clicked at center"

with gr.Blocks() as demo:
    # pass height directly instead of using .style()
    img = gr.Image(type="numpy", label="Virtual Desktop", height=480)  
    btn = gr.Button("Click Center")
    btn.click(click_center, None, None)
    demo.load(capture_screen, None, img, every=2)
    demo.launch(share=True)
