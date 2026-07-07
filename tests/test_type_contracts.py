from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
from typing import Any, cast, get_args, get_origin

import kniferpy
from kniferpy import vai, vcache, vdb, vftp, vhan, vhttp, vssh, vsys, vtok
from kniferpy.internal import aix, cachex, dbx, ftpx, httpx, pinyinx, sshx, sysx, tokenizex


def _public_module_names() -> list[str]:
    return sorted(
        name
        for _, name, is_pkg in pkgutil.iter_modules(kniferpy.__path__)
        if not is_pkg and (name.startswith("v") or name in {"verr", "vid"})
    )


def test_root_exports_resolve_to_public_modules() -> None:
    public_modules = set(_public_module_names())

    for name in kniferpy.__all__:
        assert name in public_modules
        importlib.import_module(f"kniferpy.{name}")


def test_public_module_all_exports_resolve() -> None:
    for module_name in _public_module_names():
        module = importlib.import_module(f"kniferpy.{module_name}")
        explicit_exports = getattr(module, "__all__", None)
        if explicit_exports is None:
            continue
        for export in explicit_exports:
            assert hasattr(module, export), f"{module_name}.{export} is listed in __all__"


def test_facade_reexports_keep_identity_for_core_contract_types() -> None:
    assert vhttp.HTTPRequest is httpx.HTTPRequest
    assert vhttp.HTTPResponse is httpx.HTTPResponse
    assert vhttp.URLPolicy is httpx.URLPolicy
    assert vhttp.SessionLike is httpx.SessionLike
    assert vhttp.ResponseLike is httpx.ResponseLike
    assert vdb.Entity is dbx.Entity
    assert vdb.SQLBuilder is dbx.SQLBuilder
    assert vcache.Cache is cachex.Cache
    assert vcache.CacheListener is cachex.CacheListener
    assert vtok.Provider is tokenizex.Provider
    assert vssh.Provider is sshx.Provider
    assert vftp.Provider is ftpx.Provider
    assert vhan.Provider is pinyinx.Provider
    assert vai.ChatProvider is aix.ChatProvider
    assert vsys.OsInfo is sysx.OsInfo


def test_provider_protocol_method_shapes() -> None:
    provider_methods = {
        vtok.Provider: {"tokenize", "keywords"},
        vssh.Provider: {"run", "list", "download", "upload"},
        vftp.Provider: {"list", "download", "upload"},
        vhan.Provider: {"convert", "initials"},
        vai.ChatProvider: {"chat"},
        vai.EmbeddingProvider: {"embed"},
        vhttp.SessionLike: {"request", "get", "post", "put", "delete", "patch", "head", "options"},
    }

    for protocol, methods in provider_methods.items():
        for method in methods:
            member = getattr(protocol, method)
            assert callable(member), f"{protocol.__name__}.{method} must stay callable"
            assert "self" in inspect.signature(member).parameters


def test_request_response_dataclasses_keep_slots_and_mutable_defaults() -> None:
    dataclass_types = [
        vtok.Token,
        vtok.Keyword,
        vtok.TokenizeRequest,
        vtok.TokenizeResponse,
        vtok.KeywordsRequest,
        vtok.KeywordsResponse,
        vssh.CommandRequest,
        vssh.CommandResponse,
        vssh.ListRequest,
        vssh.ListResponse,
        vssh.DownloadRequest,
        vssh.DownloadResponse,
        vssh.UploadRequest,
        vssh.UploadResponse,
        vftp.ListRequest,
        vftp.ListResponse,
        vftp.DownloadRequest,
        vftp.DownloadResponse,
        vftp.UploadRequest,
        vftp.UploadResponse,
        vhan.ConvertRequest,
        vhan.ConvertResponse,
        vhan.InitialsRequest,
        vhan.InitialsResponse,
        vai.ChatRequest,
        vai.ChatResponse,
        vai.EmbeddingRequest,
        vai.EmbeddingResponse,
    ]

    for cls in dataclass_types:
        assert dataclasses.is_dataclass(cls), f"{cls.__name__} must remain a dataclass"

    slotted_contracts = [
        vtok.Token,
        vtok.Keyword,
        vtok.TokenizeRequest,
        vtok.TokenizeResponse,
        vtok.KeywordsRequest,
        vtok.KeywordsResponse,
        vssh.CommandRequest,
        vssh.CommandResponse,
        vssh.ListRequest,
        vssh.ListResponse,
        vssh.DownloadRequest,
        vssh.DownloadResponse,
        vssh.UploadRequest,
        vssh.UploadResponse,
        vftp.ListRequest,
        vftp.ListResponse,
        vftp.DownloadRequest,
        vftp.DownloadResponse,
        vftp.UploadRequest,
        vftp.UploadResponse,
    ]

    for cls in slotted_contracts:
        assert hasattr(cls, "__slots__"), f"{cls.__name__} must keep slots"

    token_a = vtok.Token(text="a")
    token_b = vtok.Token(text="b")
    token_a.metadata["k"] = "v"
    assert token_b.metadata == {}

    command_a = vssh.CommandRequest(command="echo")
    command_b = vssh.CommandRequest(command="echo")
    command_a.args.append("hello")
    assert command_b.args == []

    chat_a = vai.ChatRequest(Model="m")
    chat_b = vai.ChatRequest(Model="m")
    chat_a.Messages.append(vai.Message(Role=vai.RoleUser, Content="hello"))
    assert chat_b.Messages == []


def test_structured_aliases_and_protocols_keep_runtime_contracts() -> None:
    json_origin = get_origin(vhttp.JSONValue)
    json_args = get_args(vhttp.JSONValue)
    assert json_origin is not None
    assert type(None) in json_args
    assert str in json_args

    assert vcache.Option is cachex.Option
    assert callable(vcache.with_capacity(10))

    entity = vdb.entity_from_map("users", {"name": "alice", "skip": None})
    assert entity.__table__ == "users"
    assert entity.fields == {"name": "alice"}
    assert cast(Any, entity).name == "alice"


def test_http_sessionlike_accepts_structural_fake() -> None:
    class Response:
        text = "ok"
        content = b"ok"
        status_code = 200
        headers: dict[str, str] = {}

        def raise_for_status(self) -> None:
            return None

    class Session:
        headers: dict[str, str] = {}

        def request(self, method: str, url: str, **kwargs: Any) -> Response:
            return Response()

        def get(self, url: str, timeout: float, **kwargs: Any) -> Response:
            return Response()

        def post(
            self, url: str, json: vhttp.JSONValue | None = None, timeout: float = 1.0, **kwargs: Any
        ) -> Response:
            return Response()

        def put(
            self, url: str, json: vhttp.JSONValue | None = None, timeout: float = 1.0, **kwargs: Any
        ) -> Response:
            return Response()

        def delete(self, url: str, timeout: float, **kwargs: Any) -> Response:
            return Response()

        def patch(
            self, url: str, json: vhttp.JSONValue | None = None, timeout: float = 1.0, **kwargs: Any
        ) -> Response:
            return Response()

        def head(self, url: str, timeout: float, **kwargs: Any) -> Response:
            return Response()

        def options(self, url: str, timeout: float, **kwargs: Any) -> Response:
            return Response()

    option = vhttp.with_session(Session())
    request = vhttp.HTTPRequest()
    option(request)
    assert request.session is not None
