"""LLM processing UI controls"""
import gradio as gr


def build_llm_controls(api_client, process_frame_fn):
    """Build LLM processing controls"""
    gr.Markdown("### AI Processing")
    
    # Get available providers
    providers_data = api_client.get_llm_providers()
    if providers_data and "providers" in providers_data:
        providers = []
        for name, info in providers_data["providers"].items():
            if info.get("available", False):
                providers.append(f"{name} ({info.get('model', '')})")
        
        if not providers:
            providers = ["local (Salesforce/blip-image-captioning-base)"]
    else:
        providers = ["local (Salesforce/blip-image-captioning-base)"]
    
    provider_dropdown = gr.Dropdown(
        choices=providers,
        value=providers[0] if providers else None,
        label="LLM Provider",
        interactive=True
    )
    
    gr.Markdown("#### Quick Actions")
    
    with gr.Row():
        read_btn = gr.Button("📖 Read Text", size="sm")
        describe_btn = gr.Button("🔍 Describe", size="sm")
    
    summarize_btn = gr.Button("📝 Summarize", size="sm")
    
    llm_output = gr.Markdown(label="AI Response")
    
    # Event handlers
    def process_with_provider(task, provider_str):
        """Process frame with selected provider"""
        provider = provider_str.split(" (")[0] if " (" in provider_str else provider_str
        return process_frame_fn(task, provider)
    
    read_btn.click(
        fn=lambda p: process_with_provider("read", p),
        inputs=[provider_dropdown],
        outputs=[llm_output]
    )
    
    describe_btn.click(
        fn=lambda p: process_with_provider("describe", p),
        inputs=[provider_dropdown],
        outputs=[llm_output]
    )
    
    summarize_btn.click(
        fn=lambda p: process_with_provider("summarize", p),
        inputs=[provider_dropdown],
        outputs=[llm_output]
    )
    
    return llm_output
