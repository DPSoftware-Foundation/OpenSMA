import dearpygui.dearpygui as dpg
from node import (NodeEditor, DragSourceContainer, Node,
                  DragSource, InputNodeAttribute, OutputNodeAttribute,
                  NodeType)
import effects

class CVSource(Node):
    @staticmethod
    def factory(name, data):
        return CVSource(name, data), NodeType.SourceNode

    def __init__(self, name, data):
        super().__init__(name, data)

        self.add_output_attribute(OutputNodeAttribute("Frame"))

    def custom(self):
        dpg.add_text("CV Source")

    def process(self, frame):
        self._output_attributes[0].execute(frame)

class CVSink(Node):
    @staticmethod
    def factory(name, data):
        return CVSink(name, data), NodeType.SinkNode

    def __init__(self, name, data):
        super().__init__(name, data)

        self.add_input_attribute(InputNodeAttribute("Frame"))

    def custom(self):
        dpg.add_text("CV Sink")

    def execute(self, _):
        return self._input_attributes[0].get_data()

# ----------------------------------------------------


class EffectsManager:
    def __init__(self, app):
        self.app = app

        self.effects_contaniar = DragSourceContainer("Effects", 150, -1)
        self.IO_container = DragSourceContainer("Input/Output", 150, -1)

        self.left_panel = dpg.generate_uuid()
        self.right_panel = dpg.generate_uuid()

        self.node_editor = NodeEditor()

        self.IO_container.add_drag_source(DragSource("CV Source", CVSource.factory, None))
        self.IO_container.add_drag_source(DragSource("CV Sink", CVSink.factory, None))

        # effect
        self.effects_contaniar.add_drag_source(DragSource("Temperature", effects.Temperature.factory, None))


    def widget(self, parent):
        with dpg.group(id=self.left_panel, parent=parent):
            self.IO_container.submit(self.left_panel)

        # center panel
        self.node_editor.submit(parent)

        # right panel
        with dpg.group(id=self.right_panel, parent=parent):
            self.effects_contaniar.submit(self.right_panel)

    #def render(self, frame):
    #    self.IO_container.add_drag_source(DragSource(label, factory, data))