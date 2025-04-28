#!/usr/bin/env python3
import os, time, threading, subprocess
from PIL import Image
import gradio as gr
from mss import mss

# ─── 1. Point at Xvfb display (must have Xvfb :99 running) ────────────────
os.environ["DISPLAY"] = ":99"

# ─── 2. Screenshot loop: save /tmp/latest_screen.png every 2s ─────────────
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

# ─── 3. Gradio callbacks + hidden components ───────────────────────────────
def load_screenshot_html() -> str:
    """
    Returns an <img> tag (base64-encoded) with an onclick handler that:
      1. Computes click x,y within the image
      2. Writes "x,y" into the hidden textbox
      3. Programmatically clicks the hidden button
    """
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet…</p>"
    import base64
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f'''
    <img id="screen" src="data:image/png;base64,{b64}"
         style="width:100%;height:auto;border:1px solid #444;"
         onclick="
           const rect = this.getBoundingClientRect();
           const x = Math.floor(event.clientX - rect.left);
           const y = Math.floor(event.clientY - rect.top);
           document.getElementById('coord_input').value = x+','+y;
           document.getElementById('coord_button').click();
         "
    />
    '''

def on_click_box(coord: str):
    """
    coord == "x,y" from the hidden textbox.
    Move & click the Xvfb mouse at those coords.
    """
    try:
        x_str, y_str = coord.split(',')
        x, y = int(x_str), int(y_str)
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y), "click", "1"],
            check=True
        )
    except Exception:
        pass  # ignore any parsing errors

# ─── 4. Build & launch Gradio UI ───────────────────────────────────────────
with gr.Blocks() as demo:
    gr.Markdown(
        "# Headless Remote Desktop Viewer\n\n"
        "Click **anywhere** on the image below to move & click the mouse."
    )

    # Live-updating HTML component with embedded JS click handler
    screen_html = gr.HTML(load_screenshot_html, every=2, label="Live Screen")  # :contentReference[oaicite:0]{index=0}

    # Hidden textbox to receive "x,y" from JS
    coord_input = gr.Textbox(value="", visible=False, elem_id="coord_input")

    # Hidden button that JS clicks to trigger our Python callback
    coord_button = gr.Button(visible=False, elem_id="coord_button")
    coord_button.click(on_click_box, inputs=coord_input, outputs=None)

    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
