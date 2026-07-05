"""Provider-neutral SSH/SFTP operation facade.

Thin facade over kniferpy.internal.sshx, porting knifer-go's vssh surface.

Python-idiomatic mappings:
- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional With* options -> keyword args on Client constructor
- Go error sentinels -> KniferError with codes knifer.ssh.*

Omitted (Go-specific):
- context.Context cancellation (not needed in sync Python)
- WithProvider functional option (provider is a constructor arg)
"""

from __future__ import annotations

from kniferpy.internal.sshx import (
    Client,
    CommandRequest,
    CommandResponse,
    DownloadRequest,
    DownloadResponse,
    Entry,
    EntryType,
    ListRequest,
    ListResponse,
    Provider,
    UploadRequest,
    UploadResponse,
    download as _download,
    list as _list,
    new as _new,
    run as _run,
    upload as _upload,
)
from kniferpy.verr import KniferError, ValidationError

# ── EntryType constants ────────────────────────────────────────────────────────

EntryTypeUnknown = EntryType.UNKNOWN
EntryTypeFile = EntryType.FILE
EntryTypeDirectory = EntryType.DIRECTORY
EntryTypeSymlink = EntryType.SYMLINK

# ── Error sentinels ────────────────────────────────────────────────────────────

ErrInvalidCommandRequest = ValidationError(message="malformed command request", code="knifer.ssh.invalid_command_request")
ErrInvalidListRequest = ValidationError(message="malformed list request", code="knifer.ssh.invalid_list_request")
ErrInvalidDownloadRequest = ValidationError(message="malformed download request", code="knifer.ssh.invalid_download_request")
ErrInvalidUploadRequest = ValidationError(message="malformed upload request", code="knifer.ssh.invalid_upload_request")
ErrOutputLimitExceeded = KniferError(message="output limit exceeded", code="knifer.ssh.output_limit_exceeded")
ErrTransferLimitExceeded = KniferError(message="transfer limit exceeded", code="knifer.ssh.transfer_limit_exceeded")
ErrMissingProvider = KniferError(message="missing provider", code="knifer.ssh.missing_provider")

# ── Go-compat standalone convenience functions ─────────────────────────────────

new = _new
run = _run
list = _list  # noqa: A001
download = _download
upload = _upload

__all__ = [
    "Client",
    "CommandRequest",
    "CommandResponse",
    "DownloadRequest",
    "DownloadResponse",
    "Entry",
    "EntryType",
    "ListRequest",
    "ListResponse",
    "Provider",
    "UploadRequest",
    "UploadResponse",
    # EntryType constants
    "EntryTypeUnknown",
    "EntryTypeFile",
    "EntryTypeDirectory",
    "EntryTypeSymlink",
    # Error sentinels
    "ErrInvalidCommandRequest",
    "ErrInvalidListRequest",
    "ErrInvalidDownloadRequest",
    "ErrInvalidUploadRequest",
    "ErrOutputLimitExceeded",
    "ErrTransferLimitExceeded",
    "ErrMissingProvider",
    # Go-compat standalone functions
    "new",
    "run",
    "list",
    "download",
    "upload",
]
