import time
import datetime
import schedule
from supabase import Client


from backend.app.core.browser import initialize_browser, close_browser
from backend.app.database.supabase_client import (
    check_pending_products,
    extract_urls_from_database,
    process_and_upsert_wine_data,
)
from backend.app.core.scraper_aux import *


def schedule_download_tasks(
    supabase: Client, interval_minutes=30, batch_size=10, max_batches=None
):
    """
    Agenda e executa tarefas de download de produtos.

    Args:
        supabase (Client): Cliente do Supabase.
        interval_minutes (int): Intervalo entre downloads em minutos.
        batch_size (int): Quantidade de produtos a baixar por vez.
    """
    print(
        f"Agendando downloads a cada {interval_minutes} minutos, {batch_size} produtos por vez num total de {max_batches}"
    )

    # Função para executar o download com o batch_size definido
    def scheduled_download():
        run_extraction(supabase, batch_size)

    # Agenda o download para executar a cada X minutos
    schedule.every(interval_minutes).minutes.do(scheduled_download)

    # Executa também imediatamente após a configuração
    scheduled_download()

    # Loop principal para manter o programa rodando
    run_scheduler_loop(supabase)


def run_scheduler_loop(supabase: Client):
    """
    Executa o loop principal do agendador, verificando e executando tarefas agendadas.

    Args:
        supabase (Client): Cliente do Supabase.
    """
    while True:
        try:
            # Verifica se há tarefas agendadas para executar
            schedule.run_pending()
            time.sleep(60)  # Pausa por 60 segundos antes de verificar novamente

            # Verifica se todos os produtos foram baixados
            pending = check_pending_products(supabase)

            if pending == 0:
                print(
                    f"{datetime.datetime.now()}: Todos os produtos foram baixados. Encerrando o programa."
                )
                break

        except KeyboardInterrupt:
            print("Programa interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            time.sleep(60)  # Continua mesmo com erros


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
