from kniferpy.verr import KniferError, ValidationError


def test_validation_error_keeps_code_and_context() -> None:
    err = ValidationError("invalid URL", code="url.invalid", context={"url": "ftp://x"})

    assert isinstance(err, KniferError)
    assert str(err) == "invalid URL"
    assert err.code == "url.invalid"
    assert err.context == {"url": "ftp://x"}
