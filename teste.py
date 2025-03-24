import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from app.core.browser import *
from app.core.downloader import *
from app.core.scraper import *
from app.core.transform_scrape import *
from app.config.settings import *


def teste(batch_size=1):

    response = (
        supabase.table("scrape_db")
        .select("id, url")
        .eq("scraped", 1)
        .limit(batch_size)
        .execute()
    )

    records = response.data

    if not records:
        print("Não há registros para processar.")
        return None

    for record in records:
        record_id = record["id"]
        url = record["url"]

    driver = initialize_browser()
    soup = BeautifulSoup(driver.page_source, "html.parser")

    if not driver:
        print("Erro: O navegador não foi inicializado corretamente")
        return 0

    driver.get(url)

    time.sleep(2)  # Aguarda carregamento inicial

    # Scroll para carregar mais produtos
    scroll_page(driver)

    nivel, descricao = verificar_nivel_forca(soup, driver)

    print(nivel, descricao)


if __name__ == "__main__":
    teste()
