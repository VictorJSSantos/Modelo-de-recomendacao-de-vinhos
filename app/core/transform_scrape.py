import time
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client, Client
import sys
import os
import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
# Import from app modules
from app.config.settings import (
    SUPABASE_URL,
    SUPABASE_KEY,
    EVINO_BASE_URL,
    MAX_SCROLLS,
    BUTTON_CLICK_DELAY,
    SCROLL_DELAY,
)
from app.core.browser import initialize_browser, close_browser

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


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


def click_button_show_tech_details(driver):
    """
    Clica no botão para mostrar detalhes técnicos completos

    Args:
        driver: Instância do Selenium WebDriver
    """
    time.sleep(SCROLL_DELAY)

    try:
        # Localiza o botão usando Selenium
        button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Ver ficha técnica completa')]"
        )

        if button.is_displayed():
            print("Botão 'Ver ficha técnica completa' encontrado. Clicando...")
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", button)
            print("Clique realizado")
            time.sleep(BUTTON_CLICK_DELAY)
            return True
        else:
            print("Botão encontrado, mas não está visível")
            return False

    except Exception as e:
        print(f"Erro ao tentar clicar no botão: {e}")
        return False


def baixar_imagem(driver, url, product_name):
    import os
    import requests
    from selenium.webdriver.common.by import By
    import time

    dest_path = r"C:/Users/victo/Documents/FIAP/Pos Tech/Módulo 3/Imagens"
    # Criar pasta de destino se não existir
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    caracteres_proibidos = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    caractere_substituto = "_"
    product_name_escaped = re.sub(
        caracteres_proibidos,
        caractere_substituto,
        product_name,
    )

    try:
        # Acessar a URL
        driver.get(url)
        print(f"Página carregada: {url}")

        # Dar tempo para a página carregar
        time.sleep(3)

        # Encontrar elementos picture
        picture_elements = driver.find_elements(By.TAG_NAME, "picture")
        print(f"Encontrados {len(picture_elements)} elementos picture")

        for i, picture in enumerate(picture_elements):
            # Primeiro tenta obter a imagem principal (img)
            try:
                img = picture.find_element(By.TAG_NAME, "img")
                src = img.get_attribute("src")

                if src and src.startswith("//"):
                    src = "https:" + src

                nome_arquivo = f"{id}.jpg"

                caracteres_proibidos = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
                caractere_substituto = "_"
                product_name_escaped = re.sub(
                    caracteres_proibidos,
                    caractere_substituto,
                    product_name,
                )
                nome_arquivo = f"{product_name_escaped}.jpg"
                caminho_completo = os.path.join(dest_path, nome_arquivo)
                if src:
                    resposta = requests.get(src)
                    with open(caminho_completo, "wb") as f:
                        f.write(resposta.content)
                    print(f"Imagem salva como {nome_arquivo}")
                    return src, product_name_escaped
            except Exception as e:
                print(f"Erro ao processar imagem {i+1}: {e}")

    except Exception as e:
        print(f"Erro geral: {e}")
        return None

    finally:
        pass


def scrape_wine_info_with_selenium(driver, url=EVINO_BASE_URL):
    """
    Loads a wine product page with Selenium and extracts detailed information
    while the page is rendered

    Args:
        driver (webdriver.Chrome): Initialized Selenium webdriver
        url (str): URL of the wine product page

    Returns:
        dict: Extracted wine data
    """
    print(f"Navegando para: {url}")

    try:
        # Navigate to the URL
        driver.get(url)

        # Wait for the page to load (adjust selector based on page structure)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "BoxProductInfo__Title"))
        )

        # Additional wait to ensure dynamic content is loaded
        time.sleep(3)

        # Get the page source after JS rendering
        html_content = driver.page_source

        # Adicionando parte de clicks dos botoes de ver mais e mostrar tudo completo
        scroll_page(driver)
        click_button_show_tech_details(driver)

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Initialize dictionary for extracted data
        wine_data = {
            "product_type": None,
            "product_name": None,
            "wine_variety": None,
            "wine_region": None,
            "item_quantity": None,
            "wine_grapes": None,
            "color_description": None,
            "scent_description": None,
            "taste_description": None,
            "harmonizes_with": None,
            "fruit_tasting": None,  # Warning: Reavaliar para kit
            "sugar_tasting": None,  # Warning: Reavaliar para kit
            "acidity_tasting": None,  # Warning: Reavaliar para kit
            "tannin_tasting": None,  # Warning: Reavaliar para kit
            "technical_sheet_wine_type": None,
            "technical_sheet_alcohol_content": None,
            "technical_sheet_volume": None,
            "technical_sheet_grapes": None,
            "technical_sheet_closure_type": None,
            "technical_sheet_service_temperature": None,
            "technical_sheet_country": None,
            "technical_sheet_region": None,
            "technical_sheet_producer": None,
            "technical_sheet_crop_year": None,
            "technical_sheet_cellaring_time": None,
            "technical_sheet_maturation_time": None,
            "created_at": datetime.datetime.now().isoformat(),  # Add timestamp
            "specialist_review_content": None,
            "specialist_review_owner": None,
            "specialist_review_occupation": None,
            "photo_url": None,
        }

        # Extract product type and name
        product_title = soup.find("h1", class_="BoxProductInfo__Title")
        if product_title:
            tag_type = product_title.find(
                "span", class_="BoxProductInfo__Title__Tagline"
            )
            product_name_elem = product_title.find(
                "span", class_="BoxProductInfo__Title__ProductName"
            )

            wine_data["product_type"] = tag_type.text.strip() if tag_type else None
            wine_data["product_name"] = (
                product_name_elem.text.strip() if product_name_elem else None
            )

        # Extract wine type information
        wine_type_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__WineType"
        )
        if wine_type_elem and wine_type_elem.find("span"):
            wine_data["wine_variety"] = wine_type_elem.text.strip()

        # Extract wine region
        wine_region_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__CountryAndRegion--Country"
        )
        if wine_region_elem and wine_region_elem.find("div"):
            wine_data["wine_region"] = wine_region_elem.text.strip()

        # Extract item quantity
        wine_quantity_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__QuantityInBundle"
        )
        if wine_quantity_elem and wine_quantity_elem.find("span"):
            wine_data["item_quantity"] = wine_quantity_elem.text.strip()
        else:
            wine_data["item_quantity"] = 1

        # Extract grape types
        wine_grapes_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__Grapes"
        )
        if wine_grapes_elem and wine_grapes_elem.find("span"):
            wine_data["wine_grapes"] = wine_grapes_elem.text.strip()

        # Extract wine color description
        if soup and soup.find("p", id="visualColor"):
            wine_data["color_description"] = soup.find(id="visualColor").text

        # Extract wine scent description
        if soup and soup.find(id="aroma"):
            wine_data["scent_description"] = soup.find(id="aroma").text

        # Extract wine taste description
        if soup and soup.find(id="mouth"):
            wine_data["taste_description"] = soup.find(id="mouth").text

        # Extract wine harmonization information
        wine_harmonizes_with_elem = soup.find(
            "div",
            class_="HowToTaste__DetailsContainer HowToTaste__DetailsContainer__Tablet",
        )
        if wine_harmonizes_with_elem and wine_harmonizes_with_elem.find(
            "p", id="pairingsTablet"
        ):
            wine_data["harmonizes_with"] = wine_harmonizes_with_elem.find(
                "p", id="pairingsTablet"
            ).text.strip()

        # Extract wine strength data (previously missing function)
        try:
            wine_data["fruit_tasting"] = get_strength_level(driver, "Fruta")
            wine_data["sugar_tasting"] = get_strength_level(driver, "Açúcar")
            wine_data["acidity_tasting"] = get_strength_level(driver, "Acidez")
            wine_data["tannin_tasting"] = get_strength_level(driver, "Tanino")

        except Exception as e:
            print(f"Erro ao extrair dados de força do vinho: {str(e)}")

        # Extract technical specifications
        try:
            wine_specs_elem = soup.find_all(
                "div",
                class_="ProductSpecifications__DetailsContainer",
            )
            specs = {}

            for wine_spec in wine_specs_elem:
                spec_title = wine_spec.find("h4", class_="sc-jlZhew")
                spec_value = wine_spec.find("p", class_="sc-jXbUNg")

                if spec_title and spec_value:
                    spec_title = spec_title.text.strip()
                    spec_value = spec_value.text.strip()
                    specs[spec_title] = spec_value

            # Map specifications to wine_data fields
            if specs:
                field_mapping = {
                    "Tipo de vinho": "technical_sheet_wine_type",
                    "Teor alcoólico": "technical_sheet_alcohol_content",
                    "Volume": "technical_sheet_volume",
                    "Uvas": "technical_sheet_grapes",
                    "Tipo de fechamento": "technical_sheet_closure_type",
                    "Temperatura de serviço": "technical_sheet_service_temperature",
                    "País": "technical_sheet_country",
                    "Região": "technical_sheet_region",
                    "Produtor": "technical_sheet_producer",
                    "Safra": "technical_sheet_crop_year",
                    "Tempo de guarda": "technical_sheet_cellaring_time",
                    "Maturação": "technical_sheet_maturation_time",
                }

                for spec_key, data_key in field_mapping.items():
                    if spec_key in specs:
                        wine_data[data_key] = specs[spec_key]

            # Extract Specialist Content
            try:
                ...
                specialist_content_elem = soup.find(
                    "div", class_="SpecialistOpinion__Container"
                )

                # Extracting specialist name
                specialist_name_and_occupation = specialist_content_elem.find(
                    "div",
                    class_="SpecialistOpinion__SommelierContainer__SommelierInfos",
                )
                if specialist_content_elem and specialist_name_and_occupation:
                    wine_data["specialist_review_owner"] = (
                        specialist_name_and_occupation.find(
                            "h4", class_="sc-jlZhew bMxkvj"
                        ).text
                    )
                # Extracting specialist occupation
                if specialist_content_elem and specialist_name_and_occupation:
                    wine_data["specialist_review_occupation"] = (
                        specialist_name_and_occupation.find(
                            "p", class_="sc-jXbUNg ejYBXU"
                        ).text
                    )

                # Extracting review content  SpecialistOpinion__ReviewContainer ReviewBorderBottom
                specialist_review_content_elem = specialist_content_elem.find(
                    "div",
                    class_="SpecialistOpinion__ReviewContainer ReviewBorderBottom",
                )
                specialist_review_content = specialist_review_content_elem.find(
                    "p", class_="sc-jXbUNg ejYBXU"
                ).text
                if specialist_review_content_elem and specialist_review_content:
                    wine_data["specialist_review_content"] = specialist_review_content

                baixar_imagem(driver, url, wine_data["product_name"])

            finally:
                pass

        except Exception as e:
            print(f"Erro ao extrair especificações técnicas: {str(e)}")

        return wine_data

    except Exception as e:
        print(f"Erro ao processar página {url}: {str(e)}")
        return None


def get_strength_level(driver, category_label):
    # Encontra o wrapper da categoria específica (Fruta, Acidez, etc.)
    wrapper_elements = driver.find_elements(
        By.CLASS_NAME, "HowToTaste__DetailsContainer__ProgressBarContainer__Wrapper"
    )

    for wrapper in wrapper_elements:
        try:
            label = wrapper.find_element(By.TAG_NAME, "p").text.strip()
            if label.lower() == category_label.lower():
                spans = wrapper.find_elements(By.CSS_SELECTOR, "span")

                for i, span in enumerate(spans, start=1):
                    # Verifica se o ::after está visível via JS
                    has_after = driver.execute_script(
                        """
                        const el = arguments[0];
                        const after = window.getComputedStyle(el, '::after');
                        return after && after.getPropertyValue('content') !== 'none';
                    """,
                        span,
                    )

                    if has_after:
                        return i  # O índice (1 a 5) indica o nível
        except Exception as e:
            print(f"Erro ao processar categoria {category_label}: {e}")

    return None  # Se não encontrou


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
        print(f"Erro ao buscar URLs: {str(e)}")
        return []


def process_and_upsert_wine_data(driver, urls):
    """
    Processes URLs and upserts the extracted data to the wine_data table

    Args:
        driver (webdriver.Chrome): Initialized Selenium webdriver
        urls (list): List of URL tuples (id, url) to process

    Returns:
        int: Number of successfully processed URLs
    """
    processed_count = 0

    for url_id, url in urls:
        try:
            wine_data = scrape_wine_info_with_selenium(driver, url)

            if wine_data:
                wine_data["id"] = url_id
                result = supabase.table("wine_data").upsert(wine_data).execute()
                update_scraped = (
                    supabase.table("scrape_db")
                    .update({"scraped": 1})
                    .eq("id", url_id)
                    .execute()
                )

                if result.data and update_scraped.data:
                    print(
                        f"Dados do vinho de ID {url_id} inseridos/atualizados com sucesso"
                    )
                    processed_count += 1

                else:
                    print(f"Falha ao inserir/atualizar dados do vinho de ID {url_id}")

            time.sleep(2)

        except Exception as e:
            print(f"Erro ao processar URL {url}: {str(e)}")

    return processed_count


def run_extraction(batch_size=10, max_batches=None):
    """
    Runs the wine data extraction process

    Args:
        batch_size (int): Number of URLs to process in each batch
        max_batches (int, optional): Maximum number of batches to process
    """
    print("Iniciando extração de dados de vinhos...")

    # Initialize browser
    driver = initialize_browser()

    if not driver:
        print("Falha ao inicializar o navegador. Abortando.")
        return

    try:
        batch_count = 0
        total_processed = 0

        while True:
            # Get URLs to process
            urls = extract_urls_from_database(batch_size)

            if not urls:
                print("Não há mais URLs para processar.")
                break

            print(f"Processando lote {batch_count + 1} com {len(urls)} URLs...")

            # Process URLs
            processed = process_and_upsert_wine_data(driver, urls)
            total_processed += processed

            batch_count += 1
            print(
                f"Lote {batch_count} concluído. Processados: {processed}. Total: {total_processed}"
            )

            if max_batches and batch_count >= max_batches:
                print(f"Limite de {max_batches} lotes atingido.")
                break

            # Add delay between batches
            time.sleep(1)

    except Exception as e:
        print(f"Erro durante a extração: {str(e)}")

    finally:
        # Clean up
        close_browser(driver)
        print(f"Extração concluída. Total de itens processados: {total_processed}")


if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Extração de dados de vinhos da Evino")
    parser.add_argument(
        "--batch-size", type=int, default=10, help="Número de URLs por lote"
    )
    parser.add_argument(
        "--max-batches", type=int, help="Número máximo de lotes a processar"
    )

    args = parser.parse_args()

    # Run extraction
    run_extraction(batch_size=args.batch_size, max_batches=args.max_batches)
