from datetime import date, datetime
import string
import hopsworks
from hsfs.feature import Feature
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import spacy
import spacy_transformers
from spacy.cli import download
from spacy.lang.en import STOP_WORDS
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from model.cluster_time_range import ClusterTimeRange
from custom_stop_words import custom_stop_words

random_seed = 42


# Connect to Hopsworks
project = hopsworks.login()
fs = project.get_feature_store()


def get_papers(time_range: ClusterTimeRange) -> pd.DataFrame:
    """Get papers for the provided time range."""
    df = (
        fs.get_feature_group("acm_papers", 1)
        .filter(
            (Feature("publication_date") >= time_range.get_start_date())
            & (Feature("publication_date") <= time_range.get_end_date())
        )
        .read(read_options={"use_hive": True})
    )
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the data."""

    df = df.drop_duplicates(subset=["abstract"], keep="first")

    # Remove "Abstract\n" from the beginning of the abstract, it's a scraping error
    scraping_error = "Abstract\n"
    df["abstract"] = df["abstract"].str.replace(f"^{scraping_error}", "", regex=True)

    # Remove punctuation and stop words

    punctuations = string.punctuation
    stop_words = list(STOP_WORDS)

    for word in custom_stop_words:
        if word not in stop_words:
            stop_words.append(word)

    # Check if English words are already downloaded for spaCy
    try:
        import en_core_web_trf
    except ImportError:
        # Download English words for spaCy
        download("en_core_web_trf")
        nlp = spacy.load("en_core_web_trf")

    import en_core_web_trf

    parser = en_core_web_trf.load(disable=["tagger", "ner"])

    def spacy_tokenizer(sentence):
        mytokens = parser(sentence)
        mytokens = [
            word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_
            for word in mytokens
        ]
        mytokens = [
            word
            for word in mytokens
            if word not in stop_words and word not in punctuations
        ]
        mytokens = " ".join([i for i in mytokens])
        return mytokens

    # Show progress bar
    tqdm.pandas()

    df["abstract_clean"] = df["abstract"].progress_apply(spacy_tokenizer)

    return df


def vectorize_abstracts(clean_abstracts: list[str]) -> list[list[float]]:
    """Vectorize the abstracts."""

    vectorizer = TfidfVectorizer(
        max_features=2**12
    )  # 2**12 = 4096 (just a big initial number, will be reduced later)
    X = vectorizer.fit_transform(clean_abstracts)

    pca = PCA(n_components=0.95, random_state=random_seed)
    X_reduced = pca.fit_transform(X.toarray())

    return X_reduced


def get_clusters_count(time_range: ClusterTimeRange) -> int:
    """Get the number of clusters for the provided time range.
    This is based on empirical observations."""

    if time_range == ClusterTimeRange.LAST_MONTH:
        k = 3
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        k = 6
    elif time_range == ClusterTimeRange.LAST_YEAR:
        k = 11

    return k


def kmeans_clustering(
    X_reduced: list[list[float]],
    df: pd.DataFrame,
    time_range: ClusterTimeRange,
) -> pd.DataFrame:
    """Cluster the data using k-means clustering."""

    kmeans = KMeans(n_clusters=get_clusters_count(time_range), random_state=random_seed)
    clusters = kmeans.fit_predict(X_reduced)
    df["cluster"] = clusters

    return df


def get_2d_embeddings(
    X_reduced: list[list[float]],
    time_range: ClusterTimeRange,
) -> list[list[float]]:
    """Get the 2D embeddings."""

    if time_range == ClusterTimeRange.LAST_YEAR:
        perplexity = 50
    else:
        perplexity = 5

    tsne = TSNE(verbose=1, perplexity=perplexity, random_state=42)
    X_embedded = tsne.fit_transform(X_reduced)

    return X_embedded


def get_keywords_for_clusters(
    df: pd.DataFrame,
    time_range: ClusterTimeRange,
) -> list[list[str]]:
    """Get the keywords for each cluster."""

    k = get_clusters_count(time_range)

    vectorizers = []
    for _ in range(0, k):
        vectorizers.append(
            CountVectorizer(
                min_df=5,
                max_df=0.9,
                stop_words="english",
                lowercase=True,
                token_pattern="[a-zA-Z-][a-zA-Z-]{2,}",
            )
        )

    vectorized_data = []
    for current_cluster, cvec in enumerate(vectorizers):
        try:
            vectorized_data.append(
                cvec.fit_transform(
                    df.loc[df["cluster"] == current_cluster, "abstract_clean"]
                )
            )
        except Exception as _:
            print("Not enough instances in cluster: " + str(current_cluster))
            vectorized_data.append(None)

    # number of topics per cluster
    NUM_TOPICS_PER_CLUSTER = k

    lda_models = []
    for ii in range(0, k):
        # Latent Dirichlet Allocation Model
        lda = LatentDirichletAllocation(
            n_components=NUM_TOPICS_PER_CLUSTER,
            max_iter=10,
            learning_method="online",
            verbose=False,
            random_state=42,
        )
        lda_models.append(lda)

    clusters_lda_data = []
    for current_cluster, lda in enumerate(lda_models):
        if vectorized_data[current_cluster] != None:
            clusters_lda_data.append(
                (lda.fit_transform(vectorized_data[current_cluster]))
            )

    # Get the keywords for each cluster
    def selected_topics(model, vectorizer, top_n=3):
        current_words = []
        keywords = []

        for _, topic in enumerate(model.components_):
            words = [
                (vectorizer.get_feature_names_out()[i], topic[i])
                for i in topic.argsort()[: -top_n - 1 : -1]
            ]
            for word in words:
                if word[0] not in current_words:
                    keywords.append(word)
                    current_words.append(word[0])

        keywords.sort(key=lambda x: x[1])
        keywords.reverse()

        return_values = []
        for ii in keywords:
            return_values.append(ii[0])
        return return_values

    all_keywords = []
    for current_vectorizer, lda in enumerate(lda_models):
        if vectorized_data[current_vectorizer] != None:
            all_keywords.append(selected_topics(lda, vectorizers[current_vectorizer]))
        else:
            all_keywords.append([])

    # Print out topics for each cluster
    for ii in range(0, k):
        if vectorized_data[ii] != None:
            print("Cluster " + str(ii) + " topics:", all_keywords[ii])

    return all_keywords


def save_clusters(
    df: pd.DataFrame,
    all_keywords: list[list[str]],
    time_range: ClusterTimeRange,
):
    """Save the clusters."""

    # Save clustered papers
    if time_range == ClusterTimeRange.LAST_MONTH:
        fg_name = "acm_papers_clustered_last_month"
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        fg_name = "acm_papers_clustered_last_half_year"
    elif time_range == ClusterTimeRange.LAST_YEAR:
        fg_name = "acm_papers_clustered_last_year"
    # for some reason, the publication_date column is not read as a date column
    df["publication_date"] = [
        datetime.strptime(date_string, "%Y-%m-%d")
        for date_string in df["publication_date"]
    ]
    clustered_papers_fg = fs.get_or_create_feature_group(
        name=fg_name,
        version=1,
        description="Clustered papers",
        primary_key=["citation"],
        event_time="publication_date",
    )
    clustered_papers_fg.insert(df, overwrite=True)

    # Save cluster keywords
    all_keywords_strings = []
    for cluster_keywords in all_keywords:
        all_keywords_strings.append(", ".join(cluster_keywords))
    df_keywords = pd.DataFrame(
        {"cluster": range(0, len(all_keywords)), "keywords": all_keywords_strings}
    )
    if time_range == ClusterTimeRange.LAST_MONTH:
        fg_name = "acm_papers_cluster_keywords_last_month"
    elif time_range == ClusterTimeRange.LAST_HALF_YEAR:
        fg_name = "acm_papers_cluster_keywords_last_half_year"
    elif time_range == ClusterTimeRange.LAST_YEAR:
        fg_name = "acm_papers_cluster_keywords_last_year"
    keywords_fg = fs.get_or_create_feature_group(
        "acm_papers_cluster_keywords_last_year",
        version=1,
        description="The keywords for each cluster",
        primary_key=["cluster"],
    )
    keywords_fg.insert(df_keywords, overwrite=True)


def cluster_papers(time_range: ClusterTimeRange):
    """Cluster papers for the provided time range."""

    papers_df = get_papers(time_range)
    papers_df = clean_data(papers_df)
    clean_abstracts = papers_df["abstract_clean"].values.tolist()
    X_reduced = vectorize_abstracts(clean_abstracts)
    papers_df = kmeans_clustering(X_reduced, papers_df, time_range)
    X_embedded = get_2d_embeddings(X_reduced, time_range)
    papers_df["x_coord"] = X_embedded[:, 0]
    papers_df["y_coord"] = X_embedded[:, 1]
    all_keywords = get_keywords_for_clusters(papers_df, time_range)
    save_clusters(papers_df, all_keywords, time_range)
