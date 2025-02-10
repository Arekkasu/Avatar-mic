import sys
import sounddevice as sd
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.volume_level = -120  # Valor inicial en dB
        self.selected_device = None
        self.selected_backend = 'ALSA'  # Default
        self.indicator_window = None  # Ventana del indicador

    def initUI(self):
        layout = QVBoxLayout()

        self.backend_label = QLabel("Selecciona el backend de audio:")
        layout.addWidget(self.backend_label)

        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["ALSA", "JACK"])
        layout.addWidget(self.backend_combo)

        self.device_label = QLabel("Selecciona el micrófono:")
        layout.addWidget(self.device_label)

        self.device_combo = QComboBox()
        self.update_device_list()
        layout.addWidget(self.device_combo)

        self.start_button = QPushButton("Iniciar Captura")
        self.start_button.clicked.connect(self.start_audio_capture)
        layout.addWidget(self.start_button)

        self.volume_label = QLabel("Nivel de entrada (dB): -120")
        layout.addWidget(self.volume_label)

        self.setLayout(layout)
        self.setWindowTitle("Monitor de Audio")

    def update_device_list(self):
        devices = sd.query_devices()
        self.device_combo.clear()
        for idx, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                self.device_combo.addItem(f"{idx} - {dev['name']}", idx)

    def start_audio_capture(self):
        self.selected_backend = self.backend_combo.currentText()
        self.selected_device = self.device_combo.currentData()

        if self.selected_device is None:
            self.volume_label.setText("Error: No se seleccionó un micrófono válido.")
            return

        device_info = sd.query_devices(self.selected_device, 'input')
        samplerate = int(device_info['default_samplerate'])  # Detecta la frecuencia correcta
        channels = 1  # Mantener en mono
        dtype = 'float32'  # Formato correcto según pactl list sources

        # Abrir la ventana del indicador
        self.indicator_window = IndicatorWindow()
        self.indicator_window.show()

        try:
            self.stream = sd.InputStream(device=self.selected_device, samplerate=samplerate, channels=channels, dtype=dtype, callback=self.audio_callback)
            self.stream.start()
        except Exception as e:
            self.volume_label.setText(f"Error: {str(e)}")

    def audio_callback(self, indata, frames, time, status):
        self.volume_level = np.linalg.norm(indata)
        db_level = 20 * np.log10(self.volume_level + 1e-6)
        self.volume_label.setText(f"Nivel de entrada (dB): {db_level:.2f}")
        print(f"Nivel de entrada (dB): {db_level:.2f}")

        if self.indicator_window:
            self.indicator_window.update_image(db_level > -50)

class IndicatorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Indicador de Sonido")
        self.setGeometry(100, 100, 600, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, 600, 600)

        self.active_pixmap = QPixmap("active.PNG").scaled(600, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.inactive_pixmap = QPixmap("inactive.PNG").scaled(600, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.label.setPixmap(self.inactive_pixmap)

    def update_image(self, is_active):
        self.label.setPixmap(self.active_pixmap if is_active else self.inactive_pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AudioApp()
    ex.show()
    sys.exit(app.exec_())
