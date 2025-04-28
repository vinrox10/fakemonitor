#!/usr/bin/env python3
import os, time, threading, subprocess
from PIL import Image
import gradio as gr
from mss import mss

# 1. Point at the virtual display (Xvfb :99 must already be running)
os.environ["DISPLAY"] = ":99"

# 2. Screenshot loop: save /tmp/latest_screen.png every 2 seconds
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

# 3. Gradio callbacks + hidden components

def load_screenshot_html() -> str:
    """
    Returns HTML with:
      1. A fixed-size <img> (1024×768) whose right-click is disabled.
      2. A transparent <div> overlaid on top to catch all click events.
      3. JS in that <div> onclick to capture coords, fill coord_input, and click coord_button.
    """
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet…</p>"
    import base64
    b64 = base64.b64encode(open(path, "rb").read()).decode("utf-8")
    return f'''
    <div style="position: relative; width: 1024px; height: 768px;">
      <!-- The actual screenshot; disable right-click on it -->
      <img id="screen" src="data:image/png;base64,{b64}"
           width="1024" height="768"
           style="border:1px solid #444; image-rendering: pixelated;"
           oncontextmenu="return false;"
      />
      <!-- Transparent overlay catches all clicks -->
      <div style="
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            cursor: crosshair;
        "
        onclick="
           const rect = this.getBoundingClientRect();
           const x = Math.floor(event.clientX - rect.left);
           const y = Math.floor(event.clientY - rect.top);
           document.getElementById('coord_input').value = x+','+y;
           document.getElementById('coord_button').click();
        "
      ></div>
    </div>
    '''

def on_click_box(coord: str, log_state: list):
    """
    coord == "x,y" from the hidden textbox.
    Move & click the Xvfb mouse at those coords, and append to log.
    """
    try:
        x_str, y_str = coord.split(',')
        x, y = int(x_str), int(y_str)
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y), "click", "1"],
            check=True
        )
        log_state.append(f"{time.strftime('%H:%M:%S')} → Click at ({x}, {y})")
    except Exception:
        log_state.append(f"{time.strftime('%H:%M:%S')} → Invalid coord: {coord}")
    return log_state[-100:]

# 4. Build & launch Gradio UI

with gr.Blocks() as demo:
    gr.Markdown(
        "# Headless Remote Desktop with Overlay Click Handler\n\n"
        "Click anywhere on the panel (even right-click) and see it logged below."
    )

    # Live-updating HTML with overlay
    screen_html = gr.HTML(load_screenshot_html, every=2, label="Live Screen")

    # Hidden textbox to shuttle "x,y" from JS → Python
    coord_input = gr.Textbox(value="", visible=False, elem_id="coord_input")

    # Visible click log
    click_log_box = gr.Textbox(
        label="Click Log",
        interactive=False,
        lines=8,
        value="(waiting for clicks...)"
    )

    # Hidden button triggered by JS
    coord_button = gr.Button(visible=False, elem_id="coord_button")
    coord_button.click(
        fn=on_click_box,
        inputs=[coord_input, gr.State([])],
        outputs=click_log_box
    )

    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
