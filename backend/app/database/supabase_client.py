import datetime
import logging
from supabase import create_client, Client


from backend.app.config.settings import SUPABASE_URL, SUPABASE_KEY, EVINO_PRODUCTS_URL
from backend.app.core.scraper_aux import *
from backend.app.core.scraper import *
from backend.app.utils.helpers import *


logger = logging.getLogger("evino_scraper")


def get_supabase_client() -> Client:
    """
    Inicializa e retorna um cliente do Supabase.

    Returns:
        Client: O cliente do Supabase configurado.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são necessárias"
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def process_product_links(soup, supabase):
    """
    Extrai e salva links de produtos, com log detalhado.

    Args:
        soup (BeautifulSoup): Objeto BeautifulSoup da página
        supabase (Client): Cliente do Supabase

    Returns:
        int: Número de novos links adicionados
    """
    logger = setup_logging()
    # Extrair links de produtos
    product_links = extract_product_links(soup)

    if not product_links:
        logger.warning("Nenhum link de produto encontrado")
        return 0

    logger.info(f"Total de {len(product_links)} links de produtos encontrados")

    # Salvar links no Supabase, já verificando duplicidades
    new_links_count = save_links_to_supabase(supabase, product_links)

    logger.info(f"{new_links_count} novos links únicos salvos no banco de dados")

    return new_links_count


def insert_product_url(supabase: Client, url: str) -> bool:
    """
    Insere uma nova URL de produto no Supabase se ela não existir.

    Args:
        supabase (Client): Cliente do Supabase.
        url (str): URL do produto a ser inserida.

    Returns:
        bool: True se a URL foi inserida, False caso contrário.
    """
    try:
        data = {
            "url": url,
            "created_at": datetime.datetime.now().isoformat(),
        }
        result = supabase.table("scrape_db").insert(data).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.info(f"Erro ao inserir URL {url}: {e}")
        return False


def get_existing_urls(supabase: Client) -> list:
    """
    Retorna todas as URLs de produtos já existentes no Supabase.

    Args:
        supabase (Client): Cliente do Supabase.

    Returns:
        list: Lista de URLs existentes.
    """
    result = supabase.table("scrape_db").select("url").execute()
    return [item["url"] for item in result.data]


def get_pending_products(supabase: Client, limit: int = 10) -> list:
    """
    Retorna produtos pendentes para download.

    Args:
        supabase (Client): Cliente do Supabase.
        limit (int): Número máximo de produtos a retornar.

    Returns:
        List[Dic]: Lista de dicionarios de produtos pendentes, cada dicionário tem o formato {"id":int, "url":str}.
    """
    result = (
        supabase.table("scrape_db")
        .select("id", "url")
        .eq("scraped", 0)
        .limit(limit)
        .execute()
    )
    return result.data


def update_product_html(supabase: Client, product_id: int, html_content: str) -> bool:
    """
    Atualiza o conteúdo HTML de um produto.

    Args:
        supabase (Client): Cliente do Supabase.
        product_id (int): ID do produto.
        html_content (str): Conteúdo HTML do produto.

    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário.
    """
    try:
        now = datetime.datetime.now().isoformat()
        result = (
            supabase.table("scrape_db")
            .update(
                {
                    "html_downloaded": 1,
                    "html_content": html_content,
                    "downloaded_at": now,
                }
            )
            .eq("id", product_id)
            .execute()
        )
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Erro ao atualizar produto {product_id}: {e}")
        return False


def get_statistics(supabase: Client) -> dict:
    """
    Retorna estatísticas sobre os produtos.

    Args:
        supabase (Client): Cliente do Supabase.

    Returns:
        dict: Dicionário com estatísticas.
    """
    # Contar total de produtos usando apenas o ID
    total_result = supabase.table("scrape_db").select("id", count="exact").execute()
    total = total_result.count

    # Contar produtos já baixados usando apenas o ID
    downloaded_result = (
        supabase.table("scrape_db")
        .select("id", count="exact")
        .eq("html_downloaded", 1)
        .execute()
    )
    downloaded = downloaded_result.count

    return {"total": total, "downloaded": downloaded, "pending": total - downloaded}


def check_pending_products(supabase: Client) -> int:
    """
    Verifica quantos produtos estão pendentes para download.

    Args:
        supabase (Client): Cliente do Supabase.

    Returns:
        int: Número de produtos pendentes.
    """
    result = supabase.table("scrape_db").select("id").eq("scraped", 0).execute()
    return len(result.data)


def scrape_product_links(driver, supabase: Client):
    """
    Extrai links de produtos da página da Evino.

    Args:
        driver (webdriver.Chrome): O navegador inicializado.
        supabase (Client): Cliente do Supabase.

    Returns:
        int: Número de novos links adicionados.
    """
    if not driver:
        logger.error("Erro: O navegador não foi inicializado corretamente")
        return 0

    try:
        logger.info(f"Acessando página de vinhos: {EVINO_PRODUCTS_URL}")
        driver.get(EVINO_PRODUCTS_URL)
        logger.info("Página carregada")

        time.sleep(5)

        # Scroll para carregar mais produtos
        scroll_page(driver)

        # Extrai links de produtos
        logger.info("Extraindo links de produtos...")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Encontra todos os links de produtos
        links = extract_product_links(soup)

        # Remove duplicados
        unique_links = list(set(links))
        logger.info(f"Total de links únicos encontrados: {len(unique_links)}")

        # Salva os links no Supabase
        return save_links_to_supabase(supabase, unique_links)

    except Exception as e:
        logger.error(f"Erro durante a extração de links: {e}")
        return 0


def save_links_to_supabase(supabase, links):
    """
    Salva os links no Supabase.

    Args:
        supabase (Client): Cliente do Supabase.
        links (list): Lista de links de produtos.

    Returns:
        int: Número de novos links adicionados.
    """
    # Busca URLs já existentes no Supabase
    existing_urls = get_existing_urls(supabase)

    count = 0
    for link in links:
        if link.startswith("/"):
            full_url = EVINO_BASE_URL + link
        else:
            full_url = link

        if full_url not in existing_urls:
            if insert_product_url(supabase, full_url):
                count += 1

    logger.info(f"{count} novos links salvos no Supabase")
    return count


def extract_urls_from_database(limit=20):
    """
    Extracts URLs to process from the database

    Args:
        limit (int): Maximum number of URLs to extract

    Returns:
        list: List of URLs to process
    """
    try:
        response = (
            supabase.table("scrape_db")
            .select("id, url")
            .eq("scraped", 0)
            .limit(limit)
            .execute()
        )
        urls = [(record["id"], record["url"]) for record in response.data]
        return urls

    except Exception as e:
        logger.error(f"Erro ao buscar URLs: {str(e)}")
        return []


def process_and_upsert_wine_data(driver, url, id):
    """
    Processes URLs and upserts the extracted data to the wine_data table

    Args:
        driver (webdriver.Chrome): Initialized Selenium webdriver
        url (list): Url to process
        id (int): Register ID on Supabase table

    Returns:
        int: Number of successfully processed URLs
    """
    processed_count = 0
    not_processed_count = 0

    try:
        wine_data = scrape_wine_info_with_selenium(driver, url)

        if wine_data:
            wine_data["id"] = id
            result = supabase.table("wine_data").upsert(wine_data).execute()
            update_scraped = (
                supabase.table("scrape_db")
                .update({"scraped": 1})
                .eq("id", id)
                .execute()
            )

            if result.data and update_scraped.data:
                logger.info(
                    f"Dados do vinho de ID {id} inseridos/atualizados com sucesso"
                )
                processed_count += 1
                return processed_count

    except KeyboardInterrupt as e:
        logger.info(f"Programa encerrado pelo usuário.")
        sys.exit(1)

    except Exception as e:
        update_scraped = (
            supabase.table("scrape_db").update({"scraped": -1}).eq("id", id).execute()
        )
        if update_scraped.data:
            logger.error(
                f"Erro ao processar o ID {id}, não é possível fazer o scraping. Scraped setado em -1."
            )
            not_processed_count -= 1
            return not_processed_count

    return processed_count
