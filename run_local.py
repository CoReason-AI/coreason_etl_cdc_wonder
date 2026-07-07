import io
import psycopg2
from unittest.mock import patch
from coreason_etl_cdc_wonder.main import run_pipeline

# 1. Automatically create the silver schema in Postgres
conn = psycopg2.connect("host=localhost port=5432 user=adarsh password=adarsh123 dbname=snomed")
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("CREATE SCHEMA IF NOT EXISTS silver;")
conn.close()

# 2. A minimal valid XML response mimicking the CDC WONDER D76 dataset
mock_xml_data = b"""<?xml version="1.0"?>
<page>
  <data-table>
    <r><c v="2020"/><c v="C34.9"/><c v="1200"/><c v="100000"/><c v="120.0"/></r>
    <r><c v="2020"/><c v="I21.9"/><c v="5000"/><c v="100000"/><c v="500.0"/></r>
    <r><c v="2021"/><c v="C50.9"/><c v="800"/><c v="100000"/><c v="80.0"/></r>
  </data-table>
</page>"""

if __name__ == "__main__":
    print("Mocking CDC WONDER API and creating Silver schema...")
    with patch("coreason_etl_cdc_wonder.resource.fetch_wonder_data") as mock_fetch:
        mock_fetch.return_value = io.BytesIO(mock_xml_data)
        run_pipeline()
    print("Pipeline execution complete! Data should now be in PostgreSQL.")
