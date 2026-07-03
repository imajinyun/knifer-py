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
)

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
]
