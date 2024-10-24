# streamlit_app.py
#######################
# Import libraries
import folium.elements
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
import folium
import folium.features
import requests
from streamlit_folium import st_folium, folium_static
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="Population Growth Metrics Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

#######################
# Load data from the BigQuery database in a DataFrame

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes.
@st.cache_data()
def get_data(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]

    # Load the query data into a DataFrame
    df = pd.DataFrame(rows)

    # Pivot the data into the desired format and reset the index
    df_pivoted = df.pivot_table(index=['year','country_name','country_code'],columns='indicator_name',values='value')
    final_df = df_pivoted.reset_index()

    # Replace NaN values with '0'
    final_df.fillna(0, inplace=True)
    return final_df

query = """
    SELECT year, country_name, country_code, indicator_name, value
    FROM `bigquery-public-data.world_bank_wdi.indicators_data`
    WHERE indicator_name IN (
            'GDP per capita (current US$)',
            'GNI per capita, Atlas method (current US$)',
            'Fertility rate, total (births per woman)',
            'Urban population (% of total population)',
            'Rural population (% of total population)',
            'Population, female (% of total population)',
            'Population, male (% of total population)',
            'Population, total',
            "Age dependency ratio (% of working-age population)",
            'Age dependency ratio, old (% of working-age population)',
            'Age dependency ratio, young (% of working-age population)',
            'Human capital index (HCI) (scale 0-1)',
            'Net migration',
            'Labor force, total',
            'Labor force with advanced education (% of total working-age population with advanced education)',
            'Labor force with basic education (% of total working-age population with basic education)',
            'Labor force with intermediate education (% of total working-age population with intermediate education)',
            'Labor force, female (% of total labor force)'
            )
    AND NOT country_name in (
        'Latin America & Caribbean',
        'Latin America & Caribbean (excluding high income)',
        'Latin America & the Caribbean (IDA & IBRD countries)',
        'Least developed countries: UN classification',
        'Low & middle income',
        'Low income',
        'Lower middle income',
        'Middle East & North Africa',
        'Middle East & North Africa (excluding high income)',
        'Africa Eastern and Southern',
        'Africa Western and Central',
        'Arab World',
        'Caribbean small states',
        'Central Europe and the Baltics',
        'Early-demographic dividend',
        'East Asia & Pacific',
        'East Asia & Pacific (excluding high income)',
        'East Asia & Pacific (IDA & IBRD countries)',
        'Upper middle income',
        'World',
        'Middle East & North Africa (IDA & IBRD countries)',
        'Middle income',
        'North America',
        'OECD members',
        'Other small states',
        'Pacific island small states',
        'Post-demographic dividend',
        'Pre-demographic dividend',
        'Euro area',
        'Europe & Central Asia',
        'Europe & Central Asia (excluding high income)',
        'Europe & Central Asia (IDA & IBRD countries)',
        'European Union',
        'Fragile and conflict affected situations',
        'Heavily indebted poor countries (HIPC)',
        'High income',
        'Small states',
        'South Asia (IDA & IBRD)',
        'South Asia',
        'Sub-Saharan Africa',
        'Sub-Saharan Africa (excluding high income)',
        'Sub-Saharan Africa (IDA & IBRD countries)',
        'IBRD only',
        'IDA & IBRD total',
        'IDA blend',
        'IDA only',
        'IDA total',
        'Late-demographic dividend')
    ORDER BY year DESC, country_name, indicator_name
"""
# Load the data into a DataFrame
data_df = get_data(query)

#######################
# Sidebar
with st.sidebar:
    st.title('Population Metrics Dashboard')
    # Create a list of the different indicators for the drop down menu
    series_names = ['Total Population', 'Fertility Rate (births per woman)', 'GDP per capita (current US$)', 'GNI per capita (current US$)', 'Age Dependency Ratio', 'Labor Force', 'Net Migration', 'Human capital index (HCI) (scale 0-1)']

    # Dropdown for indicator layers
    selection = st.selectbox("Select Metric", series_names)

     # Slider to determine the year to be displayed
    slider_year = st.slider('Select a year', 1960, 2020, 2020)
    filtered_df = data_df[data_df['year']==slider_year]

#######################
# Load and edit the GeoJSON for the map
geojson_data = requests.get(
    "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/world_countries.json"
).json()

# Add additional elements/keys to the GeoJSON using the DataFrame filtered by the selected slider year
for feature in geojson_data['features']:
    country_id = feature['id']
    feature['properties']['Fertility rate, total (births per woman)'] = 'Fertility Rate: ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Fertility rate, total (births per woman)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['GDP per capita (current US$)'] = 'GDP per capita (current US$): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'GDP per capita (current US$)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Population, total'] = 'Population, total: ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Population, total'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Urban population (% of total population)'] = 'Urban population (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Urban population (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Rural population (% of total population)'] = 'Rural population (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Rural population (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Population, female (% of total population)'] = 'Population, female (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id,'Population, female (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Population, male (% of total population)'] = 'Population, male (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Population, male (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Labor force, total'] = 'Labor force, total: ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Labor force, total'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties'][ 'Labor force with advanced education (% of total working-age population with advanced education)'] =  'Labor force with advanced education (% of total working-age population with advanced education): ' + str(filtered_df.loc[filtered_df['country_code']==country_id,  'Labor force with advanced education (% of total working-age population with advanced education)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties'][ 'Labor force with basic education (% of total working-age population with basic education)'] =  'Labor force with basic education (% of total working-age population with basic education): ' + str(filtered_df.loc[filtered_df['country_code']==country_id,  'Labor force with basic education (% of total working-age population with basic education)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Labor force with intermediate education (% of total working-age population with intermediate education)'] = 'Labor force with intermediate education (% of total working-age population with intermediate education): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Labor force with intermediate education (% of total working-age population with intermediate education)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Age dependency ratio, old (% of working-age population)'] = 'Age dependency ratio, old (% of working-age population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Age dependency ratio, old (% of working-age population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Age dependency ratio, young (% of working-age population)'] = 'Age dependency ratio, young (% of working-age population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Age dependency ratio, young (% of working-age population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Age dependency ratio (% of working-age population)'] = 'Age dependency ratio (% of working-age population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Age dependency ratio (% of working-age population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Net migration'] = 'Net migration: ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Net migration'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Population, total'] = 'Population, total: ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Population, total'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Urban population (% of total population)'] = 'Urban population (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id,'Urban population (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Rural population (% of total population)'] = 'Rural population (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Rural population (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Population, female (% of total population)'] = 'Population, female (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Population, female (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Population, male (% of total population)'] = 'Population, male (% of total population): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Population, male (% of total population)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['GNI per capita, Atlas method (current US$)'] = 'GNI per capita (current US$): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'GNI per capita, Atlas method (current US$)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')
    feature['properties']['Human capital index (HCI) (scale 0-1)'] = 'Human capital index (HCI) (scale 0-1): ' + str(filtered_df.loc[filtered_df['country_code']==country_id, 'Human capital index (HCI) (scale 0-1)'].values[0] if country_id in list(filtered_df['country_code']) else 'N/A')

#######################
# Build the main main/choropleth visual

# Set GeoJSON key to find based on what is selected in the dropdown menus and determine the list of variables to include in the hover-over popup/tooltip
match selection:
    case "Total Population":
        selected_metric = 'Population, total'
        hover_list=['name','Population, total', 'Urban population (% of total population)','Rural population (% of total population)','Population, female (% of total population)','Population, male (% of total population)']

    case "Fertility Rate (births per woman)":
        selected_metric = 'Fertility rate, total (births per woman)'
        hover_list = ['name','Fertility rate, total (births per woman)','GDP per capita (current US$)', 'GNI per capita, Atlas method (current US$)','Population, total']

    case "Human capital index (HCI) (scale 0-1)":
        selected_metric = 'Human capital index (HCI) (scale 0-1)'
        hover_list = ['name', 'Human capital index (HCI) (scale 0-1)']
    case 'GDP per capita (current US$)':
        selected_metric = 'GDP per capita (current US$)'
        hover_list = ['name','GDP per capita (current US$)', 'GNI per capita, Atlas method (current US$)','Population, total','Fertility rate, total (births per woman)']
    
    case 'GNI per capita (current US$)':
        selected_metric = 'GNI per capita, Atlas method (current US$)'
        hover_list = ['name', 'GNI per capita, Atlas method (current US$)', 'GDP per capita (current US$)', 'Population, total','Fertility rate, total (births per woman)']
    
    case 'Age Dependency Ratio':
        selected_metric = 'Age dependency ratio (% of working-age population)'
        hover_list = ['name','Age dependency ratio (% of working-age population)', 'Age dependency ratio, young (% of working-age population)','Age dependency ratio, old (% of working-age population)']

    case 'Labor Force':
        selected_metric = 'Labor force, total'
        hover_list = ['name','Labor force, total','Labor force with advanced education (% of total working-age population with advanced education)', 'Labor force with intermediate education (% of total working-age population with intermediate education)','Labor force with basic education (% of total working-age population with basic education)']

    case 'Net Migration':
        selected_metric = 'Net migration'
        hover_list = ['name', 'Net migration']


# Build the map
map = folium.Map(location=(35,0), zoom_start=2, tiles=folium.TileLayer(tiles='cartodb positron',no_wrap=True), max_bounds=True)

# Create choropleth
choropleth = folium.Choropleth(
    geo_data=geojson_data,
    name=selected_metric,
    data=filtered_df,
    columns=['country_code',selected_metric],
    key_on="feature.id",
    fill_color="YlOrBr",
    fill_opacity=0.7,
    line_opacity=0.2,
    highlight=True,
    legend_name=selected_metric,
    nan_fill_color='white',
).add_to(map)

# Create second layer that creates a hover-over popup/tooltip
hover_layer = folium.GeoJson(geojson_data, style_function=lambda feature:{"fillColor":'0000',"fillOpacity":0, "weight":0.1},zoom_on_click=True, width=850).add_to(map)

# Add additional child to hover_layer that defines the values to be displayed in the hover-over popup/tooltip
hover_layer.add_child(
    folium.features.GeoJsonTooltip(hover_list, labels=False)
)

#######################

# Get top 10 and bottom 10 countries by GDP and filter out any values with values of zero
top_bottom_df = filtered_df[(filtered_df[selected_metric] > 0)]
top_10_gdp = top_bottom_df.nlargest(10, selected_metric)
bottom_10_gdp = top_bottom_df.nsmallest(10, selected_metric)

# Bar chart for top 10 countries by GDP in 2023
top_10_gdp_fig = px.bar(top_10_gdp, x='country_name', y=selected_metric, labels={'metric': 'Metric'}, 
                            title="Top 10 Countries")

# Bar chart for bottom 10 countries by GDP in 2023
bottom_10_gdp_fig = px.bar(bottom_10_gdp, x='country_name', y=selected_metric, labels={'metric': 'Metric'}, 
                            title="Bottom 10 Countries")

#######################
# Dashboard Section

# If there is not data for the selected metric in a given year (top_bottom_df is empty) then print an error message and list the years where data is available
if top_bottom_df.empty:
    st.subheader(f"Data for {selection} is not available for this year.  Please select one of the following years:")
    years = data_df[data_df[selected_metric] > 0]['year'].unique()
    years_string = ", ".join(str(x) for x in years)
    st.subheader(years_string)
else:
    st.subheader(selection)
    st.markdown("""
            <style>
            iframe {
                width: 100%;
                min-height: 400px;
                height: 100%:
            }
            </style>
            """, unsafe_allow_html=True)
    # Display the map in Streamlit
    st.components.v1.html(map._repr_html_(), width=1050, height=1000)


    # Create Bar Chart - Top 10 and Bottom 10 Countries
    # Include html to create some design responsiveness
    st.markdown("""
            <style>
            iframe {
                width: 100%;
                min-height: 400px;
                height: 100%:
            }
            </style>
            """, unsafe_allow_html=True)

    # Create columns to hold each chart
    col = st.columns((4.5, 4), gap='small')

    # Display each bar chart an individual column
    with col[0]:
        st.plotly_chart(top_10_gdp_fig)

    with col[1]:
        st.plotly_chart(bottom_10_gdp_fig)