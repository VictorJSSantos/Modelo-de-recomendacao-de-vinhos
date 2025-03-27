import os
import datetime
import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Configura o sistema de logs.

    Returns:
        logging.Logger: O logger configurado.
    """
    # Cria diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)

    # Configura o logger
    logger = logging.getLogger("evino_scraper")
    logger.setLevel(logging.INFO)

    # Formato do log
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        "logs/evino_scraper.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setFormatter(formatter)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Adiciona os handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_user_input(prompt, valid_options=None, default=None):
    """
    Obtém entrada do usuário com validação.

    Args:
        prompt (str): Mensagem para o usuário.
        valid_options (list, optional): Lista de opções válidas.
        default (any, optional): Valor padrão caso o usuário não forneça entrada.

    Returns:
        str: Entrada do usuário validada.
    """
    while True:
        user_input = input(prompt)

        # Se a entrada for vazia e houver um valor padrão
        if not user_input and default is not None:
            return default

        # Se houver opções válidas definidas
        if valid_options:
            if user_input.lower() in valid_options:
                return user_input.lower()
            else:
                options_str = ", ".join(valid_options)
                print(f"Entrada inválida. Por favor, escolha entre: {options_str}")
        else:
            return user_input


def get_integer_input(prompt, min_value=None, max_value=None, default=None):
    """
    Obtém entrada do usuário como um número inteiro com validação.

    Args:
        prompt (str): Mensagem para o usuário.
        min_value (int, optional): Valor mínimo aceitável.
        max_value (int, optional): Valor máximo aceitável.
        default (int, optional): Valor padrão caso o usuário não forneça entrada.

    Returns:
        int: Número inteiro validado.
    """
    while True:
        user_input = input(prompt)

        # Se a entrada for vazia e houver um valor padrão
        if not user_input and default is not None:
            return default

        try:
            value = int(user_input)

            # Verifica limite mínimo
            if min_value is not None and value < min_value:
                print(f"O valor deve ser pelo menos {min_value}.")
                continue

            # Verifica limite máximo
            if max_value is not None and value > max_value:
                print(f"O valor deve ser no máximo {max_value}.")
                continue

            return value

        except ValueError:
            print("Por favor, digite um número inteiro válido.")


def format_time(seconds):
    """
    Formata tempo em segundos para um formato legível.

    Args:
        seconds (int): Tempo em segundos.

    Returns:
        str: Tempo formatado.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"
