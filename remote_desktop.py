#!/usr/bin/env python3
import os
import time
import threading
import subprocess
from PIL import Image
import gradio as gr
from mss import mss

# ──────────────────────────────────────────────────────────────────────────────
# 1️⃣ Point at the virtual display (Xvfb :99 must already be running)
os.environ["DISPLAY"] = ":99"

# ──────────────────────────────────────────────────────────────────────────────
# 2️⃣ Screenshot loop: save /tmp/latest_screen.png every 2 seconds
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

# ──────────────────────────────────────────────────────────────────────────────
# 3️⃣ Click handler & logging state

# We'll keep a running Python list of click events in memory.
click_log = []

def load_screenshot_html() -> str:
    """
    Returns an <img> tag fixed at 1024×768 with an onclick handler that:
      1. Captures the click coords (x,y)
      2. Writes "x,y" into a hidden textbox
      3. Programmatically clicks a hidden button to fire our Python handler
    """
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet…</p>"
    import base64
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f'''
    <img id="screen" src="data:image/png;base64,{b64}"
         width="1024" height="768"
         style="border:1px solid #444; image-rendering: pixelated;"
         onclick="
           const rect = this.getBoundingClientRect();
           const x = Math.floor(event.clientX - rect.left);
           const y = Math.floor(event.clientY - rect.top);
           document.getElementById('coord_input').value = x+','+y;
           document.getElementById('coord_button').click();
         "
    />
    '''

def on_click_box(coord: str, log_state: list):
    """
    coord == "x,y" from the hidden textbox.
    Moves & clicks the Xvfb mouse at those coords, and appends to log.
    Returns updated log_state for display.
    """
    try:
        x_str, y_str = coord.split(',')
        x, y = int(x_str), int(y_str)
        # Move & click
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y), "click", "1"],
            check=True
        )
        # Append a timestamped entry
        log_state.append(f"{time.strftime('%H:%M:%S')} → Click at ({x}, {y})")
    except Exception:
        log_state.append(f"{time.strftime('%H:%M:%S')} → Invalid click data: '{coord}'")
    # Keep only the last 100 entries
    return log_state[-100:]

# ──────────────────────────────────────────────────────────────────────────────
# 4️⃣ Build & launch Gradio UI

with gr.Blocks() as demo:
    gr.Markdown(
        "# Headless Remote Desktop Viewer with Click Logging\n\n"
        "Click **anywhere** on the image below to move & click the mouse, and see each click logged in real time."
    )

    # 4.1 Live-updating HTML screenshot (fixed size)
    screen_html = gr.HTML(load_screenshot_html, every=2, label="Live Screen")

    # 4.2 Hidden textbox to shuttle coordinates from JS → Python
    coord_input = gr.Textbox(value="", visible=False, elem_id="coord_input")

    # 4.3 Visible textbox to show click log
    click_log_box = gr.Textbox(
        label="Click Log",
        interactive=False,
        lines=10,
        value="(waiting for clicks...)"
    )

    # 4.4 Hidden button to trigger on_click_box()
    coord_button = gr.Button(visible=False, elem_id="coord_button")
    coord_button.click(
        fn=on_click_box,
        inputs=[coord_input, gr.State(click_log)],
        outputs=click_log_box
    )

    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
