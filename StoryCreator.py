from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFileDialog, QLineEdit, QMessageBox, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from groq import Groq
from dotenv import load_dotenv
import sys
import os
import re 

# .env dosyasını yükle
load_dotenv()

# Groq API Key Kontrolü
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

try:
    import logging
    logging.getLogger("transformers").setLevel(logging.ERROR)
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
except Exception as e:
    print(f"Model loading error: {e}")

# --- WORKER THREAD ---
class StoryGeneratorWorker(QThread):
    status_signal = pyqtSignal(str)
    stream_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, images, action_instruction):
        super().__init__()
        self.images = images
        self.action_instruction = action_instruction

    def run(self):
        try:
            self.status_signal.emit("Analyzing images... (This may take a moment)")
            captions = []
            for img_path in self.images:
                try:
                    img = Image.open(img_path)
                    inputs = processor(img, return_tensors="pt")
                    out = model.generate(**inputs)
                    caption = processor.decode(out[0], skip_special_tokens=True)
                    captions.append(caption)
                except Exception as img_err:
                    print(f"Image error: {img_err}")
                    continue

            self.status_signal.emit("AI is crafting your story...")
            
            prompt = f"""Sen ödüllü bir Türk hikaye yazarısın. 

Resim İpuçları: {' '.join(captions)}
Görev: {self.action_instruction}

KURALLAR:
1. SADECE TÜRKÇE yaz.
2. Asla yabancı harf (Çince, Japonca vb.) kullanma.
3. Akıcı ve betimleyici ol.
4. 3 paragraf olsun.

Sadece hikaye metnini ver."""

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sen Türkçeyi kusursuz kullanan bir yazarsın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_completion_tokens=500,
                top_p=1,
                stream=True,
                stop=None
            )

            full_story = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_story += content
                    self.stream_signal.emit(full_story) 
            
            self.finished_signal.emit(full_story)

        except Exception as e:
            self.error_signal.emit(str(e))


class StoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Creator")
        self.resize(1000, 700)
        
        # Icon ayarla - icon.png veya icon.ico dosyası varsa
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
        elif os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
        # Ana düzen
        main_window_layout = QVBoxLayout(self)
        main_window_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: #0a0a0a;
            }
            QScrollBar:vertical { 
                border: none; 
                background: #1a1a1a; 
                width: 12px; 
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical { 
                background: #3a3a3a; 
                min-height: 30px; 
                border-radius: 6px; 
            }
            QScrollBar::handle:vertical:hover { 
                background: #4a4a4a; 
            }
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                color: #ffffff;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)
        
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setSpacing(25)
        self.layout.setContentsMargins(50, 40, 50, 40)

        self.image_labels = []
        self.images = [] 

        # --- HEADER ---
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: #161616;
                border-radius: 20px;
                border: 1px solid #2a2a2a;
                padding: 30px;
            }
        """)
        title_layout = QVBoxLayout()
        
        title = QLabel("Story Creator")
        title.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #ffffff;
            background: transparent;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Upload your images and let AI create your story")
        subtitle.setStyleSheet("""
            font-size: 15px; 
            color: #888888; 
            margin-top: 8px;
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_frame.setLayout(title_layout)
        self.layout.addWidget(title_frame)

        # --- IMAGES ---
        image_container = QFrame()
        image_container.setStyleSheet("""
            QFrame {
                background: #161616;
                border-radius: 20px;
                border: 1px solid #2a2a2a;
                padding: 25px;
            }
        """)
        image_layout = QHBoxLayout()
        image_layout.setSpacing(20)
        
        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background: #1a1a1a;
                    border: 2px dashed #3a3a3a;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)
            
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(5, 5, 5, 5)
            
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setMinimumSize(200, 220)
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            lbl.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #555555;
                    font-size: 14px;
                    border: none;
                }
            """)
            lbl.setText(f"Image {i+1}")
            lbl.setWordWrap(True)
            
            frame_layout.addWidget(lbl)
            self.image_labels.append(lbl)
            image_layout.addWidget(frame)
        
        image_container.setLayout(image_layout)
        self.layout.addWidget(image_container)

        # --- BUTTONS ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.load_button = QPushButton("Add Images")
        self.load_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_button.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                color: white;
                border: 1px solid #3a3a3a;
                padding: 14px 30px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #333333;
                border: 1px solid #4a4a4a;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
        """)
        self.load_button.clicked.connect(self.load_images)
        button_layout.addWidget(self.load_button)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                color: #ff6b6b;
                border: 1px solid #3a3a3a;
                padding: 14px 30px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #333333;
                border: 1px solid #ff6b6b;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
        """)
        self.clear_button.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_button)
        
        self.layout.addLayout(button_layout)

        # --- THEME INPUT ---
        action_frame = QFrame()
        action_frame.setStyleSheet("""
            QFrame {
                background: #161616;
                border-radius: 20px;
                border: 1px solid #2a2a2a;
                padding: 25px;
            }
        """)
        action_layout = QVBoxLayout()
        
        self.action_label = QLabel("Story Theme (Optional)")
        self.action_label.setStyleSheet("""
            font-weight: bold;
            font-size: 15px;
            color: #cccccc;
            margin-bottom: 10px;
            background: transparent;
        """)
        action_layout.addWidget(self.action_label)
        
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText("e.g., An adventure, a romantic moment, a funny situation...")
        self.action_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
                font-size: 14px;
                background: #1a1a1a;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #4a4a4a;
                background: #202020;
            }
        """)
        action_layout.addWidget(self.action_input)
        
        action_frame.setLayout(action_layout)
        self.layout.addWidget(action_frame)

        # --- GENERATE BUTTON ---
        self.generate_button = QPushButton("Generate Story")
        self.generate_button.setEnabled(False)
        self.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #0a0a0a;
                border: none;
                padding: 18px;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
            QPushButton:disabled {
                background: #2a2a2a;
                color: #555555;
            }
            QPushButton:pressed {
                background: #cccccc;
            }
        """)
        self.layout.addWidget(self.generate_button)
        self.generate_button.clicked.connect(self.start_generation)

        # --- STORY SECTION ---
        story_container = QFrame()
        story_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #121212);
                border-radius: 20px;
                border: 1px solid #2a2a2a;
                padding: 0px;
            }
        """)
        story_layout = QVBoxLayout(story_container)
        story_layout.setSpacing(0)
        story_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title section
        title_section = QFrame()
        title_section.setStyleSheet("""
            QFrame {
                background: #1f1f1f;
                border-radius: 20px 20px 0px 0px;
                border-bottom: 1px solid #2a2a2a;
                padding: 20px 30px;
            }
        """)
        title_section_layout = QVBoxLayout(title_section)
        title_section_layout.setContentsMargins(0, 0, 0, 0)
        
        self.story_label_title = QLabel("Your Story")
        self.story_label_title.setStyleSheet("""
            font-weight: bold;
            font-size: 18px;
            color: #ffffff;
            background: transparent;
            letter-spacing: 0.5px;
        """)
        title_section_layout.addWidget(self.story_label_title)
        story_layout.addWidget(title_section)
        
        # Content section
        content_section = QFrame()
        content_section.setStyleSheet("""
            QFrame {
                background: transparent;
                border-radius: 0px 0px 20px 20px;
                padding: 30px;
            }
        """)
        content_layout = QVBoxLayout(content_section)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.story_text_label = QLabel()
        self.story_text_label.setWordWrap(True)
        self.story_text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.story_text_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 15px;
                line-height: 1.9;
                padding: 0px;
                background: transparent;
            }
        """)
        self.story_text_label.setText("Your story will appear here...")
        content_layout.addWidget(self.story_text_label)
        story_layout.addWidget(content_section)
        
        self.layout.addWidget(story_container)
        self.layout.addStretch()
        
        self.scroll_area.setWidget(self.content_widget)
        main_window_layout.addWidget(self.scroll_area)

    def clean_text_content(self, text):
        cleaned = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s.,;!?:\"\'\-\(\)]', '', text)
        return cleaned

    def update_image_display(self):
        for i in range(3):
            if i < len(self.images):
                file_name = self.images[i]
                pixmap = QPixmap(file_name)
                scaled_pixmap = pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.image_labels[i].setPixmap(scaled_pixmap)
                self.image_labels[i].setText("")
                self.image_labels[i].parent().setStyleSheet("""
                    QFrame {
                        background: #1a1a1a;
                        border: 2px solid #4a4a4a;
                        border-radius: 15px;
                        padding: 10px;
                    }
                """)
            else:
                self.image_labels[i].setPixmap(QPixmap())
                self.image_labels[i].setText(f"Image {i+1}")
                self.image_labels[i].parent().setStyleSheet("""
                    QFrame {
                        background: #1a1a1a;
                        border: 2px dashed #3a3a3a;
                        border-radius: 15px;
                        padding: 10px;
                    }
                """)
        
        if self.images:
            self.generate_button.setEnabled(True)
            self.story_text_label.setText(f"{len(self.images)} image(s) loaded. Click the button to generate your story!")
        else:
            self.generate_button.setEnabled(False)
            self.story_text_label.setText("Your story will appear here...")

    def load_images(self):
        if len(self.images) >= 3:
            QMessageBox.warning(self, "Warning", "Maximum 3 images allowed!")
            return
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not files: return
        remaining_slots = 3 - len(self.images)
        if len(files) > remaining_slots:
            files = files[:remaining_slots]
        self.images.extend(files)
        self.update_image_display()

    def clear_all(self):
        self.images = []
        self.update_image_display()
        self.action_input.clear()
        self.story_text_label.setText("Your story will appear here...")
        self.generate_button.setEnabled(False)

    def start_generation(self):
        if not client:
             QMessageBox.warning(self, "Error", "GROQ API Key not found!")
             return
        if not self.images:
            QMessageBox.warning(self, "Warning", "Please upload images first!")
            return
        
        action_text = self.action_input.text().strip()
        if not action_text:
            action_instruction = "Kendi hayal gücünle, resimlerdeki atmosferi birbirine bağlayan yaratıcı ve sürükleyici bir olay örgüsü kurgula."
        else:
            action_instruction = f"Şu olayı temel al: {action_text}"

        self.generate_button.setEnabled(False)
        self.story_text_label.setText("Generating story...")
        
        self.worker = StoryGeneratorWorker(self.images, action_instruction)
        self.worker.status_signal.connect(self.update_status)
        self.worker.stream_signal.connect(self.update_story_stream)
        self.worker.finished_signal.connect(self.on_story_finished)
        self.worker.error_signal.connect(self.on_story_error)
        self.worker.start()

    def update_status(self, message):
        self.story_text_label.setText(message)

    def update_story_stream(self, partial_text):
        self.story_text_label.setText(partial_text)

    def on_story_finished(self, full_text):
        final_clean_story = self.clean_text_content(full_text)
        self.story_text_label.setText(final_clean_story)
        self.generate_button.setEnabled(True)
    
    def on_story_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error_message}")
        self.story_text_label.setText("Story generation failed.")
        self.generate_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = StoryApp()
    window.show()
    sys.exit(app.exec())