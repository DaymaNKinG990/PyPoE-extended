"""
Hash checker for patch server files.

This module handles hash verification for files and directories.
"""

import os
from hashlib import sha256
from hmac import compare_digest
from typing import Any

from PyPoE.poe.file.ggpk import DirectoryRecord, FileRecord, GGPKFile
from PyPoE.poe.patchserver.node import DirectoryNodeExtended


def node_check_hash(
    directory_node: DirectoryNodeExtended,
    folder_path: str | None = None,
    ggpk: GGPKFile | None = None,
    recurse: bool = False,
    bufsize: int = 2**10,
) -> list[tuple[DirectoryNodeExtended, Any, bool]]:
    """
    Check that folder & files or GGPKFile contents match expected hash values.

    Example::

        import PyPoE.poe.patchserver
        patch = PyPoE.poe.patchserver.Patch()
        patch_file_list = PyPoE.poe.patchserver.PatchFileList(patch)
        poe_dir = '/mnt/poe/Path_of_Exile'
        node = ''
        hash_list = PyPoE.poe.patchserver.node_check_hash(
            patch_file_list.directory, folder_path=poe_dir, recurse=False)
        for node, node_hash, matched in hash_list:
            print('{matched} {name}'.format(
                matched='✓' if matched else '✗',
                node.record.name,
                matched))

    Args:
        directory_node: The node to check that folder & files or GGPKFile contents
            match expected values
        folder_path: File system directory where files to check are located
        ggpk: GGPK file record
        recurse: If set, recursively check all children
        bufsize: The size of the buffer to use for computing each hash

    Returns:
        List of tuples (node, node_hash, matched) where matched indicates
        if the hash matches the expected value
    """
        If set, check folders
    bufsize : int
        The size of the buffer to use for computing each hash

    Returns
    -------
    list[tuple]
        List of tuples: (DirectoryNodeExtended, sha256sum, bool)
        True if folder bytes hash == expected hash

    Raises
    ------
    ValueError
        One of either ggpk or folder_path must be given
    """
    if bool(folder_path) == bool(ggpk):
        raise ValueError("Must specify either folder_path or ggpk")

    node_hash = None
    hash_test = False
    self = directory_node

    if isinstance(self.record, FileRecord):
        file_handle = None
        if folder_path:
            file = os.path.join(folder_path, self.record.name)
            try:
                file_handle = open(file, "rb")
            except FileNotFoundError:
                return [(self, node_hash, hash_test)]
        elif ggpk:
            node_path = self.get_path()  # type: ignore[attr-defined]
            node = ggpk[node_path]
            if isinstance(node.record, FileRecord):
                file_handle = node.record.extract()
            else:
                return [(self, node_hash, hash_test)]

        if file_handle:
            file_hash = sha256()
            while True:
                # Hash max bufsize (1MB default) at a time
                buf = file_handle.read(bufsize)
                if not buf:
                    break
                file_hash.update(buf)

            node_hash = file_hash
            del file_hash

            hash_test = compare_digest(node_hash.hexdigest(), format(self.record.hash, "064x"))

            file_handle.close()
            del file_handle

        return [(self, node_hash, hash_test)]

    elif isinstance(self.record, DirectoryRecord) or self.record is None:
        if folder_path:
            folder = ""
            if self.record is not None:
                folder = self.record.name
            folder_path = os.path.join(folder_path, folder)
            children_list: list[DirectoryNodeExtended] = []
            if isinstance(self.children, list):
                children_list = [c for c in self.children if isinstance(c, DirectoryNodeExtended)]
            elif isinstance(self.children, dict):
                children_list = [c for c in self.children.values() if isinstance(c, DirectoryNodeExtended)]  # type: ignore[union-attr]
        elif ggpk:
            # PyPoE ggpk children are reversed
            if isinstance(self.children, list):
                children_list = [c for c in self.children if isinstance(c, DirectoryNodeExtended)][::-1]  # type: ignore[assignment]
            elif isinstance(self.children, dict):
                children_list = [c for c in self.children.values() if isinstance(c, DirectoryNodeExtended)][::-1]  # type: ignore[union-attr]
            else:
                children_list = []

        child_hash_list = []
        hash_list = []
        missing_files = False
        # need the order of items in folder to generate hash
        for node in children_list:
            # if node is directory and do not want to recurse
            if not (isinstance(node.record, DirectoryRecord) and not recurse):
                child_node_hash = node_check_hash(
                    node, folder_path=folder_path, ggpk=ggpk, recurse=recurse, bufsize=bufsize
                )
                if child_node_hash[-1][1] is None:
                    missing_files = True
                # only calculate the folder hash from immediate
                # children hashes ... no grandchildren
                child_hash_list.append(child_node_hash[-1])
                # store all hash results to return
                hash_list += child_node_hash
        if missing_files is False and recurse:
            folder_hash_concat = b"".join(item[1].digest() for item in child_hash_list)
            node_hash = sha256(folder_hash_concat)
            if self.record is not None:
                hash_test = compare_digest(node_hash.hexdigest(), format(self.record.hash, "064x"))
        # put folder hash at end of list if recurse and not root
        if self.record is not None and recurse:
            return hash_list + [(self, node_hash, hash_test)]

        return hash_list

    return []


def node_outdated_files(
    patch_file_list: Any,
    directory_node_path: str,
    folder_path: str,
    recurse: bool = False,
    bufsize: int = 2**10,
) -> dict[int, list[DirectoryNodeExtended]]:
    """
    Get expected hash based list of outdated files on disk for given directory node.

    Example::

        import PyPoE.poe.patchserver
        patch = PyPoE.poe.patchserver.Patch()
        patch_file_list = PyPoE.poe.patchserver.PatchFileList(patch)
        poe_dir = '/mnt/poe/Path_of_Exile'
        node = ''
        update_list = PyPoE.poe.patchserver.node_outdated_files(
            patch_file_list, node, poe_dir, recurse=False)
        print(update_list)

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

    Returns
    -------
    dict
        Dictionary mapping hash to list of DirectoryNodeExtended
    """
    # get needed depth of directory node first
    try:
        directory_node = patch_file_list.directory[directory_node_path]  # type: ignore[attr-defined]
        # if directory and no child metadata
        if isinstance(directory_node.record, DirectoryRecord) and not directory_node.children:
            raise FileNotFoundError("Just here to trigger the except")
    except FileNotFoundError:
        directory_paths = directory_node_path.split("/")
        cdir = ""
        for index, dir_name in enumerate(directory_paths):
            if cdir:
                cdir += "/"
            cdir += dir_name
            # do not know if node is file or folder
            # if file, second last node is final
            if (len(directory_paths) - index) < 1:
                directory_node = patch_file_list.directory[directory_node_path]  # type: ignore[attr-defined]
                if directory_node.record is not None and isinstance(
                    directory_node.record, FileRecord
                ):
                    break
            patch_file_list.update_filelist([cdir])  # type: ignore[attr-defined]
    directory_node = patch_file_list.directory[directory_node_path]  # type: ignore[attr-defined]

    # walk metadata
    if recurse:
        directories = directory_node.directories  # type: ignore[attr-defined]
        end_directories = []
        while directories:
            child = directories.pop()
            # if child is directory
            if isinstance(child.record, DirectoryRecord):
                # if metadata is not present
                if not child.children:
                    patch_file_list.update_filelist([child.get_path()])  # type: ignore[attr-defined]
                directories = directories + child.directories  # type: ignore[attr-defined]
                if not child.directories:  # type: ignore[attr-defined]
                    end_directories.append(child)

    node_hash_list = node_check_hash(
        directory_node, folder_path=folder_path, recurse=recurse, bufsize=bufsize
    )

    download_list: dict[int, list[DirectoryNodeExtended]] = {}
    for node, _checksum, match in node_hash_list:
        # For files that did not match
        if isinstance(node.record, FileRecord) and not match:
            try:
                # expected hash as key,
                # so not downloading same file many times
                download_list[node.record.hash].append(node)
            except KeyError:
                download_list[node.record.hash] = [node]

    return download_list

