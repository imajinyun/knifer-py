from __future__ import annotations

import pytest

from kniferpy import vssh
from kniferpy.verr import KniferError, ValidationError


class ExampleProvider:
    def run(self, request: vssh.CommandRequest) -> vssh.CommandResponse:
        return vssh.CommandResponse(
            exit_code=0,
            stdout=f"ran: {request.command}".encode(),
        )

    def list(self, request: vssh.ListRequest) -> vssh.ListResponse:
        return vssh.ListResponse(
            entries=[
                vssh.Entry(
                    name="file.txt", path="/tmp/file.txt", type=vssh.EntryType.FILE, size=100
                ),
                vssh.Entry(name="subdir", path="/tmp/subdir", type=vssh.EntryType.DIRECTORY),
            ]
        )

    def download(self, request: vssh.DownloadRequest) -> vssh.DownloadResponse:
        return vssh.DownloadResponse(
            remote_path=request.remote_path,
            content=b"file content",
            size=12,
        )

    def upload(self, request: vssh.UploadRequest) -> vssh.UploadResponse:
        return vssh.UploadResponse(
            remote_path=request.remote_path,
            size=len(request.content),
        )


# --- EntryType ------------------------------------------------------------


def test_entry_type_constants() -> None:
    assert vssh.EntryType.UNKNOWN == "unknown"
    assert vssh.EntryType.FILE == "file"
    assert vssh.EntryType.DIRECTORY == "directory"
    assert vssh.EntryType.SYMLINK == "symlink"


# --- CommandRequest validation ---------------------------------------------


def test_command_request_valid() -> None:
    req = vssh.CommandRequest(command="ls")
    req.validate()


def test_command_request_empty_command() -> None:
    with pytest.raises(ValidationError, match="command is required"):
        vssh.CommandRequest(command="").validate()


def test_command_request_nul_byte() -> None:
    with pytest.raises(ValidationError, match="nul byte"):
        vssh.CommandRequest(command="ls\x00cat").validate()


def test_command_request_arg_nul_byte() -> None:
    with pytest.raises(ValidationError, match="nul byte"):
        vssh.CommandRequest(command="ls", args=["a\x00b"]).validate()


def test_command_request_negative_max_output() -> None:
    with pytest.raises(ValidationError, match="max bytes"):
        vssh.CommandRequest(command="ls", max_output_bytes=-1).validate()


# --- ListRequest validation ------------------------------------------------


def test_list_request_valid() -> None:
    req = vssh.ListRequest(remote_dir="/tmp")
    req.validate()


def test_list_request_empty_path() -> None:
    with pytest.raises(ValidationError, match="remote path is required"):
        vssh.ListRequest(remote_dir="").validate()


def test_list_request_nul_byte() -> None:
    with pytest.raises(ValidationError, match="nul byte"):
        vssh.ListRequest(remote_dir="/tmp\x00bad").validate()


# --- DownloadRequest validation --------------------------------------------


def test_download_request_valid() -> None:
    req = vssh.DownloadRequest(remote_path="/tmp/file.txt")
    req.validate()


def test_download_request_empty_path() -> None:
    with pytest.raises(ValidationError, match="remote path is required"):
        vssh.DownloadRequest(remote_path="").validate()


def test_download_request_negative_max_bytes() -> None:
    with pytest.raises(ValidationError, match="max bytes"):
        vssh.DownloadRequest(remote_path="/tmp/file.txt", max_bytes=-1).validate()


# --- UploadRequest validation ----------------------------------------------


def test_upload_request_valid() -> None:
    req = vssh.UploadRequest(remote_path="/tmp/file.txt")
    req.validate()


def test_upload_request_empty_path() -> None:
    with pytest.raises(ValidationError, match="remote path is required"):
        vssh.UploadRequest(remote_path="").validate()


def test_upload_request_content_exceeds_max() -> None:
    with pytest.raises(ValidationError, match="upload content has"):
        vssh.UploadRequest(remote_path="/tmp/file.txt", content=b"xxxxx", max_bytes=3).validate()


# --- Client with provider -------------------------------------------------


def test_client_run() -> None:
    client = vssh.Client(provider=ExampleProvider())
    response = client.run(vssh.CommandRequest(command="ls"))
    assert response.exit_code == 0
    assert b"ran: ls" in response.stdout


def test_client_list() -> None:
    client = vssh.Client(provider=ExampleProvider())
    response = client.list(vssh.ListRequest(remote_dir="/tmp"))
    assert len(response.entries) == 2
    assert response.entries[0].name == "file.txt"


def test_client_download() -> None:
    client = vssh.Client(provider=ExampleProvider())
    response = client.download(vssh.DownloadRequest(remote_path="/tmp/file.txt"))
    assert response.content == b"file content"


def test_client_upload() -> None:
    client = vssh.Client(provider=ExampleProvider())
    response = client.upload(vssh.UploadRequest(remote_path="/tmp/new.txt", content=b"hello"))
    assert response.size == 5


def test_client_without_provider_raises() -> None:
    client = vssh.Client()
    with pytest.raises(KniferError, match="missing provider"):
        client.run(vssh.CommandRequest(command="ls"))


def test_client_output_limit_exceeded() -> None:
    client = vssh.Client(provider=ExampleProvider())
    with pytest.raises(KniferError, match="command output has"):
        client.run(vssh.CommandRequest(command="ls", max_output_bytes=1))


def test_client_download_limit_exceeded() -> None:
    client = vssh.Client(provider=ExampleProvider())
    with pytest.raises(KniferError, match="download content has"):
        client.download(vssh.DownloadRequest(remote_path="/tmp/file.txt", max_bytes=1))


def test_client_upload_limit_exceeded() -> None:
    provider = ExampleProvider()
    client = vssh.Client(provider=provider)
    with pytest.raises(KniferError, match="upload content has"):
        client.upload(
            vssh.UploadRequest(remote_path="/tmp/file.txt", content=b"hello", max_bytes=1)
        )
