import sys
import datetime
from app.core.browser import initialize_browser, close_browser
from app.core.scraper import scrape_product_links
from app.core.downloader import download_product_html
from app.database.supabase_client import get_supabase_client
from app.scheduler.tasks import schedule_download_tasks
from app.utils.helpers import setup_logging, get_user_input, get_integer_input
from app.config.settings import PRODUCTS_BATCH_SIZE, DOWNLOAD_INTERVAL


def main():
    """
    Função principal do programa.
    """
    logger = setup_logging()
    logger.info("===== Iniciando extrator de produtos da Evino com Supabase =====")
    logger.info(f"Data/Hora: {datetime.datetime.now()}")

    try:
        # Inicializa o cliente do Supabase
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

    # Pergunta se deve executar a extração inicial
    should_extract = get_user_input(
        "Deseja executar a extração inicial de links? (s/n): ", valid_options=["s", "n"]
    )

    if should_extract == "s":
        # Inicializa o navegador
        driver = initialize_browser()

        if driver:
            try:
                # Extrai links de produtos
                logger.info("Iniciando extração de links de produtos")
                scrape_product_links(driver, supabase)
                logger.info("Extração de links concluída")
            except Exception as e:
                logger.error(f"Erro durante a extração inicial: {e}")
            finally:
                # Fecha o navegador
                close_browser(driver)
        else:
            logger.error(
                "Não foi possível inicializar o navegador. Verifique se o Chrome está instalado."
            )
            sys.exit(1)

        # Primeira execução do download
        logger.info("Iniciando primeiro download de produtos")
        download_product_html(supabase, PRODUCTS_BATCH_SIZE)

    # Configura o intervalo e o tamanho do lote
    interval = get_integer_input(
        f"Digite o intervalo em minutos entre os downloads (recomendado: {DOWNLOAD_INTERVAL}): ",
        min_value=1,
        default=DOWNLOAD_INTERVAL,
    )

    batch = get_integer_input(
        f"Digite quantos produtos baixar por vez (recomendado: {PRODUCTS_BATCH_SIZE}): ",
        min_value=1,
        default=PRODUCTS_BATCH_SIZE,
    )

    # Inicia o agendador
    logger.info("\nIniciando agendador de downloads...")
    schedule_download_tasks(supabase, interval_minutes=interval, batch_size=batch)


if __name__ == "__main__":
    main()
