import sys
import os
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QLineEdit,
                             QMessageBox, QTabWidget, QGridLayout,
                             QStackedLayout, QRadioButton, QScrollArea,
                             QDesktopWidget, QComboBox)
from PyQt5.QtGui import QPixmap, QFont
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
            QComboBox {
                padding: 6px;
                font-size: 13px;
            }
            QScrollArea {
                border: none;
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
                    location TEXT,
                    area TEXT,
                    building TEXT,
                    floor TEXT,
                    specific_location TEXT,
                    date_reported TEXT DEFAULT CURRENT_TIMESTAMP
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

        # Main scroll area for the entire tab
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget for scroll area
        self.container = QWidget()
        self.main_scroll.setWidget(self.container)
        
        # Main layout for container
        self.main_layout = QVBoxLayout(self.container)
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

        # Upload UI - now in its own scrollable area
        self.upload_scroll = QScrollArea()
        self.upload_scroll.setWidgetResizable(True)
        self.upload_widget = QWidget()
        self.upload_scroll.setWidget(self.upload_widget)
        
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

        # Location Information
        self.upload_layout.addWidget(QLabel("Location Details:"), 3, 0, 1, 2)
        
        # Area (University/Hostel)
        self.upload_layout.addWidget(QLabel("Area:"), 4, 0)
        self.area_combo = QComboBox()
        self.area_combo.addItems(["University", "Hostel"])
        self.area_combo.currentIndexChanged.connect(self.update_building_options)
        self.upload_layout.addWidget(self.area_combo, 4, 1)
        
        # Building
        self.upload_layout.addWidget(QLabel("Building:"), 5, 0)
        self.building_combo = QComboBox()
        self.building_combo.currentIndexChanged.connect(self.update_floor_options)
        self.upload_layout.addWidget(self.building_combo, 5, 1)
        
        # Floor
        self.upload_layout.addWidget(QLabel("Floor:"), 6, 0)
        self.floor_combo = QComboBox()
        self.upload_layout.addWidget(self.floor_combo, 6, 1)
        
        # Specific Location
        self.upload_layout.addWidget(QLabel("Specific Location:"), 7, 0)
        self.specific_location_input = QLineEdit()
        self.specific_location_input.setPlaceholderText("e.g., Room 205, Near reception")
        self.upload_layout.addWidget(self.specific_location_input, 7, 1)

        # Initialize location dropdowns
        self.update_building_options()
        self.update_floor_options()

        # Buttons
        self.bottom_buttons_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit Report")
        self.submit_button.clicked.connect(self.submit_data)
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.reset_form)
        
        self.bottom_buttons_layout.addWidget(self.submit_button)
        self.bottom_buttons_layout.addWidget(self.clear_button)
        self.bottom_buttons_layout.addStretch()
        self.upload_layout.addLayout(self.bottom_buttons_layout, 11, 0, 1, 2)

        self.stacked_layout.addWidget(self.upload_scroll)

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
        self.search_input.setPlaceholderText("Search by tags or location...")
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

        # Set the main scroll as the layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.main_scroll)
        layout.setContentsMargins(0, 0, 0, 0)

        self.current_image_path = None
        self.displayed_image = None
        self.tags = []

    def update_building_options(self):
        self.building_combo.clear()
        area = self.area_combo.currentText()
        
        if area == "University":
            self.building_combo.addItems(["Dome building", "AB1 building", "AB2 building", "AB3 building", "Grand stairs"])
        elif area == "Hostel":
            self.building_combo.addItems(["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B10", 
                                        "G1", "G2", "G3", "G4", "G5", "G6", "G7",
                                        "Bluedove mess", "Quess mess"])
        
        self.update_floor_options()

    def update_floor_options(self):
        self.floor_combo.clear()
        area = self.area_combo.currentText()
        building = self.building_combo.currentText()
        
        if area == "University":
            if building == "Grand stairs":
                self.floor_combo.addItems(["First floor", "Second floor"])
            elif building == "Dome building":
                self.floor_combo.addItems(["Ground floor", "1st floor", "2nd floor", "3rd floor", "4th floor"])
            elif building in ["AB1 building", "AB2 building", "AB3 building"]:
                self.floor_combo.addItems(["1st floor", "2nd floor", "3rd floor"])
                self.floor_combo.setEnabled(True)
            else:  # Other university buildings
                self.floor_combo.addItems(["Ground floor", "1st floor", "2nd floor", "3rd floor"])
        elif area == "Hostel":
            if building in ["Bluedove mess", "Quess mess"]:
                self.floor_combo.addItems(["Ground floor", "First floor"])
                self.floor_combo.setEnabled(True)
            else:
                # For regular hostels, no floor selection needed
                self.floor_combo.addItem("Not applicable")
                self.floor_combo.setEnabled(False)

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
            # Load the image directly as pixmap for better performance
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                raise ValueError("Invalid image file")
                
            # Scale the pixmap while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_display_width, 
                self.image_display_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: transparent;")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")
            self.current_image_path = None
            self.image_label.setText("Failed to load image")
            self.image_label.setStyleSheet("""
                border: 2px dashed #ccc; 
                background-color: #f9f9f9;
                color: #666;
                font-style: italic;
            """)

    def submit_data(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please select an image to report.")
            return

        area = self.area_combo.currentText().strip()
        building = self.building_combo.currentText().strip()
        floor = self.floor_combo.currentText().strip()
        specific_location = self.specific_location_input.text().strip()
        tags = image_identification(self.current_image_path)
        
        if not area or not building or not specific_location:
            QMessageBox.warning(self, "Warning", "Please provide complete location information.")
            return
            
        if area == "Hostel" and building in ["Bluedove mess", "Quess mess"] and not floor:
            QMessageBox.warning(self, "Warning", "Please select a floor for the mess.")
            return
            
        location = f"{area}, {building}"
        if floor != "Not applicable":
            location += f", {floor}"
        location += f", {specific_location}"

        reply = QMessageBox.question(
            self, 
            "Confirm Submission",
            "Are you sure you want to submit this item?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        # Generate unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(self.current_image_path)[1]
        new_filename = f"{self.item_type.lower()}_{timestamp}{file_ext}"
        save_path = os.path.join(self.save_directory, new_filename)

        conn = None
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.save_directory, exist_ok=True)
            
            # Copy the image to our storage directory
            shutil.copy2(self.current_image_path, save_path)

            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO items (item_type, image_path, tags, location, area, building, floor, specific_location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.item_type, save_path, ",".join(tags), location, area, building, floor, specific_location))
            conn.commit()

            QMessageBox.information(
                self, 
                "Success", 
                f"{self.item_type} item reported successfully.\n\nLocation: {location}"
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
        
        self.current_image_path = None
        self.area_combo.setCurrentIndex(0)
        self.update_building_options()
        self.specific_location_input.clear()
        
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
                    SELECT image_path, tags, location, date_reported 
                    FROM items 
                    WHERE item_type=? AND (LOWER(tags) LIKE ? OR LOWER(location) LIKE ?)
                    ORDER BY date_reported DESC
                """, (self.item_type, f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("""
                    SELECT image_path, tags, location, date_reported 
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

                for image_path, tags, location, date_reported in items:
                    item_widget = QWidget()
                    item_layout = QVBoxLayout(item_widget)
                    item_layout.setContentsMargins(10, 10, 10, 10)
                    item_layout.setSpacing(10)

                    # Image display
                    try:
                        if os.path.exists(image_path):
                            pixmap = QPixmap(image_path)
                            if not pixmap.isNull():
                                pixmap = pixmap.scaledToWidth(image_width, Qt.SmoothTransformation)
                                image_label = QLabel()
                                image_label.setPixmap(pixmap)
                                image_label.setAlignment(Qt.AlignCenter)
                                item_layout.addWidget(image_label)
                            else:
                                error_label = QLabel("Invalid image file")
                                error_label.setAlignment(Qt.AlignCenter)
                                item_layout.addWidget(error_label)
                        else:
                            error_label = QLabel("Image not found")
                            error_label.setAlignment(Qt.AlignCenter)
                            item_layout.addWidget(error_label)
                    except Exception as e:
                        error_label = QLabel(f"Error loading image: {str(e)}")
                        error_label.setAlignment(Qt.AlignCenter)
                        item_layout.addWidget(error_label)

                    # Tags, location and date
                    details_widget = QWidget()
                    details_layout = QVBoxLayout(details_widget)
                    details_layout.setContentsMargins(5, 5, 5, 5)
                    details_layout.setSpacing(5)

                    if tags:
                        tags_label = QLabel(f"<b>Tags:</b> {tags}")
                        tags_label.setWordWrap(True)
                        details_layout.addWidget(tags_label)

                    location_label = QLabel(f"<b>Location:</b> {location}")
                    location_label.setWordWrap(True)
                    details_layout.addWidget(location_label)

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