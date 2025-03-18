import sqlite3
import os
from supabase import create_client
from dotenv import load_dotenv
import time

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# Inicializar o cliente Supabase
supabase = create_client(supabase_url, supabase_key)

# Conectar ao banco de dados SQLite
sqlite_conn = sqlite3.connect("data/evino_products.db")
sqlite_conn.row_factory = sqlite3.Row
cursor = sqlite_conn.cursor()

print("Iniciando transferência de dados do SQLite para o Supabase...")

# Buscar todos os URLs do Supabase
print("Buscando URLs existentes no Supabase...")
supabase_urls_response = supabase.table("scrape_db").select("url").execute()
supabase_urls = {record["url"] for record in supabase_urls_response.data}
print(f"Encontrados {len(supabase_urls)} URLs no Supabase.")

# Buscar todos os URLs do SQLite
print("Buscando URLs do SQLite...")
cursor.execute("SELECT url FROM products")
sqlite_urls = {row["url"] for row in cursor.fetchall()}
print(f"Encontrados {len(sqlite_urls)} URLs no SQLite.")

# Encontrar URLs que existem apenas no SQLite (novos)
new_urls = sqlite_urls - supabase_urls
print(f"Encontrados {len(new_urls)} novos URLs para transferir.")

if not new_urls:
    print("Não há novos registros para transferir.")
    sqlite_conn.close()
    exit(0)

# Buscar apenas os registros que precisam ser transferidos
placeholders = ",".join(["?"] * len(new_urls))
query = f"SELECT id, url, html_downloaded, html_content, created_at, downloaded_at FROM products WHERE url IN ({placeholders})"
cursor.execute(query, list(new_urls))
new_records = cursor.fetchall()

# Transferir apenas os novos registros
total = len(new_records)
inserted = 0
errors = 0

for i, row in enumerate(new_records):
    record = dict(row)
    url = record.get("url")

    try:
        # Remover o campo 'id'
        record.pop("id")

        # Verificações de dados
        if record["html_content"] and len(str(record["html_content"])) > 1000000:
            record["html_content"] = record["html_content"][:1000000]
            print(f"Aviso: HTML truncado para {url}")

        # Verificar valores nulos onde não são permitidos
        for field in ["url", "html_downloaded"]:
            if record[field] is None:
                record[field] = "" if field == "url" else 0

        # Inserir no Supabase
        response = supabase.table("scrape_db").insert(record).execute()
        inserted += 1
        print(f"[{i+1}/{total}] Inserido: {url}")

    except Exception as e:
        errors += 1
        print(f"[{i+1}/{total}] Erro ao inserir {url}: {str(e)}")

        # Se quiser ver detalhes completos do erro
        import traceback

        print(traceback.format_exc())

    # Mostrar progresso a cada 50 registros
    if (i + 1) % 50 == 0:
        print(f"Progresso: {i+1}/{total} ({(i+1)/total*100:.1f}%)")

    time.sleep(0.1)  # Evitar limitações de taxa

# Fechar a conexão com o SQLite
sqlite_conn.close()

print(
    f"""
Transferência concluída!
- Registros novos encontrados: {total}
- Inseridos com sucesso: {inserted}s
- Erros: {errors}
"""
)
