from flask import Flask, request, jsonify
import psycopg
import re
import logging
import time
from datetime import datetime
from psycopg.rows import dict_row

from whatsapp_service import WhatsAppService
from llm_service import LLMService

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar serviços
whatsapp = WhatsAppService()
llm_service = LLMService()

def get_db_connection():
    return psycopg.connect(
        host="localhost",
        dbname="legis_ai",
        user="kaua",
        password="ninjask23",
        row_factory=dict_row
    )

# Estado da conversa
user_sessions = {}

class UserSession:
    def __init__(self, telefone):
        self.telefone = telefone
        self.estado = "menu_principal"
        self.dados_temporarios = {}
        self.aguardando_duvida = False
        self.ultima_proposta = None

# Funções auxiliares
def parse_numero_proposicao(proposicao_str):
    """Converte string como 'PL 295/2024' em componentes"""
    match = re.match(r'(\w+)\s+(\d+)/(\d+)', proposicao_str.upper())
    if match:
        return match.group(1), int(match.group(2)), int(match.group(3))
    return None, None, None

def buscar_proposicao_legislativa(proposicao_str):
    conn = get_db_connection()
    
    tipo, numero, ano = parse_numero_proposicao(proposicao_str)
    
    if not tipo or not numero or not ano:
        conn.close()
        return None
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM proposicoes_legislativas 
            WHERE tipo = %s AND numero = %s AND ano = %s
        """, (tipo, numero, ano))
        
        proposicao = cur.fetchone()
    
    conn.close()
    return proposicao

def buscar_politico(nome):
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM politicos WHERE nome ILIKE %s", (f'%{nome}%',))
        politico = cur.fetchone()
        
        if politico:
            # Buscar votações recentes
            cur.execute("""
                SELECT pl.tipo, pl.numero, pl.ano, pl.ementa_resumo, v.voto, v.data_votacao 
                FROM votacoes v 
                JOIN proposicoes_legislativas pl ON v.proposicao_legislativa_id = pl.id 
                WHERE v.politico_id = %s 
                ORDER BY v.data_votacao DESC 
                LIMIT 5
            """, (politico['id'],))
            votacoes = cur.fetchall()
            politico['votacoes_recentes'] = votacoes
    
    conn.close()
    return politico

def criar_usuario(telefone):
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO usuarios (telefone, temas_interesse, politicos_favoritos) VALUES (%s, %s, %s)",
            (telefone, [], [])
        )
    
    conn.commit()
    conn.close()

def gerar_resumo_simples(proposicao):
    """Gera um resumo simples baseado na ementa"""
    ementa = proposicao['ementa_resumo'] or ''
    
    # Simplificação básica
    resumo = ementa.replace("Altera o", "Muda o")
    resumo = resumo.replace(" para prever", " para criar regras sobre")
    resumo = resumo.replace("Dispõe sobre", "Regulamenta")
    resumo = resumo.replace("Institui", "Cria")
    resumo = resumo.replace("Acrescenta", "Adiciona")
    
    if len(resumo) > 200:
        resumo = resumo[:197] + "..."
        
    return resumo

def identificar_temas(proposicao):
    """Identifica temas baseado no conteúdo da ementa"""
    ementa = (proposicao['ementa_resumo'] or '').lower()
    temas = []
    
    temas_keywords = {
        'Saúde': ['saúde', 'médico', 'hospital', 'medicamento', 'doença', 'enfermagem'],
        'Educação': ['educação', 'escola', 'professor', 'ensino', 'universidade', 'aluno'],
        'Segurança': ['segurança', 'polícia', 'crime', 'penal', 'violência', 'criminal'],
        'Impostos': ['imposto', 'tributo', 'taxa', 'fiscal', 'receita', 'isenção'],
        'Meio Ambiente': ['meio ambiente', 'ambiental', 'floresta', 'natureza', 'clima', 'sustentável'],
        'Transporte': ['transporte', 'trânsito', 'rodovia', 'veículo', 'mobilidade', 'táxi'],
        'Trabalho': ['trabalho', 'emprego', 'salário', 'funcionário', 'CLT', 'empregado'],
        'Tecnologia': ['tecnologia', 'digital', 'internet', 'dados', 'inovação', 'inteligência artificial'],
        'Cultura': ['cultura', 'folclórico', 'dança', 'artístico', 'patrimônio'],
        'Turismo': ['turismo', 'turístico', 'rota', 'viagem']
    }
    
    for tema, keywords in temas_keywords.items():
        if any(keyword in ementa for keyword in keywords):
            temas.append(tema)
    
    return temas if temas else ['Geral']

# Handlers dos fluxos
def handle_menu_principal(telefone, mensagem):
    session = user_sessions[telefone]
    session.aguardando_duvida = False
    
    if mensagem == '1':
        session.estado = "aguardando_proposicao"
        return "🔎 Qual proposta legislativa você quer entender?\n\nDigite o número (ex: PL 295/2024, PEC 18/2024, MPV 1286/2024)."
    
    elif mensagem == '2':
        session.estado = "aguardando_politico"
        return "📌 Digite o nome do político (ex: 'Carlos Silva', 'Maria Santos')."
    
    elif mensagem == '3':
        session.estado = "aguardando_temas"
        return """📣 Escolha os temas que deseja acompanhar:

Digite os números separados por vírgula:
1️⃣ Saúde  
2️⃣ Educação  
3️⃣ Segurança  
4️⃣ Impostos  
5️⃣ Meio Ambiente  
6️⃣ Transporte  
7️⃣ Trabalho  
8️⃣ Tecnologia"""
    
    elif mensagem == '4':
        return """💡 Para propor um Projeto de Lei:

1. Coletar assinaturas de apoio (1% do eleitorado)
2. Protocolar na Câmara ou Senado  
3. Buscar apoio de um parlamentar
4. Participar de audiências públicas

Digite 'voltar' para o menu principal."""
    
    else:
        return "❌ Opção não reconhecida. Por favor, digite 1, 2, 3 ou 4."

def handle_aguardando_proposicao(telefone, mensagem):
    session = user_sessions[telefone]
    proposicao = buscar_proposicao_legislativa(mensagem)
    
    if not proposicao:
        return "❌ Proposta legislativa não encontrada. Verifique o número e tente novamente.\nEx: PL 295/2024, PEC 18/2024"
    
    session.estado = "detalhes_proposicao"
    session.aguardando_duvida = False
    
    # Armazenar dados completos para o LLM
    session.dados_temporarios['proposicao_atual'] = f"{proposicao['tipo']} {proposicao['numero']}/{proposicao['ano']}"
    session.dados_temporarios['proposicao_id'] = proposicao['id']
    session.dados_temporarios['ementa'] = proposicao['ementa_resumo']
    session.dados_temporarios['artigo_1'] = proposicao['artigo_1_trecho']
    session.dados_temporarios['link'] = proposicao['link_pdf']
    
    # Criar contexto completo para o LLM
    contexto_completo = f"""
    Proposta: {proposicao['tipo']} {proposicao['numero']}/{proposicao['ano']}
    Ementa: {proposicao['ementa_resumo']}
    Artigo 1º: {proposicao['artigo_1_trecho'] or 'Não disponível'}
    Data: {proposicao['data_apresentacao'].strftime('%d/%m/%Y') if proposicao['data_apresentacao'] else 'Não informada'}
    """
    session.ultima_proposta = contexto_completo
    
    # Gerar informações
    resumo_simples = gerar_resumo_simples(proposicao)
    temas = identificar_temas(proposicao)
    data_formatada = proposicao['data_apresentacao'].strftime('%d/%m/%Y') if proposicao['data_apresentacao'] else 'Não informada'
    
    resposta = f"""📘 **{proposicao['tipo']} {proposicao['numero']}/{proposicao['ano']}**

📅 *Data:* {data_formatada}

📝 *Resumo simplificado:*
{resumo_simples}

💡 *O que propõe:*
{proposicao['ementa_resumo']}

🎯 *Temas:* {', '.join(temas)}

🔗 *Link completo:* {proposicao['link_pdf']}

---
🤖 **Assistente IA Disponível**

Agora você pode fazer perguntas específicas sobre esta proposta!

📋 *Opções:*
1️⃣ Ver quem votou  
2️⃣ Ativar alertas  
3️⃣ Nova proposta  
4️⃣ Voltar ao menu  
5️⃣ 🤔 Fazer uma pergunta

*Digite o número ou sua pergunta diretamente:*"""
    
    return resposta

def handle_aguardando_politico(telefone, mensagem):
    session = user_sessions[telefone]
    politico = buscar_politico(mensagem)
    
    if not politico:
        return "❌ Político não encontrado. Tente outro nome ou digite 'voltar' para o menu."
    
    session.estado = "detalhes_politico"
    session.dados_temporarios['politico_atual'] = politico['id']
    
    resposta = f"""🗳️ Atividade Recente — {politico['nome']} 
({politico['partido']} - {politico['estado']})

Votações recentes:
"""
    
    for voto in politico.get('votacoes_recentes', []):
        emoji = "✅" if voto['voto'] == 'SIM' else "❌" if voto['voto'] == 'NÃO' else "➖"
        resposta += f"{emoji} {voto['voto']} no {voto['tipo']} {voto['numero']}/{voto['ano']}\n"
    
    resposta += """
Quer:
1️⃣ Entender uma dessas votações
2️⃣ Favoritar este político
3️⃣ Ver todo histórico
4️⃣ Voltar ao menu"""
    
    return resposta

def handle_aguardando_temas(telefone, mensagem):
    try:
        numeros = [int(x.strip()) for x in mensagem.split(',')]
        temas_map = {
            1: 'Saúde',
            2: 'Educação', 
            3: 'Segurança',
            4: 'Impostos',
            5: 'Meio Ambiente',
            6: 'Transporte',
            7: 'Trabalho',
            8: 'Tecnologia'
        }
        
        temas_escolhidos = [temas_map[num] for num in numeros if num in temas_map]
        
        if not temas_escolhidos:
            return "❌ Nenhum tema válido selecionado. Tente novamente."
        
        # Salvar no banco
        conn = get_db_connection()
        
        with conn.cursor() as cur:
            # Verificar se usuário existe
            cur.execute("SELECT id FROM usuarios WHERE telefone = %s", (telefone,))
            usuario = cur.fetchone()
            
            if not usuario:
                criar_usuario(telefone)
            
            cur.execute(
                "UPDATE usuarios SET temas_interesse = %s WHERE telefone = %s",
                (temas_escolhidos, telefone)
            )
        
        conn.commit()
        conn.close()
        
        user_sessions[telefone].estado = "menu_principal"
        
        return f"""✅ Tudo certo!
Você receberá alertas sobre: {', '.join(temas_escolhidos)}

Quando ocorrer votação, mudança ou avanço de propostas nesses temas, eu te aviso imediatamente.

Digite qualquer coisa para voltar ao menu."""
    
    except ValueError:
        return "❌ Formato inválido. Digite números separados por vírgula (ex: 1, 3, 5)"

def handle_detalhes_proposicao(telefone, mensagem):
    """Handler atualizado para estado detalhes_proposicao com suporte a dúvidas"""
    session = user_sessions[telefone]
    
    # Se estiver aguardando dúvida específica
    if session.aguardando_duvida:
        session.aguardando_duvida = False
        
        if mensagem.lower() in ['voltar', 'cancelar', 'menu', '0']:
            resposta = "✅ Voltando ao menu da proposta."
        else:
            # Enviar mensagem de processamento
            whatsapp.enviar_mensagem(telefone, "🤔 Consultando o Sabiá-7B sobre sua dúvida...")
            
            # Usar Sabiá-7B para responder
            contexto = session.ultima_proposta or session.dados_temporarios.get('ementa', '')
            resposta_llm = llm_service.responder_duvida(mensagem, contexto)
            
            resposta = f"""💡 **Resposta do Assistente Legislativo**

*Sua pergunta:* "{mensagem}"

*Resposta:* {resposta_llm}

---
📋 *O que mais você gostaria de saber?*

• Digite outra pergunta sobre esta proposta
• Ou escolha uma opção:
1️⃣ Ver quem votou  
2️⃣ Receber alertas  
3️⃣ Nova proposta  
4️⃣ Voltar ao menu"""
        
        return resposta
    
    # Comandos normais do menu
    if mensagem == '1':
        # Buscar votações da proposição atual
        proposicao_id = session.dados_temporarios.get('proposicao_id')
        conn = get_db_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.nome, p.partido, p.estado, v.voto 
                FROM votacoes v 
                JOIN politicos p ON v.politico_id = p.id 
                WHERE v.proposicao_legislativa_id = %s
                ORDER BY p.nome
            """, (proposicao_id,))
            
            votacoes = cur.fetchall()
        
        conn.close()
        
        if votacoes:
            resposta = f"🗳️ **Votações na {session.dados_temporarios['proposicao_atual']}**\n\n"
            for voto in votacoes:
                emoji = "✅" if voto['voto'] == 'SIM' else "❌" if voto['voto'] == 'NÃO' else "➖"
                resposta += f"{emoji} {voto['nome']} ({voto['partido']}-{voto['estado']}): {voto['voto']}\n"
        else:
            resposta = "ℹ️ Ainda não há votações registradas para esta proposta."
        
        resposta += "\n\n💬 *Dúvidas?* Digite sua pergunta ou 'voltar'"
    
    elif mensagem == '2':
        # Registrar alerta para esta proposta
        proposicao_id = session.dados_temporarios.get('proposicao_id')
        conn = get_db_connection()
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE telefone = %s", (telefone,))
            usuario = cur.fetchone()
            
            if usuario:
                cur.execute(
                    "INSERT INTO alertas (usuario_id, proposicao_legislativa_id, tipo_alerta) VALUES (%s, %s, %s)",
                    (usuario['id'], proposicao_id, 'acompanhamento_proposicao')
                )
                conn.commit()
                resposta = "🔔 **Alerta ativado!** Você receberá atualizações sobre esta proposta.\n\n💬 *Dúvidas?* Digite sua pergunta ou 'voltar'"
            else:
                resposta = "❌ Erro ao configurar alerta. Tente novamente."
        
        conn.close()
    
    elif mensagem == '3':
        session.estado = "aguardando_proposicao"
        session.aguardando_duvida = False
        resposta = "🔎 Digite o número da nova proposta (ex: PL 295/2024):"
    
    elif mensagem == '4':
        session.estado = "menu_principal"
        session.aguardando_duvida = False
        resposta = "🏛️ Voltando ao menu principal..."
    
    elif mensagem == '5':
        session.aguardando_duvida = True
        resposta = """🤔 **Faça sua pergunta sobre a proposta**

Digite o que você gostaria de saber (exemplos):
• "Como isso afeta os cidadãos?"
• "Quem será beneficiado?"  
• "Há custos envolvidos?"
• "Quando entra em vigor?"

Ou digite 'voltar' para cancelar."""
    
    else:
        # Se não for comando numérico, assumir que é uma pergunta
        session.aguardando_duvida = False
        
        # Enviar mensagem de processamento
        whatsapp.enviar_mensagem(telefone, "🤔 Consultando o Sabiá-7B...")
        
        # Usar Sabiá-7B para responder
        contexto = session.ultima_proposta or session.dados_temporarios.get('ementa', '')
        resposta_llm = llm_service.responder_duvida(mensagem, contexto)
        
        resposta = f"""💡 **Resposta do Assistente Legislativo**

*Sua pergunta:* "{mensagem}"

*Resposta:* {resposta_llm}

---
📋 *Próximos passos:*

1️⃣ Ver votações  
2️⃣ Ativar alertas  
3️⃣ Nova proposta  
4️⃣ Voltar ao menu  
5️⃣ Fazer outra pergunta

Digite o número ou sua próxima pergunta:"""
    
    return resposta

def handle_detalhes_politico(telefone, mensagem):
    session = user_sessions[telefone]
    
    if mensagem == '1':
        # Entender uma votação específica
        session.estado = "aguardando_proposicao"
        return "🔎 Digite o número da proposta que você quer entender (ex: PL 295/2024):"
    
    elif mensagem == '2':
        # Favoritar político
        politico_id = session.dados_temporarios.get('politico_atual')
        conn = get_db_connection()
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE telefone = %s", (telefone,))
            usuario = cur.fetchone()
            
            if usuario:
                cur.execute("SELECT politicos_favoritos FROM usuarios WHERE id = %s", (usuario['id'],))
                favoritos = cur.fetchone()['politicos_favoritos'] or []
                
                if politico_id not in favoritos:
                    favoritos.append(politico_id)
                    cur.execute(
                        "UPDATE usuarios SET politicos_favoritos = %s WHERE id = %s",
                        (favoritos, usuario['id'])
                    )
                    conn.commit()
                    resposta = "⭐ Político adicionado aos favoritos!"
                else:
                    resposta = "⭐ Este político já está nos seus favoritos!"
            else:
                resposta = "❌ Erro ao favoritar político."
        
        conn.close()
    
    elif mensagem == '3':
        # Ver histórico completo
        resposta = "📊 Funcionalidade de histórico completo em desenvolvimento...\n\nDigite 'voltar' para o menu."
    
    elif mensagem == '4':
        session.estado = "menu_principal"
        resposta = handle_menu_principal(telefone, '')
    
    else:
        resposta = "❌ Opção não reconhecida. Digite 1, 2, 3 ou 4."
    
    return resposta

# Rota principal do webhook
@app.route('/webhook/whatsapp', methods=['POST'])
def webhook_whatsapp():
    data = request.get_json()
    
    # Simulação - adaptar para provedor WhatsApp real
    telefone = data.get('from', '5511999999999')
    mensagem = data.get('body', '').strip()
    
    logger.info(f"📨 Mensagem de {telefone}: {mensagem}")
    
    # Inicializar sessão se não existir
    if telefone not in user_sessions:
        user_sessions[telefone] = UserSession(telefone)
        resposta = """🏛️ Zap da Cidadania 

Olá! Eu te ajudo a entender projetos de lei, votações e acompanhar tudo isso de um jeito simples.

*Novo!* 🤖 Agora com Assistente IA para responder suas dúvidas!

O que você quer fazer hoje?

1️⃣ Entender uma Proposta Legislativa
2️⃣ Ver como os políticos votaram  
3️⃣ Ativar alertas personalizados
4️⃣ Aprender como propor um Projeto de Lei

Digite apenas o número da opção."""
        
        whatsapp.enviar_mensagem(telefone, resposta)
        return jsonify({'status': 'welcome_sent'})
    
    session = user_sessions[telefone]
    
    # Verificar se é comando de voltar
    if mensagem.lower() in ['voltar', 'menu', '0', 'cancelar']:
        session.estado = "menu_principal"
        session.aguardando_duvida = False
        resposta = "🏛️ Voltando ao menu principal...\n\n1️⃣ Entender proposta\n2️⃣ Ver votações\n3️⃣ Alertas\n4️⃣ Como propor lei"
        whatsapp.enviar_mensagem(telefone, resposta)
        return jsonify({'status': 'back_to_menu'})
    
    # Roteamento por estado
    if session.estado == "menu_principal":
        resposta = handle_menu_principal(telefone, mensagem)
    
    elif session.estado == "aguardando_proposicao":
        resposta = handle_aguardando_proposicao(telefone, mensagem)
    
    elif session.estado == "aguardando_politico":
        resposta = handle_aguardando_politico(telefone, mensagem)
    
    elif session.estado == "aguardando_temas":
        resposta = handle_aguardando_temas(telefone, mensagem)
    
    elif session.estado == "detalhes_proposicao":
        resposta = handle_detalhes_proposicao(telefone, mensagem)
    
    elif session.estado == "detalhes_politico":
        resposta = handle_detalhes_politico(telefone, mensagem)
    
    else:
        session.estado = "menu_principal"
        resposta = handle_menu_principal(telefone, '')
    
    # Enviar resposta via WhatsApp
    whatsapp.enviar_mensagem(telefone, resposta)
    
    return jsonify({'status': 'processed'})

# Rota para enviar alertas
@app.route('/alertas/enviar', methods=['POST'])
def enviar_alertas():
    data = request.get_json()
    proposicao_legislativa_id = data.get('proposicao_legislativa_id')
    tipo_alerta = data.get('tipo_alerta')
    
    conn = get_db_connection()
    
    with conn.cursor() as cur:
        # Buscar proposta
        cur.execute("SELECT * FROM proposicoes_legislativas WHERE id = %s", (proposicao_legislativa_id,))
        proposicao = cur.fetchone()
        
        if not proposicao:
            return jsonify({'error': 'Proposta não encontrada'}), 404
        
        # Identificar temas da proposta
        temas = identificar_temas(proposicao)
        
        # Buscar usuários interessados nos temas
        cur.execute("""
            SELECT telefone FROM usuarios 
            WHERE temas_interesse && %s
        """, (temas,))
        
        usuarios = cur.fetchall()
        
        alertas_enviados = []
        for usuario in usuarios:
            mensagem = f"""🚨 Alerta Importante!

{proposicao['tipo']} {proposicao['numero']}/{proposicao['ano']}
Status: {tipo_alerta}

{proposicao['ementa_resumo']}

Digite '{proposicao['tipo']} {proposicao['numero']}/{proposicao['ano']}' para entender melhor."""
            
            # Aqui integraria com API do WhatsApp
            alertas_enviados.append(usuario['telefone'])
            
            # Registrar alerta
            cur.execute(
                "INSERT INTO alertas (usuario_id, proposicao_legislativa_id, tipo_alerta) VALUES ((SELECT id FROM usuarios WHERE telefone = %s), %s, %s)",
                (usuario['telefone'], proposicao_legislativa_id, tipo_alerta)
            )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'enviado_para': alertas_enviados,
        'total': len(alertas_enviados)
    })

# Rota de saúde da API
@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        
        llm_status = "loaded" if llm_service.inicializado else "not_loaded"
        
        return jsonify({
            'status': 'healthy', 
            'database': 'connected',
            'llm_service': llm_status,
            'whatsapp_service': 'ready'
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Rota para estatísticas
@app.route('/stats', methods=['GET'])
def get_stats():
    stats = {
        'sessions_ativas': len(user_sessions),
        'llm_carregado': llm_service.inicializado,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(stats)

if __name__ == '__main__':
    logger.info("🚀 Iniciando Zap da Cidadania com Sabiá-7B...")
    logger.info(f"🤖 Status LLM: {'✅ Carregado' if llm_service.inicializado else '❌ Não carregado'}")
    app.run(debug=True, port=5000, threaded=True)