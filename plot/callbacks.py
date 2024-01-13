from bokeh.models import CustomJS

# handle the currently selected article
def selected_code():
    code = """
        var titles = [];
        var authors = [];
        var abstracts = [];
        var publicationDates = [];
        var clusters = [];

        cb_data.source.selected.indices.forEach(index => {
            titles.push(source.data['title'][index]);
            authors.push(source.data['author'][index]);
            abstracts.push(source.data['abstract'][index]);
            publicationDates.push(source.data['publication_date'][index]);
            clusters.push(source.data['cluster'][index]);
        });

        var title = "<p1><b>Title:</b> " + (titles[0] ? titles[0].toString() : "Not available.") + "<br>";
        var author = "<p1><b>Author:</b> " + (authors[0] ? authors[0].toString() : "Not available.") + "<br>";
        var abstract = "<p1><b>Abstract:</b> " + abstracts[0].toString() + "<br>";
        var publicationDate = "<p1><b>Publication Date:</b> " + publicationDates[0].toString() + "</p1><br>";
        var cluster = "<p1><b>Cluster:</b> " + clusters[0].toString() + "</p1>";

        current_selection.text = title + author + abstract + publicationDate + cluster;
        current_selection.change.emit();
    """
    return code

# handle the keywords and search
def input_callback(plot, source, out_text, topics): 

    # slider call back for cluster selection
    callback = CustomJS(args=dict(p=plot, source=source, out_text=out_text, topics=topics), code="""
				var key = text.value;
				key = key.toLowerCase();
				var cluster = slider.value;
                var clusters_count = slider.end;
                var data = source.data; 
                
                
                x = data['x'];
                y = data['y'];
                x_backup = data['x_backup'];
                y_backup = data['y_backup'];
                labels = data['cluster'];
                abstract = data['abstract'];
                title = data['title'];
                author = data['author'];
                if (cluster == clusters_count) {
                    out_text.text = 'Keywords: Slide to specific cluster to see the keywords.';
                    for (i = 0; i < x.length; i++) {
						if(abstract[i].toLowerCase().includes(key) || 
                        (title[i] && title[i].toLowerCase().includes(key)) ||
                        (author[i] && author[i].toLowerCase().includes(key))) {
							x[i] = x_backup[i];
							y[i] = y_backup[i];
						} else {
							x[i] = undefined;
							y[i] = undefined;
						}
                    }
                }
                else {
                    out_text.text = 'Keywords: ' + topics[Number(cluster)];
                    for (i = 0; i < x.length; i++) {
                        if(labels[i] == cluster) {
							if(abstract[i].toLowerCase().includes(key)
                            || (title[i] && title[i].toLowerCase().includes(key))
                            || (author[i] && author[i].toLowerCase().includes(key))) {
								x[i] = x_backup[i];
								y[i] = y_backup[i];
							} else {
								x[i] = undefined;
								y[i] = undefined;
							}
                        } else {
                            x[i] = undefined;
                            y[i] = undefined;
                        }
                    }
                }
            source.change.emit();
            """)
    return callback