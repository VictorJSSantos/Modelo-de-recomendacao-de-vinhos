import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from supabase import Client


from app.config.settings import (
    EVINO_PRODUCTS_URL,
    EVINO_BASE_URL,
    MAX_SCROLLS,
    SCROLL_DELAY,
    BUTTON_CLICK_DELAY,
)
from app.database.supabase_client import get_existing_urls, insert_product_url


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
        print("Erro: O navegador não foi inicializado corretamente")
        return 0

    try:
        print(f"Acessando página de vinhos: {EVINO_PRODUCTS_URL}")
        driver.get(EVINO_PRODUCTS_URL)
        print("Página carregada")

        time.sleep(5)  # Aguarda carregamento inicial

        # Scroll para carregar mais produtos
        scroll_page(driver)

        # Extrai links de produtos
        print("Extraindo links de produtos...")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Encontra todos os links de produtos
        links = extract_product_links(soup)

        # Remove duplicados
        unique_links = list(set(links))
        print(f"Total de links únicos encontrados: {len(unique_links)}")

        # Salva os links no Supabase
        return save_links_to_supabase(supabase, unique_links)

    except Exception as e:
        print(f"Erro durante a extração de links: {e}")
        return 0


def scroll_page(driver):
    """
    Rola a página para carregar mais produtos e clica em botões de "Mostrar mais".

    Args:
        driver (webdriver.Chrome): O navegador inicializado.
    """
    print("Rolando a página para carregar produtos...")
    last_height = driver.execute_script("return document.body.scrollHeight")

    for scroll in range(MAX_SCROLLS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_DELAY)

        try:
            # Tenta clicar em botões de "Mostrar mais"
            buttons = driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Mostrar mais') or contains(text(), 'Carregar mais')]",
            )
            if buttons:
                for button in buttons:
                    if button.is_displayed():
                        print("Botão 'Mostrar mais produtos' encontrado. Clicando...")
                        driver.execute_script(
                            "arguments[0].scrollIntoView(true);", button
                        )
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", button)
                        print("Clique realizado")
                        time.sleep(BUTTON_CLICK_DELAY)
        except Exception as e:
            print(f"Erro ao tentar clicar no botão: {e}")

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print(f"Fim da página alcançado após {scroll+1} scrolls")
            break
        last_height = new_height

        print(f"Scroll {scroll+1}/{MAX_SCROLLS} concluído")


def extract_product_links(soup):
    """
    Extrai links de produtos da página.

    Args:
        soup (BeautifulSoup): Objeto BeautifulSoup da página.

    Returns:
        list: Lista de links de produtos.
    """
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "/product/" in href:
            links.append(href)
    return links


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

    print(f"{count} novos links salvos no Supabase")
    return count
