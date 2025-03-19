import time
import datetime
import schedule
from supabase import Client


from app.core.downloader import download_product_html
from app.database.supabase_client import check_pending_products


def schedule_download_tasks(supabase: Client, interval_minutes=30, batch_size=10):
    """
    Agenda e executa tarefas de download de produtos.

    Args:
        supabase (Client): Cliente do Supabase.
        interval_minutes (int): Intervalo entre downloads em minutos.
        batch_size (int): Quantidade de produtos a baixar por vez.
    """
    print(
        f"Agendando downloads a cada {interval_minutes} minutos, {batch_size} produtos por vez"
    )

    # Função para executar o download com o batch_size definido
    def scheduled_download():
        download_product_html(supabase, batch_size)

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
