import os
import requests
import pandas as pd

class ETLTools:

    def __init__(self):
        pass

    def extract_load(self,url:str, output_folder:str, format:str):
        """
        This tool extracts the data from the API (url) and loads it into the
        the desired location (output_folder).

        Args:
            url (str): The API endpoint from which to extract data.
            output_folder (str): The folder where the extracted data will be saved.

        Returns:
            str: A message indicating the success or failure of the operation.

        """

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        output_folder = os.path.join(project_root, output_folder)

        try:
            response = requests.get(url)
            response.raise_for_status()
            data  = response.json()

            filename = os.path.join(output_folder, f"extracted_data.{format}")
            os.makedirs(output_folder, exist_ok=True)

            df = pd.json_normalize(data['results'])
            if format == "csv":
                df.to_csv(filename, index=False)
            elif format == "json":
                df.to_json(filename, orient="records", lines=True)
            elif format == "parquet":
                df.to_parquet(filename, index=False)
            else:
                return f"Unsupported format: {format}"

            return f"Data successfully extracted and saved to {filename}"
        except requests.exceptions.RequestException as e:
            return f"Failed to extract data: {e}"


# if __name__ == "__main__":
#     obj = ETLTools()
#     print(obj.extract_load("https://pokeapi.co/api/v2/pokemon/", "data/extract", "csv"))


    def transform_load_context(self, file_path:str):
        """
        This tool transforms the data from the specified file and loads it into the
        desired location (output_folder).

        Args:
            file_path (str): The path to the file containing the data to be transformed.
            output_folder (str): The folder where the transformed data will be saved.
            output_format (str): The format in which to save the transformed data (csv, json, parquet).
        Returns:
            str: A message indicating the success or failure of the operation.
        """

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".csv":
            df = pd.read_csv(file_path)
        elif file_extension == ".json":
            df = pd.read_json(file_path, lines=True)
        elif file_extension == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            return f"Unsupported file format: {file_extension}"

        top_3_rows = str(df.head(3))

        return top_3_rows

    def safe_filter_csv(
        self,
        input_file: str,
        output_file: str,
        column: str,
        value: str
    ):
        from pathlib import Path

        data_root = (
            Path(__file__).resolve().parent.parent / "data"
        ).resolve()

        def validate_path(file_path):
            path = Path(file_path)

            if path.is_absolute():
                resolved = path.resolve()
            else:
                resolved = (data_root / path).resolve()

            if not resolved.is_relative_to(data_root):
                raise ValueError("File must be inside the data directory")

            if resolved.suffix.lower() != ".csv":
                raise ValueError("Only CSV files are supported")

            return resolved

        source = validate_path(input_file)
        destination = validate_path(output_file)

        if not source.is_file():
            raise FileNotFoundError("Input CSV file does not exist")

        if source == destination:
            raise ValueError("Input and output files must be different")

        df = pd.read_csv(source)

        if column not in df.columns:
            raise ValueError(f"Column '{column}' does not exist")

        filtered_df = df[df[column].astype(str) == str(value)]

        destination.parent.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(destination, index=False)

        return {
            "status": "success",
            "rows": len(filtered_df),
            "output_file": str(destination)
        }

    def safe_extract_api(self, url: str, output_file: str) -> dict:
        import json
        from pathlib import Path
        from urllib.parse import urlparse, parse_qs

        import pandas as pd
        import requests

        data_root = (
            Path(__file__).resolve().parent.parent / "data"
        ).resolve()

        data_root.mkdir(parents=True, exist_ok=True)

        # Restrict extraction to the approved Pokemon API.
        parsed = urlparse(url)

        if (
            parsed.scheme != "https"
            or parsed.hostname != "pokeapi.co"
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in (
                "/api/v2/pokemon",
                "/api/v2/pokemon/"
            )
            or parsed.fragment
        ):
            raise ValueError("Only the approved PokeAPI endpoint is allowed.")

        query = parse_qs(parsed.query, strict_parsing=True)

        if set(query) - {"limit", "offset"}:
            raise ValueError("Unsupported API query parameter.")

        if any(len(values) != 1 for values in query.values()):
            raise ValueError("Duplicate query parameters are not allowed.")

        limit = query.get("limit", ["10"])[0]
        offset = query.get("offset", ["0"])[0]

        if not limit.isdecimal() or not offset.isdecimal():
            raise ValueError("Limit and offset must be integers.")

        if not (1 <= int(limit) <= 100):
            raise ValueError("Limit must be between 1 and 100.")

        if int(offset) < 0:
            raise ValueError("Offset cannot be negative.")

        destination = (data_root / output_file).resolve()

        if not destination.is_relative_to(data_root):
            raise ValueError("Output file must be inside the data directory.")

        if destination.suffix.lower() != ".csv":
            raise ValueError("Output file must be CSV.")

        response = requests.get(
            url,
            timeout=(5, 15),
            allow_redirects=False,
            stream=True
        )

        try:
            if 300 <= response.status_code < 400:
                raise ValueError("Redirects are not allowed.")

            response.raise_for_status()

            max_bytes = 2 * 1024 * 1024
            content = bytearray()

            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)

                if len(content) > max_bytes:
                    raise ValueError("API response is too large.")

            payload = json.loads(content)

            if (
                not isinstance(payload, dict)
                or not isinstance(payload.get("results"), list)
            ):
                raise ValueError("Expected JSON with a results list.")

            records = payload["results"]

            if len(records) > 100:
                raise ValueError("Maximum 100 records allowed.")

            df = pd.json_normalize(records)

            destination.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(destination, index=False)

            return {
                "status": "success",
                "rows": len(df),
                "output_file": str(destination)
            }

        finally:
            response.close()
if __name__ == "__main__":
    obj = ETLTools()

    result = obj.safe_filter_csv(
        input_file="extract/extracted_data.csv",
        output_file="transform/safe_filtered_pokemon.csv",
        column="name",
        value="bulbasaur"
    )

    print(result)
