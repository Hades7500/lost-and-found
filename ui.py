import sys
import os
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
                             QLineEdit, QListWidget, QListWidgetItem, QComboBox,
                             QMessageBox, QTabWidget, QGridLayout, QSpacerItem,
                             QSizePolicy, QStackedLayout, QRadioButton, QScrollArea,
                             QDesktopWidget)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QSize

DATABASE_FILE = "reported_items.db"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lost and Found Item Tracker")
        self.set_window_size_to_screen()
        self.create_database()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.tab_widget = QTabWidget()

        self.lost_tab = ImageTab("Lost")
        self.found_tab = ImageTab("Found")

        self.tab_widget.addTab(self.lost_tab, "Lost Item")
        self.tab_widget.addTab(self.found_tab, "Found Item")

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.tab_widget)

    def set_window_size_to_screen(self):
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(100, 100, int(screen.width() * 0.8), int(screen.height() * 0.8))

    def create_database(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                image_path TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT
            )
        """)
        conn.commit()
        conn.close()

class ImageTab(QWidget):
    def __init__(self, item_type, save_directory="saved_items"):
        super().__init__()
        self.item_type = item_type
        self.save_directory = os.path.join(save_directory, item_type.lower())
        os.makedirs(self.save_directory, exist_ok=True)

        self.main_layout = QVBoxLayout(self)

        # Option Selection
        self.option_layout = QHBoxLayout()
        self.upload_new_radio = QRadioButton(f"Report New {item_type} Item")
        self.view_existing_radio = QRadioButton(f"View Reported {item_type} Items")
        self.upload_new_radio.setChecked(True)
        self.option_layout.addWidget(self.upload_new_radio)
        self.option_layout.addWidget(self.view_existing_radio)
        self.main_layout.addLayout(self.option_layout)

        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # Upload New Item Widget
        self.upload_widget = QWidget()
        self.upload_layout = QGridLayout(self.upload_widget)
        self.upload_layout.setSpacing(15)
        self.upload_layout.setContentsMargins(20, 20, 20, 20)

        # Image Section
        self.image_label_title = QLabel(f"Image of {item_type} Item:")
        self.image_label_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.upload_layout.addWidget(self.image_label_title, 0, 0, 1, 2)

        screen_width = QDesktopWidget().screenGeometry().width()
        self.image_display_width = int(screen_width * 0.4)
        self.image_display_height = int(self.image_display_width * 0.75)

        self.image_label = QLabel("No image selected")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(self.image_display_width, self.image_display_height)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.upload_layout.addWidget(self.image_label, 1, 0, 1, 2)

        self.upload_button = QPushButton("Select Image")
        self.upload_button.setStyleSheet(self.get_button_style())
        self.upload_layout.addWidget(self.upload_button, 2, 0, 1, 2)
        self.upload_button.clicked.connect(self.upload_image)

        # Category Section
        self.category_label = QLabel("Category:")
        self.category_label.setFont(QFont("Arial", 10))
        self.upload_layout.addWidget(self.category_label, 3, 0)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Select Category")
        self.category_combo.addItems(["Electronics", "Documents", "Personal Items", "Keys", "Clothing", "Jewelry", "Other"])
        self.category_combo.setStyleSheet(self.get_combobox_style())
        self.upload_layout.addWidget(self.category_combo, 3, 1)

        # Tags Section
        self.tag_label = QLabel("Tags:")
        self.tag_label.setFont(QFont("Arial", 10))
        self.upload_layout.addWidget(self.tag_label, 4, 0)

        self.tag_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setStyleSheet(self.get_lineedit_style())
        self.tag_input_layout.addWidget(self.tag_input)

        self.tag_button = QPushButton("Add Tag")
        self.tag_button.setStyleSheet(self.get_add_tag_button_style())
        self.tag_button.clicked.connect(self.add_tag)
        self.tag_input_layout.addWidget(self.tag_button)

        self.upload_layout.addLayout(self.tag_input_layout, 4, 1)

        self.tag_list_label = QLabel("Added Tags:")
        self.tag_list_label.setFont(QFont("Arial", 10))
        self.upload_layout.addWidget(self.tag_list_label, 5, 0, 1, 2)

        self.tag_list_widget = QListWidget()
        self.tag_list_widget.setStyleSheet(self.get_listwidget_style())
        self.upload_layout.addWidget(self.tag_list_widget, 6, 0, 1, 2)

        # Bottom Buttons
        self.bottom_buttons_layout = QHBoxLayout()
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet(self.get_submit_button_style())
        self.submit_button.setFixedWidth(120)
        self.bottom_buttons_layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit_data)
        
        self.bottom_buttons_layout.addSpacing(20)
        
        self.delete_tag_button = QPushButton("Delete Tag")
        self.delete_tag_button.setStyleSheet(self.get_delete_tag_button_style())
        self.delete_tag_button.setFixedWidth(120)
        self.bottom_buttons_layout.addWidget(self.delete_tag_button)
        self.delete_tag_button.clicked.connect(self.delete_selected_tag)
        
        self.bottom_buttons_layout.addStretch()
        
        self.upload_layout.addLayout(self.bottom_buttons_layout, 7, 0, 1, 2)

        self.upload_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 8, 0)
        self.upload_layout.setRowStretch(8, 1)

        self.stacked_layout.addWidget(self.upload_widget)

        # View Existing Items Widget
        self.existing_widget = QWidget()
        self.existing_layout = QVBoxLayout(self.existing_widget)
        self.existing_label = QLabel(f"Reported {item_type} Items:")
        self.existing_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.existing_layout.addWidget(self.existing_label)
        
        self.existing_scroll_area = QScrollArea()
        self.existing_scroll_area.setWidgetResizable(True)
        self.existing_list_widget = QWidget()
        self.existing_list_layout = QVBoxLayout(self.existing_list_widget)
        self.existing_scroll_area.setWidget(self.existing_list_widget)
        self.existing_layout.addWidget(self.existing_scroll_area)
        
        self.stacked_layout.addWidget(self.existing_widget)

        # Initial State
        self.upload_new_radio.toggled.connect(lambda checked: self.stacked_layout.setCurrentIndex(0) if checked else None)
        self.view_existing_radio.toggled.connect(self.show_existing_items)

        self.current_image_path = None
        self.displayed_image = None
        self.tags = []
        self.selected_category = None
        self.category_combo.currentIndexChanged.connect(self.update_category)

    # Style Methods
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
        """

    def get_add_tag_button_style(self):
        return """
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """

    def get_submit_button_style(self):
        return """
            QPushButton {
                background-color: #008CBA;
                color: white;
                border: none;
                padding: 8px 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #005f73; }
        """

    def get_delete_tag_button_style(self):
        return """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #a71d2a; }
        """

    def get_combobox_style(self):
        return "padding: 8px; border: 1px solid #ccc; border-radius: 3px;"

    def get_lineedit_style(self):
        return "padding: 8px; border: 1px solid #ccc; border-radius: 3px;"

    def get_listwidget_style(self):
        return "border: 1px solid #ccc; border-radius: 3px; padding: 5px;"

    # Functionality Methods
    def upload_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Image", "",
                                                  "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.current_image_path = file_path
            try:
                image = QImage(file_path)
                if image.isNull():
                    QMessageBox.warning(self, "Error", "Could not load the selected image.")
                    return
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(
                    self.image_display_width, 
                    self.image_display_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.displayed_image = scaled_pixmap
                self.image_label.setPixmap(self.displayed_image)
                self.image_label.setAlignment(Qt.AlignCenter)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while loading the image: {e}")
                return

    def update_category(self, index):
        self.selected_category = self.category_combo.currentText() if index > 0 else None

    def add_tag(self):
        tag_text = self.tag_input.text().strip()
        if tag_text and tag_text not in self.tags:
            self.tags.append(tag_text)
            self.tag_list_widget.addItem(QListWidgetItem(tag_text))
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

        if not self.selected_category:
            QMessageBox.warning(self, "Warning", "Please select a category for the reported item.")
            return

        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        ext = os.path.splitext(self.current_image_path)[1]
        new_filename = f"{base_name}_{self.item_type.lower()}_{self.selected_category}{ext}"
        save_path = os.path.join(self.save_directory, new_filename)

        try:
            import shutil
            shutil.copy2(self.current_image_path, save_path)

            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO items (item_type, image_path, category, tags)
                VALUES (?, ?, ?, ?)
            """, (self.item_type, save_path, self.selected_category, ",".join(self.tags)))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", f"Item reported and saved to database.\nImage saved to: {save_path}")
            self.reset_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save item: {e}")

    def reset_form(self):
        self.current_image_path = None
        self.displayed_image = None
        self.image_label.setText("No image selected")
        self.category_combo.setCurrentIndex(0)
        self.tags = []
        self.tag_list_widget.clear()
        self.upload_new_radio.setChecked(True)
        self.stacked_layout.setCurrentIndex(0)
        self.show_existing_items()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_existing_items(self):
        self.clear_layout(self.existing_list_layout)
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT image_path, category, tags FROM items WHERE item_type=?", (self.item_type,))
        items = cursor.fetchall()
        conn.close()

        if not items:
            no_items_label = QLabel(f"No reported {self.item_type.lower()} items yet.")
            no_items_label.setAlignment(Qt.AlignCenter)
            self.existing_list_layout.addWidget(no_items_label)
        else:
            screen_width = QDesktopWidget().screenGeometry().width()
            image_width = int(screen_width * 0.4)
            
            for image_path, category, tags in items:
                item_widget = QWidget()
                item_layout = QVBoxLayout(item_widget)
                item_layout.setAlignment(Qt.AlignCenter)
                item_layout.setSpacing(10)

                try:
                    pixmap = QPixmap(image_path).scaledToWidth(image_width, Qt.SmoothTransformation)
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    item_layout.addWidget(image_label)
                except:
                    error_label = QLabel("Image not found or could not be loaded")
                    error_label.setAlignment(Qt.AlignCenter)
                    item_layout.addWidget(error_label)

                details_label = QLabel(f"Category: {category}\nTags: {tags if tags else 'None'}")
                details_label.setFont(QFont("Arial", 10))
                details_label.setAlignment(Qt.AlignCenter)
                item_layout.addWidget(details_label)

                self.existing_list_layout.addWidget(item_widget)

        self.stacked_layout.setCurrentIndex(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())