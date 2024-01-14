from enum import Enum
import hopsworks
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    CustomJS,
    Slider,
    TapTool,
    TextInput,
)
from bokeh.palettes import Category20
from bokeh.transform import linear_cmap
from bokeh.plotting import figure
from bokeh.models import TextInput, Div, Paragraph
from bokeh.layouts import row, layout
from bokeh.plotting import save
import re
from model.cluster_data import ClusterData
from model.cluster_time_range import ClusterTimeRange
from plot.callbacks import input_callback, selected_code
from plot.plot_text import (
    header_with_time_range,
    description,
    time_range_title,
    time_range_last_month_button,
    time_range_last_half_year_button,
    time_range_last_year_button,
    description_search,
    description_slider,
)


def get_clusters(time_range: ClusterTimeRange) -> ClusterData:
    # Login to Hopsworks
    project = hopsworks.login()
    fs = project.get_feature_store()

    # Get the papers for the provided time range
    if time_range == ClusterTimeRange.LAST_MONTH:
        papers_fg_name = "acm_papers_clustered_last_month"
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        papers_fg_name = "acm_papers_clustered_last_half_year"
    elif time_range == ClusterTimeRange.LAST_YEAR:
        papers_fg_name = "acm_papers_clustered_last_year"
    papers_fg = fs.get_feature_group(papers_fg_name, 1)
    papers_df = papers_fg.read(read_options={"use_hive": True})

    # Get the topics for the provided time range
    if time_range == ClusterTimeRange.LAST_MONTH:
        keywords_fg_name = "acm_papers_cluster_keywords_last_month"
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        keywords_fg_name = "acm_papers_cluster_keywords_last_half_year"
    elif time_range == ClusterTimeRange.LAST_YEAR:
        keywords_fg_name = "acm_papers_cluster_keywords_last_year"
    keywords_fg = fs.get_feature_group(keywords_fg_name, 1)
    keywords_df = keywords_fg.read(read_options={"use_hive": True})
    # sort by cluster
    keywords_df.sort_values(by=["cluster"], inplace=True)
    topics = keywords_df["keywords"].values.tolist()

    cluster_data = ClusterData(papers_df, topics)
    return cluster_data


def extract_bibtex_field(bibtex_string, field):
    pattern = re.compile(rf"{field}\s*=\s*{{([^{{}}]*)}}", re.IGNORECASE)
    match = pattern.search(bibtex_string)
    value = match.group(1) if match else None
    return value


def plot_clusters(time_range: ClusterTimeRange):
    """Plot the clusters for the provided time range to a html file."""

    # -------- Data --------
    cluster_data = get_clusters(time_range)
    papers_df = cluster_data.papers_df
    topics = cluster_data.topics

    # extract title and author from citation
    papers_df["title"] = papers_df["citation"].apply(
        lambda x: extract_bibtex_field(x, "title")
    )
    papers_df["author"] = papers_df["citation"].apply(
        lambda x: extract_bibtex_field(x, "author")
    )

    # data sources
    source = ColumnDataSource(
        data=dict(
            x=papers_df["x_coord"],
            y=papers_df["y_coord"],
            x_backup=papers_df["x_coord"],
            y_backup=papers_df["y_coord"],
            abstract=papers_df["abstract"],
            title=papers_df["title"],
            author=papers_df["author"],
            publication_date=papers_df["publication_date"],
            cluster=papers_df["cluster"],
            labels=["C-" + str(x) for x in papers_df["cluster"]],
        )
    )

    max_cluster_value = papers_df["cluster"].max()
    min_cluster_value = papers_df["cluster"].min()
    clusters_count = max_cluster_value - min_cluster_value + 1

    # hover over information
    hover = HoverTool(
        tooltips=[
            ("Title", "@title"),
            ("Author", "@author"),
            ("Abstract", "@abstract{safe}"),
            ("Publication Date", "@publication_date"),
            ("Cluster", "@cluster"),
        ],
        point_policy="follow_mouse",
    )

    # map colors
    mapper = linear_cmap(
        field_name="cluster",
        palette=Category20[clusters_count],
        low=min_cluster_value,
        high=max_cluster_value,
    )

    # prepare the figure
    plot = figure(
        width=500,
        height=500,
        tools=[hover, "pan", "wheel_zoom", "box_zoom", "reset", "save", "tap"],
        title="Clustering of the ACM papers on Supervised Learning by Classification",
        toolbar_location="above",
    )

    # plot settings
    plot.scatter(
        "x",
        "y",
        size=5,
        source=source,
        fill_color=mapper,
        line_alpha=0.3,
        line_color="black",
        legend="labels",
    )
    plot.legend.background_fill_alpha = 0.6

    # -------- Callbacks --------

    # Keywords
    text_banner = Paragraph(
        text="Keywords: Slide to specific cluster to see the keywords.", height=25
    )
    input_callback_1 = input_callback(plot, source, text_banner, topics)

    # currently selected article
    div_curr = Div(
        text="""Click on a plot to see the info about the article.""", width=150
    )
    callback_selected = CustomJS(
        args=dict(source=source, current_selection=div_curr), code=selected_code()
    )
    tap_tool = plot.select(type=TapTool)
    tap_tool.callback = callback_selected

    # WIDGETS
    slider = Slider(
        start=0,
        end=clusters_count,
        value=clusters_count,
        step=1,
        title="Cluster #",
        callback=input_callback_1,
    )
    keyword = TextInput(title="Search:", callback=input_callback_1)

    # pass call back arguments
    input_callback_1.args["text"] = keyword
    input_callback_1.args["slider"] = slider

    if time_range == ClusterTimeRange.LAST_MONTH:
        plot_file_name = "docs/clusters_last_month.html"
        time_range_str = "Last Month"
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        plot_file_name = "docs/clusters_last_half_year.html"
        time_range_str = "Last Half Year"
    elif time_range == ClusterTimeRange.LAST_YEAR:
        plot_file_name = "docs/clusters_last_year.html"
        time_range_str = "Last Year"

    header = header_with_time_range(time_range_str)

    # -------- Style --------

    header.sizing_mode = "stretch_width"
    header.style = {"color": "#2e484c", "font-family": "Julius Sans One, sans-serif;"}
    header.margin = 5

    description.style = {
        "font-family": "Helvetica Neue, Helvetica, Arial, sans-serif;",
        "font-size": "1.1em",
    }
    description.sizing_mode = "stretch_width"
    description.margin = 5

    description_slider.style = {
        "font-family": "Helvetica Neue, Helvetica, Arial, sans-serif;",
        "font-size": "1.1em",
    }
    description_slider.sizing_mode = "stretch_width"

    description_search.style = {
        "font-family": "Helvetica Neue, Helvetica, Arial, sans-serif;",
        "font-size": "1.1em",
    }
    description_search.sizing_mode = "stretch_width"
    description_search.margin = 5

    time_range_title.style = {
        "font-family": "Helvetica Neue, Helvetica, Arial, sans-serif;",
        "font-size": "1.1em",
    }
    time_range_title.sizing_mode = "stretch_width"

    slider.sizing_mode = "stretch_width"
    slider.margin = 15

    keyword.sizing_mode = "scale_both"
    keyword.margin = 15

    div_curr.style = {
        "color": "#BF0A30",
        "font-family": "Helvetica Neue, Helvetica, Arial, sans-serif;",
        "font-size": "1.1em",
    }
    div_curr.sizing_mode = "scale_both"
    div_curr.margin = 20

    text_banner.style = {
        "color": "#0269A4",
        "font-family": "Helvetica Neue, Helvetica, Arial, sans-serif;",
        "font-size": "1.1em",
    }
    text_banner.sizing_mode = "stretch_width"
    text_banner.margin = 20
    text_banner.height = 75

    plot.sizing_mode = "scale_both"
    plot.margin = 5

    r = row(div_curr, text_banner)
    r.sizing_mode = "stretch_width"

    # -------- Layout --------

    if time_range == ClusterTimeRange.LAST_MONTH:
        plot_file_name = "docs/clusters_last_month.html"
        time_range_str = "Last Month"
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        plot_file_name = "docs/clusters_last_half_year.html"
        time_range_str = "Last Half Year"
    elif time_range == ClusterTimeRange.LAST_YEAR:
        plot_file_name = "docs/clusters_last_year.html"
        time_range_str = "Last Year"

    l = layout(
        [
            [header],
            [description],
            [time_range_title],
            [
                time_range_last_month_button,
                time_range_last_half_year_button,
                time_range_last_year_button,
            ],
            [description_slider, description_search],
            [slider, keyword],
            [text_banner],
            [plot],
            [div_curr],
        ]
    )

    save(
        l,
        title="Clustering papers on Supervised Learning by Classification",
        filename=plot_file_name,
    )
