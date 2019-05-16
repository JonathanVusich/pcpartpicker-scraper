from pcpartpicker_scraper import Scraper


def main():
    scraper = Scraper()
    results = scraper.retrieve_all_html()
    print(results)

if __name__ == "__main__":
    main()