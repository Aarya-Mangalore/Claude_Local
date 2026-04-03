# Claude Chat UI

A beautiful, custom web interface for Claude AI that runs locally in your browser.

![UI Preview](https://via.placeholder.com/800x400/1a1a2e/e94560?text=Claude+Chat+UI)

## Features

- 🤖 Multiple Claude models (Opus 4.6, Sonnet 4.6, Haiku 4.5)
- 💬 Clean, modern chat interface
- 🎨 Dark theme with beautiful gradients
- ✨ Markdown rendering with code highlighting
- 🔄 Persistent conversation history
- ⌨️ Keyboard shortcuts (Enter to send, Shift+Enter for new line)

## Quick Start

### Option 1: Double-click to run (Windows)
1. Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com/)
2. Double-click `start.bat`
3. Enter your API key when prompted
4. Open http://localhost:5000 in Chrome

### Option 2: Command line

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key:**
   ```bash
   # Windows
   set ANTHROPIC_API_KEY=your_key_here

   # Or PowerShell
   $env:ANTHROPIC_API_KEY="your_key_here"
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open in browser:**
   Navigate to http://localhost:5000

## File Structure

```
claude-ui/
├── app.py              # Flask backend
├── start.bat           # Windows launcher
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── static/
│   └── style.css      # UI styling
└── templates/
    └── index.html     # Chat interface
```

## Customization

### Change the theme
Edit `static/style.css` to modify colors:
- Primary: `#e94560` (pink/red)
- Secondary: `#0f3460` (dark blue)
- Background: `#1a1a2e` (dark)
- Surface: `#16213e` (card backgrounds)

### Change the port
Edit `app.py` line 48:
```python
app.run(host='0.0.0.0', port=5000, debug=True)  # Change 5000 to your port
```

## Security Note

Your API key is stored in memory only. Never commit it to version control!

## License

MIT - Built with ❤️ for Claude users
