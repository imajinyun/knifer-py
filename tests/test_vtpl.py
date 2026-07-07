import pytest

from kniferpy.vtpl import (
    EngineFunc,
    ErrInvalidRenderRequest,
    ErrMissingEngine,
    new_html_engine,
    new_text_engine,
    render,
    render_template,
    render_with_engine,
    render_with_options,
    with_delims,
    with_engine_delims,
    with_engine_func_map,
    with_engine_template_name,
    with_func_map,
    with_template_executor,
    with_template_factory,
    with_template_name,
    with_template_parser,
)

# --- render_template ------------------------------------------------------


def test_render_template():
    out = render_template("hi {{.Name}}", {"Name": "gokit"})
    assert out == "hi gokit"


# --- render and options ---------------------------------------------------


def test_render():
    out = render("hello {{.Name}}", {"Name": "tpl"})
    assert out == "hello tpl"


def test_render_with_options():
    out = render_with_options(
        "hello [[upper .Name]]",
        {"Name": "tpl"},
        with_template_name("custom"),
        with_delims("[[", "]]"),
        with_func_map({"upper": str.upper}),
    )
    assert out == "hello TPL"


def test_render_with_dot():
    out = render("value is {{.}}", {".": "the dot"})
    assert out == "value is the dot"


# --- render_with_options providers ----------------------------------------


def test_render_with_factory_parser_executor():
    factory_called = []
    parser_called = []
    executor_called = []

    def factory(name: str):
        factory_called.append(name)

    def parser(source: str) -> str:
        parser_called.append(source)
        return "provider {{.Name}}"

    def executor(tpl: str, data) -> str:
        executor_called.append(True)
        return render(tpl, data)

    out = render_with_options(
        "ignored",
        {"Name": "provider"},
        with_template_factory(factory),
        with_template_name("provider-name"),
        with_template_parser(parser),
        with_template_executor(executor),
    )
    assert out == "provider provider"
    assert factory_called == ["provider-name"]
    assert parser_called == ["ignored"]
    assert executor_called == [True]


# --- render_with_engine ---------------------------------------------------


def test_render_with_engine():
    engine = EngineFunc(lambda req: f"hello {req.Data['Name']}")
    out = render_with_engine(engine, "{{.Name}}", {"Name": "adapter"})
    assert out == "hello adapter"


def test_render_with_engine_missing():
    with pytest.raises(ErrMissingEngine, match="missing engine"):
        render_with_engine(None, "{{.}}", "x")


def test_render_with_engine_empty_source():
    with pytest.raises(ErrInvalidRenderRequest, match="empty source"):
        render_with_engine(new_text_engine(), "", None)


# --- built-in engines -----------------------------------------------------


def test_html_engine_escapes():
    out = render_with_engine(new_html_engine(), "{{.}}", "<tag>")
    assert out == "&lt;tag&gt;"


def test_text_engine_no_escape():
    out = render_with_engine(new_text_engine(), "{{.}}", "<tag>")
    assert out == "<tag>"


def test_text_engine_with_func_map():
    engine = new_text_engine(
        with_engine_template_name("custom"),
        with_engine_delims("[[", "]]"),
        with_engine_func_map({"upper": str.upper}),
    )
    out = render_with_engine(engine, "[[upper .Name]]", {"Name": "facade"})
    assert out == "FACADE"


def test_html_engine_with_func_map():
    engine = new_html_engine(with_engine_func_map({"upper": str.upper}))
    out = render_with_engine(engine, "{{upper .Name}}", {"Name": "html"})
    assert out == "HTML"


# --- render_with_engine error contracts -----------------------------------


def test_render_with_engine_error_missing():
    with pytest.raises(ErrMissingEngine, match="missing engine"):
        render_with_engine(None, "{{.}}", "x")


def test_render_with_engine_empty_source_err():
    with pytest.raises(ErrInvalidRenderRequest, match="empty source"):
        render_with_engine(new_text_engine(), "", None)


# --- render_with_options error propagation --------------------------------


def test_render_with_options_parser_error():
    with pytest.raises(RuntimeError, match="parse failed"):
        render_with_options(
            "bad",
            None,
            with_template_parser(lambda src: (_ for _ in ()).throw(RuntimeError("parse failed"))),
        )


def test_render_with_options_executor_error():
    with pytest.raises(RuntimeError, match="execute failed"):
        render_with_options(
            "ok",
            None,
            with_template_executor(
                lambda tpl, data: (_ for _ in ()).throw(RuntimeError("execute failed"))
            ),
        )


# --- render simple data types ---------------------------------------------


def test_render_none_data():
    out = render("hello", None)
    assert out == "hello"


def test_render_scalar_data():
    out = render("{{.}}", "world")
    assert out == "world"


def test_render_dict_data():
    out = render("{{.Name}}", {"Name": "tpl"})
    assert out == "tpl"


# --- custom delimiters ----------------------------------------------------


def test_custom_delimiters():
    out = render_with_options("hello [[.Name]]", {"Name": "tpl"}, with_delims("[[", "]]"))
    assert out == "hello tpl"


# --- render default -------------------------------------------------------


def test_render_default():
    out = render("hi {{.Name}}", {"Name": "go"})
    assert out == "hi go"


# --- render_template default ----------------------------------------------


def test_render_template_default():
    out = render_template("hi {{.Name}}", {"Name": "python"})
    assert out == "hi python"
