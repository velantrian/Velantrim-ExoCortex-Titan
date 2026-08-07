"""One-shot exact patch for OpenLoop adapter result-level as_of ownership."""

from pathlib import Path


path = Path("core/continuity/open_loop_source_adapter.py")
text = path.read_text(encoding="utf-8")

projection_as_of = '        "as_of": _dt(projection.as_of),\n'
if text.count(projection_as_of) != 1:
    raise SystemExit(
        f"expected one projection as_of payload line, found {text.count(projection_as_of)}"
    )
text = text.replace(projection_as_of, "")

validation = '''    if projection.as_of != result.as_of:
        raise ContinuitySourceAdmissionError(
            "OpenLoop projection as_of does not match result as_of"
        )
'''
if text.count(validation) != 1:
    raise SystemExit(
        f"expected one projection as_of validation block, found {text.count(validation)}"
    )
text = text.replace(validation, "")

path.write_text(text, encoding="utf-8")
