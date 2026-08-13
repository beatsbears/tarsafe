import io
import os
import inspect
import tarfile

import pytest

import tarsafe
from tarsafe import TarSafe, TarSafeException


def test_bad_files():
    files = os.listdir("./test/data/bad")
    for file_ in files:
        with pytest.raises(TarSafeException) as ex:
            with TarSafe.open(f"./test/data/bad/{file_}", "r") as tar:
                tar.extractall()


def test_good_files():
    files = os.listdir("./test/data/good")
    for file_ in files:
        with TarSafe.open(f"./test/data/good/{file_}", "r") as tar:
            tar.extractall()
        assert os.path.exists("./evil.sh")
        os.remove("./evil.sh")


def test_good_file():
    files = os.listdir("./test/data/good")
    for file_ in files:
        with TarSafe.open(f"./test/data/good/{file_}", "r") as tar:
            tar.extract("evil.sh")
        assert os.path.exists("./evil.sh")
        os.remove("./evil.sh")


def test_tarsafe_is_dropin_for_tarfile():
    assert _get_exposed_members(tarfile) <= _get_exposed_members(tarsafe)


def test_multi_dot_symlink_stays_contained(tmp_path):
    """
    Regression test for a reported bypass claiming that a symlink target like
    "...../...../etc" is resolved by os.path the same way as "../../etc",
    letting it escape the extraction directory. It is not: POSIX and Windows
    path resolution only treat a component consisting of exactly ".." as
    "parent directory" -- "....." is just an ordinary (if unusual) filename.
    os.path.normpath/ntpath.normpath do not collapse it either, so the
    existing abspath()+startswith() containment check in
    TarSafe._is_unsafe_symlink already handles it correctly.
    """
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    extract_dir = tmp_path / "extract"
    extract_dir.mkdir()

    tar_path = archive_dir / "evil.tar"
    dummy_path = archive_dir / "dummy.txt"
    dummy_path.write_text("test")

    with tarfile.open(tar_path, "w") as tar:
        tar.add(dummy_path, arcname="dummy.txt")
        symlink = tarfile.TarInfo(name="escape_symlink")
        symlink.type = tarfile.SYMTYPE
        symlink.linkname = "...../...../...../...../...../etc"
        tar.addfile(symlink)

    cwd = os.getcwd()
    os.chdir(extract_dir)
    try:
        with TarSafe.open(str(tar_path)) as tar:
            tar.extractall()
    finally:
        os.chdir(cwd)

    link_path = extract_dir / "escape_symlink"
    assert link_path.is_symlink()
    resolved_target = os.path.normpath(
        os.path.join(str(extract_dir), os.readlink(link_path))
    )
    assert resolved_target.startswith(str(extract_dir))
    assert not (extract_dir.parent / "etc").exists()


def _make_sibling_escape_tar(tar_path, dummy_path, member_name):
    with tarfile.open(tar_path, "w") as tar:
        dummy_path.write_text("test")
        tar.add(dummy_path, arcname="dummy.txt")
        ti = tarfile.TarInfo(name=member_name)
        data = b"owned"
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))


@pytest.mark.parametrize(
    "member_name",
    [
        "../sibling/pwned.txt",
        "../../sibling/pwned.txt",
        "/sibling/pwned.txt",
        "../app-secret/pwned.txt",
        "../app-secret/sub/pwned.txt",
        "./../app-secret/pwned.txt",
    ],
)
def test_sibling_prefix_escape_is_blocked(tmp_path, member_name):
    """
    Regression test for a reported bug where the traversal check used an
    unbounded string prefix comparison (root.startswith(...)), so a resolved
    path only had to share a string prefix with the root -- not actually be
    inside it. E.g. with root "/opt/app", the member "../app-secret/owned.txt"
    resolves to "/opt/app-secret/owned.txt", which naively startswith
    "/opt/app" despite being a sibling directory, not a descendant.
    """
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    tar_path = archive_dir / "evil.tar"
    _make_sibling_escape_tar(tar_path, archive_dir / "dummy.txt", member_name)

    cwd = os.getcwd()
    os.chdir(app_dir)
    try:
        with pytest.raises(TarSafeException):
            with TarSafe.open(str(tar_path)) as tar:
                tar.extractall()
    finally:
        os.chdir(cwd)

    assert not (tmp_path / "sibling").exists()
    assert not (tmp_path / "app-secret").exists()


def test_extractall_checks_the_actual_target_path(tmp_path):
    """
    Regression test: the safety check must validate against the directory
    files will actually be written to (the `path` argument of extractall()),
    not the process cwd captured when the TarSafe object was constructed --
    those can differ, e.g. when cwd is unrelated to the upload/extraction
    target directory.
    """
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()

    tar_path = archive_dir / "evil.tar"
    _make_sibling_escape_tar(tar_path, archive_dir / "dummy.txt", "../uploads-secret/pwned.txt")

    unrelated_cwd = tmp_path / "unrelated"
    unrelated_cwd.mkdir()
    cwd = os.getcwd()
    os.chdir(unrelated_cwd)
    try:
        with pytest.raises(TarSafeException):
            with TarSafe.open(str(tar_path)) as tar:
                tar.extractall(path=str(uploads_dir))
    finally:
        os.chdir(cwd)

    assert not (tmp_path / "uploads-secret").exists()


@pytest.mark.parametrize(
    "name",
    [
        "/tmp/x.txt",
        "\\tmp\\x.txt",
        "C:/tmp/x.txt",
        "C:\\tmp\\x.txt",
        "../evil.txt",
    ],
)
def test_looks_suspicious_flags_windows_absolute_paths(name):
    """
    Regression test for a Windows-only gap in the cheap pre-filter that gates
    the (expensive) containment check in _is_traversal_attempt. The old
    condition was `name.startswith(os.sep) or ".." in name`. Tar member names
    always use "/" regardless of host OS, but os.sep is "\\" on Windows, so a
    member named e.g. "/tmp/x.txt" never tripped the pre-filter there, the
    containment check never ran, and os.path.join treated the leading "/" as
    drive-relative -- landing outside the extraction root. This test exercises
    the OS-independent predicate directly so it's verifiable without a real
    Windows host.
    """
    assert TarSafe._looks_suspicious(name) is True


def test_looks_suspicious_allows_plain_relative_names():
    assert TarSafe._looks_suspicious("safe.txt") is False
    assert TarSafe._looks_suspicious("dir/safe.txt") is False


def _get_exposed_members(module):
    return set(module.__all__)
