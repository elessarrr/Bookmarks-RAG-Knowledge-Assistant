import runpy
from unittest.mock import patch


def test_container_entrypoint_binds_external_interface():
    with patch("uvicorn.run") as mock_run:
        runpy.run_path("run.py", run_name="__main__")

    mock_run.assert_called_once_with(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
