from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# TODO: Set ChromeDriver path
driver_path = "/path/to/chromedriver"
# TODO: Set search link to search for last month's papers
search_link = "https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&ConceptID=1994&expand=all&field1=AllField&text1=BMW&startPage=0&pageSize=10"


def save_paper(abstract: str, publication_date: date, citation: str):
    print("Saving paper...")
    print(f"Abstract: {abstract}")
    print(f"Publication date: {publication_date}")
    print(f"Citation: {citation}")
    print("Paper saved!")


def initialize_driver() -> webdriver.Remote:
    driver = webdriver.Chrome()
    return driver


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


def scrape_paper_on_paper_page(driver: webdriver.Remote):
    # Get necessary information
    abstract: str = get_abstract_on_paper_page(driver)
    publication_date: date = get_publication_date_on_paper_page(driver)
    citation: str = get_citation_on_paper_page(driver)
    # Save the paper
    save_paper(abstract, publication_date, citation)


def scrape_papers_on_search_page(driver: webdriver.Remote):
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
    for paper_link in paper_links:
        driver.get(paper_link)
        scrape_paper_on_paper_page(driver)


def scrape_papers_by_search_link(search_link: str):
    driver: webdriver.Remote = initialize_driver()

    current_page = search_link
    while current_page is not None:
        print(f"Scraping page: {current_page}")
        driver.get(current_page)
        scrape_papers_on_search_page(driver)
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
    scrape_papers_by_search_link(search_link)
