# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
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

# Load the data
df = pd.read_json('Population_Mortality_2013_2023.json')

# Exclude South Asia from the dataset
df = df[df['Country Name'] != 'South Asia']

# Reshape the dataset to have 'Year' as a column instead of multiple year columns
df_melted = pd.melt(df, 
                    id_vars=['Series Name', 'Country Name', 'Country Code'], 
                    var_name='Year', 
                    value_name='Value')

# Convert Year to int for proper filtering and plotting
df_melted['Year'] = df_melted['Year'].astype(int)

# List of unique Series Names
series_names = df_melted['Series Name'].unique()

# List of unique Country Names + 'All Countries' option
country_names = ['All Countries'] + df_melted['Country Name'].unique().tolist()

# Function to calculate the sum of all countries
def calculate_all_countries(df):
    all_countries_data = df.groupby(['Year', 'Series Name']).sum(numeric_only=True).reset_index()
    all_countries_data['Country Name'] = 'All Countries'
    all_countries_data['Country Code'] = 'ALL'
    return all_countries_data

# Backend process to add "All Countries" option
all_countries_df = calculate_all_countries(df_melted)
df_melted = pd.concat([all_countries_df, df_melted], ignore_index=True)

# Streamlit App
st.title("Global Population & Mortality Trends (2013-2023)")

# Dropdowns for Series and Country
selected_series = st.selectbox("Select Series", series_names)
selected_country = st.selectbox("Select Country", country_names)

# Filter data for selected series and country
if selected_country == 'All Countries':
    df_filtered = df_melted[(df_melted['Series Name'] == selected_series) & (df_melted['Country Name'] == 'All Countries')]
else:
    df_filtered = df_melted[(df_melted['Series Name'] == selected_series) & (df_melted['Country Name'] == selected_country)]

# Line Chart for the selected series and country
fig = px.line(df_filtered, x='Year', y='Value', title=f"{selected_series} Trends for {selected_country} (2013-2023)")
st.plotly_chart(fig)

# Additional Visualizations

# Comparison between multiple countries (Line Chart)
st.subheader(f"Comparison of {selected_series} Across Countries")
selected_countries = st.multiselect("Select Countries for Comparison", country_names, default=["All Countries"])
df_compare = df_melted[(df_melted['Series Name'] == selected_series) & (df_melted['Country Name'].isin(selected_countries))]
fig_compare = px.line(df_compare, x='Year', y='Value', color='Country Name', title=f"{selected_series} Comparison (2013-2023)")
st.plotly_chart(fig_compare)

# Bar Chart - Top 10 countries for the selected series and year (excluding 'All Countries')
st.subheader(f"Top 10 and Bottom 10 Countries by {selected_series} in a Selected Year")
selected_year = st.slider("Select Year", 2013, 2023, 2023)
df_year = df_melted[(df_melted['Series Name'] == selected_series) & (df_melted['Year'] == selected_year) & (df_melted['Country Name'] != 'All Countries')]

# Top 10 countries
df_top_10 = df_year.nlargest(10, 'Value')
fig_bar_top = px.bar(df_top_10, x='Country Name', y='Value', title=f"Top 10 Countries by {selected_series} in {selected_year}")
st.plotly_chart(fig_bar_top)

# Bottom 10 countries
df_bottom_10 = df_year.nsmallest(10, 'Value')
df_bottom_10 = df_bottom_10[df_bottom_10['Value'] > 0]  # Filter out null or zero values
fig_bar_bottom = px.bar(df_bottom_10, x='Country Name', y='Value', title=f"Bottom 10 Countries by {selected_series} in {selected_year}")
st.plotly_chart(fig_bar_bottom)

# Choropleth Map
st.subheader("Global Overview on a Map")
df_map = df_year[df_year['Country Name'] != 'All Countries']
fig_map = px.choropleth(df_map, locations='Country Code', color='Value', hover_name='Country Name',
                        title=f"Global Distribution of {selected_series} in {selected_year}",
                        color_continuous_scale='Viridis', projection='natural earth')
st.plotly_chart(fig_map)

# Analysis Over Time (Grouped by Year for all countries or selected countries)
st.subheader(f"Time Trend Analysis of {selected_series}")
selected_trend_countries = st.multiselect("Select Countries for Trend Analysis", country_names, default=["All Countries"])
df_trend = df_melted[(df_melted['Series Name'] == selected_series) & (df_melted['Country Name'].isin(selected_trend_countries))]
fig_trend = px.line(df_trend, x='Year', y='Value', color='Country Name', title=f"Time Trend Analysis of {selected_series}")
st.plotly_chart(fig_trend)

# Pie Chart for Selected Year and Series (Proportions across countries)
st.subheader(f"Proportions of {selected_series} across Countries in {selected_year}")
df_pie = df_year[df_year['Country Name'] != 'All Countries']
fig_pie = px.pie(df_pie, names='Country Name', values='Value', title=f"{selected_series} Distribution in {selected_year}")
st.plotly_chart(fig_pie)
