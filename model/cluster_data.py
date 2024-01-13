from dataclasses import dataclass
import pandas as pd


@dataclass
class ClusterData:
    papers_df: pd.DataFrame
    topics: list
    