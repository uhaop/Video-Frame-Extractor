# 🖼️ Video Frame Extractor with Blur Filter

A desktop GUI tool for extracting high-quality, non-blurry frames from video files, built for **photogrammetry workflows** and other computer vision or machine learning needs.

Developed with Python, OpenCV, and TTKBootstrap.

---

## ✨ Features

- 🎥 **Supports .mp4, .mov, .avi, .mkv** formats
- 🧠 **Blur Filtering** – skips blurry frames using Laplacian variance
- ⚙️ **Multi-Core Processing** – choose 4, 8, or 16 workers
- 💾 **Resume & Session Saving** – avoid reprocessing on crash
- 📈 **Real-Time Progress Tracking** – per-worker progress bars
- 💻 **CPU or GPU Ready** – UI dropdown lets you switch processing mode
- 📁 **CSV Logging (optional)** – includes detailed stats per worker

---

## 📦 Installation

You can run it in two ways:

### Option 1: Download Precompiled `.exe`

> *(Built using Nuitka to avoid dependency issues and icon bugs)*

Just download and run the `.exe` from the [Releases](https://github.com/yourusername/frame-extractor/releases) page.

---

### Option 2: Run from Source

#### 📋 Requirements

- Python 3.10+
- pip

Install dependencies:

```bash
pip install -r requirements.txt

Run the app:
python frame_extractor_gui.py


🛠️ Building the Executable with Nuitka
If you'd like to build the .exe yourself:

1. Install Nuitka
❗ Nuitka does not work with Python installed via Microsoft Store. Install standalone Python.
pip install nuitka
2. Build
Run the batch file or manually run:
nuitka --standalone --enable-plugin=tk-inter --windows-icon-from-ico=icon.ico frame_extractor_gui.py
Your .exe will be in the frame_extractor_gui.dist/ folder.

🧩 Use Cases
Photogrammetry: Extract only sharp frames from a video for 3D model generation

Machine Learning: Generate clean datasets from footage

Surveillance: Archive only usable frames from long footage

📁 Frame Extractor/
├── frame_extractor_gui.py      # Main application
├── icon.ico                    # App icon
├── build.bat / cleanup.bat     # Build utilities
├── requirements.txt            # Python dependencies
├── .gitignore                  # Clean repo
└── README.md                   # This file


🧑‍💻 Author
Developed by @uhaop & chatgpt


📄 License
MIT License
