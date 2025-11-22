import requests
import io
import pdfplumber
import urllib3
import time
import re
import psycopg2
from psycopg2.extras import execute_values

# --- CONFIGURAÇÕES ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
URL_BASE = "https://dadosabertos.camara.leg.br/api/v2"
ANO_BUSCA = 2024

# Configurações do PostgreSQL
DB_CONFIG = {
    'dbname': 'legislativo_2024',
    'user': 'seu_usuario',      # <--- ALTERE PARA SEU USUÁRIO
    'password': 'sua_senha',    # <--- ALTERE PARA SUA SENHA
    'host': 'localhost',
    'port': '5432'
}

# Tipos a monitorar
TIPOS_A_BUSCAR = ['PL', 'PEC', 'MPV']
LIMITE_TOTAL_PROJETOS = 20  # 0 = sem limite


def limpar_texto(texto):
    """Remove pontilhados, espaços duplos e caracteres problemáticos."""
    if not texto:
        return ""
    texto_limpo = re.sub(r'\.{3,}', '', texto)
    texto_limpo = " ".join(texto_limpo.split())
    return texto_limpo.replace('"', "'")


def extrair_artigo_1_pdf(url):
    """Baixa PDF e extrai o início do Artigo 1º."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url, headers=headers, verify=False, timeout=10)
        arquivo = io.BytesIO(resposta.content)
        
        with pdfplumber.open(arquivo) as pdf:
            texto_completo = ""
            for pagina in pdf.pages[:1]:
                txt = pagina.extract_text()
                if txt:
                    texto_completo += txt + "\n"
        
        linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
        for i, linha in enumerate(linhas):
            if "Art. 1" in linha or "Art. 1º" in linha or "Artigo 1" in linha:
                return limpar_texto(" ".join(linhas[i:i+10]))
        
        return "Artigo 1º não localizado."
    except:
        return "Erro no download do PDF."


def conectar_banco():
    """Cria conexão com o PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None


def proposicao_existe(conn, tipo, numero, ano):
    """Verifica se a proposição já existe no banco."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM proposicoes_legislativas WHERE tipo = %s AND numero = %s AND ano = %s",
            (tipo, numero, ano)
        )
        return cur.fetchone() is not None


def inserir_proposicoes(conn, proposicoes):
    """Insere múltiplas proposições no banco (batch insert)."""
    sql = """
        INSERT INTO proposicoes_legislativas 
        (numero, tipo, ano, data_apresentacao, ementa_resumo, artigo_1_trecho, link_pdf)
        VALUES %s
        ON CONFLICT (tipo, numero, ano) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, proposicoes)
        conn.commit()
        return cur.rowcount


def processar_tipo(sigla_tipo):
    """Busca proposições de um tipo e insere no banco."""
    print(f"\n{'='*50}")
    print(f"⏩ PROCESSANDO: {sigla_tipo}")
    print(f"{'='*50}")

    conn = conectar_banco()
    if not conn:
        return

    pagina_atual = 1
    projetos_coletados = 0
    projetos_inseridos = 0

    try:
        while True:
            if LIMITE_TOTAL_PROJETOS > 0 and projetos_coletados >= LIMITE_TOTAL_PROJETOS:
                print(f"🛑 Limite atingido: {LIMITE_TOTAL_PROJETOS} {sigla_tipo}.")
                break

            print(f"  📄 Página {pagina_atual}...", end="")

            try:
                endpoint = f"{URL_BASE}/proposicoes"
                parametros = {
                    'ano': ANO_BUSCA,
                    'siglaTipo': sigla_tipo,
                    'itens': 15,
                    'pagina': pagina_atual,
                    'ordem': 'DESC',
                    'ordenarPor': 'id'
                }

                resp = requests.get(endpoint, params=parametros, verify=False, timeout=30)
                lista_proposicoes = resp.json()['dados']

                if not lista_proposicoes:
                    print(" | Fim dos dados.")
                    break

                print(f" | {len(lista_proposicoes)} itens encontrados.")

                # Prepara lista para batch insert
                batch = []

                for projeto in lista_proposicoes:
                    if LIMITE_TOTAL_PROJETOS > 0 and projetos_coletados >= LIMITE_TOTAL_PROJETOS:
                        break

                    tipo = projeto['siglaTipo']
                    numero = projeto['numero']
                    ano = projeto['ano']

                    # Verifica duplicata
                    if proposicao_existe(conn, tipo, numero, ano):
                        print(f"    ↳ {tipo} {numero}/{ano} já existe. Pulando...")
                        projetos_coletados += 1
                        continue

                    # Busca detalhes
                    try:
                        detalhes = requests.get(
                            f"{URL_BASE}/proposicoes/{projeto['id']}",
                            verify=False,
                            timeout=10
                        ).json()['dados']

                        ementa = limpar_texto(detalhes.get('ementa'))
                        url_pdf = detalhes.get('urlInteiroTeor')
                        data_apresentacao = detalhes.get('dataApresentacao')

                        # Extrai Artigo 1º
                        artigo_1 = "Sem PDF"
                        if url_pdf:
                            artigo_1 = extrair_artigo_1_pdf(url_pdf)

                        # Adiciona ao batch
                        batch.append((
                            numero,
                            tipo,
                            ano,
                            data_apresentacao,
                            ementa,
                            artigo_1,
                            url_pdf
                        ))

                        projetos_coletados += 1

                    except Exception as e:
                        print(f"    ❌ Erro ao processar {tipo} {numero}: {e}")
                        continue

                # Insere batch no banco
                if batch:
                    inseridas = inserir_proposicoes(conn, batch)
                    projetos_inseridos += inseridas
                    print(f"    ✅ Inseridas {inseridas} novas proposições.")

                pagina_atual += 1
                time.sleep(1.5)

            except Exception as e:
                print(f"\n❌ Erro crítico na página {pagina_atual}: {e}")
                time.sleep(5)

    finally:
        conn.close()

    print(f"\n✅ FIM do {sigla_tipo}: {projetos_inseridas}/{projetos_coletadas} novas inseridas.")


def main():
    """Executa o processamento para todos os tipos."""
    print(f"🔍 INICIANDO COLETA PARA {ANO_BUSCA}...")
    print(f"💾 Destino: PostgreSQL ({DB_CONFIG['host']})")

    for tipo in TIPOS_A_BUSCAR:
        processar_tipo(tipo)

    print("\n🎉 COLETA FINALIZADA!")


if __name__ == "__main__":
    main()