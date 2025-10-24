import time
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import mido
import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QWidget, QInputDialog, QProgressBar, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont
from piano_widget import PianoWidget

class MidiPlaybackThread(QThread):
    update_notes = pyqtSignal(list)
    advance_page = pyqtSignal()
    finished = pyqtSignal()
    def __init__(self, midi_path, page_times=None, parent=None):
        super().__init__(parent)
        self.midi_path = midi_path
        self.page_times = page_times or []  # List of (time, page_idx)
        self._stop = False

    def run(self):
        try:
            mid = mido.MidiFile(self.midi_path)
        except Exception:
            self.finished.emit()
            return
        current_notes = set()
        next_page_idx = 0
        abs_time = 0
        start_time = time.time()

        # Gather all events with their absolute times
        events = []
        for msg in mid:
            abs_time += msg.time
            events.append((abs_time, msg.copy()))

        # Skip initial silence: shift all event times so first note-on is at 0
        shift = 0
        for t, msg in events:
            if msg.type == 'note_on' and msg.velocity > 0:
                shift = t
                break
        if events:
            events = [(t - shift, msg) for (t, msg) in events]
        abs_time = 0
        i = 0
        start_time = time.time()
        while i < len(events):
            if self._stop:
                break
            event_time, msg = events[i]
            now = time.time() - start_time
            wait_time = event_time - now
            if wait_time > 0:
                time.sleep(wait_time)

            # Auto-advance page if needed
            while (next_page_idx < len(self.page_times) and event_time >= self.page_times[next_page_idx][0]):
                self.advance_page.emit()
                next_page_idx += 1
            if msg.type == 'note_on' and msg.velocity > 0:
                current_notes.add(msg.note)
            elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                current_notes.discard(msg.note)

            # Emit after all note changes at this time (handle chords)
            # Look ahead for more events at the same time
            j = i + 1
            while j < len(events) and abs(events[j][0] - event_time) < 1e-6:
                next_msg = events[j][1]
                if next_msg.type == 'note_on' and next_msg.velocity > 0:
                    current_notes.add(next_msg.note)
                elif (next_msg.type == 'note_off') or (next_msg.type == 'note_on' and next_msg.velocity == 0):
                    current_notes.discard(next_msg.note)
                j += 1
            self.update_notes.emit(list(current_notes))
            i = j
        self.update_notes.emit([])
        self.finished.emit()

    def stop(self):
        self._stop = True


class Verdi(QMainWindow):
    def set_piano_theme(self, theme='dark'):
        """Change the theme of the piano widget. Supports 'dark', 'light', and 'modern'."""
        if hasattr(self, 'piano_widget'):
            if theme == 'modern' or theme == 'dark':
                # Modern dark theme with key color distinction
                self.piano_widget.setStyleSheet('''
                    background: #181c20;
                    border: 2px solid #444;
                    border-radius: 8px;
                ''')
            elif theme == 'light':
                self.piano_widget.setStyleSheet('''
                    background: #f5f5f5;
                    border: 2px solid #bbb;
                    border-radius: 8px;
                ''')
            # You can expand this with more themes/colors as needed
        else:
            print('Piano widget not found.')
    update_notes = pyqtSignal(list)
    advance_page = pyqtSignal()
    finished = pyqtSignal()
    def __init__(self, midi_path=None, page_times=None, parent=None):
        super().__init__(parent)
        self.musescore_path = None
        from PyQt5.QtGui import QIcon
        self.setWindowIcon(QIcon(r"D:\MyProject\Verdi\logo.ico"))
        self.setWindowTitle("Verdi")
        self.midi_path = midi_path
        self.page_times = page_times or []  # List of (time, page_idx)
        self._stop = False

        # Central widget and main layout
        central = QWidget()
        main_layout = QVBoxLayout()
        main_h_layout = QHBoxLayout()

        # --- Left panel with all controls ---
        left_panel = QVBoxLayout()
        self.download_yt_btn = QPushButton("Download YouTube MP3")
        self.open_btn = QPushButton("Convert MP3 to WAV")
        self.play_wav_btn = QPushButton("Play WAV")
        self.stop_wav_btn = QPushButton("Stop")
        self.convert_midi_btn = QPushButton("Convert to MIDI")
        self.import_midi_btn = QPushButton("Import MIDI")
        self.midi_progress = QProgressBar()
        self.midi_progress.setMinimum(0)
        self.midi_progress.setMaximum(0)
        self.midi_progress.setVisible(False)
        self.midi_progress.setFixedWidth(180)

        left_panel.addStretch(1)
        button_width = 200
        button_height = 48
        for btn in [self.download_yt_btn, self.open_btn, self.play_wav_btn, self.stop_wav_btn, self.convert_midi_btn, self.import_midi_btn]:
            btn.setMinimumWidth(button_width)
            btn.setMaximumWidth(button_width)
            btn.setMinimumHeight(button_height)
            btn.setMaximumHeight(button_height)
            btn.setStyleSheet("""
QPushButton {
    white-space: normal;
    font-size: 14px;
    font-family: 'Georgia', serif;
    font-weight: bold;
    color: #7c4a03;
    background: #f7e7c1;
    border: 1.5px solid #bfa76f;
    border-radius: 9px;
    margin: 3px 0;
    padding: 6px 10px;
}
QPushButton:hover {
    background: #ffe9b3;
    border: 2px solid #d4a13a;
    color: #a05a00;
}
            """)
        left_panel.addWidget(self.download_yt_btn)
        left_panel.addWidget(self.open_btn)
        left_panel.addWidget(self.play_wav_btn)
        left_panel.addWidget(self.stop_wav_btn)
        left_panel.addWidget(self.convert_midi_btn)
        left_panel.addWidget(self.import_midi_btn)
        left_panel.addWidget(self.midi_progress)
        left_panel.addStretch(1)

        self.download_yt_btn.clicked.connect(self.download_youtube_mp3)
        self.open_btn.clicked.connect(self.open_file_dialog)
        self.play_wav_btn.clicked.connect(self.play_wav_file)
        self.stop_wav_btn.clicked.connect(self.stop_wav_file)
        self.convert_midi_btn.clicked.connect(self.convert_to_midi)
        self.import_midi_btn.clicked.connect(self.import_midi_file)

        # --- Status and file labels (now above song title, centered in right panel) ---
        self.status_label = QLabel("<span style='color:green'>Ready.</span>")
        self.status_label.setStyleSheet("font-size: 13px; color: #222; background: #f9f6e7; border: 1px solid #bfa14a; border-radius: 8px; padding: 4px 12px; margin-bottom: 4px;")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_label.setMinimumHeight(32)
        self.status_label.setMaximumHeight(48)
        self.status_label.setToolTip('Status messages will appear here.')

        right_panel = QVBoxLayout()
        status_label_container = QHBoxLayout()
        status_label_container.addStretch(1)
        status_label_container.addWidget(self.status_label)
        status_label_container.addStretch(1)
        right_panel.addLayout(status_label_container)

        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 12px 0 8px 0;")
        right_panel.addWidget(self.title_label)

        self.staff_img_label = QLabel()
        self.staff_img_label.setAlignment(Qt.AlignCenter)
        self.staff_img_label.setStyleSheet("background: #fafafa; border: 1px solid #ddd;")
        self.staff_img_label.setText("<i>Staff image will appear here.</i>")
        right_panel.addWidget(self.staff_img_label, stretch=1)

        self.piano_widget = PianoWidget()
        right_panel.addWidget(self.piano_widget)
        self.set_piano_theme('modern')

        controls_layout = QHBoxLayout()
        controls_layout.addStretch(1)
        self.prev_btn = QPushButton("Prev Page")
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.next_btn = QPushButton("Next Page")
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addStretch(1)
        right_panel.addLayout(controls_layout)

        self.play_btn.clicked.connect(self.play_midi)
        self.stop_btn.clicked.connect(self.stop_midi)
        self.prev_btn.clicked.connect(self.show_prev_page)
        self.next_btn.clicked.connect(self.show_next_page)

        left_container = QWidget()
        left_container.setLayout(left_panel)
        try:
            left_container.setFixedWidth(button_width + 32)
        except NameError:
            left_container.setFixedWidth(232)
        left_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_h_layout.addWidget(left_container)
        main_h_layout.addLayout(right_panel)
        main_layout.addLayout(main_h_layout)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.setStyleSheet('''
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f5e6, stop:1 #e7dfc6);
            }
            QWidget#centralWidget {
                background: #f8f5e6;
                border: 2.5px solid #bfa14a;
                border-radius: 18px;
                box-shadow: 0 6px 24px 0 rgba(80,60,20,0.10);
            }
            QLabel {
                color: #4b2e19;
                font-family: 'Georgia', 'Times New Roman', serif;
                font-size: 18px;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffe9a0, stop:1 #bfa14a);
                color: #4b2e19;
                border: 2px solid #bfa14a;
                border-radius: 10px;
                font-weight: bold;
                font-family: 'Georgia', 'Times New Roman', serif;
                font-size: 10px;
                padding: 8px 12px;
                margin: 4px 0;
                box-shadow: 0 2px 8px 0 rgba(80,60,20,0.08);
                transition: background 0.2s, color 0.2s;
                min-width: 200px;
                min-height: 40px;
                max-width: 200px;
                max-height: 40px;
                white-space: normal;
            }
            QPushButton:hover {
                background: #fffbe6;
                color: #bfa14a;
            }
            QProgressBar {
                background: #e7dfc6;
                border: 1.5px solid #bfa14a;
                border-radius: 8px;
                color: #4b2e19;
                font-family: 'Georgia', 'Times New Roman', serif;
                font-size: 15px;
            }
        ''')

        self.setWindowState(self.windowState() | Qt.WindowMaximized)

    def run(self):
        try:
            mid = mido.MidiFile(self.midi_path)
        except Exception:
            self.finished.emit()
            return
        current_notes = set()
        start_time = time.time()
        next_page_idx = 0
        abs_time = 0
        for msg in mid:
            if self._stop:
                break
            abs_time += msg.time

            # Auto-advance page if needed
            while (next_page_idx < len(self.page_times) and abs_time >= self.page_times[next_page_idx][0]):
                self.advance_page.emit()
                next_page_idx += 1
            if msg.type == 'note_on' and msg.velocity > 0:
                current_notes.add(msg.note)
                self.update_notes.emit(list(current_notes))
            elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                current_notes.discard(msg.note)
                self.update_notes.emit(list(current_notes))
            if msg.time > 0:
                time.sleep(msg.time)
        self.update_notes.emit([])
        self.finished.emit()

    def stop(self):
        self._stop = True
    def convert_to_midi(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import os

        # Step 1: Select WAV file
        wav_path, _ = QFileDialog.getOpenFileName(self, "Select WAV File to Convert", "", "WAV Files (*.wav)")
        if not wav_path or not os.path.exists(wav_path):
            self.status_label.setText("No WAV file selected for MIDI conversion.")
            return

        # Step 2: Select output folder
        output_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder for MIDI")
        if not output_folder:
            self.status_label.setText("No output folder selected for MIDI.")
            return

        try:
            from basic_pitch.inference import predict_and_save, ICASSP_2022_MODEL_PATH
        except Exception as import_exc:
            self.status_label.setText(f"Failed to import basic-pitch: {import_exc}")
            QMessageBox.critical(self, "MIDI Conversion Failed", f"Failed to import basic-pitch:\n{import_exc}")
            return

        self.status_label.setText("Converting WAV to MIDI using basic-pitch...")
        midi_base = os.path.splitext(os.path.basename(wav_path))[0]
        midi_name = midi_base + ".mid"
        midi_path = os.path.join(output_folder, midi_name)
        midi_path_basic_pitch = os.path.join(output_folder, midi_base + "_basic_pitch.mid")

        # Remove both possible MIDI files before conversion
        if os.path.exists(midi_path):
            os.remove(midi_path)
        if os.path.exists(midi_path_basic_pitch):
            os.remove(midi_path_basic_pitch)
        try:
            predict_and_save(
                [wav_path],
                output_directory=output_folder,
                save_midi=True,
                save_notes=False,
                sonify_midi=False,
                save_model_outputs=False,
                model_or_model_path=ICASSP_2022_MODEL_PATH
            )
        except Exception as e:
            self.status_label.setText(f"MIDI conversion failed: {e}")
            QMessageBox.critical(self, "MIDI Conversion Failed", f"MIDI conversion failed:\n{e}")
            return
        # Check for both default and *_basic_pitch.mid output
        if os.path.exists(midi_path):
            found_path = midi_path
        elif os.path.exists(midi_path_basic_pitch):
            found_path = midi_path_basic_pitch
        else:
            found_path = None

        if found_path:
            self.status_label.setText(f"MIDI file created: {found_path}")
            QMessageBox.information(self, "MIDI Conversion Complete", f"MIDI file created:\n{found_path}")
        else:
            self.status_label.setText(f"Conversion finished, but MIDI file not found in {output_folder}.")
            QMessageBox.warning(self, "MIDI Conversion", f"Conversion finished, but MIDI file not found in {output_folder}.")
    def stop_wav_file(self):
        if hasattr(self, 'wav_player') and self.wav_player:
            self.wav_player.stop()
            self.status_label.setText("WAV playback stopped.")
        else:
            self.status_label.setText("No WAV playback to stop.")
    def play_wav_file(self):
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
        from PyQt5.QtCore import QUrl
        import os
        # Prompt for WAV file
        wav_path, _ = QFileDialog.getOpenFileName(self, "Select WAV File to Play", "", "WAV Files (*.wav)")
        if not wav_path or not os.path.exists(wav_path):
            self.status_label.setText("No WAV file selected.")
            return
        # Stop previous playback if any
        if hasattr(self, 'wav_player') and self.wav_player:
            self.wav_player.stop()
        self.wav_player = QMediaPlayer(self)
        self.wav_player.setMedia(QMediaContent(QUrl.fromLocalFile(wav_path)))
        self.wav_player.play()
        self.status_label.setText(f"Playing WAV: {wav_path}")
        # Optionally, connect to finished signal to update status
        self.wav_player.mediaStatusChanged.connect(self._on_wav_status)

    def _on_wav_status(self, status):
        from PyQt5.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.EndOfMedia:
            self.status_label.setText("WAV playback finished.")
    def download_youtube_mp3(self):
        from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox
        import os
        import glob
        try:
            import yt_dlp
        except ImportError:
            self.status_label.setText("yt_dlp is not installed.")
            return
        url, ok = QInputDialog.getText(self, "Download YouTube MP3", "Enter YouTube URL:")
        if not ok or not url.strip():
            return
        dest_folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder for MP3")
        if not dest_folder:
            return
        self.repaint()
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        old_cwd = os.getcwd()
        try:
            os.chdir(dest_folder)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except Exception as e:
            self.status_label.setText(f"Download failed: {e}")
            QMessageBox.critical(self, "Download Failed", f"Download failed:\n{e}")
            os.chdir(old_cwd)
            return
        os.chdir(old_cwd)
        mp3_files = glob.glob(os.path.join(dest_folder, '*.mp3'))
        if mp3_files:
            mp3_path = max(mp3_files, key=os.path.getctime)
            import re
            mp3_dir = os.path.dirname(mp3_path)
            mp3_filename = os.path.basename(mp3_path)
            new_filename = re.sub(r'[\s\'"()\[\]{}]+', "_", mp3_filename)
            new_filename = re.sub(r"[^A-Za-z0-9_.-]", "", new_filename)
            new_path = os.path.join(mp3_dir, new_filename)
            if new_path != mp3_path:
                os.rename(mp3_path, new_path)
                mp3_path = new_path
                mp3_filename = new_filename
            self.status_label.setText(f"Downloaded: {mp3_filename}")
            self.status_label.setToolTip(mp3_path)
            QMessageBox.information(self, "Download Complete", f"MP3 downloaded to:\n{mp3_path}")
        else:
            self.status_label.setText("Download finished, but MP3 not found.")
            QMessageBox.warning(self, "Download", "Download finished, but MP3 file not found.")

    def on_midi_conversion_error(self, error_msg):
        self.midi_progress.setVisible(False)
        self.convert_midi_btn.setEnabled(True)
        self.status_label.setText(f"<span style='color:red'>MIDI conversion with crepe failed: {error_msg}</span>")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "MIDI Conversion Failed", f"MIDI conversion failed:\n{error_msg}")

    def open_file_dialog(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from pydub import AudioSegment
        import os

        # Step 1: Select MP3 source file
        mp3_path, _ = QFileDialog.getOpenFileName(self, "Convert MP3 to WAV", "", "MP3 Files (*.mp3)")
        if not mp3_path:
            self.file_label.setText("No file selected.")
            self.status_label.setText("<span style='color:red'>No file selected.</span>")
            return

        # Step 2: Select destination folder
        dest_folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder for WAV")
        if not dest_folder:
            self.file_label.setText("No destination folder selected.")
            self.status_label.setText("<span style='color:red'>No destination folder selected.</span>")
            return

        # Step 2.5: Create subfolder with song name
        base_name = os.path.splitext(os.path.basename(mp3_path))[0]
        song_folder = os.path.join(dest_folder, base_name)
        try:
            os.makedirs(song_folder, exist_ok=True)
        except Exception as e:
            self.status_label.setText(f"Failed to create folder: {e}")
            return

        # Step 3: Convert MP3 to WAV
        try:
            audio = AudioSegment.from_mp3(mp3_path)
            wav_path = os.path.join(song_folder, base_name + ".wav")
            audio.export(wav_path, format="wav")
        except Exception as e:
            self.status_label.setText(f"Conversion failed: {e}")
            return

        # Step 4: Update UI
        self.status_label.setText("MP3 converted to WAV successfully.")

    def import_midi_file(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
        from PyQt5.QtGui import QPixmap, QImage
        import tempfile
        import subprocess
        import os
        try:
            import fitz  # PyMuPDF
        except ImportError:
            QMessageBox.critical(self, "Error", "PyMuPDF (fitz) is required to render PDF. Please install it with 'pip install pymupdf'.")
            self.status_label.setText("PyMuPDF (fitz) not installed.")
            return

        midi_path, _ = QFileDialog.getOpenFileName(self, 'Open MIDI File', '', 'MIDI Files (*.mid *.midi)')
        if not midi_path:
            return
        # Set the song title from the filename, removing '_basic_pitch' if present
        song_title = os.path.splitext(os.path.basename(midi_path))[0]
        song_title = song_title.replace('_basic_pitch', '')
        self.title_label.setText(song_title)
        self.status_label.setText('Converting MIDI to staff...')
        pdf_path = midi_path + '.pdf'
        musescore_path = self.musescore_path
        import shutil
        if not musescore_path or not shutil.which(musescore_path):
            # Try common locations
            possible_paths = [
                r'C:\Program Files\MuseScore 4\bin\MuseScore4.exe',
                r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe',
                r'C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe',
                r'C:\Program Files\MuseScore 2\bin\MuseScore.exe',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    musescore_path = path
                    break
        if not musescore_path or not os.path.exists(musescore_path):
            musescore_path, ok = QInputDialog.getText(self, 'MuseScore Path', 'Enter full path to MuseScore executable:')
            if not ok or not os.path.exists(musescore_path):
                QMessageBox.critical(self, 'MuseScore Not Found', 'MuseScore executable not found. Please install MuseScore and provide the correct path.')
                self.status_label.setText('MuseScore not found.')
                return
            self.musescore_path = musescore_path
        # Export MIDI to PDF directly (no title)
        pdf_cmd = [musescore_path, midi_path, '-o', pdf_path]
        subprocess.run(pdf_cmd, capture_output=True)
        self.conversion_thread = MidiConversionThread(midi_path, pdf_path, musescore_path)
        self.conversion_thread.finished.connect(self.on_conversion_finished)
        self.conversion_thread.error.connect(self.on_conversion_error)
        self.conversion_thread.start()

    def on_conversion_finished(self, midi_path, pdf_path):
        self.status_label.setText('Conversion complete.')
        from PyQt5.QtGui import QImage
        from PyQt5.QtCore import Qt
        import fitz  # PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                raise RuntimeError("PDF has no pages.")
            self.staff_pages = []
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=220, alpha=False)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                self.staff_pages.append(QPixmap.fromImage(img))
            self.current_staff_page = 0
            self.show_staff_page(0)
            self.status_label.setText(f"Staff rendering complete ({len(self.staff_pages)} page(s)).")
            self.staff_img_label.setScaledContents(False)
            self.staff_img_label.setAlignment(Qt.AlignCenter)
            self.staff_img_label.setMaximumSize(16777215, 16777215)
            self.staff_img_label.setMinimumHeight(120)
            # Also ensure the piano widget and controls are always visible
            if hasattr(self, 'piano_widget'):
                self.piano_widget.setMinimumHeight(60)
                self.piano_widget.setMaximumHeight(120)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Rendering failed: {e}")
            self.staff_img_label.setText("<i>Staff image will appear here.</i>")
            self.status_label.setText("Rendering failed.")
            self.staff_pages = []
            self.current_staff_page = 0

        # Setup MIDI playback
        try:
            from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
            from PyQt5.QtCore import QUrl
            self.midi_player = QMediaPlayer(self)  # parented to self to avoid GC
            # For Qt6 compatibility, set audio output if available
            if hasattr(self.midi_player, 'setAudioOutput'):
                from PyQt5.QtMultimedia import QAudioOutput
                self.audio_output = QAudioOutput(self)
                self.midi_player.setAudioOutput(self.audio_output)
            self.midi_player.setMedia(QMediaContent(QUrl.fromLocalFile(midi_path)))
        except Exception as e:
            self.status_label.setText(self.status_label.text() + f" (MIDI playback unavailable: {e})")
        self.last_midi_path = midi_path

    def on_conversion_error(self, error_msg):
        self.status_label.setText(f'Error: {error_msg}')
        QMessageBox.critical(self, 'Conversion Error', error_msg)

    def show_staff_page(self, page_idx):
        if not self.staff_pages:
            self.staff_img_label.setText("<i>Staff image will appear here.</i>")
            return
        if 0 <= page_idx < len(self.staff_pages):
            pixmap = self.staff_pages[page_idx]
            # Reduce size to fit label, maintain aspect ratio
            label_size = self.staff_img_label.size()
            if label_size.width() > 10 and label_size.height() > 10:
                scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                scaled_pixmap = pixmap
            self.staff_img_label.setPixmap(scaled_pixmap)
            self.current_staff_page = page_idx
            self.status_label.setText(f"Showing page {page_idx+1} of {len(self.staff_pages)}")

    def prev_staff_page(self):
        if self.staff_pages and self.current_staff_page > 0:
            self.show_staff_page(self.current_staff_page - 1)

    def next_staff_page(self):
        if self.staff_pages and self.current_staff_page < len(self.staff_pages) - 1:
            self.show_staff_page(self.current_staff_page + 1)


    def play_midi(self):
        if not hasattr(self, 'last_midi_path') or not self.last_midi_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No MIDI File", "Please import a MIDI file first.")
            self.status_label.setText("No MIDI file loaded. Please import a MIDI file first.")
            return
        # Stop any previous playback
        self.stop_midi()

        # --- Start TiMidity++ for audio playback ---
        import subprocess, os
        midi_path = self.last_midi_path
        timidity_dir = r'D:\MyProject\Verdi\TiMidity'
        timidity_exe = os.path.join(timidity_dir, 'timidity.exe')
        timidity_cfg = os.path.join(timidity_dir, 'timidity.cfg')
        cmd = [timidity_exe, '-c', timidity_cfg, '-EFreverb=0']
        if midi_path:
            cmd.append(midi_path)
        print(f"[DEBUG] TiMidity++ command: {' '.join(cmd)}")
        self.timidity_process = None
        if os.path.exists(timidity_exe) and os.path.exists(timidity_cfg) and midi_path:
            try:
                self.timidity_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("[DEBUG] TiMidity++ process started.")
                # Read and print stderr output (non-blocking, short wait)
                import threading
                def print_stderr(proc):
                    try:
                        for line in iter(proc.stderr.readline, b''):
                            if not line:
                                break
                            print('[TiMidity++ stderr]', line.decode(errors='replace').strip())
                    except Exception as e:
                        print(f"[ERROR] Reading TiMidity++ stderr: {e}")
                threading.Thread(target=print_stderr, args=(self.timidity_process,), daemon=True).start()
            except Exception as e:
                self.status_label.setText(self.status_label.text() + f" (TiMidity++ failed: {e})")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "TiMidity++ Error", f"Failed to start TiMidity++:\n{e}\nCommand: {' '.join(cmd)}")
                print(f"[ERROR] Failed to start TiMidity++: {e}")
        else:
            print("[ERROR] TiMidity++ executable, config, or MIDI file not found.")

        # --- Start MidiPlaybackThread for note highlighting and page advance ---
        page_times = []
        if hasattr(self, 'staff_pages') and self.staff_pages:
            try:
                mid = mido.MidiFile(self.last_midi_path)
                total_time = sum(msg.time for msg in mid)
                num_pages = len(self.staff_pages)
                page_times = [(total_time * (i+1) / num_pages, i) for i in range(num_pages-1)]
            except Exception:
                page_times = []
        self.midi_thread = MidiPlaybackThread(self.last_midi_path, page_times)
        self.midi_thread.update_notes.connect(self.piano_widget.set_pressed_keys)
        self.midi_thread.advance_page.connect(self.show_next_page)
        self.midi_thread.finished.connect(self.on_midi_playback_finished)
        self.midi_thread.start()
        self.status_label.setText("Playing MIDI with note highlights and TiMidity++ audio...")

    def on_midi_playback_finished(self):
        self.piano_widget.set_pressed_keys([])
        self.status_label.setText("MIDI playback finished.")

    def stop_midi(self):
        # Stop MIDI playback thread if running (for highlights and page advance)
        if hasattr(self, 'midi_thread') and self.midi_thread and self.midi_thread.isRunning():
            self.midi_thread.stop()
            self.midi_thread.wait()
            self.midi_thread = None
        # Stop TiMidity++ process if running (for audio)
        if hasattr(self, 'timidity_process') and self.timidity_process:
            try:
                self.timidity_process.terminate()
            except Exception:
                pass
            self.timidity_process = None
        # Stop QMediaPlayer if used elsewhere
        if hasattr(self, 'midi_player') and self.midi_player:
            self.midi_player.stop()
        # Always clear piano highlights after stopping thread
        self.piano_widget.set_pressed_keys([])

    def stop_timidity(self):
        import subprocess
        try:
            subprocess.run(['taskkill', '/IM', 'timidity.exe', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def pause_midi(self):
        if hasattr(self, 'midi_player') and self.midi_player:
            self.midi_player.pause()


    def resizeEvent(self, event):
        # Redraw staff image on resize
        if hasattr(self, 'staff_pages') and self.staff_pages:
            self.show_staff_page(self.current_staff_page)
        super().resizeEvent(event)

    def show_prev_page(self):
        if hasattr(self, 'staff_pages') and self.staff_pages and self.current_staff_page > 0:
            self.show_staff_page(self.current_staff_page - 1)

    def show_next_page(self):
        if hasattr(self, 'staff_pages') and self.staff_pages and self.current_staff_page < len(self.staff_pages) - 1:
            self.show_staff_page(self.current_staff_page + 1)

    def auto_advance_page(self):
        pass

class MidiConversionThread(QThread):
    error = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    def __init__(self, midi_path, pdf_path, musescore_path, parent=None):
        super().__init__(parent)
        self.midi_path = midi_path
        self.pdf_path = pdf_path
        self.musescore_path = musescore_path

    def run(self):
        import subprocess
        try:
            cmd = [self.musescore_path, self.midi_path, '-o', self.pdf_path]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                err = result.stderr.decode(errors='ignore') if result.stderr else 'Unknown error'
                self.error.emit(f"MuseScore failed: {err}")
                return
            if not os.path.exists(self.pdf_path):
                self.error.emit("PDF was not created by MuseScore.")
                return
            self.finished.emit(self.midi_path, self.pdf_path)
        except Exception as e:
            self.error.emit(str(e))

# Main entry point for Verdi
if __name__ == "__main__":
    print("Starting Verdi...")
    try:
        from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
        from PyQt5.QtGui import QIcon, QPixmap
        import sys, os
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(r"D:\MyProject\Verdi\logo.ico"))
        # Show splash screen with piano photo and wait for user to click OK
        splash_img_path = os.path.join(os.path.dirname(__file__), 'photo.jpg')
        splash = None
        if os.path.exists(splash_img_path):
            pixmap = QPixmap(splash_img_path)
            splash = QSplashScreen(pixmap)
            splash.show()
            app.processEvents()
            # Show modal dialog on top of splash
            msg = QMessageBox()
            msg.setWindowTitle("Welcome to Verdi")
            msg.setText("Welcome to Verdi. With this application You can download MP3 from Youtube, then convert the MP3 to WAV, then convert the WAV to MIDI and finally import the MIDI file to generate the staff. Have fun! Author: Roberto Raimondo IS Senior System Engineer II.")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowModality(Qt.ApplicationModal)
            msg.exec_()
        win = Verdi()
        win.setWindowState(win.windowState() | Qt.WindowMaximized)
        win.showMaximized()
        if splash:
            splash.finish(win)
        print("App window should now be visible.")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
