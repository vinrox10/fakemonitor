#!/usr/bin/env python3
import os
import time
import threading
import subprocess
from PIL import Image
import gradio as gr
from mss import mss

# ──────────────────────────────────────────────────────────────────────────────
# 1️⃣ ENVIRONMENT SETUP — EVDEV → Xvfb
# evdev provides /dev/input/event*, Xvfb implements a full X11 server in memory,
# and xdotool uses XTEST to inject pointer events back into that server.
os.environ["DISPLAY"] = ":99"  # ensure all X clients/subprocesses target the same Xvfb

# ──────────────────────────────────────────────────────────────────────────────
# 2️⃣ SCREENSHOT THREAD — mss → PIL → /tmp/latest_screen.png
# mss hooks into the X server framebuffer (even under Xvfb), returns BGRA bytes.
# Converting via Image.frombytes gives us an exact 1024×768 snapshot.
def save_screenshot():
    with mss() as sct:
        shot = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        img.save("/tmp/latest_screen.png")

def screenshot_loop():
    while True:
        save_screenshot()
        time.sleep(2)

threading.Thread(target=screenshot_loop, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# 3️⃣ CLICK HANDLER & LOGGING — XTEST injection via xdotool
# We keep an in-memory Python list of logs; each click yields two events:
# - recv coord string
# - injected xdotool event
click_log = []

def load_screenshot_canvas() -> str:
    """
    Build an HTML <canvas> (1024×768), load the latest screenshot into it,
    and set up a JS onclick handler that:
      • computes true Xvfb x,y (no scaling)
      • writes "x,y" into the hidden coord_input
      • programmatically clicks coord_button
    """
    path = "/tmp/latest_screen.png"
    if not os.path.exists(path):
        return "<p>No screenshot yet…</p>"

    import base64
    data = base64.b64encode(open(path, "rb").read()).decode("utf-8")

    return f'''
    <canvas id="screen" width="1024" height="768"
            style="border:1px solid #444; image-rendering: pixelated;"></canvas>
    <script>
    (function() {{
      const canvas = document.getElementById('screen');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, 1024, 768);
      img.src = "data:image/png;base64,{data}";
      canvas.onclick = event => {{
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor(event.clientX - rect.left);
        const y = Math.floor(event.clientY - rect.top);
        // shuttle back to Python
        document.getElementById('coord_input').value = x + ',' + y;
        document.getElementById('coord_button').click();
      }};
    }})();
    </script>
    '''

def on_click_box(coord: str, log_state: list):
    """
    coord == "x,y".
    1. Append recv record
    2. Parse ints, inject via xdotool
    3. Append fired record
    """
    timestamp = time.strftime("%H:%M:%S")
    log_state.append(f"{timestamp} → recv '{coord}'")
    try:
        x_str, y_str = coord.split(',')
        x, y = int(x_str), int(y_str)
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y), "click", "1"],
            check=True
        )
        log_state.append(f"{timestamp} → xdotool clicked at ({x},{y})")
    except Exception as e:
        log_state.append(f"{timestamp} → error parsing/injecting: {e}")
    # keep recent 50 entries
    return log_state[-50:]

# ──────────────────────────────────────────────────────────────────────────────
# 4️⃣ GRADIO UI — hidden coord_input/button shuttle, visible canvas & log
with gr.Blocks() as demo:
    gr.Markdown(
        "# Headless Xvfb Remote Desktop Viewer  \n"
        "Click anywhere on the canvas to move & click the virtual mouse.  \n"
        "Logs appear below."
    )

    # Live canvas snapshot
    screen_canvas = gr.HTML(load_screenshot_canvas, every=2, label="Live Screen")

    # Hidden shuttle for coords
    coord_input = gr.Textbox(value="", visible=False, elem_id="coord_input")

    # Visible log box
    click_log_box = gr.Textbox(
        value="(waiting for clicks…)",
        label="Click Log",
        interactive=False,
        lines=8
    )

    # Hidden trigger button
    coord_button = gr.Button(visible=False, elem_id="coord_button")
    coord_button.click(
        fn=on_click_box,
        inputs=[coord_input, gr.State(click_log)],
        outputs=click_log_box
    )

    demo.queue()
    demo.launch(server_name="0.0.0.0", share=True)
