import array
import traceback
from threading import Thread, Lock
import dearpygui.dearpygui as dpg
import numpy as np

from OpenSMA.effects_manager import EffectsManager
from OpenSMA.manager import ConfigManager, ProjectManager
from ui import ui
from pathlib import Path
from cv2_enumerate_cameras import enumerate_cameras
import cv2

class App:
    def __init__(self):
        self.ui = ui(self)
        self.version = "1.0.0"
        self.system_folder = Path.home() / 'Documents' / "DPSoftware" / "OpenSMA"
        self.CM = ConfigManager(self.system_folder / "config.json")
        self.camera_list = []
        self.isopenProject = False
        self.ProMan = None
        self.cap = None
        self.isInitCap = False
        self.preview_size = (673, 380)
        self.frame_lock = Lock()
        self.camera_thread = None
        self.running = False
        self.current_frame = None

    def pre_new_project(self, _, __):
        dpg.show_item("new_project_window")

    def start_camera(self):
        dpg.show_item("dialog_window")
        dpg.hide_item("dialog_window_bclose")
        dpg.set_value("dialog_window_title", "Please wait...")
        dpg.set_value("dialog_window_text", "Starting camera...")
        self.cap = cv2.VideoCapture(self.CM.cameraID)
        dpg.set_value("dialog_window_text", "apply camera settings...")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.CM.cameraResolutionWidth)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.CM.cameraResolutionHeight)
        self.cap.set(cv2.CAP_PROP_FPS, self.CM.cameraFPS)
        #self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.CM.cameraBrightness)
        #self.cap.set(cv2.CAP_PROP_CONTRAST, self.CM.cameraContrast)
        #self.cap.set(cv2.CAP_PROP_SATURATION, self.CM.cameraSaturation)
        #self.cap.set(cv2.CAP_PROP_HUE, self.CM.cameraHue)
        #self.cap.set(cv2.CAP_PROP_GAIN, self.CM.cameraGain)
        #self.cap.set(cv2.CAP_PROP_EXPOSURE, self.CM.cameraExposure)

        dpg.hide_item("dialog_window")
        self.isInitCap = True
        dpg.show_item("capture_window")
        dpg.show_item("dialog_window_bclose")
        self.start_camera_thread()

    def start_camera_thread(self):
        self.running = True
        self.camera_thread = Thread(target=self.camera_capture_loop, daemon=True)
        self.camera_thread.start()

    def stop_camera_thread(self):
        self.running = False
        if self.camera_thread:
            self.camera_thread.join()

    def camera_capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.frame_lock:
                    output_frame = self.effects_manager.node_editor.render(frame.copy())

                    self.current_frame = output_frame
        self.cap.release()

    def capture(self, _, __):
        if not self.isInitCap:
            return

        if self.ProMan is None:
            return

        frame = self.current_frame.copy() if self.current_frame is not None else None

        if frame is not None:
            frame_file = self.ProMan.frames_folder / f"{len(list(self.ProMan.frames_folder.glob('*.png'))):06d}.png"
            cv2.imwrite(str(frame_file), frame)  # Fix: Convert Path to string

    def render_capture(self):
        if not (self.isInitCap and self.isopenProject):
            return

        with self.frame_lock:
            frame = self.current_frame.copy() if self.current_frame is not None else None

        if frame is not None:
            display_frame = cv2.resize(frame, self.preview_size)
            # Convert BGR to RGB for Dear PyGui
            data = np.flip(display_frame, 2).ravel()  # Flatten the data
            data = np.asfarray(data, dtype='f')  # Convert to 32-bit floats
            texture_data = np.true_divide(data, 255.0)  # Normalize to [0, 1]
            dpg.set_value("texture_preview", texture_data)

    def create_project(self, _, __):
        project_name = dpg.get_value("new_project_name")
        project_fps = dpg.get_value("new_project_fps")
        project_width = dpg.get_value("new_project_width")
        project_height = dpg.get_value("new_project_height")
        project_location = dpg.get_value("new_project_location")

        self.ProMan = ProjectManager(
            project_name,
            project_fps,
            project_width,
            project_height,
            project_location
        )

        # Create the project
        try:
            self.ProMan.create_project()
            self.isopenProject = True
            Thread(target=self.start_camera).start()
        except Exception as e:
            dpg.show_item("dialog_window")
            dpg.set_value("dialog_window_title", "can't create project")
            dpg.set_value("dialog_window_text", str(traceback.format_exc()))

    def open_project(self, _, data):
        try:
            self.ProMan = ProjectManager.load_project(data["file_path_name"])
            self.isopenProject = True
            Thread(target=self.start_camera).start()
        except Exception as e:
            dpg.show_item("dialog_window")
            dpg.set_value("dialog_window_title", "can't create project")
            dpg.set_value("dialog_window_text", str(traceback.format_exc()))

    def close_project(self, _, __):
        if not self.isopenProject:
            return

        if self.isInitCap:
            self.stop_camera_thread()

        dpg.hide_item("capture_window")

        self.ProMan = None
        self.cap = None
        self.isopenProject = False
        self.isInitCap = False

    def init(self):
        dpg.create_context()
        dpg.create_viewport(title='OpenSMA', width=1280, height=720, large_icon="icon.ico")  # set viewport window
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.render_dearpygui_frame()
        # -------------- add code here --------------

        with dpg.texture_registry():
            width, height, channels, data = dpg.load_image("logo.png")

            dpg.add_static_texture(width=width, height=height, default_value=data, tag="app_logo_background")

        with dpg.window(tag="splash_window", no_move=True, no_close=True, no_title_bar=True, no_resize=True):
            dpg.add_image("app_logo_background")
            dpg.add_text("Please wait...")
            dpg.add_text("Initialization...", tag="starting_status")
        dpg.render_dearpygui_frame()

        dpg.set_value("starting_status", "Creating System Folder"); dpg.render_dearpygui_frame()

        self.system_folder.mkdir(parents=True, exist_ok=True)

        if (self.system_folder / "config.json").exists():
            dpg.set_value("starting_status", "Loading config file")
            self.CM.load()
        else:
            dpg.set_value("starting_status", "Creating config file")
            self.CM.save()

        dpg.set_value("starting_status", "Scanning camera"); dpg.render_dearpygui_frame()

        for camera_info in enumerate_cameras(cv2.CAP_ANY):
            self.camera_list.append([camera_info.index, camera_info.name])

        dpg.set_value("starting_status", "Creating texture"); dpg.render_dearpygui_frame()
        texture_data = []
        for i in range(0, self.preview_size[0] * self.preview_size[1]):
            texture_data.append(255 / 255)
            texture_data.append(0)
            texture_data.append(255 / 255)

        raw_data = array.array("f", texture_data)

        with dpg.texture_registry():
            dpg.add_raw_texture(self.preview_size[0], self.preview_size[1], raw_data, format=dpg.mvFormat_Float_rgb, tag="texture_preview")
            dpg.add_raw_texture(self.preview_size[0], self.preview_size[1], raw_data, format=dpg.mvFormat_Float_rgb, tag="texture_playback")

        dpg.set_value("starting_status", "Init Windows..."); dpg.render_dearpygui_frame()

        self.ui.menubar()
        self.ui.windows()

        dpg.set_value("starting_status", "Init Effects GUI..."); dpg.render_dearpygui_frame()

        self.effects_manager = EffectsManager(self)
        self.effects_manager.widget("effect_window_group")

        dpg.hide_item("splash_window")
        # -------------------------------------------

        while dpg.is_dearpygui_running():
            self.render()
            self.render_capture()
            dpg.render_dearpygui_frame()

        self.exit()

    def render(self):
        if dpg.is_viewport_resizable():
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()

            window_width = viewport_width / 1.75

            # Define maximum height for capture_window and calculate the remaining height for effect_window
            max_capture_height = 480  # Fixed maximum height for capture_window
            capture_y = 18  # Compensate for menu bar

            # Capture window height
            capture_height = min(viewport_height / 1.5, max_capture_height)
            dpg.configure_item("capture_window", width=window_width, height=capture_height, pos=(0, capture_y))

            # Get actual height of capture_window including internal padding
            capture_rect = dpg.get_item_rect_size("capture_window")
            effect_y = capture_y + capture_rect[1]  # Position of effect_window directly below capture_window

            # Remaining height for effect_window
            effect_height = viewport_height - effect_y
            effect_height = max(effect_height, 100)  # Ensure effect_window has a minimum height of 100px

            dpg.configure_item("effect_window", width=window_width, height=effect_height, pos=(0, effect_y))

    def exit(self):
        self.close_project(None, None)
        dpg.destroy_context()


app = App()
app.init()
