"""Provider-neutral FTP operation facade.

Ports knifer-go's internal/ftp with Python-idiomatic mappings:

- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional options -> keyword args
- Go error sentinels -> KniferError with codes

Errors use kniferpy.verr types with codes knifer.ftp.<reason>.
"""

from __future__ import annotations

import copy
import dataclasses
from datetime import datetime
from typing import Protocol

from kniferpy.verr import KniferError, ValidationError


class EntryType:
    UNKNOWN = "unknown"
    FILE = "file"
    DIRECTORY = "directory"


@dataclasses.dataclass(slots=True)
class Entry:
    name: str = ""
    path: str = ""
    type: str = EntryType.UNKNOWN
    size: int = 0
    modified: datetime | None = None
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class ListRequest:
    remote_dir: str
    recursive: bool = False
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        _validate_remote_path(self.remote_dir, "knifer.ftp.invalid_list_request")

    def clone(self) -> ListRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class ListResponse:
    entries: list[Entry] = dataclasses.field(default_factory=list)
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class DownloadRequest:
    remote_path: str
    max_bytes: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        code = "knifer.ftp.invalid_download_request"
        _validate_remote_path(self.remote_path, code)
        _validate_limit(self.max_bytes, code)

    def clone(self) -> DownloadRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class DownloadResponse:
    remote_path: str = ""
    content: bytes = b""
    size: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class UploadRequest:
    remote_path: str
    content: bytes = b""
    max_bytes: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        code = "knifer.ftp.invalid_upload_request"
        _validate_remote_path(self.remote_path, code)
        _validate_limit(self.max_bytes, code)
        if self.max_bytes > 0 and len(self.content) > self.max_bytes:
            raise ValidationError(
                message=f"upload content has {len(self.content)} bytes," f" max {self.max_bytes}",
                code="knifer.ftp.transfer_limit_exceeded",
            )

    def clone(self) -> UploadRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class UploadResponse:
    remote_path: str = ""
    size: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


class Provider(Protocol):
    def list(self, request: ListRequest) -> ListResponse: ...

    def download(self, request: DownloadRequest) -> DownloadResponse: ...

    def upload(self, request: UploadRequest) -> UploadResponse: ...


class Client:
    def __init__(self, provider: Provider | None = None) -> None:
        self._provider = provider

    def list(self, request: ListRequest) -> ListResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ftp.missing_provider")
        request.validate()
        return self._provider.list(request.clone())

    def download(self, request: DownloadRequest) -> DownloadResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ftp.missing_provider")
        request.validate()
        response = self._provider.download(request.clone())
        if request.max_bytes > 0 and len(response.content) > request.max_bytes:
            raise KniferError(
                message=f"download content has {len(response.content)} bytes,"
                f" max {request.max_bytes}",
                code="knifer.ftp.transfer_limit_exceeded",
            )
        return response

    def upload(self, request: UploadRequest) -> UploadResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ftp.missing_provider")
        request.validate()
        response = self._provider.upload(request.clone())
        if request.max_bytes > 0 and response.size > request.max_bytes:
            raise KniferError(
                message=f"uploaded {response.size} bytes, max {request.max_bytes}",
                code="knifer.ftp.transfer_limit_exceeded",
            )
        return response


def _validate_remote_path(path: str, code: str) -> None:
    if not path.strip():
        raise ValidationError(message="remote path is required", code=code)
    if "\x00" in path:
        raise ValidationError(message="remote path contains nul byte", code=code)


def _validate_limit(max_bytes: int, code: str) -> None:
    if max_bytes < 0:
        raise ValidationError(message="max bytes must be non-negative", code=code)
