import sqlite3
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import datetime
import schedule


# Configuração do banco de dados
def setup_database():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/evino_products.db")
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        html_downloaded INTEGER DEFAULT 0,
        html_content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        downloaded_at TIMESTAMP
    )
    """
    )

    conn.commit()
    print("Banco de dados configurado com sucesso")
    return conn, cursor


# Inicialização do navegador
def initialize_browser():
    print("Inicializando o navegador...")
    try:
        options = Options()

        # Configurações essenciais
        options.add_argument("--headless=new")  # Novo formato do headless mode
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Configurações para estabilidade
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        # Identidade do navegador
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Ignorar erros de certificado
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-insecure-localhost")

        # Reduzir logs
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Configurações para performance
        options.page_load_strategy = (
            "eager"  # Não espera imagens carregarem completamente
        )

        # Inicializa o navegador
        driver = webdriver.Chrome(options=options)

        # Configura timeouts
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)

        print("Navegador inicializado com sucesso")
        return driver

    except WebDriverException as e:
        print(f"Erro ao inicializar o navegador: {e}")
        return None


# Função para extrair links de produtos
def scrape_product_links(driver, conn, cursor):
    if not driver:
        print("Erro: O navegador não foi inicializado corretamente")
        return

    try:
        print("Acessando página de vinhos...")
        driver.get("https://www.evino.com.br/vinhos")
        print("Página carregada")

        time.sleep(5)

        last_height = driver.execute_script("return document.body.scrollHeight")

        print("Rolando a página para carregar produtos...")
        max_scrolls = 15
        for scroll in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            try:
                buttons = driver.find_elements(
                    By.XPATH,
                    "//button[contains(text(), 'Mostrar mais') or contains(text(), 'Carregar mais')]",
                )
                if buttons:
                    for button in buttons:
                        if button.is_displayed():
                            print(
                                "Botão 'Mostrar mais produtos' encontrado. Clicando..."
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView(true);", button
                            )
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", button)
                            print("Clique realizado")
                            time.sleep(3)
            except Exception as e:
                print(f"Erro ao tentar clicar no botão: {e}")

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"Fim da página alcançado após {scroll+1} scrolls")
                break
            last_height = new_height

            print(f"Scroll {scroll+1}/{max_scrolls} concluído")

        print("Extraindo links de produtos...")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/product/" in href:
                links.append(href)

        unique_links = list(set(links))
        print(f"Total de links únicos encontrsados: {len(unique_links)}")

        base_url = "https://www.evino.com.br"
        count = 0

        for link in unique_links:
            if link.startswith("/"):
                full_url = base_url + link
            else:
                full_url = link

            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO products (url) VALUES (?)", (full_url,)
                )
                if cursor.rowcount > 0:
                    count += 1
            except sqlite3.Error as e:
                print(f"Erro ao salvar link {full_url}: {e}")

        conn.commit()
        print(f"{count} novos links salvos no banco de dados")

    except Exception as e:
        print(f"Erro durante a extração de links: {e}")


# Função para baixar o HTML das páginas de produtos
def download_product_html(batch_size=10):
    try:
        # Criamos uma nova conexão para cada execução
        conn = sqlite3.connect("data/evino_products.db")
        cursor = conn.cursor()

        # Verifica se há produtos pendentes
        cursor.execute("SELECT COUNT(*) FROM products WHERE html_downloaded = 0")
        pending_count = cursor.fetchone()[0]

        if pending_count == 0:
            print(
                f"{datetime.datetime.now()}: Não há produtos pendentes para download."
            )
            conn.close()
            return

        # Busca produtos pendentes
        cursor.execute(
            "SELECT id, url FROM products WHERE html_downloaded = 0 LIMIT ?",
            (batch_size,),
        )
        products = cursor.fetchall()

        print(
            f"{datetime.datetime.now()}: Baixando HTML de {len(products)} produtos (de {pending_count} pendentes)..."
        )

        # Configurações para o request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.evino.com.br/vinhos",
            "Connection": "keep-alive",
        }

        session = requests.Session()

        for product_id, url in products:
            try:
                print(f"Baixando: {url}")
                response = session.get(url, headers=headers, timeout=30)

                if response.status_code == 200:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "UPDATE products SET html_downloaded = 1, html_content = ?, downloaded_at = ? WHERE id = ?",
                        (response.text, now, product_id),
                    )
                    print(f"✓ Produto {product_id} baixado com sucesso")
                else:
                    print(
                        f"✗ Falha ao baixar produto {product_id}. Status code: {response.status_code}"
                    )

                time.sleep(2)  # Pausa entre downloads

            except Exception as e:
                print(f"✗ Erro ao baixar {url}: {str(e)}")

        conn.commit()

        # Atualiza estatísticas
        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products WHERE html_downloaded = 1")
        downloaded = cursor.fetchone()[0]

        print(f"\nEstatísticas - {datetime.datetime.now()}:")
        print(f"Total de produtos: {total}")
        print(f"Produtos baixados: {downloaded}")
        print(f"Produtos pendentes: {total - downloaded}")

        conn.close()

    except Exception as e:
        print(f"Erro ao baixar produtos: {e}")
        if "conn" in locals() and conn:
            conn.close()


# Função para executar a extração inicial
def initial_extraction():
    conn, cursor = setup_database()
    driver = initialize_browser()

    if driver:
        try:
            scrape_product_links(driver, conn, cursor)
            driver.quit()
            print("Navegador fechado")
        except Exception as e:
            print(f"Erro durante a extração inicial: {e}")
            try:
                driver.quit()
            except:
                pass

    conn.close()

    # Primeira execução do download
    download_product_html(batch_size=10)


# Agenda as tarefas
def schedule_tasks(interval_minutes=30, batch_size=10):
    print(
        f"Agendando downloads a cada {interval_minutes} minutos, {batch_size} produtos por vez"
    )

    # Função para executar o download com o batch_size definido
    def scheduled_download():
        download_product_html(batch_size)

    # Agenda o download para executar a cada X minutos
    schedule.every(interval_minutes).minutes.do(scheduled_download)

    # Executa também imediatamente após a configuração
    scheduled_download()

    # Loop principal para manter o programa rodando
    while True:
        try:
            # Verifica se há tarefas agendadas para executar
            schedule.run_pending()
            time.sleep(60)  # Pausa por 60 segundos antes de verificar novamente

            # Verifica se todos os produtos foram baixados
            conn = sqlite3.connect("data/evino_products.db")
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM products WHERE html_downloaded = 0")
            pending = cursor.fetchone()[0]

            if pending == 0:
                print(
                    f"{datetime.datetime.now()}: Todos os produtos foram baixados. Encerrando o programa."
                )
                conn.close()
                break

            conn.close()

        except KeyboardInterrupt:
            print("Programa interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            time.sleep(60)  # Continua mesmo com erros


# Função principal
def main():
    print("===== Iniciando extrator de produtos da Evino =====")
    print(f"Data/Hora: {datetime.datetime.now()}")

    # Pergunta se deve executar a extração inicial
    while True:
        should_extract = input(
            "Deseja executar a extração inicial de links? (s/n): "
        ).lower()
        if should_extract in ["s", "n"]:
            break
        print("Por favor, responda com 's' para sim ou 'n' para não.")

    if should_extract == "s":
        initial_extraction()

    # Configura o intervalo e o tamanho do lote
    try:
        interval = int(
            input(
                "Digite o intervalo em minutos entre os downloads (recomendado: 30): "
            )
        )
        batch = int(input("Digite quantos produtos baixar por vez (recomendado: 10): "))
    except ValueError:
        print(
            "Valor inválido. Usando valores padrão: 30 minutos e 10 produtos por vez."
        )
        interval = 30
        batch = 10

    # Inicia o agendador
    print("\nIniciando agendador de downloads...")
    schedule_tasks(interval_minutes=interval, batch_size=batch)


if __name__ == "__main__":
    main()
