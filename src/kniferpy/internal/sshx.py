"""Provider-neutral SSH/SFTP operation facade.

Ports knifer-go's internal/ssh with Python-idiomatic mappings:

- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional options -> keyword args
- Go error sentinels -> KniferError with codes

Errors use kniferpy.verr types with codes knifer.ssh.<reason>.
"""

from __future__ import annotations

import copy
import dataclasses
from datetime import datetime
from typing import Protocol

from kniferpy.verr import KniferError, ValidationError


class EntryType:
    """Kind of remote SFTP entry."""

    UNKNOWN = "unknown"
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


@dataclasses.dataclass(slots=True)
class Entry:
    """One remote SFTP directory entry."""

    name: str = ""
    path: str = ""
    type: str = EntryType.UNKNOWN
    size: int = 0
    modified: datetime | None = None
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class CommandRequest:
    """Remote SSH command request."""

    command: str
    args: list[str] = dataclasses.field(default_factory=list)
    max_output_bytes: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        code = "knifer.ssh.invalid_command_request"
        if not self.command.strip():
            raise ValidationError(message="command is required", code=code)
        if "\x00" in self.command:
            raise ValidationError(message="command contains nul byte", code=code)
        for i, arg in enumerate(self.args):
            if "\x00" in arg:
                raise ValidationError(message=f"arg {i} contains nul byte", code=code)
        _validate_limit(self.max_output_bytes, code)

    def clone(self) -> CommandRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class CommandResponse:
    """Remote command output and exit metadata."""

    exit_code: int = 0
    stdout: bytes = b""
    stderr: bytes = b""
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class ListRequest:
    """Remote SFTP directory listing request."""

    remote_dir: str
    recursive: bool = False
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        _validate_remote_path(self.remote_dir, "knifer.ssh.invalid_list_request")

    def clone(self) -> ListRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class ListResponse:
    """Remote SFTP directory entries."""

    entries: list[Entry] = dataclasses.field(default_factory=list)
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class DownloadRequest:
    """Remote SFTP file download request."""

    remote_path: str
    max_bytes: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        code = "knifer.ssh.invalid_download_request"
        _validate_remote_path(self.remote_path, code)
        _validate_limit(self.max_bytes, code)

    def clone(self) -> DownloadRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class DownloadResponse:
    """Downloaded bytes and transfer metadata."""

    remote_path: str = ""
    content: bytes = b""
    size: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class UploadRequest:
    """In-memory SFTP upload to a remote path."""

    remote_path: str
    content: bytes = b""
    max_bytes: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        code = "knifer.ssh.invalid_upload_request"
        _validate_remote_path(self.remote_path, code)
        _validate_limit(self.max_bytes, code)
        if self.max_bytes > 0 and len(self.content) > self.max_bytes:
            raise ValidationError(
                message=f"upload content has {len(self.content)} bytes," f" max {self.max_bytes}",
                code="knifer.ssh.transfer_limit_exceeded",
            )

    def clone(self) -> UploadRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class UploadResponse:
    """Upload transfer metadata."""

    remote_path: str = ""
    size: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


class Provider(Protocol):
    """Performs provider-specific SSH/SFTP operations for validated requests."""

    def run(self, request: CommandRequest) -> CommandResponse: ...

    def list(self, request: ListRequest) -> ListResponse: ...

    def download(self, request: DownloadRequest) -> DownloadResponse: ...

    def upload(self, request: UploadRequest) -> UploadResponse: ...


class Client:
    """Routes validated SSH/SFTP requests to an injected provider."""

    def __init__(self, provider: Provider | None = None) -> None:
        self._provider = provider

    def run(self, request: CommandRequest) -> CommandResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ssh.missing_provider")
        request.validate()
        response = self._provider.run(request.clone())
        if request.max_output_bytes > 0:
            output_bytes = len(response.stdout) + len(response.stderr)
            if output_bytes > request.max_output_bytes:
                raise KniferError(
                    message=f"command output has {output_bytes} bytes,"
                    f" max {request.max_output_bytes}",
                    code="knifer.ssh.output_limit_exceeded",
                )
        return response

    def list(self, request: ListRequest) -> ListResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ssh.missing_provider")
        request.validate()
        return self._provider.list(request.clone())

    def download(self, request: DownloadRequest) -> DownloadResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ssh.missing_provider")
        request.validate()
        response = self._provider.download(request.clone())
        if request.max_bytes > 0 and len(response.content) > request.max_bytes:
            raise KniferError(
                message=f"download content has {len(response.content)} bytes,"
                f" max {request.max_bytes}",
                code="knifer.ssh.transfer_limit_exceeded",
            )
        return response

    def upload(self, request: UploadRequest) -> UploadResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.ssh.missing_provider")
        request.validate()
        response = self._provider.upload(request.clone())
        if request.max_bytes > 0 and response.size > request.max_bytes:
            raise KniferError(
                message=f"uploaded {response.size} bytes, max {request.max_bytes}",
                code="knifer.ssh.transfer_limit_exceeded",
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


# ── Go-compat standalone convenience functions ──────────────────────────────


def new(provider: Provider | None = None) -> Client:
    """Create a new SSH client (Go compat)."""
    return Client(provider=provider)


def run(provider: Provider, request: CommandRequest) -> CommandResponse:
    """Run a command via the provider (Go compat)."""
    return Client(provider=provider).run(request)


def list(provider: Provider, request: ListRequest) -> ListResponse:
    """List directory entries via the provider (Go compat)."""
    return Client(provider=provider).list(request)


def download(provider: Provider, request: DownloadRequest) -> DownloadResponse:
    """Download a file via the provider (Go compat)."""
    return Client(provider=provider).download(request)


def upload(provider: Provider, request: UploadRequest) -> UploadResponse:
    """Upload a file via the provider (Go compat)."""
    return Client(provider=provider).upload(request)
