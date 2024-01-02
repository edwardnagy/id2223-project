from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import hopsworks
from hsfs import feature_group as fg
import pandas as pd
import os

is_ci_env = os.getenv("GITHUB_ACTIONS") == "true"


def initialize_feature_group():
    project = hopsworks.login()
    fs = project.get_feature_store()
    acm_papers_fg = fs.get_feature_group("acm_papers", 1)
    return acm_papers_fg


def initialize_driver() -> webdriver.Remote:
    if is_ci_env:
        service = Service(executable_path="/usr/local/bin/chromedriver")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome()
    return driver


def get_past_month_search_link():
    # Get the current date
    today = date.today()
    # Get the first day of the previous month
    if today.month == 1:
        first_day_of_previous_month = today.replace(
            year=today.year - 1, month=12, day=1
        )
    else:
        first_day_of_previous_month = today.replace(month=today.month - 1, day=1)
    # Get the search link for the past month
    search_link = (
        "https://dl.acm.org/topic/ccs2012/10010147.10010257.10010258.10010259.10010263?expand=all&EpubDate=%5B"
        + first_day_of_previous_month.strftime("%Y%m%d")
        + "+TO+"
        + today.strftime("%Y%m%d")
        + "2359%5D&queryID=54/6448494997&pageSize=50&startPage=0&sortBy=EpubDate_asc"
    )
    return search_link


class Paper:
    def __init__(self, abstract: str, publication_date: date, citation: str):
        self.abstract = abstract
        self.publication_date = publication_date
        self.citation = citation

    def __str__(self):
        return f"Paper(abstract={self.abstract}, publication_date={self.publication_date}, citation={self.citation})"


def save_papers_to_feature_group(feature_group: fg.FeatureGroup, papers: list[Paper]):
    print("Saving papers to feature group...")
    papers_data = {
        "abstract": map(lambda paper: paper.abstract, papers),
        "publication_date": map(lambda paper: paper.publication_date, papers),
        "citation": map(lambda paper: paper.citation, papers),
    }
    papers_df = pd.DataFrame(data=papers_data)
    feature_group.insert(papers_df)
    print("Papers saved to feature group!")


def get_abstract_on_paper_page(driver: webdriver.Remote) -> str:
    abstract = (
        WebDriverWait(driver, 10)
        .until(EC.visibility_of_element_located((By.CLASS_NAME, "abstractSection")))
        .text
    )
    return abstract


def get_publication_date_on_paper_page(driver: webdriver.Remote) -> date:
    # expected format: 01 January 2024
    try:
        publication_date_string = driver.find_element(
            By.CLASS_NAME, "CitationCoverDate"
        ).text
    except:
        # Books have a different format
        publication_date_string = driver.find_element(
            By.XPATH,
            '//div[@class="item-meta__info"]/div[3]/div[2]',
        ).text
    publication_date = datetime.strptime(publication_date_string, "%d %B %Y").date()
    return publication_date


def get_citation_on_paper_page(driver: webdriver.Remote) -> str:
    # Wait for the button to load. For some unknown reason, it would redirect
    # to the homepage if the button is clicked too early.
    time.sleep(1)
    try:
        export_citation_button = driver.find_element(
            By.CSS_SELECTOR,
            'a[aria-label="Export Citations"]',
        )
    except:
        # Books have a different format
        export_citation_button = driver.find_element(
            By.CSS_SELECTOR,
            'a[data-title="Export Citation"]',
        )
    export_citation_button.click()
    citation = (
        WebDriverWait(driver, 10)
        .until(EC.visibility_of_element_located((By.CLASS_NAME, "csl-right-inline")))
        .text
    )
    return citation


def get_paper_on_paper_page(driver: webdriver.Remote) -> Paper:
    # Get necessary information
    abstract: str = get_abstract_on_paper_page(driver)
    publication_date: date = get_publication_date_on_paper_page(driver)
    citation: str = get_citation_on_paper_page(driver)
    paper = Paper(abstract, publication_date, citation)

    return paper


def scrape_papers_on_search_page(
    driver: webdriver.Remote, feature_group: fg.FeatureGroup
):
    print(f"Scraping papers on search page: {driver.current_url}")

    # Get all search results
    search_results = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.CLASS_NAME, "issue-item__content"))
    )
    # Get all paper links
    paper_links = []
    for search_result in search_results:
        title_span = search_result.find_element(By.CLASS_NAME, "issue-item__title")
        paper_link = title_span.find_element(By.TAG_NAME, "a").get_attribute("href")
        paper_links.append(paper_link)
    # Scrape each paper
    papers = []
    for paper_link in paper_links:
        print(f"Scraping paper on paper page: {paper_link}")
        driver.get(paper_link)
        paper = get_paper_on_paper_page(driver)
        print(f"Paper scraped: {paper_link}")
        papers.append(paper)
    # Save the papers
    save_papers_to_feature_group(feature_group, papers)


def scrape_papers_by_search_link(search_link: str, feature_group: fg.FeatureGroup):
    driver: webdriver.Remote = initialize_driver()

    current_page = search_link
    while current_page is not None:
        driver.get(current_page)
        scrape_papers_on_search_page(driver, feature_group)
        # Go back to the search page
        driver.get(current_page)
        try:
            # Go to the next page
            next_page = driver.find_element(By.CLASS_NAME, "pagination__btn--next")
            current_page = next_page.get_attribute("href")
        except:
            # No more pages
            current_page = None


if __name__ == "__main__":
    feature_group = initialize_feature_group()
    search_link = get_past_month_search_link()
    # scrape_papers_by_search_link(search_link, feature_group)
