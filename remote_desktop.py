#!/usr/bin/env python3
import os, time, threading, subprocess
from PIL import Image
import gradio as gr
from mss import mss

# 1️⃣ Xvfb display
os.environ["DISPLAY"] = ":99"

# 2️⃣ Screenshot thread
def save_screenshot():
    with mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save("/tmp/latest_screen.png")

def screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)

threading.Thread(target=screenshot_loop, daemon=True).start()

# 3️⃣ Click handler with logging
click_log = []

def load_screenshot_html() -> str:
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet…</p>"
    import base64
    b64 = base64.b64encode(open(path,"rb").read()).decode("utf-8")
    # Note: we’ve made coord_input visible below, but keep onclick the same.
    return f'''
    <img id="screen" src="data:image/png;base64,{b64}"
         width="1024" height="768"
         style="border:1px solid #444; image-rendering: pixelated;"
         onclick="
           const rect = this.getBoundingClientRect();
           const x = Math.floor(event.clientX - rect.left);
           const y = Math.floor(event.clientY - rect.top);
           console.log('JS click at', x, y);
           document.getElementById('coord_input').value = x+','+y;
           document.getElementById('coord_button').click();
         "
    />
    '''

def on_click_box(coord: str, log_state: list):
    # Append raw coord so we see exactly what Python got
    log_state.append(f"{time.strftime('%H:%M:%S')} → recv coord '{coord}'")
    try:
        x_str, y_str = coord.split(',')
        x, y = int(x_str), int(y_str)
        subprocess.run(["xdotool","mousemove",str(x),str(y),"click","1"],check=True)
        log_state.append(f"{time.strftime('%H:%M:%S')} → fired xdotool at ({x},{y})")
    except Exception as e:
        log_state.append(f"{time.strftime('%H:%M:%S')} → parse/error: {e}")
    return log_state[-50:]

# 4️⃣ Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## Headless Remote Desktop Viewer (DEBUG MODE)\n"
                "— click on the image; watch JS console, the visible coord box, and the Python log.")
    screen_html = gr.HTML(load_screenshot_html, every=2)
    # Make this VISIBLE so we can see if JS wrote anything
    coord_input = gr.Textbox(value="", label="DEBUG: coord_input (visible!)", lines=1, elem_id="coord_input")
    click_log_box = gr.Textbox(value="(waiting...)", label="Python Click Log", lines=8)
    coord_button = gr.Button("Hidden Trigger", visible=False, elem_id="coord_button")
    coord_button.click(on_click_box, inputs=[coord_input, gr.State(click_log)], outputs=click_log_box)
    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
