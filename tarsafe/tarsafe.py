"""
tarsafe module is a more secure drop-in replacement for tarfile module.

We expose everything tarfile does, but some methods are overridden to add
safety features.
"""

import ntpath
import os
import tarfile
from tarfile import *  # noqa: F401, F403


__all__ = tarfile.__all__ + [
    "TarSafe",
    "TarSafeException",
]


class TarSafe(tarfile.TarFile):
    """
    A safe subclass of the TarFile class for interacting with tar files.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.directory = os.getcwd()

    @classmethod
    def open(cls, name=None, mode="r", fileobj=None, bufsize=tarfile.RECORDSIZE, **kwargs):
        return super().open(name, mode, fileobj, bufsize, **kwargs)

    def extract(self, member, path="", set_attrs=True, *, numeric_owner=False):
        """
        Override the parent extract method and add safety checks.
        """
        self._safetar_check(path or os.getcwd())
        super().extract(member, path, set_attrs=set_attrs, numeric_owner=numeric_owner)

    def extractall(self, path=".", members=None, *, numeric_owner=False):
        """
        Override the parent extractall method and add safety checks.
        """
        self._safetar_check(path)
        super().extractall(path, members, numeric_owner=numeric_owner)

    def _safetar_check(self, target_dir):
        """
        Runs all necessary checks for the safety of a tarfile.

        target_dir is the actual root the archive is about to be extracted into (the
        path argument passed to extract()/extractall()), resolved to a real, absolute
        path so every containment check below is anchored to where files will land,
        not to the cwd at TarSafe construction time.
        """
        root = os.path.realpath(target_dir)
        try:
            for tarinfo in self.__iter__():
                if self._is_traversal_attempt(tarinfo=tarinfo, root=root):
                    raise TarSafeException(f"Attempted directory traversal for member: {tarinfo.name}")
                if self._is_unsafe_symlink(tarinfo=tarinfo, root=root):
                    raise TarSafeException(f"Attempted directory traversal via symlink for member: {tarinfo.linkname}")
                if self._is_unsafe_link(tarinfo=tarinfo, root=root):
                    raise TarSafeException(f"Attempted directory traversal via link for member: {tarinfo.linkname}")
                if self._is_device(tarinfo=tarinfo):
                    raise TarSafeException(f"tarfile returns true for isblk() or ischr()")
        except Exception:
            raise

    def _is_traversal_attempt(self, tarinfo, root):
        # Adding this additional simple qualifier that the path seems suspect in order to avoid expensive
        # path normalization when testing deeply nested archives.
        if self._looks_suspicious(tarinfo.name):
            resolved = os.path.abspath(os.path.join(root, tarinfo.name))
            if not self._is_contained(root, resolved):
                return True
        return False

    @staticmethod
    def _looks_suspicious(name):
        """
        Cheap pre-filter for _is_traversal_attempt: True if `name` merits the more
        expensive containment check.

        Tar member names always use "/" per the tar spec (GNU tar, POSIX.1-2001)
        regardless of host OS, so checking only os.sep misses "/..." names on
        Windows, where os.sep is "\\" -- os.path.join then treats a leading "/"
        as drive-relative and it lands outside the extraction root with no check
        ever running. Also catch a bare drive-letter prefix (e.g. "C:/x"), which
        os.path.join/ntpath.join likewise treat as an absolute, drive-relative
        path on Windows.
        """
        return (
            name.startswith(("/", "\\"))
            or ".." in name
            or bool(ntpath.splitdrive(name)[0])
        )

    def _is_unsafe_symlink(self, tarinfo, root):
        if tarinfo.issym():
            resolved = os.path.abspath(os.path.join(root, tarinfo.linkname))
            if not self._is_contained(root, resolved):
                return True
        return False

    def _is_unsafe_link(self, tarinfo, root):
        if tarinfo.islnk():
            resolved = os.path.abspath(os.path.join(root, tarinfo.linkname))
            if not self._is_contained(root, resolved):
                return True
        return False

    def _is_device(self, tarinfo):
        return tarinfo.ischr() or tarinfo.isblk()

    @staticmethod
    def _is_contained(root, resolved):
        """
        True if resolved is root itself or a path strictly beneath it.

        A plain root.startswith(prefix) check is not a path-boundary check: it also
        matches siblings that merely share a string prefix (e.g. "/opt/app-secret"
        startswith "/opt/app"). commonpath() splits on path separators instead, so
        it can't be fooled by that.
        """
        try:
            return os.path.commonpath([root, resolved]) == root
        except ValueError:
            return False


class TarSafeException(Exception):
    pass


class TarFile(TarSafe):
    """Override of tarfile.TarFile to maintain compatibility."""


open = TarSafe.open
