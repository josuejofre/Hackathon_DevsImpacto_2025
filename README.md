# 🏛️ Zap da Cidadania - Assistente Legislativo com IA

Um chatbot inteligente via WhatsApp que ajuda cidadãos a entender propostas legislativas brasileiras, acompanhar votações de políticos e ficar informado sobre temas de interesse. Powered by Sabiá-7B LLM.

## 📋 O que a aplicação faz

O **Zap da Cidadania** democratiza o acesso a informações legislativas complexas através de um assistente conversacional via WhatsApp. A aplicação:

### 🎯 Funcionalidades principais

1. **Entender Propostas Legislativas**
   - Busca propostas por número (ex: PL 295/2024, PEC 18/2024)
   - Fornece resumo simplificado e ementa oficial
   - Classifica temas automaticamente
   - Usa IA para responder dúvidas específicas sobre a proposta

2. **Acompanhar Votações**
   - Mostra como políticos votaram em propostas específicas
   - Identifica histórico de votações por político
   - Organiza por partido e estado

3. **Alertas Personalizados**
   - Ativa notificações para temas de interesse (Saúde, Educação, Segurança, etc.)
   - Recebe alertas automáticos sobre avanços em propostas relevantes
   - Acompanha votações de políticos favoritos

4. **Assistente com IA**
   - Usa o modelo **Sabiá-7B** para responder perguntas sobre propostas
   - Explica termos legislativos em linguagem simples
   - Analisa impacto das leis na população

5. **Informações Sobre Proposição de Leis**
   - Explica como um cidadão pode propor um novo projeto de lei

## 🛠️ Arquitetura e Componentes

### `app.py` - API Principal Flask
- Servidor Flask que gerencia o webhook do WhatsApp
- Mantém sessões de usuários em memória
- Controla fluxo conversacional com máquina de estados
- **Endpoints principais:**
  - `POST /webhook/whatsapp` - Processa mensagens recebidas
  - `POST /alertas/enviar` - Envia alertas para usuários
  - `GET /health` - Status da aplicação
  - `GET /stats` - Estatísticas de uso

**Estados da conversa:**
- `menu_principal` - Menu inicial com opções
- `aguardando_proposicao` - Aguardando número de proposta
- `aguardando_politico` - Aguardando nome de político
- `aguardando_temas` - Seleção de temas para alertas
- `detalhes_proposicao` - Mostra detalhes da proposta
- `detalhes_politico` - Mostra histórico de votações

### `llm_service.py` - Serviço de IA
Integração com o modelo **Sabiá-7B** da Marítaca:
- Carrega o modelo com otimizações de memória (`float16`, `device_map="auto"`)
- Gera respostas contextizadas sobre propostas legislativas
- Limpa e formata respostas para caber em mensagens WhatsApp
- Configurado com `temperature=0.7` para respostas equilibradas

### `whatsapp_service.py` - Integração WhatsApp
Gerencia envio de mensagens:
- Usa `pywhatkit` para enviar mensagens instantaneamente
- Implementa rate limiting (10 segundos entre mensagens)
- Formata números de telefone para o padrão internacional

### `test_llm.py` - Testes
Script para testar o modelo Sabiá-7B:
- Testa carregamento do modelo
- Simula perguntas sobre propostas reais
- Mede tempo de resposta
- Valida qualidade das respostas

## 📊 Banco de Dados

A aplicação utiliza **PostgreSQL** com as seguintes tabelas:

```
usuarios
├── id (PK)
├── telefone (UNIQUE)
├── temas_interesse (array)
└── politicos_favoritos (array)

proposicoes_legislativas
├── id (PK)
├── tipo (PL, PEC, MPV)
├── numero
├── ano
├── ementa_resumo
├── artigo_1_trecho
├── link_pdf
├── data_apresentacao
└── ...

politicos
├── id (PK)
├── nome
├── partido
├── estado
└── ...

votacoes
├── id (PK)
├── politico_id (FK)
├── proposicao_legislativa_id (FK)
├── voto (SIM/NÃO/ABSTENÇÃO)
└── data_votacao

alertas
├── id (PK)
├── usuario_id (FK)
├── proposicao_legislativa_id (FK)
├── tipo_alerta
└── data_criacao
```

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.8+
- PostgreSQL 12+ instalado e rodando
- Banco de dados `legis_ai` criado
- 8GB+ de RAM (para carregar modelo Sabiá-7B)
- GPU NVIDIA (recomendado, mas funciona em CPU)

### 1. Clonar o repositório

```bash
git clone https://github.com/josuejofre/Hackathon_DevsImpacto_2025.git
cd Hackathon_DevsImpacto_2025
```

### 2. Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar banco de dados

Crie o banco de dados e execute as migrações:

```bash
# No PostgreSQL
createdb legis_ai

# Depois, execute o script de schema (crie um arquivo schema.sql com as tabelas)
psql -d legis_ai -f schema.sql
```

### 5. Configurar credenciais

Edite o arquivo `app.py` e atualize as credenciais do banco de dados (atualmente codificadas):

```python
def get_db_connection():
    return psycopg.connect(
        host="localhost",
        dbname="legis_ai",
        user="seu_usuario",  # Altere aqui
        password="sua_senha",  # Altere aqui
        row_factory=dict_row
    )
```

**Melhor prática:** Use variáveis de ambiente

```bash
export DB_HOST="localhost"
export DB_NAME="legis_ai"
export DB_USER="seu_usuario"
export DB_PASSWORD="sua_senha"
```

### 6. Iniciar a aplicação

```bash
python3 app.py
```

A aplicação iniciará em `http://localhost:5000`

Você deve ver algo como:
```
🚀 Iniciando Zap da Cidadania com Sabiá-7B...
🤖 Status LLM: ✅ Carregado
```

### 7. Testar o modelo IA (opcional)

```bash
python3 test_llm.py
```

## 💬 Como Utilizar

### Via WhatsApp

Envie um webhook POST para o endpoint da aplicação:

```bash
curl -X POST http://localhost:5000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "from": "5585991471915",
    "body": "1"
  }'
```

### Fluxo de Uso

#### 1️⃣ Entender uma Proposta Legislativa

```
Usuário: 1
Bot: 🔎 Qual proposta legislativa você quer entender?
Digite o número (ex: PL 295/2024, PEC 18/2024, MPV 1286/2024).

Usuário: PL 295/2024
Bot: 📘 PL 295/2024
📅 Data: 15/03/2024
📝 Resumo simplificado: ...
💡 O que propõe: ...
🎯 Temas: Segurança, Direitos
🔗 Link: ...

🤖 Assistente IA Disponível
1️⃣ Ver quem votou
2️⃣ Ativar alertas
3️⃣ Nova proposta
4️⃣ Voltar ao menu
5️⃣ 🤔 Fazer uma pergunta

Usuário: Quem se beneficia com esta lei?
Bot: 💡 Resposta do Assistente Legislativo
Sua pergunta: "Quem se beneficia com esta lei?"
Resposta: [Resposta gerada por IA]
```

#### 2️⃣ Acompanhar Votações

```
Usuário: 2
Bot: 📌 Digite o nome do político (ex: 'Carlos Silva')

Usuário: Jair Bolsonaro
Bot: 🗳️ Atividade Recente — Jair Bolsonaro (PL - RJ)
Votações recentes:
✅ SIM no PL 295/2024
❌ NÃO no PEC 18/2024
...

Quer:
1️⃣ Entender uma dessas votações
2️⃣ Favoritar este político
3️⃣ Ver todo histórico
4️⃣ Voltar ao menu
```

#### 3️⃣ Ativar Alertas Personalizados

```
Usuário: 3
Bot: 📣 Escolha os temas que deseja acompanhar:
1️⃣ Saúde
2️⃣ Educação
3️⃣ Segurança
...

Usuário: 1, 3, 5
Bot: ✅ Tudo certo!
Você receberá alertas sobre: Saúde, Segurança, Meio Ambiente
```

#### 4️⃣ Como Propor um Projeto de Lei

```
Usuário: 4
Bot: 💡 Para propor um Projeto de Lei:
1. Coletar assinaturas de apoio (1% do eleitorado)
2. Protocolar na Câmara ou Senado
3. Buscar apoio de um parlamentar
4. Participar de audiências públicas
```

### Comandos Especiais

- `voltar` - Volta ao menu principal
- `menu` - Vai para o menu principal
- `cancelar` - Cancela operação atual
- `0` - Volta ao menu

## 🤖 Usando o Assistente IA

Após selecionar uma proposta legislativa, você pode fazer perguntas diretas sobre ela:

**Exemplos de perguntas:**
- "Como isso afeta os cidadãos?"
- "Quem será beneficiado?"
- "Há custos envolvidos?"
- "Quando entra em vigor?"
- "O que significa 'ação penal pública incondicionada'?"

O modelo **Sabiá-7B** analisará a proposta e responderá em linguagem simples e acessível.

## 📞 Endpoints da API

### POST `/webhook/whatsapp`
Recebe mensagens do WhatsApp e processa

**Request:**
```json
{
  "from": "5585991471915",
  "body": "PL 295/2024"
}
```

**Response:**
```json
{
  "status": "processed"
}
```

### POST `/alertas/enviar`
Envia alertas para usuários interessados

**Request:**
```json
{
  "proposicao_legislativa_id": 1,
  "tipo_alerta": "nova_votacao"
}
```

**Response:**
```json
{
  "enviado_para": ["5585991471915", "5511988776655"],
  "total": 2
}
```

### GET `/health`
Verifica saúde da aplicação

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "llm_service": "loaded",
  "whatsapp_service": "ready"
}
```

### GET `/stats`
Retorna estatísticas de uso

**Response:**
```json
{
  "sessions_ativas": 5,
  "llm_carregado": true,
  "timestamp": "2025-11-23T10:30:45.123456"
}
```

## ⚙️ Dependências

```
Flask==2.3.3           # Framework web
psycopg==3.1.18        # Driver PostgreSQL
pywhatkit==5.4         # Integração WhatsApp
transformers==4.35.2   # Carregamento do modelo Sabiá-7B
torch>=2.1.0           # Deep Learning
sentencepiece==0.1.99  # Tokenização
accelerate==0.24.1     # Otimização GPU
requests==2.31.0       # Requisições HTTP
```

## 🔧 Configurações Importantes

### Sabiá-7B Model
- **Modelo:** `maritaca-ai/sabia-7b`
- **Precision:** float16 (otimizado para memória)
- **Device Map:** auto (CPU/GPU automático)
- **Temperatura:** 0.7 (respostas equilibradas)
- **Max Tokens:** 256 (limite para WhatsApp)
- **Top-p:** 0.9 (diversity balanceado)

### WhatsApp Service
- **Rate Limit:** 10 segundos entre mensagens
- **Ferramenta:** pywhatkit
- **Wait Time:** 15 segundos por mensagem

## 🚨 Tratamento de Erros

A aplicação possui logging detalhado com emojis:
- ✅ Sucesso
- ❌ Erro
- 🔄 Processamento
- 💡 Informação
- ⚠️ Aviso

Todos os logs são salvos no console e podem ser redirecionados para arquivo.

## 📝 Notas de Desenvolvimento

### Melhorias Futuras
1. Integração com API oficial do WhatsApp (atualmente via pywhatkit)
2. Cache de respostas frequentes
3. Sistema de feedback do usuário
4. Dashboard de análise legislativa
5. Integração com redes sociais
6. Suporte a múltiplos idiomas
7. Análise de tendências legislativas

### Troubleshooting

**Modelo não carrega:**
```bash
# Baixe o modelo manualmente
python3 -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
AutoTokenizer.from_pretrained('maritaca-ai/sabia-7b'); \
AutoModelForCausalLM.from_pretrained('maritaca-ai/sabia-7b')"
```

**Erro de conexão com banco:**
- Verifique se PostgreSQL está rodando
- Teste conexão: `psql -U usuario -d legis_ai`
- Valide credenciais em `app.py`

**WhatsApp não envia mensagens:**
- Verifique se o browser está aberto
- Confirme número de telefone em formato internacional
- Verifique logs para detalhes do erro

## 📄 Licença

Projeto desenvolvido para o Hackathon DevImpacto 2025

## 👥 Contribuidores

- **Equipe DevImpacto 2025**

## 📧 Contato

Para dúvidas ou contribuições, abra uma issue no GitHub ou entre em contato com a equipe.

---

**Made with ❤️ for Brazilian Democracy**

🏛️ Zap da Cidadania - Entendendo a legislação, juntos!
