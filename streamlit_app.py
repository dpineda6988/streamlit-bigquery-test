# streamlit_app.py

import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows

query = """
    SELECT year, country_name, indicator_name, value
    FROM `bigquery-public-data.world_bank_wdi.indicators_data`
    WHERE indicator_name IN (
            'GDP per capita (current US$)',
            'Fertility rate, total (births per woman)',
            'Urban population',
            'Rural population')
    ORDER BY year DESC, country_name, indicator_name
"""

rows = run_query(query)

for row in rows:
    st.write(row)