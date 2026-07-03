"""Provider-neutral FTP operation facade.

Thin facade over kniferpy.internal.ftpx, porting knifer-go's vftp surface.

Python-idiomatic mappings:
- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional With* options -> keyword args on Client constructor
- Go error sentinels -> KniferError with codes knifer.ftp.*

Omitted (Go-specific):
- context.Context cancellation (synchronous Python)
- WithProvider functional option (provider is a constructor arg)
"""

from __future__ import annotations

from kniferpy.internal.ftpx import (
    Client,
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
