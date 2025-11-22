# 🇧🇷 Zap da Cidadania: Assessor Legislativo via WhatsApp

O Zap da Cidadania é um assistente de inteligência artificial via WhatsApp projetado para **democratizar o acesso à informação legislativa**. Nossa solução traduz a linguagem complexa das leis em termos simples, fornecendo ao cidadão ferramentas essenciais para compreensão, fiscalização e participação política ativa.

Diferente de plataformas de dados políticos que exigem conhecimento técnico e dedicação para serem usadas, o Zap da Cidadania é simples, acessível e funciona diretamente no WhatsApp, o aplicativo que é o principal canal de comunicação de mais de 120 milhões de brasileiros.

---

### 📝 Resumo do Projeto

| Categoria | Descrição |
| :--- | :--- |
| **Problema** | Linguagem legislativa inacessível e informações políticas dispersas. |
| **Solução** | IA que resume leis e votações, via WhatsApp. |
| **Benefício Central** | Mais compreensão, participação e fiscalização cidadã. |
| **Diferencial** | Personalização, linguagem simples e presença onde o cidadão já está (WhatsApp). |

---

## 🚀 Estrutura e Tecnologias

O projeto é construído em torno de um *workflow* de automação robusto que conecta o canal de comunicação (WhatsApp) com o processamento inteligente (IA e Dados Abertos).

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Gatilho/Comunicação** | Z-API | Recebe as mensagens e envia as respostas via WhatsApp. |
| **Automação/Workflow** | n8n | Orquestra o fluxo de dados (Webhook -> Busca de Dados -> Processamento IA -> Envio). |
| **Inteligência** | OpenAI (GPT-4o) | Traduz o texto complexo das leis e votações para linguagem simples. |
| **Dados** | Python / APIs Públicas | Scripts para buscar e estruturar dados do Poder Executivo e Legislativo. |

---

## ⚙️ Como Usar (Deployment)

Para colocar o Zap da Cidadania em funcionamento, você precisará configurar o *workflow* no n8n e garantir que os dados das APIs públicas estejam disponíveis.

### 1. Configuração do Workflow (n8n)

O coração do projeto é o arquivo `.json` do n8n, que contém toda a lógica do *workflow*.

* **Ação:** Siga os passos para **Importar o arquivo .json** do *workflow* e configure as credenciais essenciais (OpenAI Key, ID e Token do Z-API) conforme as instruções do seu painel.

---

### 2. Preparando os Dados (Python Scripts)

Os scripts Python são a fonte de dados do projeto, buscando informações em três APIs diferentes:

#### A. Governo Federal (Portal da Transparência)

* **API:** [https://api.portaldatransparencia.gov.br/swagger-ui/index.html](https://api.portaldatransparencia.gov.br/swagger-ui/index.html)
* **Script de Chamada:** `importrequestsServidores.py`

⚠️ **Atenção:** Para acessar esta API, é **obrigatório** alterar o *token* de autenticação dentro do script `importrequestsServidores.py` com a chave que você obtiver no portal.

#### B. Câmara dos Deputados

* **API:** [https://dadosabertos.camara.leg.br](https://dadosabertos.camara.leg.br)
* **Script de Chamada:** `importrequestsCamara.py`
* **Função:** Puxa dados de Proposições, Votações, e Deputados.

#### C. Senado Federal

* **API:** [https://legis.senado.leg.br/dadosabertos](https://legis.senado.leg.br/dadosabertos)
* **Script de Chamada:** `importrequestsSenado.py`
* **Função:** Puxa dados de Matérias Legislativas e Senadores.

#### Como Chamar os Scripts

Os scripts devem ser executados periodicamente (via Cron Job ou n8n) para manter a base de dados atualizada:

```bash
# Exemplo de chamada para atualizar os dados da Câmara
python importrequestsCamara.py [PARAMETROS]

# Exemplo de chamada para atualizar os dados do Senado
python importrequestsSenado.py [PARAMETROS]
