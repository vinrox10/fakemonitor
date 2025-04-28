#!/usr/bin/env python3
import os, io, base64, subprocess, numpy as np
from PIL import Image
import gradio as gr
from mss import mss

# 1. Point GUI calls to the virtual framebuffer
os.environ["DISPLAY"] = ":99"                                  

def screen_html() -> str:
    """Capture the virtual desktop, encode as base64, and return an <img> tag."""
    with mss() as sct:                                          
        screenshot = sct.grab(sct.monitors[1])                 # grab monitor 1 :contentReference[oaicite:4]{index=4}
    img = Image.fromarray(np.array(screenshot))                
    buffer = io.BytesIO()                                      
    img.save(buffer, format="PNG")                             
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f'<img src="data:image/png;base64,{b64}" ' \
           f'style="width:100%; height:auto; border:1px solid #333;" />'

def click_center() -> str:
    """Simulate a click at the center of 1024×768 in the virtual display."""
    subprocess.run(
        ["xdotool","mousemove","512","384","click","1"], check=True
    )                                                          
    return "Clicked at screen center"

with gr.Blocks() as demo:
    gr.Markdown("## Headless Remote Desktop (Auto‐refresh every 2 s)")  
    # 2. HTML output that auto‐polls `screen_html` every 2 seconds
    screen = gr.HTML(screen_html, every=2, label="Live Virtual Desktop") :contentReference[oaicite:5]{index=5}
    btn   = gr.Button("Click Center")                            
    btn.click(click_center, None, None)                          

    demo.queue()      # enable background processing                       
    demo.launch(share=True)
