import dearpygui.dearpygui as dpg
import numpy as np

# Node type definitions remain the same
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

    def remove_child(self, child):
        if child in self._children:
            self._children.remove(child)
            child.set_parent(None)
            child._data = None

    def execute(self, data):
        self._data = data
        for child in self._children:
            child._data = self._data

    def clear_connections(self):
        for child in self._children[:]:  # Create a copy of the list to avoid modification during iteration
            self.remove_child(child)
        self._children = []
        self._data = None

    def submit(self, parent):
        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Output,
                                user_data=self, id=self.uuid):
            dpg.add_text(self._label)


class InputNodeAttribute:
    def __init__(self, label: str = "input"):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._parent = None
        self._data = None

    def get_data(self):
        return self._data

    def set_parent(self, parent: OutputNodeAttribute):
        self._parent = parent

    def clear_connection(self):
        if self._parent:
            self._parent.remove_child(self)
        self._parent = None
        self._data = None

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

    def clear_all_connections(self):
        # Clear all input connections
        for input_attr in self._input_attributes:
            input_attr.clear_connection()

        # Clear all output connections
        for output_attr in self._output_attributes:
            output_attr.clear_connections()

    def finish(self):
        pass

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

    def _count_node_type(self, node_type):
        return sum(1 for node in self._nodes if node[1] == node_type)

    def can_add_node_type(self, node_type):
        if node_type == NodeType.SourceNode:
            return self._count_node_type(NodeType.SourceNode) == 0
        elif node_type == NodeType.SinkNode:
            return self._count_node_type(NodeType.SinkNode) == 0
        else:  # ProcessNode
            return True

    def add_node(self, node_tuple):
        node, node_type = node_tuple
        if self.can_add_node_type(node_type):
            self._nodes.append(node_tuple)
            return True
        else:
            # If we can't add the node, delete it from the UI
            dpg.delete_item(node.uuid)
            return False

    def remove_node(self, node):
        if node in self._nodes:
            # Clear all connections before removing the node
            node[0].clear_all_connections()
            self._nodes.remove(node)

    def on_drop(self, sender, app_data, user_data):
        source, generator, data = app_data
        node_tuple = generator(source.label, data)

        # Check if we can add this type of node
        if not self.can_add_node_type(node_tuple[1]):
            # Show an error message using DPG modal dialog
            with dpg.window(label="Error", modal=True, show=True, width=300, height=100):
                node_type_name = "Source" if node_tuple[1] == NodeType.SourceNode else "Sink"
                dpg.add_text(f"Only one {node_type_name} node is allowed!")
                dpg.add_button(label="OK", width=75,
                               callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item())))
            return

        node_tuple[0].submit(self.uuid)
        self.add_node(node_tuple)

    def _delete_selected(self, sender, app_data):
        selected_nodes = dpg.get_selected_nodes(self.uuid)
        selected_links = dpg.get_selected_links(self.uuid)

        # First find all links connected to nodes that will be deleted
        links_to_delete = set(selected_links)  # Start with manually selected links

        # Get all links in the editor
        all_links = dpg.get_item_children(self.uuid, slot=1)  # slot 1 contains links
        if all_links is None:
            all_links = []

        # Add links connected to nodes that will be deleted
        for link in all_links:
            try:
                link_conf = dpg.get_item_configuration(link)
                # Check if either end of the link is connected to a node being deleted
                for node_id in selected_nodes:
                    node_attrs = dpg.get_item_children(node_id, slot=0)  # slot 0 contains attributes
                    if node_attrs and (link_conf["attr_1"] in node_attrs or link_conf["attr_2"] in node_attrs):
                        links_to_delete.add(link)
            except Exception as e:
                # Handle case where link might have been already deleted
                print(e)

        # Delete all identified links
        for link in links_to_delete:
            try:
                # Get the nodes connected by this link
                link_conf = dpg.get_item_configuration(link)
                output_attr_id = link_conf["attr_1"]
                input_attr_id = link_conf["attr_2"]

                # Get the attribute objects
                input_attr = dpg.get_item_user_data(input_attr_id)
                output_attr = dpg.get_item_user_data(output_attr_id)

                # Clear the connection
                if input_attr and output_attr:
                    output_attr.remove_child(input_attr)

                # Delete the link visually
                dpg.delete_item(link)
            except SystemError:
                # Handle case where link might have been already deleted
                continue

        # Then handle the nodes
        for node_id in selected_nodes:
            # Find the corresponding node in our internal list
            node_to_delete = None
            for node in self._nodes:
                if node[0].uuid == node_id:
                    node_to_delete = node
                    break

            if node_to_delete:
                # Clear all connections
                node_to_delete[0].clear_all_connections()

                # Delete all attributes visually
                for attr in node_to_delete[0]._input_attributes + node_to_delete[0]._output_attributes:
                    dpg.delete_item(attr.uuid)

                # Delete the static attribute
                dpg.delete_item(node_to_delete[0].static_uuid)

                # Delete the node visually
                dpg.delete_item(node_id)

                # Remove from internal list
                self._nodes.remove(node_to_delete)

    def submit(self, parent):
        with dpg.handler_registry():
            dpg.add_key_down_handler(dpg.mvKey_Delete, callback=self._delete_selected)

        with dpg.child_window(width=-160, parent=parent, user_data=self,
                              drop_callback=lambda s, a, u: dpg.get_item_user_data(s).on_drop(s, a, u)):
            with dpg.node_editor(tag=self.uuid, callback=NodeEditor._link_callback, width=-1, height=-1):
                for node in self._nodes:
                    node.submit(self.uuid)

    def render(self, frame):
        for source_node in [node for node in self._nodes if node[1] == NodeType.SourceNode]:
            source_node[0].execute(frame)

        for process_node in [node for node in self._nodes if node[1] == NodeType.ProcessNode]:
            process_node[0].execute(None)

        sink_nodes = [node for node in self._nodes if node[1] == NodeType.SinkNode]
        if sink_nodes:
            final_frame = sink_nodes[0][0].execute(None)
        else:
            final_frame = np.zeros((100, 100, 3), np.uint8)

        return final_frame

class DragSource:
    def __init__(self, label: str, node_generator, data):
        self.label = label
        self._generator = node_generator
        self._data = data

    def submit(self, parent):
        dpg.add_button(label=self.label, parent=parent, width=-1)

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