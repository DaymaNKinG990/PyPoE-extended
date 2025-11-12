"""
Extended directory node for patch server.

This module contains DirectoryNodeExtended class with additional methods.
"""

from collections import OrderedDict
from typing import Any

from PyPoE.poe.file.ggpk import DirectoryNode
from PyPoE.poe.patchserver.records import (
    BaseRecordData,
    VirtualDirectoryRecord,
    VirtualFileRecord,
)


class DirectoryNodeExtended(DirectoryNode):
    """
    Extended DirectoryNode with additional methods.

    Adds methods:
        :meth:`.get_dict`
        :meth:`.load_dict`
        :meth:`.gen_walk`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize DirectoryNodeExtended."""
        super().__init__(*args, **kwargs)

    def get_dict(self, recurse: bool = True) -> OrderedDict[str, Any]:
        """
        Get a dict of DirectoryNode record item details.

        Example::

            from json import dump
            dump_dict = patch_file_list.directory.get_dict()
            dump_dict['version'] = patch_file_list.patch.version
            file_handle = open('poe_file_details.json', 'w', encoding='utf-8')
            dump(dump_dict, file_handle)
            file_handle.close()

        Parameters
        ----------
        recurse : bool
            If set, recursively get all children

        Returns
        -------
        OrderedDict
            Dictionary representation of directory structure
        """
        record_dict = OrderedDict()

        if isinstance(self.record, BaseRecordData):
            record_dict["name"] = self.record._name
            pretty_hash = format(self.record.hash, "064x")
            record_dict["hash"] = pretty_hash

            if isinstance(self.record, VirtualDirectoryRecord):
                record_dict["type"] = "folder"
            elif isinstance(self.record, VirtualFileRecord):
                record_dict["type"] = "file"
                record_dict["size"] = self.record.data_length
        else:
            record_dict["name"] = "ROOT"

        if recurse is True and len(self.children) > 1:
            children: list[dict[str, Any]] = []
            record_dict["children"] = children  # type: ignore[assignment]

            for child in self.children:
                if isinstance(child, DirectoryNodeExtended):
                    children.append(child.get_dict())  # type: ignore[arg-type]

        return record_dict

    def load_dict(self, node_dict: OrderedDict[str, Any], parent: Any = None) -> None:
        """
        Load directory structure from dict.

        Parameters
        ----------
        node_dict : OrderedDict
            Dictionary representation of directory structure
        parent : DirectoryNodeExtended, optional
            Parent node
        """
        if not isinstance(node_dict, OrderedDict):
            raise TypeError("OrderedDict required")

        node_children = []

        node_name = node_dict["name"]
        if node_name == "ROOT":
            temp_record = None
            node_hash = None
        else:
            node_type = node_dict["type"]

            # unpretty hash. str hex bytes -> bytes
            pretty_hash = node_dict["hash"]
            # store sha256sum as int
            node_hash = int(pretty_hash, 16)

            if node_type == "file":
                node_file_size = node_dict["size"]
                temp_record = VirtualFileRecord(name=node_name, hash=node_hash, size=node_file_size)
            elif node_type == "folder":
                temp_record = VirtualDirectoryRecord(name=node_name, hash=node_hash)  # type: ignore[assignment]
            else:
                raise KeyError(f"Unknown type: {node_type}")

        if parent is None:
            self.record = temp_record  # type: ignore[assignment]
            self.hash = node_hash  # type: ignore[assignment]
            self.parent = None  # type: ignore[assignment]
            child_node = self
        else:
            child_node = DirectoryNodeExtended(record=temp_record, hash=node_hash, parent=parent)  # type: ignore[arg-type]
            parent.children.append(child_node)  # type: ignore[attr-defined]

        try:
            node_children = node_dict["children"]
            if node_children:
                for child in node_children:
                    child_node.load_dict(child, child_node)  # type: ignore[arg-type]
        except KeyError:
            pass

    def gen_walk(self, max_depth: int = -1, _depth: int = 0):
        """
        A depth first recursive generator for a DirectoryNode.

        Example::

            for node, depth in patch_file_list.directory.gen_walk():
              try:
                name = node.record.name
              except:
                name = 'ROOT'
              print('{blank:>{width}}{name}'.format(
                name=name, width=depth, blank=''))

        Parameters
        ----------
        max_depth : int
            how many levels of children to walk
        _depth : int
            current depth (internal use)

        Yields
        ------
        tuple
            (DirectoryNodeExtended, depth)
        """
        # only continue if not past maximum depth
        if max_depth == -1 or _depth <= max_depth:
            yield (self, _depth)
            _depth += 1
            # don't recurse it that goes over max_depth
            if max_depth == -1 or _depth <= max_depth:
                # depth first
                for child in self.children:
                    if isinstance(child, DirectoryNodeExtended):
                        yield from child.gen_walk(max_depth, _depth)
                    else:
                        yield (child, _depth)

