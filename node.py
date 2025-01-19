import dearpygui.dearpygui as dpg
import numpy as np

# Node type
class NodeType:
    SourceNode = 0
    ProcessNode = 1
    SinkNode = 2

class OutputNodeAttribute:

    def __init__(self, label: str = "output"):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._children = []  # output attributes
        self._data = None

    def add_child(self, parent, child):
        dpg.add_node_link(self.uuid, child.uuid, parent=parent)
        child.set_parent(self)
        self._children.append(child)

    def execute(self, data):
        self._data = data
        for child in self._children:
            child._data = self._data

    def submit(self, parent):
        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Output,
                                user_data=self, id=self.uuid):
            dpg.add_text(self._label)


class InputNodeAttribute:

    def __init__(self, label: str = "input"):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._parent = None  # input attribute
        self._data = None

    def get_data(self):
        return self._data

    def set_parent(self, parent: OutputNodeAttribute):
        self._parent = parent

    def submit(self, parent):
        with dpg.node_attribute(parent=parent, user_data=self, id=self.uuid):
            dpg.add_text(self._label)


class Node:

    def __init__(self, label: str, data):

        self.label = label
        self.uuid = dpg.generate_uuid()
        self.static_uuid = dpg.generate_uuid()
        self._input_attributes = []
        self._output_attributes = []
        self._data = data

    def finish(self):
        pass
        #dpg.bind_item_theme(self.uuid, _completion_theme)

    def add_input_attribute(self, attribute: InputNodeAttribute):
        self._input_attributes.append(attribute)

    def add_output_attribute(self, attribute: OutputNodeAttribute):
        self._output_attributes.append(attribute)

    def execute(self, frame):

        for attribute in self._output_attributes:
            attribute.execute(self._data)

        self.finish()
        return frame

    def custom(self):
        pass

    def submit(self, parent):

        with dpg.node(parent=parent, label=self.label, tag=self.uuid):

            for attribute in self._input_attributes:
                attribute.submit(self.uuid)

            with dpg.node_attribute(parent=self.uuid, attribute_type=dpg.mvNode_Attr_Static,
                                    user_data=self, tag=self.static_uuid):
                self.custom()

            for attribute in self._output_attributes:
                attribute.submit(self.uuid)


class NodeEditor:

    @staticmethod
    def _link_callback(sender, app_data, user_data):
        output_attr_uuid, input_attr_uuid = app_data

        input_attr = dpg.get_item_user_data(input_attr_uuid)
        output_attr = dpg.get_item_user_data(output_attr_uuid)

        output_attr.add_child(sender, input_attr)

    def __init__(self):
        self._nodes = []
        self.uuid = dpg.generate_uuid()

    def add_node(self, node: Node):
        self._nodes.append(node)

    def on_drop(self, sender, app_data, user_data):
        source, generator, data = app_data
        node = generator(source.label, data)
        node[0].submit(self.uuid)
        self.add_node(node)

    def submit(self, parent):
        with dpg.child_window(width=-160, parent=parent, user_data=self,
                              drop_callback=lambda s, a, u: dpg.get_item_user_data(s).on_drop(s, a, u)):
            with dpg.node_editor(tag=self.uuid, callback=NodeEditor._link_callback, width=-1, height=-1):
                for node in self._nodes:
                    node.submit(self.uuid)

    def render(self, frame):
        """Trigger the execution of all nodes, get data from source, process with OpenCV, and output from sink."""

        # put data into source node

        for source_node in [node for node in self._nodes if node[1] == NodeType.SourceNode]:
            source_node[0].execute(frame)

        # process data
        for process_node in [node for node in self._nodes if node[1] == NodeType.ProcessNode]:
            process_node[0].execute(None)

        sink_nodes = [node for node in self._nodes if node[1] == NodeType.SinkNode]
        if sink_nodes:
            final_frame = sink_nodes[0][0].execute(None)
        else:
            # make blank image
            final_frame = np.zeros((100, 100, 3), np.uint8)



        # Assuming final_frame is the processed data (image) after all nodes have been executed
        return final_frame

class DragSource:

    def __init__(self, label: str, node_generator, data):
        self.label = label
        self._generator = node_generator
        self._data = data

    def submit(self, parent):
        dpg.add_button(label=self.label, parent=parent, width=-1)
        #dpg.bind_item_theme(dpg.last_item(), _source_theme)

        with dpg.drag_payload(parent=dpg.last_item(), drag_data=(self, self._generator, self._data)):
            dpg.add_text(f"Name: {self.label}")


class DragSourceContainer:

    def __init__(self, label: str, width: int = 150, height: int = -1):
        self._label = label
        self._width = width
        self._height = height
        self._uuid = dpg.generate_uuid()
        self._children = []  # drag sources

    def add_drag_source(self, source: DragSource):
        self._children.append(source)

    def submit(self, parent):
        with dpg.child_window(parent=parent, width=self._width, height=self._height, tag=self._uuid,
                              menubar=True) as child_parent:
            with dpg.menu_bar():
                dpg.add_menu(label=self._label)

            for child in self._children:
                child.submit(child_parent)