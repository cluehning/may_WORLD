"""
country_info.py
Provides country intelligence summaries, source links, and UI components
for the MUN Crisis Map.
"""

from dash import html
from data import COUNTRY_INTEL   # <-- NEW: real country intelligence

# ------------------------------------------------------------
# 1. Fallback generic descriptions (used only if no intel exists)
# ------------------------------------------------------------

GENERIC_DESCRIPTIONS = {
    "terrorism": "This country shows measurable terrorism-related activity. Refer to GTD and UN CTED for detailed incident data.",
    "humanitarian": "This country shows humanitarian stress indicators such as displacement, food insecurity, or emergency aid needs.",
    "conflict": "This country shows signs of armed conflict or political violence.",
    "war_crimes": "This country shows indicators of human rights violations or attacks on civilians.",
    "tariff": "This country shows elevated trade or tariff pressure.",
}

# ------------------------------------------------------------
# 2. Generate a country-specific summary
# ------------------------------------------------------------

def generate_country_summary(country_name, iso3, active_filters, df):
    """
    Creates a meaningful intelligence summary for a clicked country.
    Uses COUNTRY_INTEL when available, otherwise falls back to generic text.
    """
    lines = [f"**Country:** {country_name} ({iso3})"]

    for f in active_filters:
        key = f.replace("_score", "")  # e.g. "humanitarian_score" → "humanitarian"

        # Score from the dataset
        score = df.loc[df["iso3"] == iso3, f].values[0]

        # If we have real intel for this country and this crisis type
        if iso3 in COUNTRY_INTEL and key in COUNTRY_INTEL[iso3]:
            intel = COUNTRY_INTEL[iso3][key]["summary"]
            lines.append(f"\n### {key.title()} — Score: {score:.2f}")
            lines.append(intel)

        # Otherwise fallback to generic
        else:
            generic = GENERIC_DESCRIPTIONS.get(key, "No information available.")
            lines.append(f"\n### {key.title()} — Score: {score:.2f}")
            lines.append(generic)

    return "\n".join(lines)

# ------------------------------------------------------------
# 3. Build the intelligence panel UI
# ------------------------------------------------------------

def build_country_panel(country_name, iso3, active_filters, df):
    """
    Returns a Dash HTML block containing:
    - Country name
    - Crisis summaries
    - Source links (country-specific when available)
    """
    summary_text = generate_country_summary(country_name, iso3, active_filters, df)

    # Build source links
    source_blocks = []

    for f in active_filters:
        key = f.replace("_score", "")

        # If we have country-specific sources
        if iso3 in COUNTRY_INTEL and key in COUNTRY_INTEL[iso3]:
            source_blocks.append(html.H5(f"Sources for {key.title()}"))
            for label, url in COUNTRY_INTEL[iso3][key]["sources"]:
                source_blocks.append(html.Div(html.A(label, href=url, target="_blank")))

    return html.Div(
        style={
            "border": "1px solid #ccc",
            "padding": "12px",
            "borderRadius": "6px",
            "backgroundColor": "#ffffff",
            "marginTop": "12px",
        },
        children=[
            html.H3(f"{country_name} — Crisis Intelligence"),
            html.Pre(summary_text, style={"whiteSpace": "pre-wrap"}),
            html.Hr(),
            html.Div(source_blocks),
        ],
    )
