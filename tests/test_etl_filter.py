from pathlib import Path

import pandas as pd
import pytest

from utils.etl_tools import ETLTools


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_safe_filter_csv(tmp_path):
    tool = ETLTools()

    input_file = DATA_DIR / "test_input.csv"
    output_file = DATA_DIR / "test_output.csv"

    try:
        df = pd.DataFrame({
            "name": ["bulbasaur", "ivysaur", "charmander"],
            "type": ["grass", "grass", "fire"]
        })

        df.to_csv(input_file, index=False)

        result = tool.safe_filter_csv(
            input_file="test_input.csv",
            output_file="test_output.csv",
            column="name",
            value="bulbasaur"
        )

        assert result["status"] == "success"
        assert result["rows"] == 1

        filtered_df = pd.read_csv(output_file)

        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]["name"] == "bulbasaur"

    finally:
        input_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)


def test_filter_invalid_column():
    tool = ETLTools()

    input_file = DATA_DIR / "test_invalid_column.csv"
    output_file = DATA_DIR / "test_invalid_output.csv"

    try:
        pd.DataFrame({
            "name": ["bulbasaur"]
        }).to_csv(input_file, index=False)

        with pytest.raises(ValueError, match="does not exist"):
            tool.safe_filter_csv(
                input_file="test_invalid_column.csv",
                output_file="test_invalid_output.csv",
                column="unknown_column",
                value="bulbasaur"
            )

    finally:
        input_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)


def test_filter_path_traversal():
    tool = ETLTools()

    with pytest.raises(ValueError, match="inside the data directory"):
        tool.safe_filter_csv(
            input_file="../outside.csv",
            output_file="test_output.csv",
            column="name",
            value="bulbasaur"
        )