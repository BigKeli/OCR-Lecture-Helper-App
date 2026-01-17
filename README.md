# Assistive Classroom - AI Camera Assistant

An AI-powered camera system to help students with vision or hearing difficulties in classrooms. Point a camera at slides or boards, and AI will read, describe, or summarize the content in real-time.

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 2. Frontend Setup (New Terminal)
```bash
cd frontend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 3. Access the App
- **Frontend:** http://localhost:7860
- **Backend:** http://localhost:6969 (or your configured port)
- **Phone Camera:** Scan QR code shown in backend terminal

## Features

### Camera Sources
- **Laptop/Webcam** - Plug and play, works immediately
- **Phone Camera** - Requires HTTPS (use laptop for testing)
- **IP Camera** - RTSP streaming support

### AI Processing
- **Read Text** - Extract all text from slides/boards
- **Describe** - Get visual description of content
- **Summarize** - Bullet-point summaries

### LLM Providers
- **Local (BLIP)** - Free, CPU-based, good for basic tasks (default)
- **OpenAI GPT-4 Vision** - High quality, requires API key
- **Claude 3.5 Sonnet** - High quality, requires API key

## Configuration

### Backend (.env)
```env
# Server
FLASK_PORT=6969
FLASK_DEBUG=True

# Default LLM Provider (local, openai, claude)
DEFAULT_LLM_PROVIDER=local

# Optional: API Keys
OPENAI_API_KEY=your-key-here
CLAUDE_API_KEY=your-key-here
```

### Frontend (.env)
```env
BACKEND_URL=http://localhost:6969
```

## Usage

### Using Laptop Camera
1. Open frontend at http://localhost:7860
2. Go to "Laptop Camera" tab
3. Click "Start Laptop Camera"
4. Live video feed appears automatically
5. Click "Read Text", "Describe", or "Summarize"

### Using Phone Camera (Advanced)
**Note:** Requires HTTPS for browser camera access.

**Option 1: Use Laptop Camera** (Recommended for testing)
- Works immediately, no setup needed

**Option 2: HTTPS Setup** (For production)
- Set up SSL certificate
- Or use ngrok/cloudflare tunnel
- See DevDocs.html for details

## Project Structure

```
assistive-classroom/
├── backend/              # Flask API (Port 6969)
│   ├── app/
│   │   ├── api/         # Camera & LLM endpoints
│   │   ├── models/      # Video processor with multi-LLM support
│   │   ├── utils/       # Camera handler (OpenCV)
│   │   └── static/      # Phone camera HTML page
│   ├── config.py        # Configuration
│   ├── run.py           # Entry point
│   └── requirements.txt
│
├── frontend/            # Gradio UI (Port 7860)
│   ├── app.py          # Main interface
│   └── requirements.txt
│
└── DevDocs.html        # Technical documentation
```

## API Endpoints

### Camera
- `POST /api/camera/start/laptop` - Start laptop camera
- `POST /api/camera/start/ip` - Start IP camera (RTSP)
- `POST /api/camera/phone/frame` - Receive phone frame
- `GET /api/camera/stream` - MJPEG video stream
- `POST /api/camera/stop` - Stop camera
- `GET /api/camera/status` - Get status

### LLM
- `POST /api/llm/process` - Process frame with AI
- `GET /api/llm/providers` - List available providers
- `GET /api/llm/tasks` - List available tasks

### Utility
- `GET /health` - Health check
- `GET /phone` - Phone camera web page

## Troubleshooting

### Backend won't start
```bash
# Check port availability
lsof -ti:6969  # Mac/Linux
netstat -ano | findstr :6969  # Windows

# Kill process if needed
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

### Camera shows black screen
- Fixed in latest version! If still occurs:
- Restart backend
- Check camera permissions
- Ensure no other app is using camera

### Frontend can't connect to backend
- Ensure backend is running (check terminal)
- Verify `BACKEND_URL` in frontend/.env
- Check firewall settings

### Phone camera error: "HTTPS Required"
- **Solution:** Use laptop camera for testing
- Phone camera requires HTTPS (browser security)
- For production, set up SSL certificate

### LLM processing fails
- **Local model:** First run downloads ~1GB model
- **OpenAI/Claude:** Verify API key in backend/.env
- Check logs in backend terminal (color-coded)

## Development

### Adding New LLM Provider
See `backend/app/models/video_processor.py`

### Adding New Camera Source
See `backend/app/utils/camera_handler.py`

### Customizing UI
See `frontend/app.py`

## Performance

### Testing (Recommended)
- Laptop camera + Local BLIP model
- Instant startup, free, CPU-only
- Good for slide text recognition

### Production
- IP camera + OpenAI/Claude API
- Higher quality results
- Costs ~$0.01-0.03 per image

## Security

- Never commit `.env` files
- API keys stay in `.env` (not git)
- Use HTTPS in production
- Restrict CORS in production

## Technical Details

See **DevDocs.html** for:
- Architecture deep-dive
- Frame processing pipeline
- MJPEG streaming implementation
- Bug fixes and optimizations
- HTTPS setup guide

## License

MIT License - Educational use encouraged

## Contributing

Pull requests welcome! This project helps students with disabilities access classroom content.

## Roadmap

- [ ] Text-to-speech output
- [ ] Real-time continuous processing
- [ ] Multi-language support
- [ ] Save transcripts to file
- [ ] Mobile student app
- [ ] Multiple camera support

## Support

For issues, see DevDocs.html troubleshooting section or open a GitHub issue.

---

**Built with:** Flask, Gradio, OpenCV, Transformers, OpenAI, Anthropic
