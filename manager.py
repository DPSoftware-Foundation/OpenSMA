import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path

        self.cameraID = 0
        self.cameraResolutionWidth = 1920
        self.cameraResolutionHeight = 1080
        self.cameraFPS = 30
        self.cameraBrightness = -1.0
        self.cameraContrast = -1.0
        self.cameraSaturation = -1.0
        self.cameraHue = -1.0
        self.cameraGain = -1.0
        self.cameraExposure = -1.0

        self.exportFolder = Path.home() / "Videos"
        self.exportFilename = "%Y-%m-%d_%H-%M-%S"
        self.exportFormat = "mp4"
        self.exportCodec = "libx264"
        self.exportBitrate = "2500k"
        self.exportFPS = 30

    def save(self):
        config = {
            "camera": {
                "camera_id": self.cameraID,
                "resolution": {
                    "width": self.cameraResolutionWidth,
                    "height": self.cameraResolutionHeight
                },
                "fps": self.cameraFPS,
                "brightness": self.cameraBrightness,
                "contrast": self.cameraContrast,
                "saturation": self.cameraSaturation,
                "hue": self.cameraHue,
                "gain": self.cameraGain,
                "exposure": self.cameraExposure
            },
            "export": {
                "folder": str(self.exportFolder),
                "filename": self.exportFilename,
                "format": self.exportFormat,
                "codec": self.exportCodec,
                "bitrate": self.exportBitrate,
                "fps": self.exportFPS
            }
        }
        with open(self.config_path, 'w') as json_file:
            json.dump(config, json_file, indent=4)

    def load(self):
        if not os.path.exists(self.config_path):
            print(f"Config file {self.config_path} not found.")
            return

        with open(self.config_path, 'r') as json_file:
            config = json.load(json_file)

        # Camera settings
        self.cameraID = config["camera"]["camera_id"]
        self.cameraResolution = (config["camera"]["resolution"]["width"], config["camera"]["resolution"]["height"])
        self.cameraFPS = config["camera"]["fps"]
        self.cameraBrightness = config["camera"]["brightness"]
        self.cameraContrast = config["camera"]["contrast"]
        self.cameraSaturation = config["camera"]["saturation"]
        self.cameraHue = config["camera"]["hue"]
        self.cameraGain = config["camera"]["gain"]
        self.cameraExposure = config["camera"]["exposure"]

        # Export settings
        self.exportFolder = config["export"]["folder"]
        self.exportFilename = config["export"]["filename"]
        self.exportFormat = config["export"]["format"]
        self.exportCodec = config["export"]["codec"]
        self.exportBitrate = config["export"]["bitrate"]
        self.exportFPS = config["export"]["fps"]

class ProjectManager:
    def __init__(self, project_name, project_fps, project_width, project_height, project_location):
        self.project_name = project_name
        self.project_fps = project_fps
        self.project_width = project_width
        self.project_height = project_height
        self.project_location = project_location

        self.project_folder = Path(project_location)
        self.frames_folder = self.project_folder / "frames"  # Define the frames folder
        self.current_frame = None

    def create_project(self):
        # Check if project name is blank
        if not self.project_name.strip():
            raise NameError("Project name cannot be blank!")

        # Check if the folder already exists
        if self.project_folder.exists():
            raise FileExistsError(f"Folder already exists at {self.project_folder}")

        # Create the project folder
        self.project_folder.mkdir(parents=True)
        self.frames_folder.mkdir(parents=True)

        # Save project settings to a JSON file
        project_settings = {
            "name": self.project_name,
            "fps": self.project_fps,
            "width": self.project_width,
            "height": self.project_height,
        }

        settings_file = self.project_folder / "project.json"
        with open(settings_file, "w") as file:
            json.dump(project_settings, file)

    @staticmethod
    def load_project(project_location):
        # Define the project folder and settings file
        project_folder = Path(project_location)
        settings_file = project_folder / "project.json"

        # Check if the settings file exists
        if not settings_file.exists():
            raise FileNotFoundError(f"Project settings file not found at {settings_file}")

        # Load project settings from the JSON file
        with open(settings_file, "r") as file:
            project_settings = json.load(file)

        # Ensure all required fields are present
        required_fields = ["name", "fps", "width", "height"]
        for field in required_fields:
            if field not in project_settings:
                raise KeyError(f"Missing required project setting: {field}")

        # Create and return a ProjectManager instance
        return ProjectManager(
            project_name=project_settings["name"],
            project_fps=project_settings["fps"],
            project_width=project_settings["width"],
            project_height=project_settings["height"],
            project_location=project_location
        )
