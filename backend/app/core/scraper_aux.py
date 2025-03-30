import os
import requests
import re
import sys
from selenium.webdriver.common.by import By
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.config.settings import (
    MAX_SCROLLS,
    SCROLL_DELAY,
    BUTTON_CLICK_DELAY,
)


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


def escape_caractere_product_name(product_name):
    if product_name:
        caracteres_proibidos = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        caractere_substituto = "_"
        pattern = "[" + re.escape("".join(caracteres_proibidos)) + "]"
        product_name_escaped = re.sub(
            pattern,
            caractere_substituto,
            product_name,
        )
        return product_name_escaped

    return None


def baixar_imagem(driver, url, product_name):
    dest_path = r"C:\Users\tatia\OneDrive\Documentos\Cursos\FIAP\POS - Eng ML\Arquitetura ML e Aprendizado\Projeto\Imagens"
    # Criar pasta de destino se não existir
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    product_name_escaped = escape_caractere_product_name(
        product_name,
    )

    try:
        driver.get(url)
        print(f"Página carregada: {url}")
        time.sleep(3)

        # Encontrar elementos picture
        picture_elements = driver.find_elements(
            By.CSS_SELECTOR, ".NewProductImage.NewProductImage--loaded"
        )
        print(f"Encontrados {len(picture_elements)} elementos picture")

        for i, picture in enumerate(picture_elements):
            try:
                img = picture.find_element(By.TAG_NAME, "img")
                src = img.get_attribute("src")

                if src and src.startswith("//"):
                    src = "https:" + src + ".jpg"

                nome_arquivo = f"{product_name_escaped}"
                caminho_completo = os.path.join(dest_path, nome_arquivo)
                if src:
                    resposta = requests.get(src)
                    with open(caminho_completo, "wb") as f:
                        f.write(resposta.content)

                    return src, product_name_escaped
            except Exception as e:
                print(f"Erro ao processar imagem {i+1}: {e}")

    except Exception as e:
        print(f"Erro geral: {e}")
        return None

    finally:
        pass


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

    return None
