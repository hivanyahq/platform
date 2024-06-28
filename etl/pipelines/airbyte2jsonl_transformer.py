import logging
import csv
import json

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Airbyte2jsonlTransformer:
    def __init__(self, field_map):
        self.field_map = field_map

    def transform_airbyte_row(self, data, mapkey):
        """
        Evaluates expressions from fieldmap using the provided data dict for eval.
        """
        evaluated_values = {}
        for key, path in self.field_map[mapkey].items():
            try:
                evaluated_values[key] = eval(path, {'data': data})
            except KeyError:
                evaluated_values[key] = None
        return evaluated_values

    def transform_airbyte2jsonl_format(self, source_file, output_file, mapkey):
        """
        Only fields defined in FIELD_MAP are transformed.
        """
        with open(output_file, 'w') as fh:
            with open(source_file, 'r', newline='') as csv_file:
                reader = csv.DictReader(
                    csv_file,
                    fieldnames=["_airbyte_ab_id", "_airbyte_emitted_at", "_airbyte_data"]
                )
                next(reader)
                for row in reader:
                    data = self.transform_airbyte_row(json.loads(row['_airbyte_data']), mapkey)
                    fh.write(f'{json.dumps(data)}\n')
        logger.info(f'Generated {output_file}')
