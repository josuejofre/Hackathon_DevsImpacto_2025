# Zap da Cidadania: Assessor Legislativo via WhatsApp

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
| **Dados** | Python / API Pública Legislativa | Script para buscar e estruturar dados do Legislativo Federal (Projetos de Lei, Votações, etc.). |

---

## ⚙️ Como Usar (Deployment)

Para colocar o Zap da Cidadania em funcionamento, você precisará configurar o *workflow* no n8n e garantir que os dados das APIs públicas estejam disponíveis.

### 1. Configuração do Workflow (n8n)

O coração do projeto é o arquivo `.json` do n8n, que contém toda a lógica do *workflow* (Webhook, Google Sheets, OpenAI e Z-API).

#### A. Importando o Arquivo `.json`

1.  Acesse sua instância do n8n (local ou cloud).
2.  No painel principal, clique em **"New"** (Novo) e depois em **"Import from JSON"** (Importar de JSON).
3.  Carregue o arquivo do *workflow* (`zap_da_cidadania_workflow.json` – nome de exemplo).
4.  O *workflow* será carregado, mas exigirá a configuração das credenciais.

#### B. Credenciais Essenciais

Antes de ativar o *workflow*, você deve configurar:

| Credencial | Nó | Descrição |
| :--- | :--- | :--- |
| **API Key OpenAI** | `Message a model` | Chave de acesso à API do GPT. |
| **ID da Instância** | `HTTP Request` (Z-API) | ID fornecido pelo seu painel Z-API. |
| **Token de Integração** | `HTTP Request` (Z-API) | Token fornecido pelo seu painel Z-API (incluído na URL ou Headers). |
| **Webhook URL** | `Webhook` | A URL gerada deve ser copiada e configurada no painel **Z-API** (seção "Ao receber"). |

---

### 2. Preparando os Dados (Python Script)

O script Python é responsável por coletar dados das APIs públicas do Legislativo e alimentar o banco de dados usado pelo n8n.

#### A. Estrutura do Script Python

Assumindo que o script se chama `fetch_data.py`, a estrutura de execução é a seguinte:

```bash
python fetch_data.py [PARAMETROS]
