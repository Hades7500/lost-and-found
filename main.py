import sys
import os
import sqlite3
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QTabWidget, QGridLayout,
                             QStackedLayout, QRadioButton, QScrollArea,
                             QDesktopWidget)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt
from image_detection import image_identification

# Configure database path
DATABASE_DIR = Path.home() / "lost-and-found"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_FILE = str(DATABASE_DIR / "reported_items.db")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lost and Found Item Tracker")
        self.set_window_size_to_screen()
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d89ef;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e5fbd;
            }
            QPushButton:pressed {
                background-color: #174d99;
            }
            QRadioButton {
                font-weight: bold;
                font-size: 13px;
            }
            QLabel {
                font-size: 13px;
            }
            QLineEdit {
                padding: 6px;
                font-size: 13px;
            }
            QListWidget {
                font-size: 13px;
            }
        """)
        self.create_database()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.tab_widget = QTabWidget()
        self.lost_tab = ImageTab("Lost")
        self.found_tab = ImageTab("Found")
        self.tab_widget.addTab(self.lost_tab, "Lost Items")
        self.tab_widget.addTab(self.found_tab, "Found Items")

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.tab_widget)

    def set_window_size_to_screen(self):
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(100, 100, int(screen.width() * 0.8), int(screen.height() * 0.8))

    def create_database(self):
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    tags TEXT,
                    date_reported DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not initialize database: {str(e)}")
        finally:
            if conn:
                conn.close()

class ImageTab(QWidget):
    def __init__(self, item_type, save_directory="saved_items"):
        super().__init__()
        self.item_type = item_type
        self.save_directory = os.path.join(save_directory, item_type.lower())
        os.makedirs(self.save_directory, exist_ok=True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # Top Options
        self.option_layout = QHBoxLayout()
        self.option_layout.setSpacing(20)
        self.upload_new_radio = QRadioButton(f"Report New {item_type} Item")
        self.view_existing_radio = QRadioButton(f"View Reported {item_type} Items")
        self.upload_new_radio.setChecked(True)
        self.option_layout.addWidget(self.upload_new_radio)
        self.option_layout.addWidget(self.view_existing_radio)
        self.option_layout.addStretch()
        self.main_layout.addLayout(self.option_layout)

        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # Upload UI
        self.upload_widget = QWidget()
        self.upload_layout = QGridLayout(self.upload_widget)
        self.upload_layout.setSpacing(15)
        self.upload_layout.setContentsMargins(20, 20, 20, 20)

        self.image_label = QLabel("No image selected")
        screen_width = QDesktopWidget().screenGeometry().width()
        self.image_display_width = int(screen_width * 0.4)
        self.image_display_height = int(self.image_display_width * 0.75)
        self.image_label.setMinimumSize(self.image_display_width, self.image_display_height)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            border: 2px dashed #ccc; 
            background-color: #f9f9f9;
            color: #666;
            font-style: italic;
        """)

        self.upload_layout.addWidget(QLabel(f"Image of {item_type} Item:"), 0, 0, 1, 2)
        self.upload_layout.addWidget(self.image_label, 1, 0, 1, 2)

        self.upload_button = QPushButton("Select Image")
        self.upload_button.clicked.connect(self.upload_image)
        self.upload_layout.addWidget(self.upload_button, 2, 0, 1, 2)

        # Tags
        self.upload_layout.addWidget(QLabel("Tags (comma separated):"), 3, 0)
        self.tag_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("e.g., wallet, black, leather")
        self.tag_button = QPushButton("Add Tags")
        self.tag_button.clicked.connect(self.add_tags)
        self.tag_input_layout.addWidget(self.tag_input)
        self.tag_input_layout.addWidget(self.tag_button)
        self.upload_layout.addLayout(self.tag_input_layout, 3, 1)

        self.upload_layout.addWidget(QLabel("Current Tags:"), 4, 0, 1, 2)
        self.tag_list_widget = QListWidget()
        self.tag_list_widget.setMaximumHeight(100)
        self.upload_layout.addWidget(self.tag_list_widget, 5, 0, 1, 2)

        # Buttons
        self.bottom_buttons_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit Report")
        self.submit_button.clicked.connect(self.submit_data)
        self.delete_tag_button = QPushButton("Delete Selected Tag")
        self.delete_tag_button.clicked.connect(self.delete_selected_tag)
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.reset_form)
        
        self.bottom_buttons_layout.addWidget(self.submit_button)
        self.bottom_buttons_layout.addWidget(self.delete_tag_button)
        self.bottom_buttons_layout.addWidget(self.clear_button)
        self.bottom_buttons_layout.addStretch()
        self.upload_layout.addLayout(self.bottom_buttons_layout, 6, 0, 1, 2)

        self.stacked_layout.addWidget(self.upload_widget)

        # Existing Items
        self.existing_widget = QWidget()
        self.existing_layout = QVBoxLayout(self.existing_widget)
        self.existing_layout.setContentsMargins(10, 10, 10, 10)
        self.existing_layout.setSpacing(15)
        
        self.existing_label = QLabel(f"Reported {item_type} Items:")
        self.existing_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.existing_layout.addWidget(self.existing_label)

        self.search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by tags...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.show_existing_items)
        self.clear_search_button = QPushButton("Clear")
        self.clear_search_button.clicked.connect(self.clear_search)
        
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.search_button)
        self.search_layout.addWidget(self.clear_search_button)
        self.existing_layout.addLayout(self.search_layout)

        self.existing_scroll_area = QScrollArea()
        self.existing_scroll_area.setWidgetResizable(True)
        self.existing_scroll_content = QWidget()
        self.existing_list_layout = QVBoxLayout(self.existing_scroll_content)
        self.existing_list_layout.setContentsMargins(5, 5, 5, 5)
        self.existing_list_layout.setSpacing(20)
        self.existing_scroll_area.setWidget(self.existing_scroll_content)
        self.existing_layout.addWidget(self.existing_scroll_area)
        
        self.stacked_layout.addWidget(self.existing_widget)

        self.upload_new_radio.toggled.connect(lambda checked: self.stacked_layout.setCurrentIndex(0) if checked else None)
        self.view_existing_radio.toggled.connect(self.show_existing_items)

        self.current_image_path = None
        self.displayed_image = None
        self.tags = []

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image", 
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if not file_path:
            return

            
        self.current_image_path = file_path
        try:
            image = QImage(file_path)
            if image.isNull():
                raise ValueError("Invalid image file")
                
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                self.image_display_width, 
                self.image_display_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.displayed_image = scaled_pixmap
            self.image_label.setPixmap(self.displayed_image)
            self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: transparent;")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")
            self.current_image_path = None

    def add_tags(self):
        tag_text = self.tag_input.text().strip()
        if not tag_text:
            return
            
        # Split tags by commas and clean them up
        new_tags = [tag.strip() for tag in tag_text.split(",") if tag.strip()]
        
        if not new_tags:
            return
            
        if len(self.tags) + len(new_tags) > 10:
            QMessageBox.warning(self, "Limit Reached", "Maximum 10 tags allowed")
            return
            
        for tag in new_tags:
            if len(tag) > 50:
                QMessageBox.warning(self, "Too Long", "Individual tags must be 50 characters or less")
                continue
                
            if tag not in self.tags:
                self.tags.append(tag)
                self.tag_list_widget.addItem(QListWidgetItem(tag))
                
        self.tag_input.clear()

    def delete_selected_tag(self):
        selected_items = self.tag_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a tag to delete.")
            return
            
        for item in selected_items:
            self.tags.remove(item.text())
            self.tag_list_widget.takeItem(self.tag_list_widget.row(item))

    def submit_data(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please select an image to report.")
            return

        if not self.tags:
            reply = QMessageBox.question(
                self,
                "No Tags Added",
                "You haven't added any tags. Are you sure you want to submit without tags?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        reply = QMessageBox.question(
            self, 
            "Confirm Submission",
            "Are you sure you want to submit this item?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        ext = os.path.splitext(self.current_image_path)[1]
        new_filename = f"{base_name}{ext}"
        save_path = os.path.join(self.save_directory, new_filename)
        tags = image_identification(self.current_image_path)
        conn = None
        try:
            # Copy the image to our storage directory
            shutil.copy2(self.current_image_path, save_path)

            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO items (item_type, image_path, tags)
                VALUES (?, ?, ?)
            """, (self.item_type, save_path, ",".join(tags)))
            conn.commit()

            QMessageBox.information(
                self, 
                "Success", 
                f"{self.item_type} item reported successfully.\n\nTags: {', '.join(self.tags) if self.tags else 'None'}"
            )
            self.reset_form()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to save item:\n\n{str(e)}\n\nPlease try again."
            )
            # Clean up if we copied the file but failed to save to DB
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except:
                    pass
        finally:
            if conn:
                conn.close()

    def reset_form(self):
        self.image_label.clear()
        self.image_label.setText("No image selected")
        self.image_label.setStyleSheet("""
            border: 2px dashed #ccc; 
            background-color: #f9f9f9;
            color: #666;
            font-style: italic;
        """)
        
        if hasattr(self, 'displayed_image'):
            del self.displayed_image
        self.current_image_path = None
        
        self.tags = []
        self.tag_list_widget.clear()
        self.tag_input.clear()
        
        # Switch back to upload view but don't trigger show_existing_items
        self.upload_new_radio.setChecked(True)
        self.stacked_layout.setCurrentIndex(0)

    def clear_search(self):
        self.search_input.clear()
        self.show_existing_items()

    def show_existing_items(self):
        # Clear the existing layout
        while self.existing_list_layout.count():
            child = self.existing_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        search_term = self.search_input.text().strip().lower()
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            if search_term:
                cursor.execute("""
                    SELECT image_path, tags, date_reported 
                    FROM items 
                    WHERE item_type=? AND tags LIKE ?
                    ORDER BY date_reported DESC
                """, (self.item_type, f"%{search_term}%"))
            else:
                cursor.execute("""
                    SELECT image_path, tags, date_reported 
                    FROM items 
                    WHERE item_type=? 
                    ORDER BY date_reported DESC
                """, (self.item_type,))
                
            items = cursor.fetchall()

            if not items:
                no_items_label = QLabel(f"No reported {self.item_type.lower()} items found.")
                no_items_label.setAlignment(Qt.AlignCenter)
                self.existing_list_layout.addWidget(no_items_label)
            else:
                screen_width = QDesktopWidget().screenGeometry().width()
                image_width = int(screen_width * 0.4)

                for image_path, tags, date_reported in items:
                    item_widget = QWidget()
                    item_layout = QVBoxLayout(item_widget)
                    item_layout.setContentsMargins(10, 10, 10, 10)
                    item_layout.setSpacing(10)

                    # Image display
                    try:
                        if os.path.exists(image_path):
                            pixmap = QPixmap(image_path).scaledToWidth(image_width, Qt.SmoothTransformation)
                            image_label = QLabel()
                            image_label.setPixmap(pixmap)
                            image_label.setAlignment(Qt.AlignCenter)
                            item_layout.addWidget(image_label)
                        else:
                            error_label = QLabel("Image not found")
                            error_label.setAlignment(Qt.AlignCenter)
                            item_layout.addWidget(error_label)
                    except Exception as e:
                        error_label = QLabel(f"Error loading image: {str(e)}")
                        error_label.setAlignment(Qt.AlignCenter)
                        item_layout.addWidget(error_label)

                    # Tags and date
                    details_widget = QWidget()
                    details_layout = QVBoxLayout(details_widget)
                    details_layout.setContentsMargins(5, 5, 5, 5)
                    details_layout.setSpacing(5)

                    if tags:
                        tags_label = QLabel(f"<b>Tags:</b> {tags}")
                        tags_label.setWordWrap(True)
                        details_layout.addWidget(tags_label)

                    date_label = QLabel(f"<small>Reported on: {date_reported}</small>")
                    date_label.setStyleSheet("color: #666;")
                    details_layout.addWidget(date_label)

                    item_layout.addWidget(details_widget)
                    self.existing_list_layout.addWidget(item_widget)

                self.existing_list_layout.addStretch()
                
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, 
                "Database Error", 
                f"Could not load items:\n\n{str(e)}"
            )
        finally:
            if conn:
                conn.close()

        self.stacked_layout.setCurrentIndex(1)

app = QApplication(sys.argv)
app.setStyle("Fusion")

# Set application font
font = QFont()
font.setFamily("Arial")
font.setPointSize(10)
app.setFont(font)

main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())
