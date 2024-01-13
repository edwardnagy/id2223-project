from bokeh.models import Div

def header_with_time_range(time_range: str):
    return Div(text=f"""<h1>Clustering Literature on Supervised Learning by Classification ({time_range})</h1>""")

# header
header = Div(text="""<h1>Clustering Literature on Supervised Learning by Classification</h1>""")

time_range_title = Div(
    text="""<h3>Time Range:</h3><p1>Click on the button to change the time range of the plot.</p1>"""
)

time_range_last_month_button = Div(
    text="""<a href="clusters_last_month.html" target="_blank"><button>Last Month</button></a>"""
)

time_range_last_half_year_button = Div(
    text="""<a href="clusters_last_half_year.html" target="_blank"><button>Last Half Year</button></a>"""
)

time_range_last_year_button = Div(
    text="""<a href="clusters_last_year.html" target="_blank"><button>Last Year</button></a>"""
)

# project description
description = Div(
    text="""Clustering of literature on supervised learning by classification from ACM Digital Library. 
    The dataset is extracted from <a href="https://dl.acm.org/topic/ccs2012/10010147.10010257.10010258.10010259.10010263?expand=all&startPage=">here</a>."""
)

description_search = Div(
    text="""<h3>Filter by Text:</h3><p1>Search keyword to filter out the plot. It will search abstracts, titles and authors. 
    Press enter when ready. Clear and press enter to reset the plot.</p1>"""
)

description_slider = Div(
    text="""<h3>Filter by the Clusters:</h3><p1>The slider below can be used to filter the target cluster. 
Simply slide the slider to the desired cluster number to display the plots that belong to that cluster. 
Slide back to the last cluster to show all the plots.</p1>"""
)

description_keyword = Div(text="""<h3>Keywords:</h3>""")

description_current = Div(text="""<h3>Selected:</h3>""")
