
import json
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from utils.etl_tools import ETLTools


API_URL = "https://pokeapi.co/api/v2/pokemon?limit=2"


def make_mock_response():
    payload = {
        "results": [
            {
                "name": "bulbasaur",
                "url": "https://pokeapi.co/api/v2/pokemon/1/"
            },
            {
                "name": "ivysaur",
                "url": "https://pokeapi.co/api/v2/pokemon/2/"
            }
        ]
    }

    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.iter_content.return_value = [
        json.dumps(payload).encode("utf-8")
    ]
    return response


def test_safe_extract_success(tmp_path):
    with patch("utils.etl_tools.requests.get") as mock_get:
        mock_get.return_value = make_mock_response()

        result = ETLTools().safe_extract_api(
            url=API_URL,
            output_file="extract/test_mock_pokemon.csv"
        )

        assert result["status"] == "success"
        assert result["rows"] == 2

        df = pd.read_csv(result["output_file"])

        assert len(df) == 2
        assert df.iloc[0]["name"] == "bulbasaur"
        assert df.iloc[1]["name"] == "ivysaur"

        mock_get.assert_called_once()

        # Remove only the file created by this test.
        from pathlib import Path
        Path(result["output_file"]).unlink(missing_ok=True)


def test_reject_unapproved_api():
    with patch("utils.etl_tools.requests.get") as mock_get:
        with pytest.raises(ValueError, match="approved PokeAPI"):
            ETLTools().safe_extract_api(
                url="https://example.com/api/data",
                output_file="extract/invalid_api.csv"
            )

        mock_get.assert_not_called()


def test_reject_path_traversal():
    with patch("utils.etl_tools.requests.get") as mock_get:
        with pytest.raises(ValueError, match="inside the data directory"):
            ETLTools().safe_extract_api(
                url=API_URL,
                output_file="../outside.csv"
            )

        mock_get.assert_not_called()


def test_reject_excessive_limit():
    with patch("utils.etl_tools.requests.get") as mock_get:
        with pytest.raises(ValueError, match="between 1 and 100"):
            ETLTools().safe_extract_api(
                url="https://pokeapi.co/api/v2/pokemon?limit=1000",
                output_file="extract/too_many.csv"
            )

        mock_get.assert_not_called()
