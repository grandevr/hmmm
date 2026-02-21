import sys
import os
import json
import shutil
import zipfile
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QDialog, QLabel, QLineEdit, QFileDialog, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QIcon, QPixmap

MODS_DIR = "mods"
CONFIG_FILE = "mods.json"
STATE_FILE = "state.json"
BACKUP_DIR = "backup"
ASSETS_DIR = "assets"
icon_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), ASSETS_DIR, "icon.png")
icon_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), ASSETS_DIR, "icon.ico")

def get_game_data_dir():
    if os.name == "nt":
        return os.path.join(os.environ["LOCALAPPDATA"], "HotlineMiami2")
    return os.path.expanduser("~/.local/share/HotlineMiami2")

GAME_DATA_DIR = get_game_data_dir()
PATCHWAD_PATH = os.path.join(GAME_DATA_DIR, "patchwad.wad")
PATCHWAD_MODS_DIR = os.path.join(GAME_DATA_DIR, "mods")


class ModManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HMMM - Vanilla")
        self.resize(900, 500)
        self.setWindowIcon(QIcon(icon_png))

        os.makedirs(MODS_DIR, exist_ok=True)
        os.makedirs(PATCHWAD_MODS_DIR, exist_ok=True)

        self.active_mod = None
        self.game_music_path = None
        self.last_folder = os.getcwd()

        self.load_state()

        if not self.game_music_path:
            self.show_welcome()
        else:
            self.init_main_ui()

    # -------------------- FILE PICKER --------------------
    def qt_open_file(self, title, filter_str):
        file_path, _ = QFileDialog.getOpenFileName(self, title, self.last_folder, filter_str)
        if file_path:
            self.last_folder = os.path.dirname(file_path)
        return file_path or None

    def qt_open_files(self, title, filter_str):
        files, _ = QFileDialog.getOpenFileNames(self, title, self.last_folder, filter_str)
        if files:
            self.last_folder = os.path.dirname(files[0])
        return files or []

    # -------------------- WELCOME --------------------
    def show_welcome(self):
        self.welcome = QDialog(self)
        self.welcome.setWindowTitle("You have one new message! *BEEP*")
        self.welcome.setModal(True)
        self.welcome.resize(700, 300)

        # ---------------- Layout ----------------
        main_layout = QHBoxLayout(self.welcome)

        phone_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "phone.png")
        phone_label = QLabel()
        pixmap = QPixmap(phone_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        phone_label.setPixmap(pixmap)
        phone_label.setAlignment(Qt.AlignTop)
        main_layout.addWidget(phone_label)

        text_layout = QVBoxLayout()
        main_font = QFont("Arial", 14)
        italic_font = QFont("Arial", 12)
        italic_font.setItalic(True)

        main_text = (
            "Hi, it's Homer, the new workshop manager.\n\n"
            "I was told you're the one to speak to about client folders? Some joker hid our music vinyl there, and this place will need a lively ambience...\n\n"
            "I heard the files are kept somewhere in the common area, past the steam room. But you'll know best. Good luck. *CLICK*\n\n"
        )
        last_line = "(Select hlm2_music_desktop.wad in your HM2 installation folder, typically in /Steam/steamapps/common/Hotline Miami 2/)"

        main_label = QLabel(main_text)
        main_label.setFont(main_font)
        main_label.setWordWrap(True)
        main_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        last_label = QLabel(last_line)
        last_label.setFont(italic_font)
        last_label.setWordWrap(True)
        last_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        text_layout.addWidget(main_label)
        text_layout.addWidget(last_label)

        btn = QPushButton("Select Game Folder")
        btn.clicked.connect(self.on_welcome_select)
        text_layout.addWidget(btn)

        main_layout.addLayout(text_layout)

        self.welcome.exec()

    def on_welcome_select(self):
        if self.select_game_file():
            self.welcome.accept()
            self.init_main_ui()

    def select_game_file(self):
        file_path = self.qt_open_file("Select hlm2_music_desktop.wad", "hlm2_music_desktop.wad")
        if not file_path:
            return False

        folder = os.path.dirname(file_path)
        data_wad = os.path.join(folder, "hlm2_data_desktop.wad")
        if not os.path.exists(data_wad):
            QMessageBox.critical(
                self,
                "Error",
                "This doesn't seem like the correct game folder.\n"
                "Make sure you aren't just selecting a modded music WAD."
            )
            return False

        self.game_music_path = file_path
        self.save_state()
        return True

    # -------------------- MAIN UI --------------------
    def init_main_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Active", "Mod Name", "Patch WAD(s)", "Music WAD"])
        self.tree.setSortingEnabled(True)
        self.tree.sortItems(1, Qt.AscendingOrder)

        self.tree.setStyleSheet("""
            QTreeWidget::item { height: 50px; }
            QTreeWidget::item:selected { background-color: #444444; color: #ffffff; }
            QTreeWidget { gridline-color: #999999; font-size: 10pt; }
        """)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)  # remove expand/collapse icons

        self.tree.itemDoubleClicked.connect(self.on_row_activated)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        install_btn = QPushButton("Install Mod")
        install_btn.clicked.connect(self.on_install_mod)
        restore_btn = QPushButton("Restore Vanilla")
        restore_btn.clicked.connect(self.on_restore_vanilla)
        import_btn = QPushButton("Import Mod Package")
        import_btn.clicked.connect(self.on_import_mod_package)
        btn_layout.addWidget(install_btn)
        btn_layout.addWidget(restore_btn)
        btn_layout.addWidget(import_btn)
        layout.addLayout(btn_layout)

        self.load_mods()
        self.update_active_column()
        self.refresh_title()
        self.show()

    # -------------------- ADD ROW --------------------
    def add_mod_row(self, mod_name, patch_files, music_file):
        patch_text = "\n".join(os.path.basename(p) for p in patch_files)
        music_text = os.path.basename(music_file) if music_file else ""

        item = QTreeWidgetItem(["", mod_name, patch_text, music_text])
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        # store full paths for internal use
        item.setData(2, Qt.UserRole, ";".join(patch_files))
        item.setData(3, Qt.UserRole, music_file)

        # fonts
        font_name = item.font(1)
        font_name.setPointSize(11)
        font_name.setBold(True)
        item.setFont(1, font_name)
        font_active = item.font(0)
        font_active.setPointSize(16)
        item.setFont(0, font_active)

        # add to tree
        self.tree.addTopLevelItem(item)
        self.update_active_column()


    # -------------------- INSTALL MOD --------------------
    def on_install_mod(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Install Mod")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Mod Name:"))
        mod_name_input = QLineEdit("NewMod")
        layout.addWidget(mod_name_input)

        layout.addWidget(QLabel("Selected Files:"))
        file_list = QTreeWidget()
        file_list.setColumnCount(1)
        file_list.setHeaderLabels(["File"])
        layout.addWidget(file_list)
        selected_files = []

        def refresh_list():
            file_list.clear()
            for f in selected_files:
                file_list.addTopLevelItem(QTreeWidgetItem([os.path.basename(f)]))

        def add_files():
            nonlocal selected_files
            files = self.qt_open_files("Add WAD Files", "WAD Files (*.wad *.patchwad)")
            for f in files:
                if f.lower().endswith(".wad") and any(x.lower().endswith(".wad") for x in selected_files):
                    QMessageBox.warning(self, "Error", "Only one music .wad allowed.")
                    continue
                selected_files.append(f)
            refresh_list()

        def remove_selected():
            for item_sel in file_list.selectedItems():
                name = item_sel.text(0)
                for f in selected_files[:]:
                    if os.path.basename(f) == name:
                        selected_files.remove(f)
            refresh_list()

        add_btn = QPushButton("Add Files")
        remove_btn = QPushButton("Remove Selected")
        layout.addWidget(add_btn)
        layout.addWidget(remove_btn)
        add_btn.clicked.connect(add_files)
        remove_btn.clicked.connect(remove_selected)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        cancel_btn.clicked.connect(dialog.reject)

        def on_ok():
            mod_name = mod_name_input.text().strip()
            if not mod_name:
                QMessageBox.warning(self, "Error", "Mod name cannot be empty.")
                return

            music_wads = [f for f in selected_files if f.lower().endswith(".wad")]
            if len(music_wads) > 1:
                QMessageBox.warning(self, "Error", "Only one music .wad allowed.")
                return

            mod_folder = os.path.join(MODS_DIR, mod_name)
            os.makedirs(mod_folder, exist_ok=True)

            patch_wads = [f for f in selected_files if f.lower().endswith(".patchwad")]
            copied_patch_files = [self._copy_wad(p, mod_folder) for p in patch_wads]
            copied_music_file = self._copy_wad(music_wads[0], mod_folder) if music_wads else ""

            self.add_mod_row(mod_name, copied_patch_files, copied_music_file)
            self.save_mods()
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        dialog.exec()

    # -------------------- EDIT MOD --------------------
    def on_edit_mod(self, item):
        mod_name = item.text(1)
        mod_folder = os.path.join(MODS_DIR, mod_name)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Mod - {mod_name}")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Mod Name:"))
        name_input = QLineEdit(mod_name)
        layout.addWidget(name_input)

        layout.addWidget(QLabel("Files in Mod:"))
        file_list = QTreeWidget()
        file_list.setColumnCount(1)
        file_list.setHeaderLabels(["File"])
        layout.addWidget(file_list)

        selected_files = [os.path.join(mod_folder, f) for f in os.listdir(mod_folder)]

        def refresh_list():
            file_list.clear()
            for f in selected_files:
                file_list.addTopLevelItem(QTreeWidgetItem([os.path.basename(f)]))

        refresh_list()

        def add_files():
            nonlocal selected_files
            files = self.qt_open_files("Add WAD Files", "WAD Files (*.wad *.patchwad)")
            for f in files:
                if f.lower().endswith(".wad") and any(x.lower().endswith(".wad") for x in selected_files):
                    QMessageBox.warning(self, "Error", "Only one music .wad allowed.")
                    continue
                copied = self._copy_wad(f, mod_folder)
                selected_files.append(copied)
            refresh_list()

        def remove_selected():
            for item_sel in file_list.selectedItems():
                name = item_sel.text(0)
                for f in selected_files[:]:
                    if os.path.basename(f) == name:
                        os.remove(f)
                        selected_files.remove(f)
            refresh_list()

        add_btn = QPushButton("Add Files")
        remove_btn = QPushButton("Remove Selected")
        layout.addWidget(add_btn)
        layout.addWidget(remove_btn)
        add_btn.clicked.connect(add_files)
        remove_btn.clicked.connect(remove_selected)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        cancel_btn.clicked.connect(dialog.reject)

        def save_changes():
            new_name = name_input.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Error", "Mod name cannot be empty.")
                return

            current_folder = os.path.join(MODS_DIR, mod_name)
            new_folder = os.path.join(MODS_DIR, new_name)
            if new_name != mod_name:
                if os.path.exists(new_folder):
                    QMessageBox.warning(self, "Error", "A mod with that name already exists.")
                    return
                os.rename(current_folder, new_folder)
                mod_name_local = new_name
            else:
                mod_name_local = mod_name

            patch_files = [f for f in selected_files if f.lower().endswith(".patchwad")]
            music_files = [f for f in selected_files if f.lower().endswith(".wad")]

            item.setData(2, Qt.UserRole, "; ".join(patch_files))
            item.setData(3, Qt.UserRole, music_files[0] if music_files else "")

            item.setText(1, new_name)
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            self.add_mod_row(new_name, patch_files, music_files[0] if music_files else "")

            if self.active_mod == mod_name:
                self.active_mod = new_name
                self.refresh_title()

            self.save_mods()
            dialog.accept()

        ok_btn.clicked.connect(save_changes)
        dialog.exec()

    # -------------------- DELETE / EXPORT --------------------
    def on_delete_mod(self, item):
        mod_name = item.text(1)
        confirm = QMessageBox.question(self, "Confirm", f"Delete mod '{mod_name}'?")
        if confirm == QMessageBox.Yes:
            if mod_name == self.active_mod:
                self._restore_vanilla_silent()
            shutil.rmtree(os.path.join(MODS_DIR, mod_name), ignore_errors=True)
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            self.save_mods()

    def on_export_mod_package(self, item):
        mod_name = item.text(1)
        mod_folder = os.path.join(MODS_DIR, mod_name)
        save_path = QFileDialog.getSaveFileName(self, "Export Mod Package", f"{mod_name}.zip", "*.zip")[0]
        if not save_path:
            return
        with zipfile.ZipFile(save_path, "w") as zipf:
            for root, _, files in os.walk(mod_folder):
                for f in files:
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, MODS_DIR)
                    zipf.write(fp, arcname)

    # -------------------- IMPORT MOD PACKAGE --------------------
    def on_import_mod_package(self):
        zip_path = self.qt_open_file("Select Mod Package", "*.zip")
        if not zip_path:
            return
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                root_folders = {name.split("/")[0] for name in zipf.namelist() if "/" in name}
                if not root_folders:
                    QMessageBox.warning(self, "Error", "Invalid mod package structure.")
                    return
                mod_name = list(root_folders)[0]
                dest = os.path.join(MODS_DIR, mod_name)
                if os.path.exists(dest):
                    QMessageBox.warning(self, "Error", "Mod already exists.")
                    return
                zipf.extractall(MODS_DIR)

            patch_wads, music_wad = [], ""
            for root, _, files in os.walk(dest):
                for f in files:
                    fp = os.path.join(root, f)
                    if f.endswith(".patchwad"):
                        patch_wads.append(fp)
                    elif f.endswith(".wad"):
                        music_wad = fp

            self.add_mod_row(mod_name, patch_wads, music_wad)
            self.save_mods()
            QMessageBox.information(self, "Success", f"Mod '{mod_name}' installed successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to install mod package:\n{str(e)}")

    # -------------------- CONTEXT MENU --------------------
    def show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        delete_action = QAction("Delete", self)
        export_action = QAction("Export Mod Package", self)
        edit_action.triggered.connect(lambda: self.on_edit_mod(item))
        delete_action.triggered.connect(lambda: self.on_delete_mod(item))
        export_action.triggered.connect(lambda: self.on_export_mod_package(item))
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(export_action)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # -------------------- ACTIVATE --------------------
    def on_row_activated(self, item):
        mod_name = item.text(1)
        patch_wads = item.data(2, Qt.UserRole)
        music_wad = item.data(3, Qt.UserRole)
        patch_list = patch_wads.split("; ") if patch_wads else []
        if self.active_mod == mod_name:
            return
        self._restore_vanilla_silent()
        self.activate_mod(mod_name, patch_list, music_wad)

    def activate_mod(self, mod_name, patch_wads, music_wad):
        self.backup_vanilla()
        for patch in patch_wads:
            if patch and os.path.exists(patch):
                shutil.copy2(patch, PATCHWAD_PATH)
        if music_wad and os.path.exists(music_wad):
            shutil.copy2(music_wad, self.game_music_path)
        self.active_mod = mod_name
        self.update_active_column()
        self.save_state()
        self.refresh_title()

    # -------------------- BACKUP / RESTORE --------------------
    def backup_vanilla(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        music_backup = os.path.join(BACKUP_DIR, "hlm2_music_desktop.wad")
        patch_backup = os.path.join(BACKUP_DIR, "patchwad.wad")
        if self.game_music_path and not os.path.exists(music_backup):
            shutil.copy2(self.game_music_path, music_backup)
        if os.path.exists(PATCHWAD_PATH) and not os.path.exists(patch_backup):
            shutil.copy2(PATCHWAD_PATH, patch_backup)

    def _restore_vanilla_silent(self):
        music_backup = os.path.join(BACKUP_DIR, "hlm2_music_desktop.wad")
        patch_backup = os.path.join(BACKUP_DIR, "patchwad.wad")
        if self.game_music_path and os.path.exists(music_backup):
            shutil.copy2(music_backup, self.game_music_path)
        if os.path.exists(patch_backup):
            shutil.copy2(patch_backup, PATCHWAD_PATH)
        self.active_mod = None
        self.update_active_column()
        self.save_state()
        self.refresh_title()

    def on_restore_vanilla(self):
        confirm = QMessageBox.question(self, "Confirm", "Restore vanilla game files?")
        if confirm == QMessageBox.Yes:
            self._restore_vanilla_silent()

    # -------------------- SAVE / LOAD --------------------
    def save_mods(self):
        data = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            data.append({
                "mod_name": item.text(1),
                "patch_wads": item.data(2, Qt.UserRole),
                "music_wad": item.data(3, Qt.UserRole)
            })
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    def load_mods(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        for mod in data:
            patch_files = mod.get("patch_wads", "").split("; ") if mod.get("patch_wads") else []
            music_file = mod.get("music_wad", "")
            self.add_mod_row(mod.get("mod_name", ""), patch_files, music_file)

    def save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump({
                "active_mod": self.active_mod,
                "game_music_path": self.game_music_path,
                "last_folder": self.last_folder
            }, f)

    def load_state(self):
        if not os.path.exists(STATE_FILE):
            return
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        self.active_mod = state.get("active_mod")
        self.game_music_path = state.get("game_music_path")
        self.last_folder = state.get("last_folder", os.getcwd())

    def refresh_title(self):
        if self.active_mod:
            self.setWindowTitle(f"HMMM - Active: {self.active_mod}")
        else:
            self.setWindowTitle("HMMM - Vanilla")

    def update_active_column(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setText(0, "✅" if item.text(1) == self.active_mod else "")

    def _copy_wad(self, src_path, dest_dir):
        if not src_path:
            return ""
        file_name = os.path.basename(src_path)
        base, ext = os.path.splitext(file_name)
        dest_path = os.path.join(dest_dir, file_name)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
            counter += 1
        shutil.copy2(src_path, dest_path)
        return dest_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModManager()
    window.show()
    sys.exit(app.exec())
