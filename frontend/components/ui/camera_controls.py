"""Camera control UI components"""
import gradio as gr


def build_camera_controls(start_fn, stop_fn):
    """Build camera control UI section - RTSP only"""

    with gr.Accordion("Camera Settings", open=True):
        rtsp_url = gr.Textbox(
            label="RTSP URL",
            placeholder="rtsp://username:password@ip:port/stream",
            lines=1,
        )
        with gr.Row():
            start_btn = gr.Button("Start Camera", variant="primary")
            stop_btn = gr.Button("Stop Camera", variant="stop")

    camera_status = gr.Textbox(
        label="Status", value="No camera active", interactive=False
    )

    # Event handlers
    start_btn.click(fn=start_fn, inputs=[rtsp_url], outputs=[camera_status])

    stop_btn.click(fn=stop_fn, outputs=[camera_status])

    return camera_status, rtsp_url
