import time
import datetime
import requests
from supabase import Client


from app.config.settings import BROWSER_USER_AGENT, DOWNLOAD_DELAY
from app.database.supabase_client import (
    get_pending_products,
    update_product_html,
    get_statistics,
)


def download_product_html(supabase: Client, batch_size=10):
    """
    Baixa o HTML das páginas de produtos pendentes.

    Args:
        supabase (Client): Cliente do Supabase.
        batch_size (int): Quantidade de produtos a baixar por vez.

    Returns:
        int: Número de produtos baixados com sucesso.
    """
    try:
        # Obtém produtos pendentes
        products = get_pending_products(supabase, batch_size)

        if not products:
            print(
                f"{datetime.datetime.now()}: Não há produtos pendentes para download."
            )
            return 0

        print(
            f"{datetime.datetime.now()}: Baixando HTML de {len(products)} produtos..."
        )

        session = requests.Session()
        session.headers.update(get_request_headers())

        success_count = 0

        for product in products:
            product_id = product["id"]
            url = product["url"]

            if download_single_product(session, supabase, product_id, url):
                success_count += 1

            time.sleep(DOWNLOAD_DELAY)  # Pausa entre downloads

        # Mostra estatísticas
        stats = get_statistics(supabase)
        print(f"\nEstatísticas - {datetime.datetime.now()}:")
        print(f"Total de produtos: {stats['total']}")
        print(f"Produtos baixados: {stats['downloaded']}")
        print(f"Produtos pendentes: {stats['pending']}")

        return success_count

    except Exception as e:
        print(f"Erro ao baixar produtos: {e}")
        return 0


def download_single_product(session, supabase, product_id, url):
    """
    Baixa o HTML de um único produto.

    Args:
        session (requests.Session): Sessão HTTP para fazer requisições.
        supabase (Client): Cliente do Supabase.
        product_id (int): ID do produto.
        url (str): URL do produto.

    Returns:
        bool: True se o download foi bem-sucedido, False caso contrário.
    """
    try:
        print(f"Baixando: {url}")
        response = session.get(url, timeout=30)

        if response.status_code == 200:
            # Atualiza o registro no Supabase
            if update_product_html(supabase, product_id, response.text):
                print(f"✓ Produto {product_id} baixado com sucesso")
                return True
            else:
                print(f"✗ Falha ao atualizar produto {product_id} no Supabase")
                return False
        else:
            print(
                f"✗ Falha ao baixar produto {product_id}. Status code: {response.status_code}"
            )
            return False

    except Exception as e:
        print(f"✗ Erro ao baixar {url}: {str(e)}")
        return False


def get_request_headers():
    """
    Retorna os cabeçalhos para as requisições HTTP.

    Returns:
        dict: Cabeçalhos para as requisições.
    """
    return {
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.evino.com.br/vinhos",
        "Connection": "keep-alive",
    }
