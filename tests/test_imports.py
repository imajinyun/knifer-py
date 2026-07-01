def test_package_imports() -> None:
    import kniferpy

    assert "vjson" in kniferpy.__all__
    assert "vhttp" in kniferpy.__all__
