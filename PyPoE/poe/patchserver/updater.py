"""
File updater for patch server.

This module handles updating files from the patch server.
"""

import contextlib
import os
from typing import Any

from PyPoE.poe.patchserver.hash_checker import node_outdated_files


def node_update_files(
    patch_file_list: Any,
    directory_node_path: str,
    folder_path: str,
    recurse: bool = False,
    bufsize: int = 2**10,
) -> None:
    """
    Update files and folders on disk for given node path.

    Example::

        import PyPoE.poe.patchserver
        patch = PyPoE.poe.patchserver.Patch()
        patch_file_list = PyPoE.poe.patchserver.PatchFileList(patch)
        poe_dir = '/tmp/pypoe/poe'
        node = 'Metadata/Items/Amulets'
        PyPoE.poe.patchserver.node_update_files(
          patch_file_list, node, poe_dir, recurse=False)
        node = 'Metadata/Items/Rings'
        PyPoE.poe.patchserver.node_update_files(
          patch_file_list, node, poe_dir, recurse=False)

    Parameters
    ----------
    patch_file_list : PatchFileList
        The connection to a patch server
    directory_node_path : str
        The path name of the node to update folder & files for.
    folder_path : str
        File system directory where files to check are located
    recurse : bool
        If set, update all files in directories below directory_node_path
    bufsize : int
        The size of the buffer to use for computing each hash
    """
    from json import dump

    node_parent_split = directory_node_path.rsplit("/", 1)
    node_parent = directory_node_path.rsplit("/", 1)[0]
    if len(node_parent_split) == 1:
        node_parent = ""
    hash_path = os.path.join(folder_path, node_parent)
    download_list = node_outdated_files(
        patch_file_list, directory_node_path, hash_path, recurse=recurse, bufsize=bufsize
    )

    dump_dict = patch_file_list.directory.get_dict()  # type: ignore[attr-defined]
    dump_dict["version"] = patch_file_list.patch.version  # type: ignore[attr-defined]
    file_handle = open(os.path.join(folder_path, "poe_file_details.json"), "w", encoding="utf-8")
    dump(dump_dict, file_handle)
    file_handle.close()

    dir_fd = os.open(folder_path, os.O_DIRECTORY)  # type: ignore[attr-defined]

    files_subdir = "files"
    files_count = len(download_list.keys())
    for download_index, (hash_val, nodes) in enumerate(download_list.items()):
        pretty_hash = format(hash_val, "064x")
        dst_file = os.path.join(folder_path, files_subdir, pretty_hash)
        node_file_name = nodes[0].get_path()  # type: ignore[attr-defined]
        print(f"{files_count - download_index} file downloads remaining")
        patch_file_list.patch.download(node_file_name, dst_file=dst_file)  # type: ignore[attr-defined]
        print(f"downloaded: {node_file_name}")

        for node in nodes:
            link_src = dst_file
            node_path = node.get_path()  # type: ignore[attr-defined]
            link_dst = os.path.join(folder_path, node_path)
            link_parent = os.path.dirname(link_dst)
            os.makedirs(link_parent, exist_ok=True)
            link_source_rel = os.path.relpath(link_src, link_parent)
            try:
                old_source = os.path.realpath(link_dst)
                if old_source != link_src:
                    os.remove(old_source, dir_fd=dir_fd)  # type: ignore[call-overload]
            except FileNotFoundError:
                pass

            with contextlib.suppress(FileNotFoundError):
                os.remove(node_path, dir_fd=dir_fd)  # type: ignore[call-overload]

            os.symlink(link_source_rel, node_path, dir_fd=dir_fd)  # type: ignore[call-overload]

    os.close(dir_fd)

