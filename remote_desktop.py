#!/usr/bin/env python3
import os, time, threading, subprocess
from PIL import Image
import gradio as gr
from mss import mss

# 1️⃣ Point at virtual display
os.environ["DISPLAY"] = ":99"

# 2️⃣ Screenshot loop (unchanged)
def save_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save("/tmp/latest_screen.png")

def screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)

threading.Thread(target=screenshot_loop, daemon=True).start()

# 3️⃣ Gradio callbacks + hidden controls

def load_screenshot_html() -> str:
    """
    Return an <img> tag whose onclick JS captures click coords,
    stuffs them in a hidden textbox, and clicks a hidden button.
    """
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet…</p>"
    b64 = ""
    with open(path, "rb") as f:
        import base64
        b64 = base64.b64encode(f.read()).decode()
    return f'''
    <img id="screen" src="data:image/png;base64,{b64}"
         style="width:100%;height:auto;border:1px solid #444;"
         onclick="
           const img=this.getBoundingClientRect();
           const x=Math.floor(event.clientX - img.left);
           const y=Math.floor(event.clientY - img.top);
           document.getElementById('coord_input').value = x+','+y;
           document.getElementById('coord_button').click();
         "
    />
    '''

def on_click_box(coord: str):
    """
    coord is 'x,y' from the hidden textbox.
    Move the Xvfb mouse there and click.
    """
    try:
        x_str, y_str = coord.split(",")
        x, y = int(x_str), int(y_str)
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y), "click", "1"],
            check=True
        )
    except Exception:
        pass  # ignore parsing errors

# 4️⃣ Build & launch UI
with gr.Blocks() as demo:
    gr.Markdown(
        "# Headless Remote Desktop Viewer  \n"
        "Click **anywhere** on the image to move & click the mouse."
    )
    # The live-updating HTML+JS screenshot:
    screen_html = gr.HTML(load_screenshot_html, every=2, label="Live Screen")
    # Hidden textbox to receive "x,y" from JS:
    coord_input = gr.Textbox(value="", visible=False, elem_id="coord_input")
    # Hidden button auto-clicked by JS:
    coord_button = gr.Button(visible=False, elem_id="coord_button")
    coord_button.click(on_click_box, inputs=coord_input, outputs=None)

    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
