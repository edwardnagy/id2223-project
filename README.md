# Clustering Literature on Supervised Learning by Classification

*Made for the course ID2223 Scalable Machine Learning and Deep Learning at KTH Royal Institute of Technology.*

The project clusters the literature from the ACM Digital Library on the topic of Supervised Learning by Classification, by using the abstracts of the papers as input. The clustering is done by using the K-Means algorithm, and the results are visualized in a user interface, displaying the clusters for the last month, 6 months, and 12 months.

The system is built in the form of a Serverless Machine Learning System, where the data is scraped periodically, stored in a feature store (Hopsworks), and then used to form clusters. The results are then saved to the feature store, and visualized in a user interface, which is deployed on GitHub Pages. These steps are run separately on GitHub Actions.

User interface link: https://edwardnagy.github.io/id2223-project

## Dataset

The dataset used in this project is the literature from the ACM Digital Library on the topic of Supervised Learning by Classification. 

Link to the dataset: https://dl.acm.org/topic/ccs2012/10010147.10010257.10010258.10010259.10010263?expand=all&startPage=

## Method

### 1. Data collection

The data is collected by scraping the ACM Digital Library website, using the algorithm in the file `monthly_feature_pipeline.py`. The papers are scraped and uploaded to the Hopsworks Feature Store in batches of 50.

The following features are extracted from the papers:
* Citation
* Abstract
* Publication date

### 2. Data processing and clustering

The data processing and clustering algorithm can be found in the `training_pipeline.py` and `training_pipeline.ipynb` files. 

The algorithm is as follows:
1. Read the data from the Hopsworks Feature Store.
2. Preprocess the data (abstracts) by removing stop words and punctuation.
3. Vectorize the abstracts by using the TF-IDF algorithm.
4. Cluster the abstracts by using the K-Means algorithm. The number of clusters has been determined by using the Elbow method, and is set to 11, 6 and 3 for the last year, 6 months, and month, respectively.
5. Create 2D embeddings of the abstracts by using the TSNE algorithm.
6. Get the top keywords for each cluster by vectorizing the abstracts in each cluster, applying Latent Dirichlet Allocation (LDA) to the vectorized abstracts, and then extracting the words based on the LDA model.
7. Save the results to the Hopsworks Feature Store.


This algorithm is run at the beginning of each month, after the input data has been scraped and uploaded to the Hopsworks Feature Store. The algorithm is run in parallel for clustering the papers of the last month, last 6 months, and last year. The trigger files for the GitHub Actions workflows are `training_last_month_pipeline.py`, `training_last_half_year_pipeline.py`, and `training_last_year_pipeline.py`, which call the described algorithm for the corresponding time period.

### 3. Visualization

The plotting algorithm reads the results from the Hopsworks Feature Store, and plots the clusters for the last month, 6 months, and 12 months using the Bokeh library, then saves the plots to the `docs` folder as HTML files.
The algorithm can be found in the `plot_clusters.py` file.

The user interface provides the following functionality:
* Select the time period to display the clusters for – last month, last 6 months, or last year (default).
* Filter by the cluster number.
* Filter by a text, which will display the papers that contain the text in their abstracts, authors, or titles.
* Display the top keywords for each cluster.
* Display information about a paper by hovering over it or clicking on it.
* Zoom, pan, and reset the plot.


## Results

The user interface can be found at the following link: https://edwardnagy.github.io/id2223-project

### Conclusion
The clusters appear well-separated for the past year, with top keywords relevant to each cluster. However, the clustering is less successful for the last 6 months and last month, due to the limited number of papers in the dataset these periods.

### Suggestions for improvement:
* Use a larger dataset, rather than the curated dataset from the ACM Digital Library.
* Analyze the whole content of the papers, rather than just the abstracts.

## Running the code

1. Activate your virtual Python environment with Python 3.11.5, and install the required packages with the following command:

```
pip install -r requirements.txt
```

2. Run any of the pipelines and algorithms described above by running the corresponding Python or Jupyter Notebook file.

## References

[COVID-19 Kaggle Literature Organization - Maksim Eren, 2020](https://www.maksimeren.com/publication/eren_doceng2021/)

