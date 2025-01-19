import dearpygui.dearpygui as dpg
from node import Node, InputNodeAttribute, OutputNodeAttribute, NodeType
import cv2
import numpy as np

# Tone mapping effect node

class Temperature(Node):
    @staticmethod
    def factory(name, data):
        return Temperature(name, data), NodeType.ProcessNode

    def __init__(self, name, data):
        super().__init__(name, data)

        self.add_input_attribute(InputNodeAttribute("Frame"))
        self.add_output_attribute(OutputNodeAttribute("Frame"))

        self.temp_in = dpg.generate_uuid()

    def custom(self):
        dpg.add_text("Temperature")
        dpg.add_input_float(label="Temperature", tag=self.temp_in, step=0, max_value=100, min_value=-100, default_value=0, width=150)

    def execute(self, _):
        frame = self._input_attributes[0].get_data()

        output_frame = cv2.convertScaleAbs(frame, alpha=1, beta=dpg.get_value(self.temp_in))

        self._output_attributes[0].execute(output_frame)

