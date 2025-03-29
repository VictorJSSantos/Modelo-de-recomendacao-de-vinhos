import sys
import datetime
from bs4 import BeautifulSoup

from app.config.settings import EVINO_PRODUCTS_URL, EVINO_BASE_URL
from app.core.browser import initialize_browser, close_browser
from app.core.scraper_aux import extract_product_links, scroll_page
from app.core.scraper import scrape_wine_info_with_selenium
from app.database.supabase_client import (
    get_supabase_client,
    save_links_to_supabase,
    process_and_upsert_wine_data,
    process_product_links,
    get_pending_products,
)
from app.utils.helpers import setup_logging, get_user_input, get_integer_input
from app.scheduler.tasks import *


def main():
    """
    Main function to orchestrate the Evino wine scraping process.
    """
    logger = setup_logging()
    logger.info("===== Iniciando extrator de vinhos da Evino com Supabase =====")
    logger.info(f"Data/Hora: {datetime.datetime.now()}")

    try:
        supabase = get_supabase_client()
        logger.info("Conexão com Supabase estabelecida com sucesso")
    except ValueError as e:
        logger.error(f"Erro: {e}")
        logger.error(
            "Adicione as variáveis de ambiente SUPABASE_URL e SUPABASE_KEY antes de continuar."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro ao conectar com Supabase: {e}")
        sys.exit(1)

    # Ask if initial extraction should be performed
    should_extract = get_user_input(
        "Deseja executar a extração inicial de links de vinhos? (s/n): ",
        valid_options=["s", "n"],
    )
    new_links_count = None

    # Initialize browser
    driver = initialize_browser()

    if should_extract == "s":

        if driver:
            try:
                # Navigate to products page and get page source
                driver.get(EVINO_PRODUCTS_URL)
                scroll_page(driver)  # Scroll to load more products
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")

                logger.info("Iniciando extração de links de produtos")
                product_links = extract_product_links(soup)

                if not product_links:
                    logger.warning("Nenhum link de produto encontrado")
                    return None  # Ou return, dependendo do contexto

                logger.info(
                    f"Total de {len(product_links)} links de produtos encontrados"
                )

                # Salvar links no Supabase
                new_links_count = save_links_to_supabase(supabase, product_links)
                logger.info(f"Novos links salvos: {new_links_count}")

            except Exception as e:
                logger.error(f"Erro durante a extração inicial: {e}")
            # finally:
            #     # Close the browser
            #     close_browser(driver)
        else:
            logger.error(
                "Não foi possível inicializar o navegador. Verifique se o Chrome está instalado."
            )
            new_links_count = None

    # Option to schedule future extractions
    schedule_extraction = get_user_input(
        "Deseja agendar extrações futuras? (s/n): ", valid_options=["s", "n"]
    )

    if schedule_extraction == "s":
        interval = get_integer_input(
            "Digite o intervalo em minutos entre as extrações: ",
            min_value=0,
            default=30,
        )

        batch_size = get_integer_input(
            "Digite o tamanho do batch das extrações: ",
            min_value=1,
            default=30,
        )

        max_batches = get_integer_input(
            "Digite o tamanho do batch das extrações: ",
            min_value=1,
            default=1,
            max_value=10,
        )

        logger.info(
            f"\nAgendamento de extrações a cada {interval} minutos  para a retirada de {batch_size} produtos por lote em {max_batches} lotes."
        )

        if new_links_count:
            pending_product_data = get_pending_products(supabase, limit=new_links_count)
        else:
            pending_product_data = get_pending_products(
                supabase, limit=batch_size * max_batches
            )

        # pending_product_urls = [i["url"] for i in pending_product_data]
        # pending_product_ids = [i["id"] for i in pending_product_data]

        # print(f'\URLS: {pending_product_urls}\n')
        # print(f'\nIDS: {pending_product_ids}\n')

        schedule_download_tasks(
            driver,
            supabase,
            pending_product_data,
            interval_minutes=interval,
            batch_size=batch_size,
            max_batches=max_batches,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
