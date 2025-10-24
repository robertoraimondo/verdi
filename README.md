
# Verdi Music2Notes App

Verdi is a visually rich, orchestral-themed music application for Windows, built with Python and PyQt5. It provides tools for converting, playing, and visualizing MIDI and WAV files, with a focus on piano music and educational features.

<img width="1446" height="953" alt="image" src="https://github.com/user-attachments/assets/b70434a6-f498-4fb6-a120-cd5e9c6b1b34" />
<img width="1918" height="1027" alt="image" src="https://github.com/user-attachments/assets/4c4af572-dba8-4433-b066-518f774009bc" />


## Features

- **Orchestral-themed GUI**: Modern, visually appealing interface with piano visualization and staff rendering.
- **Create Staff from MIDI**: Use the "Create Staff" button to select a MIDI file and generate a staff PDF (requires MuseScore).
- **Convert MP3/WAV to MIDI**: Convert audio files to MIDI using basic-pitch, with progress bar and status feedback.
- **Playback**: Play WAV and MIDI files with note highlights and page turning.
- **Download YouTube MP3**: Download and convert YouTube videos to MP3 directly from the app.
- **Status and Progress**: Status label and progress bar show conversion/playback status. Popup dialogs guide user actions.

## Requirements

- Python 3.11+
- PyQt5
- mido
- TiMidity++ (with soundfont and config in `TiMidity/`)
- MuseScore (for PDF export, optional)

## Installation

1. Clone or download this repository.
2. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Ensure TiMidity++ is installed and configured. Place your soundfont in `TiMidity/` and check `timidity.cfg`.
4. (Optional) Install MuseScore and set its path in the app for PDF export.

## Usage


Run the application from the project directory:

```sh
python Verdi.py
```

- Use the left panel buttons to open, convert, and play files.
- Click "Download YouTube MP3" to download and convert a YouTube video to MP3.
- Click "Create Staff" to select a MIDI file and generate a staff PDF.
- The status label above the staff image shows playback and conversion status.
- The piano widget highlights notes during playback.
- Progress bar and popup dialogs provide feedback during long operations.

## Troubleshooting

- If MIDI playback is silent, check TiMidity++ configuration and ensure filenames are ASCII-only (use `rename_midi_ascii.py`).
- For PDF export, set the correct MuseScore path in the app settings.

## Folder Structure

- `Verdi.py` — Main application
- `piano_widget.py` — Piano visualization widget
- `requirements.txt` — Python dependencies
- `TiMidity/` — TiMidity++ config and soundfonts
- `rename_midi_ascii.py` — Script to batch-rename MIDI files to ASCII
- `Midi/`, `Mp3/`, etc. — Music files

## License

This project is open source and available under the MIT License.

**Author: Roberto Raimondo - IS Senior Systems Engineer II**

© 2025 All Rights Reserved.

---

For questions or contributions, please open an issue or pull request.

