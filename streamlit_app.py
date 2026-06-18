import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='GDP dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Try the repository's data/ directory first, then the repo root.
    base = Path(__file__).parent
    candidates = [base / 'data' / 'gdp_data.csv', base / 'gdp_data.csv']

    DATA_FILENAME = None
    for p in candidates:
        if p.exists():
            DATA_FILENAME = p
            break

    if DATA_FILENAME is None:
        # Let the app show a helpful message instead of crashing deeper inside.
        raise FileNotFoundError(
            f"gdp_data.csv not found. Expected one of: {candidates}"
        )

    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # Pivot year columns into Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers and GDP to numeric
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'], errors='coerce')
    gdp_df['GDP'] = pd.to_numeric(gdp_df['GDP'], errors='coerce')

    return gdp_df


# Load data (show a friendly error if the file is missing)
try:
    gdp_df = get_gdp_data()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
st.title(':earth_americas: GDP dashboard')
st.write("Browse GDP data from the World Bank Open Data website. The dataset goes to 2022 and some datapoints may be missing.")

min_value = int(gdp_df['Year'].min())
max_value = int(gdp_df['Year'].max())

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value]
)

# Use sorted, dropna country codes
countries = sorted(gdp_df['Country Code'].dropna().unique())

if len(countries) == 0:
    st.warning("No countries available in the dataset.")
    st.stop()

# Provide sensible defaults only if they're present in the dataset
default_countries = [c for c in ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'] if c in countries]

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    default_countries if default_countries else countries[:6]
)

if not selected_countries:
    st.warning("Please select at least one country to view the charts and metrics.")

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time')

# st.line_chart expects a tidy dataframe; we'll pivot so each country is a column
if not filtered_gdp_df.empty:
    try:
        chart_df = filtered_gdp_df.pivot_table(index='Year', columns='Country Code', values='GDP')
        st.line_chart(chart_df)
    except Exception:
        # Fallback to plotting the tidy frame (Streamlit can handle this too)
        st.line_chart(filtered_gdp_df, x='Year', y='GDP', color='Country Code')
else:
    st.info('No data available for the selected countries/years.')

# Summary metrics for the selected range
first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}')

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        # Safely get GDP for country/year; return NaN if missing
        def safe_get_gdp(df, country, year):
            s = df[(df['Country Code'] == country) & (df['Year'] == year)]['GDP']
            if s.empty:
                return math.nan
            return float(s.iat[0])

        first_gdp = safe_get_gdp(first_year, country, from_year)
        last_gdp = safe_get_gdp(last_year, country, to_year)

        # Convert to billions for display when available
        def fmt_billions(x):
            if x is None or (isinstance(x, float) and math.isnan(x)):
                return 'n/a'
            return f"{(x/1_000_000_000):,.0f}B"

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        elif first_gdp == 0 or math.isnan(last_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=fmt_billions(last_gdp),
            delta=growth,
            delta_color=delta_color
        )
