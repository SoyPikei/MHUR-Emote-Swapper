import sys
import os
import subprocess
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path
import shutil
import re

# --- Datos Maestro ---
CHARACTERS = [
    ("001", "Izuku"), ("002", "Bakugo"), ("003", "Ochako"), ("004", "Shoto"),
    ("005", "Iida"), ("006", "Froppy"), ("007", "Denki"), ("008", "Kirishima"),
    ("009", "Jiro"), ("010", "Momo"), ("011", "Tokoyami"), ("012", "All Might"),
    ("013", "Aizawa"), ("014", "Gran Torino"), ("015", "Shigaraki"), ("016", "All for One"),
    ("017", "Dabi"), ("018", "Toga"), ("019", "Stain"), ("020", "Muscular"),
    ("022", "Inasa"), ("023", "Endeavor"), ("024", "Mirio"), ("025", "Nejire"),
    ("026", "Tamaki"), ("027", "Mina"), ("028", "Mineta"), ("029", "Camie"),
    ("030", "Seiji"), ("031", "Nighteye"), ("032", "Gang Orca"), ("033", "FatGum"),
    ("034", "Overhaul"), ("036", "Rappa"), ("037", "Twice"),
    ("038", "Compress"), ("043", "Hawks"), ("044", "Gentle"), ("045", "Mei Hatsume"),
    ("046", "Kendo"), ("047", "Tetsutetsu"), ("048", "Nomu"), ("093", "La Brava"),
    ("100", "Mt. Lady"), ("101", "Cementoss"), ("102", "Ibara"), ("103", "Kurogiri"),
    ("104", "Monoma"), ("105", "Shinso"), ("109", "Present Mic"), ("110", "Sero"),
    ("111", "Mirko"), ("112", "Hood"), ("113", "Midnight"), ("115", "Lady Nagant"),
    ("114", "Star and Stripes"), ("200", "Armored All Might"), ("201", "Young AFO"), ("202", "OFADeku")
]

EMOTE_SLOTS = [
    ("em000_EmotionAct000", "Greeting"),
    ("em001_EmotionAct001", "Roger That"),
    ("em002_EmotionAct002", "No Can Do"),
    ("em003_EmotionAct003", "Clap Your Hands"),
    ("em004_EmotionAct004", "Bow"),
    ("em005_EmotionAct005", "At Attention"),
    ("em006_EmotionAct006", "Taunt"),
    ("em007_EmotionAct007", "Thats The Point")
]
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class CharacterButton(QtWidgets.QToolButton):
    def __init__(self, char_id, name, parent=None):
        super().__init__(parent)
        self.char_id = char_id
        self.setText(name)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QtCore.QSize(128, 128)) 
        img_path = resource_path(f"imgs/{char_id}.png")
        self.setIcon(QtGui.QIcon(img_path if os.path.exists(img_path) else resource_path("imgs/default.png")))

class EmoteSwapperUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MHUR Emote Swapper")
        self.setFixedSize(900, 700)
        
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self.original_pak_path = ""
        self.target_pj_id = ""

        self.cleanup_assets()

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_step1()
        self.setup_step2()
        # El paso 3 se genera dinámicamente en go_to_emotes
        self.page_emotes = QtWidgets.QWidget()
        self.stack.addWidget(self.page_emotes)

    def cleanup_assets(self):
        assets_path = Path("./assets")
        if assets_path.exists():
            try: shutil.rmtree(assets_path)
            except: pass

    def reset_to_start(self, message=None, is_error=False):
        self.cleanup_assets()
        if message:
            if is_error: QtWidgets.QMessageBox.critical(self, "Error", message)
            else: QtWidgets.QMessageBox.information(self, "Éxito", message)
        self.stack.setCurrentIndex(0)

    def setup_step1(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        btn = QtWidgets.QPushButton("Select and Extract mod .pak")
        btn.setMinimumHeight(100)
        btn.clicked.connect(self.run_extraction)
        layout.addStretch(); layout.addWidget(btn, alignment=QtCore.Qt.AlignCenter); layout.addStretch()
        self.stack.addWidget(page)

    def setup_step2(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(QtWidgets.QLabel("<h2>Select the Destination Character</h2>"))
        scroll = QtWidgets.QScrollArea()
        container = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(container)
        for i, (cid, name) in enumerate(CHARACTERS):
            btn = CharacterButton(cid, name)
            btn.clicked.connect(lambda checked=False, c=cid: self.go_to_emotes(c))
            grid.addWidget(btn, i // 5, i % 5)
        scroll.setWidget(container); scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        self.stack.addWidget(page)

    def go_to_emotes(self, cid):
        self.target_pj_id = cid
        
        char_name = next((name for id, name in CHARACTERS if id == cid), cid)
        
        if self.page_emotes.layout():
            QtWidgets.QWidget().setLayout(self.page_emotes.layout())

        layout = QtWidgets.QVBoxLayout(self.page_emotes)
        layout.setContentsMargins(40, 40, 40, 40)
        

        title = QtWidgets.QLabel(f"<h2>Select slot for {char_name}</h2>")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grid de emotes centrado
        grid_container = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(grid_container)
        grid.setSpacing(20) 

        restricted = []
        if cid == "011": # Tokoyami
            restricted = ["No Can Do", "Bow"]
        elif cid == "202": # Deku (OFA)
            restricted = ["Greeting", "Roger That", "No Can Do", "Bow", "Thats The Point"]
        elif cid == "114": # Star and Stripes
            restricted = ["No Can Do", "Bow", "Thats The Point"]

        visible_emotes = [e for e in EMOTE_SLOTS if e[1] not in restricted]

        for i, (eid, ename) in enumerate(visible_emotes):
            btn = QtWidgets.QToolButton()
            btn.setText(ename)
            btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            btn.setIconSize(QtCore.QSize(140, 140)) 
            btn.setFixedSize(160, 190)

            emote_img_path = resource_path(f"imgs/{eid.split('_')[0]}.png")
            if os.path.exists(emote_img_path):
                btn.setIcon(QtGui.QIcon(emote_img_path))
            btn.clicked.connect(lambda checked=False, e=eid: self.process_mod(e))
            grid.addWidget(btn, i // 4, i % 4, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(grid_container, alignment=QtCore.Qt.AlignCenter)
        layout.addStretch() # Empuja todo hacia el centro vertical
        self.stack.setCurrentIndex(2)
        
    def run_extraction(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select mod PAK", "", "PAK (*.pak)")
        if path:
            self.original_pak_path = path
            self.cleanup_assets()
            if self.unpack_logic(path, Path("./assets")):
                self.stack.setCurrentIndex(1)
            else:
                self.reset_to_start("Extraction error.", True)

    def unpack_logic(self, pak_path, output_dir):
        exe = resource_path(os.path.join("dependencies", "unrealpak", "UnrealPak.exe"))
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [exe, str(Path(pak_path).absolute()), "-Extract", str(output_dir.absolute())]
        try:
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except: return False

    def process_mod(self, emote_id):
        assets_path = Path("./assets").absolute()
        # Regex para buscar ChXXX solo si le sigue /Animation/
        ch_anim_pattern = re.compile(rb'/Ch(\d{3})/Animation/')
        emote_pattern = re.compile(rb'em\d{3}_EmotionAct\d{3}')
        
        try:
            # 1. Renombrar Carpetas Físicas
            for folder in list(assets_path.rglob("Ch*")):
                if folder.is_dir() and re.match(r'Ch\d{3}$', folder.name):
                    if folder.name != "Ch000":
                        new_folder = folder.parent / f"Ch{self.target_pj_id}"
                        if not new_folder.exists(): os.rename(folder, new_folder)

            # 2. Procesar carpeta em/
            for file_path in list(assets_path.rglob("*")):
                if not file_path.name.endswith((".uasset", ".uexp")): continue
                if "/Animation/em/" not in str(file_path).replace("\\", "/"): continue
                if "SK_Ch" in file_path.name: continue

                current_name = file_path.name
                is_standard = re.search(r'em\d{3}_EmotionAct\d{3}', current_name)
                
                work_path = file_path
                if is_standard:
                    ext = file_path.suffix
                    is_montage = "_Montage" in current_name
                    new_filename = f"{emote_id}{'_Montage' if is_montage else ''}{ext}"
                    work_path = file_path.parent / new_filename
                    if file_path != work_path:
                        if work_path.exists(): os.remove(work_path)
                        os.rename(file_path, work_path)

                with open(work_path, 'rb') as f: 
                    data = bytearray(f.read())

                pj_bytes = self.target_pj_id.encode()
                for m in ch_anim_pattern.finditer(data):
                    data[m.start(1):m.end(1)] = pj_bytes

                if is_standard:
                    new_em_bytes = emote_id.encode()
                    for m in emote_pattern.finditer(data):
                        if len(m.group()) == len(new_em_bytes):
                            data[m.start():m.end()] = new_em_bytes

                with open(work_path, 'wb') as f: 
                    f.write(data)

            save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save PAK", os.path.basename(self.original_pak_path), "PAK (*.pak)")
            if save_path and self.repack_logic(assets_path, save_path):
                self.reset_to_start("Swap Done!")
            else: self.reset_to_start()

        except Exception as e: self.reset_to_start(f"Error: {str(e)}", True)

    def repack_logic(self, input_folder, output_pak):
        exe = resource_path(os.path.join("dependencies", "unrealpak", "UnrealPak.exe"))
        resp_file = Path("repack_list.txt")
        try:
            with open(resp_file, 'w', encoding='utf-8') as f:
                for root, _, files in os.walk(input_folder):
                    for file in files:
                        full = Path(root) / file
                        rel = full.relative_to(input_folder)
                        f.write(f'"{full.absolute()}" "../../../HerovsGame/Content/{str(rel).replace("\\", "/")}"\n')
            subprocess.run([exe, str(Path(output_pak).absolute()), f"-create={resp_file.absolute()}", "-compress"], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except: return False
        finally: 
            if resp_file.exists(): os.remove(resp_file)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = EmoteSwapperUI(); window.show()
    sys.exit(app.exec())