import datetime
from supabase import create_client, Client


from app.config.settings import SUPABASE_URL, SUPABASE_KEY


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
            "html_downloaded": 0,
            "created_at": datetime.datetime.now().isoformat(),
        }
        result = supabase.table("scrape_db").insert(data).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Erro ao inserir URL {url}: {e}")
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


def get_pending_products(supabase: Client, limit: int) -> list:
    """
    Retorna produtos pendentes para download.

    Args:
        supabase (Client): Cliente do Supabase.
        limit (int): Número máximo de produtos a retornar.

    Returns:
        list: Lista de produtos pendentes.
    """
    result = (
        supabase.table("scrape_db")
        .select("id", "url")
        .eq("html_downloaded", 0)
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
        print(f"Erro ao atualizar produto {product_id}: {e}")
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
    result = supabase.table("scrape_db").select("id").eq("html_downloaded", 0).execute()
    return len(result.data)
