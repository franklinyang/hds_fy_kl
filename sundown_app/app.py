from urllib.request import urlopen
import json
import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # or plotly.express as px

from .about_us import about_us_html

# from .sundown_map import sundown_map_html


def county2fips_fct(x):
    if x in county2fips:
        return str(int(county2fips[x]))
    else:
        return np.nan


# # define data dir
data_dir = "../data"
data_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), data_dir)

counties_with_latlong = pd.read_csv(
    os.path.join(data_filepath, "counties.txt"), dtype={"GEOID": str}, sep="\t"
)
# strip column headers
counties_with_latlong.columns = map(lambda s: s.strip(), counties_with_latlong.columns)

# get sundown town data
df = pd.read_csv(os.path.join(data_filepath, "sundown_with_counties.csv"), encoding="latin-1")
df["County_no_states"] = df.county.str.split(",").apply(lambda x: x[0])
county_long_names = []
for i in df.county.values:
    x = i.split(",")
    if len(x) == 2:
        county_long_names.append(x[0] + " " + x[1])
    else:
        county_long_names.append(x)
df["county_long_names"] = county_long_names

# get fips data
fips_codes = pd.read_csv(os.path.join(data_filepath, "county_fips_master.csv"), encoding="latin-1")
county2fips = dict(fips_codes[["long_name", "fips"]].values)
# lower everything to ensure a match
county2fips = {k.lower(): v for k, v in county2fips.items()}

county_sundown_counts = pd.DataFrame(df.groupby(by="county").size())
county_sundown_counts = county_sundown_counts.reset_index()
county_sundown_counts.county = county_sundown_counts.county.apply(lambda x: x.replace(",", ""))
county_sundown_counts = county_sundown_counts.reset_index()
county_sundown_counts = county_sundown_counts.rename(columns={"County_no_states": "County", 0: "#"})
county_sundown_counts["fips"] = county_sundown_counts.county.apply(
    lambda x: county2fips_fct(x.lower())
)
# prepend 0 to handle any fips that had their leading 0 cut off
county_sundown_counts["fips"] = county_sundown_counts["fips"].apply(
    lambda x: str(x) if len(str(x)) == 5 else "0" + str(x)
)
county_sundown_counts = county_sundown_counts[county_sundown_counts.fips.notnull()]

##### Fetch towns #######
county_sundown_counts = county_sundown_counts.sort_values(by=["county"])
county_sundown_towns = pd.DataFrame(
    df.groupby(by="county")["city"].transform(lambda x: ", ".join(x))
)
county_sundown_towns["county"] = df.county
county_sundown_towns = county_sundown_towns.drop_duplicates()
county_sundown_towns = county_sundown_towns.sort_values(by=["county"])

county_sundown_towns = county_sundown_towns.reset_index()
county_sundown_counts["towns"] = county_sundown_towns["city"]
########################

with urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
) as response:
    counties = json.load(response)

df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
    dtype={"fips": str},
)

tab_style = {
    "borderBottom": "1px solid #d6d6d6",
    "padding": "6px",
    "margin-bottom": "10px",
    "fontWeight": "bold",
}

tab_selected_style = {
    "borderTop": "1px solid #d6d6d6",
    "borderBottom": "1px solid #d6d6d6",
    "padding": "6px",
    "margin-bottom": "10px",
}

fig = px.choropleth_mapbox(
    county_sundown_counts,
    geojson=counties,
    locations="fips",
    color="#",
    color_continuous_scale="Viridis",
    range_color=(0, 12),
    mapbox_style="carto-positron",
    zoom=3,
    center={"lat": 37.0902, "lon": -95.7129},
    opacity=0.5,
    labels={"towns": "Sundown Towns"},
)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
# fig.show()

sundown_map_html = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.Strong("Select a county"),
                            dcc.Dropdown(
                                id="sundown-county",
                                options=[
                                    {"label": c, "value": fips}
                                    for c, fips in zip(
                                        county_sundown_counts.county.values,
                                        county_sundown_counts.fips.values,
                                    )
                                ],
                                value="Counties",
                                placeholder="Select a county",
                            ),
                            html.Div(style={"margin-bottom": "10px"}),
                            html.Strong("Select a state"),
                            dcc.Dropdown(
                                id="sundown-state",
                                options=[
                                    {"label": c, "value": c}
                                    for c in counties_with_latlong.USPS.unique()
                                ],
                                value="States",
                                placeholder="Select a state",
                            ),
                        ]
                    ),
                    width={"size": 3, "order": 1},
                ),
                dbc.Col(dcc.Graph(id="sundown-map", figure=fig), width={"size": 9, "order": 2}),
            ]
        )
    ]
)

external_stylesheets = [dbc.themes.BOOTSTRAP, "https://codepen.io/chriddyp/pen/bWLwgP.css"]


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        dbc.Row(
            [
                dbc.Col(
                    html.H2("Sundown Towns across the United States"),
                    width={"size": 6, "offset": 3},
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Tabs(
                        id="tabs-example",
                        value="sundown_map",
                        children=[
                            dcc.Tab(
                                label="Map",
                                value="sundown_map",
                                style=tab_style,
                                selected_style=tab_selected_style,
                            ),
                            dcc.Tab(
                                label="About",
                                value="about",
                                style=tab_style,
                                selected_style=tab_selected_style,
                            ),
                        ],
                    ),
                    width={"size": 6, "offset": 1},
                )
            ]
        ),
        dbc.Row([dbc.Col(html.Div(id="tabs-example-content"), width={"size": 10, "offset": 1})]),
    ]
)


@app.callback(
    dash.dependencies.Output("tabs-example-content", "children"),
    [dash.dependencies.Input("tabs-example", "value")],
)
def render_content(tab):
    if tab == "sundown_map":
        # return (html.Div(id="page-content"),)
        return sundown_map_html
    elif tab == "about":
        return about_us_html


@app.callback(
    dash.dependencies.Output("sundown-map", "figure"),
    [
        dash.dependencies.Input("sundown-county", "value"),
        dash.dependencies.Input("sundown-state", "value"),
    ],
)
def update_graph_by_county(sundown_county, sundown_state):
    if (sundown_county == "Counties" and sundown_state == "State") or not sundown_county:
        # print("1:", "sundown_county: ", sundown_county, "sundown_state: ", sundown_state)
        return fig

    if sundown_county and sundown_county != "Counties":
        # print("2:", "sundown_county: ", sundown_county, "sundown_state: ", sundown_state)
        matching_county = counties_with_latlong[counties_with_latlong["GEOID"] == sundown_county]
        latlon = matching_county[matching_county.columns[-2:]].values.tolist()[0]
        fig.update_layout(mapbox_zoom=9, mapbox_center={"lat": latlon[0], "lon": latlon[1]})
        return fig

    elif sundown_state and sundown_state != "States":
        # print("3:", "sundown_county: ", sundown_county, "sundown_state: ", sundown_state)
        matching_state = counties_with_latlong[counties_with_latlong["USPS"] == sundown_state]
        latlon = [np.mean(matching_state.INTPTLAT), np.mean(matching_state.INTPTLONG)]
        fig.update_layout(mapbox_zoom=5, mapbox_center={"lat": latlon[0], "lon": latlon[1]})
        return fig

    # not needed
    else:
        return fig


server = app.server


@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")],
)
def display_page(pathname):
    if pathname == "/about-us":
        return about_us_html
    else:
        return sundown_map_html


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  # Turn off reloader if inside Jupyter
