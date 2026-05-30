"""
Global Crisis & Conflict Map for MUN Delegates
(using verified public datasets)
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

from data import build_master_dataframe

# ------------------------------------------------------------
# Data setup
# ------------------------------------------------------------

FILTER_CONFIG = {
    "terrorism_score": {
        "label": "Violence / terrorism risk",
        "description": "World Bank PV.EST proxy (inverse = higher risk)",
    },
    "humanitarian_score": {
        "label": "Humanitarian pressure",
        "description": "IDP total + new conflict displacement composite",
    },
    "conflict_score": {
        "label": "War / armed conflict",
        "description": "Battle-related deaths",
    },
    "refugee_outflow_score": {
        "label": "Refugee outflow",
        "description": "Refugees by country of origin",
    },
    "tariff_score": {
        "label": "Trade / tariff pressure",
        "description": "Customs and import duties (% of tax revenue)",
    },
}

RAW_COLUMNS = {
    "terrorism_score": [("pv_estimate", "PV.EST"), ("terrorism_year", "Year")],
    "humanitarian_score": [
        ("idp_total_conflict", "IDPs total (conflict/violence)"),
        ("idp_total_year", "IDPs total year"),
        ("idp_new_conflict", "New conflict displacement"),
        ("idp_new_year", "New displacement year"),
    ],
    "conflict_score": [("battle_deaths", "Battle-related deaths"), ("conflict_year", "Year")],
    "refugee_outflow_score": [("refugees_origin", "Refugees by origin"), ("refugee_year", "Year")],
    "tariff_score": [("customs_duties_pct_tax", "Customs/import duties % of tax revenue"), ("tariff_year", "Year")],
}

master_df = build_master_dataframe()

# Optional: use 0 only for map-computation where score is missing;
# keep raw columns as-is.
score_cols = list(FILTER_CONFIG.keys())
for col in score_cols:
    master_df[col] = pd.to_numeric(master_df[col], errors="coerce").fillna(0.0).clip(0, 1)


# ------------------------------------------------------------
# Scoring helpers
# ------------------------------------------------------------


def compute_combined_score(df: pd.DataFrame, active_filters: list[str]) -> pd.Series:
    if not active_filters:
        return pd.Series([0.0] * len(df), index=df.index)
    return df[active_filters].max(axis=1, skipna=True)


def prepare_plot_dataframe(df: pd.DataFrame, active_filters: list[str], threshold: float) -> pd.DataFrame:
    plot_df = df.copy()
    plot_df["combined_score"] = compute_combined_score(plot_df, active_filters)
    plot_df["passes_threshold"] = plot_df["combined_score"] >= threshold
    plot_df["display_score"] = plot_df["combined_score"].where(plot_df["passes_threshold"], None)
    return plot_df


def format_number(value):
    if pd.isna(value):
        return "No data"
    try:
        value = float(value)
    except Exception:
        return str(value)

    if abs(value) >= 1_000_000:
        return f"{value:,.0f}"
    if abs(value) >= 1_000:
        return f"{value:,.0f}"
    if abs(value) >= 100:
        return f"{value:,.1f}"
    return f"{value:,.2f}"


# ------------------------------------------------------------
# Figure
# ------------------------------------------------------------


def create_choropleth_figure(df: pd.DataFrame, active_filters: list[str], threshold: float):
    plot_df = prepare_plot_dataframe(df, active_filters, threshold)

    hover_data = {
        "region": True,
        "combined_score": ":.2f",
        "display_score": False,
        "passes_threshold": False,
    }

    for col in score_cols:
        hover_data[col] = ":.2f"

    fig = px.choropleth(
        plot_df,
        locations="iso3",
        color="display_score",
        hover_name="country",
        hover_data=hover_data,
        color_continuous_scale="Reds",
        range_color=(0, 1),
        projection="natural earth",
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="Intensity"),
    )
    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="LightGray",
        showland=True,
        landcolor="#f5f5f5",
        bgcolor="white",
    )
    return fig


# ------------------------------------------------------------
# Country panel
# ------------------------------------------------------------

def build_country_panel(iso3: str, active_filters: list[str]):
    row = master_df[master_df["iso3"] == iso3]
    if row.empty:
        return html.Div("No data available for this country.")

    row = row.iloc[0]

    sections = [
        html.H3(f"{row['country']} ({row['iso3']})"),
        html.P(f"Region: {row['region']}"),
        html.Hr(),
    ]

    if not active_filters:
        sections.append(html.P("No filters selected."))
        return html.Div(sections)

    for score_col in active_filters:
        label = FILTER_CONFIG[score_col]["label"]
        description = FILTER_CONFIG[score_col]["description"]
        score_val = row.get(score_col, 0)

        items = [
            html.Li(f"Normalized score: {score_val:.2f}")
        ]

        for col_name, nice_name in RAW_COLUMNS.get(score_col, []):
            items.append(html.Li(f"{nice_name}: {format_number(row.get(col_name))}"))

        sections.extend(
            [
                html.H4(label),
                html.P(description, style={"fontSize": "12px", "color": "#666"}),
                html.Ul(items),
            ]
        )

    return html.Div(sections)


# ------------------------------------------------------------
# Summary blocks
# ------------------------------------------------------------

def build_stats(df: pd.DataFrame, active_filters: list[str], threshold: float):
    plot_df = prepare_plot_dataframe(df, active_filters, threshold)
    visible = plot_df[plot_df["passes_threshold"]].copy()

    visible_count = int(visible.shape[0])

    if visible_count == 0:
        return html.Div(
            [
                html.P("No countries match the selected threshold."),
            ]
        )

    top = visible.nlargest(10, "combined_score")[["country", "combined_score"]]
    avg_score = visible["combined_score"].mean()

    return html.Div(
        [
            html.P(f"Visible countries: {visible_count}"),
            html.P(f"Average visible intensity: {avg_score:.2f}"),
            html.P("Top countries in current view:"),
            html.Ol(
                [
                    html.Li(f"{r.country}: {r.combined_score:.2f}")
                    for r in top.itertuples(index=False)
                ]
            ),
        ]
    )


def build_text_summary(df: pd.DataFrame, active_filters: list[str], threshold: float):
    if not active_filters:
        return html.Div(
            "Select at least one indicator to generate an overview."
        )

    plot_df = prepare_plot_dataframe(df, active_filters, threshold)
    visible = plot_df[plot_df["passes_threshold"]].copy()

    if visible.empty:
        return html.Div(
            "At the current threshold, no country remains visible on the map."
        )

    top_regions = (
        visible.groupby("region")["combined_score"]
        .mean()
        .sort_values(ascending=False)
        .head(3)
        .reset_index()
    )
    top_countries = visible.nlargest(5, "combined_score")[["country", "combined_score"]]

    selected_labels = ", ".join(FILTER_CONFIG[f]["label"] for f in active_filters)

    region_text = "; ".join(
        [f"{r.region} ({r.combined_score:.2f})" for r in top_regions.itertuples(index=False)]
    )
    country_text = ", ".join(
        [f"{r.country} ({r.combined_score:.2f})" for r in top_countries.itertuples(index=False)]
    )

    text = (
        f"Active dimensions: {selected_labels}. "
        f"At threshold {threshold:.2f}, the map shows {len(visible)} countries. "
        f"Highest regional average intensity in the current view: {region_text}. "
        f"Top country cases in the current view: {country_text}."
    )
    return html.Div(text)


# ------------------------------------------------------------
# App Layout
# ------------------------------------------------------------

app = Dash(__name__)
app.title = "Global Crisis & Conflict Map for MUN Delegates"

app.layout = html.Div(
    style={"display": "flex", "height": "100vh", "fontFamily": "Arial"},
    children=[
        html.Div(
            style={
                "width": "30%",
                "minWidth": "340px",
                "padding": "16px",
                "borderRight": "1px solid #ddd",
                "overflowY": "auto",
                "backgroundColor": "#f9f9f9",
            },
            children=[
                html.H2("Global Crisis & Conflict Map for MUN Delegates"),

                html.Div(
                    style={
                        "backgroundColor": "#eef5ff",
                        "border": "1px solid #c5d6ff",
                        "padding": "10px",
                        "borderRadius": "6px",
                        "fontSize": "12px",
                        "marginBottom": "12px",
                    },
                    children=[
                        html.Strong("How to use this tool: "),
                        html.Span(
                            "Select one or more indicators, adjust the threshold, "
                            "then click a country to inspect the underlying data."
                        ),
                    ],
                ),

                html.H4("Indicators"),
                dcc.Checklist(
                    id="filter-checklist",
                    options=[
                        {"label": v["label"], "value": k}
                        for k, v in FILTER_CONFIG.items()
                    ],
                    value=["conflict_score", "humanitarian_score"],
                    labelStyle={"display": "block", "marginBottom": "4px"},
                ),

                html.Br(),
                html.H4("Severity threshold"),
                dcc.Slider(
                    id="threshold-slider",
                    min=0,
                    max=1,
                    step=0.05,
                    value=0.35,
                    marks={0: "0", 0.25: "0.25", 0.5: "0.5", 0.75: "0.75", 1: "1"},
                ),
                html.Div(id="threshold-display", style={"fontSize": "12px", "marginTop": "6px"}),

                html.Hr(),

                html.H4("Summary statistics"),
                html.Div(id="stats-container", style={"fontSize": "12px"}),

                html.Hr(),

                html.H4("Analytical overview"),
                html.Div(id="text-summary", style={"fontSize": "13px"}),

                html.Hr(),

                html.H4("Country intelligence"),
                html.Div(
                    id="country-panel",
                    children="Click a country on the map to inspect the data.",
                    style={"fontSize": "13px"},
                ),

                html.Hr(),

                html.H4("Data notes"),
                html.Ul(
                    [
                        html.Li("Violence / terrorism risk = inverse World Bank PV.EST proxy"),
                        html.Li("Humanitarian pressure = IDP total + new conflict displacement"),
                        html.Li("Conflict = battle-related deaths"),
                        html.Li("Refugee outflow = refugees by country of origin"),
                        html.Li("Trade pressure = customs/import duties share of tax revenue"),
                    ],
                    style={"fontSize": "12px", "color": "#555"},
                ),
            ],
        ),

        html.Div(
            style={"flex": 1, "padding": "8px"},
            children=[
                dcc.Graph(
                    id="world-map",
                    style={"height": "100%", "width": "100%"},
                    config={"displayModeBar": True, "scrollZoom": True},
                )
            ],
        ),
    ],
)

# ------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------


@app.callback(
    Output("world-map", "figure"),
    Output("stats-container", "children"),
    Output("text-summary", "children"),
    Output("threshold-display", "children"),
    Input("filter-checklist", "value"),
    Input("threshold-slider", "value"),
)
def update_dashboard(active_filters, threshold):
    fig = create_choropleth_figure(master_df, active_filters, threshold)
    stats = build_stats(master_df, active_filters, threshold)
    summary = build_text_summary(master_df, active_filters, threshold)
    threshold_text = f"Showing countries with combined score ≥ {threshold:.2f}"
    return fig, stats, summary, threshold_text


@app.callback(
    Output("country-panel", "children"),
    Input("world-map", "clickData"),
    Input("filter-checklist", "value"),
)
def update_country_panel(clickData, active_filters):
    if clickData is None:
        return "Click a country on the map to inspect the latest values behind the scores."

    iso3 = clickData["points"][0]["location"]
    return build_country_panel(iso3, active_filters)


if __name__ == "__main__":
    app.run(debug=True)
