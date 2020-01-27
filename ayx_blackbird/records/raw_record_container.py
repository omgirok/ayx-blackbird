"""RawRecordContainer class definition."""
from typing import Dict, List, Optional

from ..proxies import FieldProxy, RecordCopierProxy
from ..utilities import fill_df_nulls_with_blackbird_nulls


class RawRecordContainer:
    """Container for copying and holding raw records."""

    __slots__ = [
        "records",
        "_input_record_info",
        "_storage_record_info",
        "_field_map",
        "_record_copier",
        "_input_fields",
    ]

    def __init__(
        self,
        input_record_info,
        storage_record_info=None,
        field_map: Optional[Dict[str, str]] = None,
    ):
        """Construct a container."""
        if (storage_record_info is None) ^ (field_map is None):
            raise ValueError(
                "storage_record_info and field_map must both be specified."
            )

        self._input_record_info = input_record_info

        self._storage_record_info = storage_record_info
        if self._storage_record_info is None:
            self._storage_record_info = self._input_record_info.clone()
        else:
            self._storage_record_info = storage_record_info

        if field_map is None:
            self._field_map = {
                str(field.name): str(field.name) for field in self._storage_record_info
            }
        else:
            self._field_map = field_map

        self._record_copier = RecordCopierProxy(
            self._input_record_info, self._storage_record_info, self._field_map
        )
        self._input_fields = {
            field.name: FieldProxy(field) for field in input_record_info
        }
        self.records: List[RecordCopierProxy] = []

    def add_record(self, record) -> None:
        """Make a copy of the record and add it to the container."""
        self.records.append(self._record_copier.copy(record))

    def clear_records(self) -> None:
        """Clear all accumulated records."""
        self.records = []

    def update_with_dataframe(self, df):
        """Update stored records with values from a dataframe."""
        num_rows, _ = df.shape

        if num_rows != len(self.records):
            raise ValueError(
                "Dataframe and source container must have the same number of records."
            )

        fill_df_nulls_with_blackbird_nulls(df)

        for record, (_, row) in zip(self.records, df.iterrows()):
            for column_name in list(df):
                field = self._storage_record_info.get_field_by_name(column_name)
                field.set(record, row[column_name])
