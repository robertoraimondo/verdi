from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

class PianoWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(80)
		self.setMinimumWidth(800)
		self.num_keys = 88
		self.pressed_keys = set()  # MIDI note numbers (A0=21, C8=108)
		# Modern style: subtle gradient background
		self.setStyleSheet('''
			background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #23272b, stop:1 #181c20);
			border: 2px solid #444;
			border-radius: 12px;
		''')

	def set_pressed_keys(self, midi_notes):
		self.pressed_keys = set(midi_notes)
		self.update()

	def paintEvent(self, event):
		p = QPainter(self)
		# Build lists of white and black keys with their MIDI notes and white key indices
		white_keys = []  # (white_idx, midi_note)
		black_keys = []  # (white_idx, midi_note)
		white_idx = 0
		for i in range(self.num_keys):
			midi_note = 21 + i
			if self.is_white(midi_note):
				white_keys.append((white_idx, midi_note))
				white_idx += 1
			else:
				# Black key is between previous and next white keys
				black_keys.append((white_idx - 1, midi_note))
		num_white = len(white_keys)
		key_width = self.width() / num_white
		# Draw white keys with rounded corners and subtle shadow
		for idx, midi_note in white_keys:
			x = idx * key_width
			if midi_note in self.pressed_keys:
				p.setBrush(QColor('#ffe066'))  # Highlighted white key
			else:
				p.setBrush(QColor('#f8f9fa'))
			p.setPen(QPen(QColor('#b0b0b0'), 1))
			p.drawRoundedRect(int(x), 0, int(key_width)+1, self.height(), 6, 6)
			# Draw subtle shadow at the bottom
			p.setPen(Qt.NoPen)
			p.setBrush(QColor(0,0,0,18))
			p.drawRect(int(x), self.height()-6, int(key_width)+1, 6)
		# Draw black keys with modern look
		black_key_height = int(self.height() * 0.6)
		black_key_width = key_width * 0.6
		for left_white_idx, midi_note in black_keys:
			# Black key is between left_white_idx and left_white_idx+1
			x = (left_white_idx + 1) * key_width - black_key_width/2
			if midi_note in self.pressed_keys:
				p.setBrush(QColor('#ffb700'))  # Highlighted black key
			else:
				p.setBrush(QColor('#23272b'))
			p.setPen(QPen(QColor('#444'), 1))
			p.drawRoundedRect(int(x), 0, int(black_key_width)+1, black_key_height, 4, 4)

	@staticmethod
	def is_white(midi_note):
		# C D E F G A B = white, sharps/flats = black
		return (midi_note % 12) in [0, 2, 4, 5, 7, 9, 11]
