# Story Creator

Story Creator is a desktop application that automatically generates stories from your images using artificial intelligence. The application analyzes uploaded images and creates coherent, creative narratives in Turkish.

## Features

- **Image Analysis**: Upload up to 3 images in PNG, JPG, JPEG or BMP format
- **AI-Powered Story Generation**: Combines BLIP image captioning with Groq's LLaMA 3.3 70B model
- **Customizable Themes**: Optionally specify the story direction (adventure, romance, comedy, etc.)
- **Real-Time Streaming**: Watch the story being generated word by word
- **Modern Dark Theme UI**: Clean and user-friendly interface built with PyQt6

## Installation

### Requirements

- Python 3.8 or higher
- Stable internet connection
- Groq API key (free tier available)

### Install Dependencies

```bash
pip install PyQt6 Pillow transformers groq python-dotenv torch
```

Or use requirements.txt:

```bash
pip install -r requirements.txt
```

### Configure API Key

1. Create a free account at [Groq Console](https://console.groq.com/)
2. Generate an API key from the dashboard
3. Create a `.env` file in the project root directory
4. Add your API key:

```env
GROQ_API_KEY=your_api_key_here
```

**Important**: Add `.env` to your `.gitignore` file to keep your API key secure.

## Usage

### Starting the Application

```bash
python StoryCreator.py
```

**Note**: On first run, the BLIP model (approximately 2GB) will be downloaded automatically. This only happens once.

### Creating Stories

1. **Add Images**: Click "Add Images" and select up to 3 images
2. **Set Theme** (Optional): Enter a story theme like "adventure in the forest" or "romantic evening"
3. **Generate**: Click "Generate Story" and watch the AI create your story in real-time
4. **Clear**: Use "Clear All" to reset and start a new story

## Technical Details

### Architecture

The application uses a multi-threaded architecture to keep the UI responsive:

- **Main Thread**: Handles UI updates and user interactions
- **Worker Thread**: Processes images and generates stories

### Technologies

- **PyQt6**: GUI framework with modern widgets and threading support
- **BLIP**: Salesforce's image captioning model (blip-image-captioning-large)
- **Groq LLaMA 3.3 70B**: Large language model for story generation with streaming support
- **PIL/Pillow**: Image processing and loading
- **python-dotenv**: Secure environment variable management

### Project Structure

```
StoryCreator/
├── StoryCreator.py       # Main application
├── .env                  # API keys (create this)
├── README.md             # Documentation
├── requirements.txt      # Dependencies
└── icon.png/ico          # Application icon (optional)
```

## Limitations

- Maximum 3 images per story
- Requires active internet connection for API calls
- Free tier API has rate limits (check Groq documentation)
- Stories are generated in Turkish (configurable in code)
- First run requires ~2GB download for BLIP model

## License

This project is licensed under the MIT License. See LICENSE file for details.