from project_x_ai.contracts import CONTRACT_VERSION, validate_result


def sample_payload() -> dict:
    return {
        "contract": CONTRACT_VERSION,
        "job_id": "job-1",
        "pipeline_version": "skeleton",
        "model_versions": {},
        "media_info": {"duration_ms": 0, "width": 0, "height": 0},
        "coverage": {"sampled_frames": 0, "decode_failures": 0},
        "observations": [],
        "warnings": [],
    }


def test_cv_result_round_trips_documented_contract_fields() -> None:
    result = validate_result(sample_payload())
    assert result.to_dict() == sample_payload()


def test_cv_result_rejects_invalid_observation_window() -> None:
    payload = sample_payload()
    payload["observations"] = [{"window_start_ms": 10, "window_end_ms": 10}]
    try:
        validate_result(payload)
    except ValueError as error:
        assert "windows" in str(error)
    else:
        raise AssertionError("invalid observation window was accepted")


def test_contract_version_is_required() -> None:
    payload = sample_payload()
    payload["contract"] = "cv-observations/v2"
    try:
        validate_result(payload)
    except ValueError as error:
        assert "contract" in str(error)
    else:
        raise AssertionError("unsupported contract version was accepted")
