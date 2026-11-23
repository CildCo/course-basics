import pytest

from pipeline_demo.release import (
    artifact_name,
    bump,
    checksum,
    parse_version,
    release_tag,
)


def test_parse_version():
    assert parse_version("1.2.3") == (1, 2, 3)


@pytest.mark.parametrize("text", ["1.2", "v1.2.3", "1.2.3.4", ""])
def test_parse_version_rejects_bad_input(text):
    with pytest.raises(ValueError):
        parse_version(text)


def test_bump():
    assert bump("1.2.3", "patch") == "1.2.4"
    assert bump("1.2.3", "minor") == "1.3.0"
    assert bump("1.2.3", "major") == "2.0.0"


def test_bump_rejects_unknown_part():
    with pytest.raises(ValueError):
        bump("1.2.3", "beta")


def test_release_tag():
    assert release_tag("0.3.0", "abcdef123456") == "v0.3.0-abcdef1"


def test_artifact_name():
    assert artifact_name("Pipeline_Demo", "0.3.0") == "pipeline-demo-0.3.0-py3-none-any.whl"


def test_checksum_is_stable():
    assert checksum(b"wheel") == checksum(b"wheel")
    assert checksum(b"wheel") != checksum(b"wheel ")
    assert len(checksum(b"wheel")) == 64
