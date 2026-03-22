import polars as pl

from coreason_etl_cdc_wonder.transform import transform_bronze_to_silver

raw_data_series = pl.Series(
    "raw_data",
    [
        # Normal row
        {
            "c": [
                {"@v": "2010"},
                {"@v": "C44.9"},
                {"@v": "500"},
                {"@v": "200000"},
                {"@v": "250.0"},
            ]
        },
        # Partially Suppressed row
        {
            "c": [
                {"@v": "2010"},
                {"@v": "C45.0"},
                {"@v": "Suppressed"},
                {"@v": "300000"},
                {"@v": "Unreliable"},
            ]
        },
        # Missing essential column (should be filtered)
        {
            "c": [
                {"@v": ""},
                {"@v": "C46.0"},
                {"@v": "100"},
                {"@v": "1000"},
                {"@v": "10.0"},
            ]
        },
        # Summary Totals row (should be filtered)
        {
            "c": [
                {"@v": "Totals"},
                {"@v": "1500"},
                {"@v": "250000"},
                {"@v": "600.0"},
            ]
        },
        # Excessive columns (should only take first 5)
        {
            "c": [
                {"@v": "2011"},
                {"@v": "C47.0"},
                {"@v": "10"},
                {"@v": "1000"},
                {"@v": "1.0"},
                {"@v": "Extra data"},
                {"@v": "More extra data"},
            ]
        },
        # Strings instead of dicts in struct array (handled gracefully)
        {"c": ["2012", "C48.0", "50", "5000", "10.0"]},
        # Null completely
        None,
    ],
    strict=False,
)

df = pl.DataFrame([raw_data_series])
result = transform_bronze_to_silver(df)
print(result)
