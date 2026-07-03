from __future__ import annotations

import pytest

from kniferpy import vftp
from kniferpy.verr import KniferError, ValidationError


class ExampleProvider:
    def list(self, request: vftp.ListRequest) -> vftp.ListResponse:
        return vftp.ListResponse(
            entries=[
                vftp.Entry(
                    name="file.txt", path="/tmp/file.txt", type=vftp.EntryType.FILE, size=100
                ),
                vftp.Entry(name="subdir", path="/tmp/subdir", type=vftp.EntryType.DIRECTORY),
            ]
        )

    def download(self, request: vftp.DownloadRequest) -> vftp.DownloadResponse:
        return vftp.DownloadResponse(
            remote_path=request.remote_path,
            content=b"file content",
            size=12,
        )

    def upload(self, request: vftp.UploadRequest) -> vftp.UploadResponse:
        return vftp.UploadResponse(
            remote_path=request.remote_path,
            size=len(request.content),
        )


def test_entry_type_constants() -> None:
    assert vftp.EntryType.UNKNOWN == "unknown"
    assert vftp.EntryType.FILE == "file"
    assert vftp.EntryType.DIRECTORY == "directory"


def test_list_request_valid() -> None:
    req = vftp.ListRequest(remote_dir="/tmp")
    req.validate()


def test_list_request_empty_path() -> None:
    with pytest.raises(ValidationError, match="remote path is required"):
        vftp.ListRequest(remote_dir="").validate()


def test_list_request_nul_byte() -> None:
    with pytest.raises(ValidationError, match="nul byte"):
        vftp.ListRequest(remote_dir="/tmp\x00bad").validate()


def test_download_request_valid() -> None:
    req = vftp.DownloadRequest(remote_path="/tmp/file.txt")
    req.validate()


def test_download_request_empty_path() -> None:
    with pytest.raises(ValidationError, match="remote path is required"):
        vftp.DownloadRequest(remote_path="").validate()


def test_download_request_negative_max_bytes() -> None:
    with pytest.raises(ValidationError, match="max bytes"):
        vftp.DownloadRequest(remote_path="/tmp/file.txt", max_bytes=-1).validate()


def test_upload_request_valid() -> None:
    req = vftp.UploadRequest(remote_path="/tmp/file.txt")
    req.validate()


def test_upload_request_content_exceeds_max() -> None:
    with pytest.raises(ValidationError, match="upload content has"):
        vftp.UploadRequest(remote_path="/tmp/file.txt", content=b"xxxxx", max_bytes=3).validate()


def test_client_list() -> None:
    client = vftp.Client(provider=ExampleProvider())
    response = client.list(vftp.ListRequest(remote_dir="/tmp"))
    assert len(response.entries) == 2
    assert response.entries[0].name == "file.txt"


def test_client_download() -> None:
    client = vftp.Client(provider=ExampleProvider())
    response = client.download(vftp.DownloadRequest(remote_path="/tmp/file.txt"))
    assert response.content == b"file content"


def test_client_upload() -> None:
    client = vftp.Client(provider=ExampleProvider())
    response = client.upload(vftp.UploadRequest(remote_path="/tmp/new.txt", content=b"hello"))
    assert response.size == 5


def test_client_without_provider_raises() -> None:
    client = vftp.Client()
    with pytest.raises(KniferError, match="missing provider"):
        client.list(vftp.ListRequest(remote_dir="/tmp"))


def test_client_download_limit_exceeded() -> None:
    client = vftp.Client(provider=ExampleProvider())
    with pytest.raises(KniferError, match="download content has"):
        client.download(vftp.DownloadRequest(remote_path="/tmp/file.txt", max_bytes=1))


def test_client_upload_limit_exceeded() -> None:
    client = vftp.Client(provider=ExampleProvider())
    with pytest.raises(KniferError, match="upload content has"):
        client.upload(
            vftp.UploadRequest(remote_path="/tmp/file.txt", content=b"hello", max_bytes=1)
        )
