import dearpygui.dearpygui as dpg
import ast

class ui:
    def __init__(self, app):
        self.app = app

    def windows(self):
        with dpg.window(label="New Project", tag="new_project_window", width=520, show=False):
            dpg.add_input_text(label="Project Name", tag="new_project_name")
            dpg.add_input_float(label="Frame Rate", tag="new_project_fps", default_value=12)
            with dpg.child_window(height=90):
                dpg.add_text("Resolution")
                dpg.add_input_int(label="Width", tag="new_project_width", default_value=1920)
                dpg.add_input_int(label="Height", tag="new_project_height", default_value=1080)

            with dpg.child_window(height=90):
                dpg.add_text("Project Location")
                dpg.add_input_text(label="Location", tag="new_project_location")
                dpg.add_button(label="Browse", callback=lambda: dpg.show_item("project_location_selector"))
                dpg.add_file_dialog(label="Project Location", show=False, directory_selector=True, callback=lambda _, data: dpg.set_value("new_project_location", data["file_path_name"].replace("\\", "/") + "/" + dpg.get_value("new_project_name")), tag="project_location_selector", modal=True)

            dpg.add_button(label="Create", callback=self.app.create_project)

        with dpg.window(label="Capture", tag="capture_window", width=750, show=True, no_close=True, no_resize=True, no_title_bar=True, pos=(0, 18), no_move=True):
            dpg.add_text("Capture")
            dpg.add_image("texture_preview")
            dpg.add_button(label="Capture", callback=self.app.capture)

        with dpg.window(label="Effect", tag="effect_window", show=True, no_close=True, no_resize=True, no_title_bar=True, no_move=True):
            dpg.add_text("Effect")
            dpg.add_group(horizontal=True, tag="effect_window_group")

        with dpg.window(label="Frames", tag="frames_window", show=True, no_close=True, no_resize=True, no_title_bar=True, no_move=True):
            dpg.add_text("Frames")
            # add group for frames
            dpg.add_group(horizontal=True, tag="frames_window_group")


        dpg.add_file_dialog(label="Open Project", tag="open_project_dialog", callback=self.app.open_project, directory_selector=True, show=False)

        with dpg.window(label="Preferences", tag="preferences_window", show=False):
            with dpg.tab_bar():
                with dpg.tab(label="Camera"):
                    dpg.add_combo(label="Camera", items=self.app.camera_list, callback=lambda _, data: (setattr(self.app.CM, "cameraID", ast.literal_eval(data)[0]), self.app.CM.save()), default_value=self.app.camera_list[next((i for i, item in enumerate(self.app.camera_list) if item[0] == self.app.CM.cameraID), None)])
                    dpg.add_input_int(label="Width", default_value=self.app.CM.cameraResolutionWidth, callback=lambda _, data: (setattr(self.app.CM, "cameraResolutionWidth", data), self.app.CM.save()))
                    dpg.add_input_int(label="Height", default_value=self.app.CM.cameraResolutionHeight, callback=lambda _, data: (setattr(self.app.CM, "cameraResolutionHeight", data), self.app.CM.save()))
                    dpg.add_input_float(label="FPS", default_value=self.app.CM.cameraFPS, callback=lambda _, data: (setattr(self.app.CM, "cameraFPS", data), self.app.CM.save()))
                    #dpg.add_input_float(label="Brightness", default_value=self.app.CM.cameraBrightness, callback=lambda _, data: (setattr(self.app.CM, "cameraBrightness", data), self.app.CM.save()))
                    #dpg.add_input_float(label="Contrast", default_value=self.app.CM.cameraContrast, callback=lambda _, data: (setattr(self.app.CM, "cameraContrast", data), self.app.CM.save()))
                    #dpg.add_input_float(label="Saturation", default_value=self.app.CM.cameraSaturation, callback=lambda _, data: (setattr(self.app.CM, "cameraSaturation", data), self.app.CM.save()))
                    #dpg.add_input_float(label="Hue", default_value=self.app.CM.cameraHue, callback=lambda _, data: (setattr(self.app.CM, "cameraHue", data), self.app.CM.save()))
                    #dpg.add_input_float(label="Gain", default_value=self.app.CM.cameraGain, callback=lambda _, data: (setattr(self.app.CM, "cameraGain", data), self.app.CM.save()))
                    #dpg.add_input_float(label="Exposure", default_value=self.app.CM.cameraExposure, callback=lambda _, data: (setattr(self.app.CM, "cameraExposure", data), self.app.CM.save()))

        with dpg.window(tag="dialog_window", show=False, modal=True, no_move=True, no_title_bar=True, width=320):
            dpg.add_text(tag="dialog_window_title")
            dpg.add_text(tag="dialog_window_text")
            dpg.add_spacer()
            dpg.add_button(label="Close", callback=lambda: dpg.hide_item("dialog_window"), tag="dialog_window_bclose")

        with dpg.window(label="About", tag="about_window", show=False):
            dpg.add_text("OpenSMA (Open Stop Motion Animator)")
            dpg.add_text(f"Version {self.app.version}")
            dpg.add_spacer()
            dpg.add_text(f"Copyright (C) 2024-2025 DPSoftware Foundation All rights reserved. (GPLv3)")

    def menubar(self):
        with dpg.viewport_menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="New Project", shortcut="Ctrl+N", callback=self.app.pre_new_project)
                dpg.add_menu_item(label="Open", shortcut="Ctrl+O", callback=lambda: dpg.show_item("open_project_dialog"))
                # project always save
                #dpg.add_menu_item(label="Save", shortcut="Ctrl+S")
                #dpg.add_menu_item(label="Save as", shortcut="Ctrl+Shift+S")
                dpg.add_menu_item(label="Close Project", callback=self.app.close_project)
                dpg.add_spacer()
                dpg.add_menu_item(label="Import", shortcut="Ctrl+I")
                dpg.add_menu_item(label="Export", shortcut="Ctrl+M")
                dpg.add_spacer()
                dpg.add_menu_item(label="Exit", callback=lambda: self.app.exit())

            with dpg.menu(label="Edit"):
                dpg.add_menu_item(label="Undo", shortcut="Ctrl+Z")
                dpg.add_menu_item(label="Redo", shortcut="Ctrl+Y")
                dpg.add_spacer()
                dpg.add_menu_item(label="Cut", shortcut="Ctrl+X")
                dpg.add_menu_item(label="Copy", shortcut="Ctrl+C")
                dpg.add_menu_item(label="Paste", shortcut="Ctrl+V")
                dpg.add_menu_item(label="Delete", shortcut="Del")
                dpg.add_spacer()
                dpg.add_menu_item(label="Preferences", callback=lambda: dpg.show_item("preferences_window"))

            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="Manual", shortcut="F1")
                dpg.add_menu_item(label="Bug Report & Feedback")
                dpg.add_menu_item(label="About", callback=lambda: dpg.show_item("about_window"))


