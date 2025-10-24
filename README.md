# Verdi Music2Notes App

Verdi is a visually rich, orchestral-themed music application for Windows, built with Python and PyQt5. It provides tools for converting, playing, and visualizing MIDI and WAV files, with a focus on piano music and educational features.

<img width="1453" height="943" alt="verdi1" src="https://github.com/user-attachments/assets/c4bcf1cc-450a-4bdf-9e12-02506e0e2ac1" />

<img width="1919" height="1030" alt="verdi2" src="https://github.com/user-attachments/assets/ffcac910-5803-4a7e-bdea-1f3731762d17" />

## Features

- **Beautiful Orchestral GUI**: Parchment backgrounds, gold/copper accents, and modern, readable layouts.
- **Piano Widget**: Interactive piano keyboard for note visualization.
- **MIDI & WAV Support**: Open, play, and convert MIDI and WAV files.
- **YouTube MP3 Download**: Download and convert YouTube MP3s to WAV.
- **PDF Export**: Export sheet music to PDF (requires MuseScore).
- **SoundFont Support**: Uses TiMidity++ and custom soundfonts for high-quality MIDI playback.
- **Batch MIDI Renaming**: Script included to convert MIDI filenames to ASCII for compatibility.

## Requirements

- Python 3.7+
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
- The status label above the staff image shows playback and conversion status.
- The piano widget highlights notes during playback.

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

Author: Roberto Raimondo - IS Senior Systems Engineer II

© 2025 All Rights Reserved.

---

For questions or contributions, please open an issue or pull request.


