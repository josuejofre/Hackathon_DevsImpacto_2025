import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.inicializado = False
        self._carregar_modelo_sabia()
    
    def _carregar_modelo_sabia(self):
        """Carrega o modelo Sabiá-7B"""
        try:
            logger.info("🔄 Carregando modelo Sabiá-7B...")
            
            # Modelo Sabiá-7B
            model_name = "maritaca-ai/sabia-7b"
            
            # Carregar tokenizer e modelo
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            
            # Configurar tokenizer
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.inicializado = True
            logger.info("✅ Modelo Sabiá-7B carregado com sucesso!")
            logger.info(f"📊 Modelo carregado em: {self.model.device}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo Sabiá-7B: {e}")
            self.inicializado = False
    
    def responder_duvida(self, pergunta, contexto_proposta):
        """Responde dúvidas específicas sobre a proposta usando Sabiá-7B"""
        if not self.inicializado:
            return "Desculpe, o serviço de respostas não está disponível no momento."
        
        try:
            # Preparar prompt específico para o Sabiá-7B
            prompt = f"""<|system|>
Você é um assistente especializado em explicar propostas legislativas brasileiras de forma clara e simples.

Contexto da proposta: {contexto_proposta}

Responda à pergunta do usuário de maneira direta e útil, focando nos aspectos práticos.</|system|>
<|user|>
{pergunta}</|user|>
<|assistant|>"""
            
            # Tokenizar
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            # Mover para o mesmo dispositivo do modelo
            if hasattr(self.model, 'device'):
                inputs = inputs.to(self.model.device)
            
            # Gerar resposta
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decodificar resposta
            resposta_completa = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extrair apenas a parte do assistente
            resposta = resposta_completa.split("<|assistant|>")[-1].strip()
            
            # Limpar e formatar resposta
            resposta = self._limpar_resposta(resposta)
            
            logger.info(f"🤖 Resposta gerada ({len(resposta)} caracteres)")
            return resposta
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta: {e}")
            return "Desculpe, não consegui processar sua pergunta no momento. Tente reformular ou perguntar sobre outro aspecto."
    
    def _limpar_resposta(self, resposta):
        """Limpa e formata a resposta"""
        # Remover tags específicas do modelo se existirem
        tags_para_remover = ["<|end|>", "<|system|>", "<|user|>", "<|assistant|>"]
        for tag in tags_para_remover:
            resposta = resposta.replace(tag, "")
        
        # Limitar tamanho
        if len(resposta) > 400:
            # Tentar cortar em uma frase completa
            ultimo_ponto = resposta[:400].rfind('.')
            if ultimo_ponto > 200:
                resposta = resposta[:ultimo_ponto + 1]
            else:
                resposta = resposta[:397] + "..."
        
        # Garantir que termina com pontuação
        if not resposta.endswith(('.', '!', '?')):
            resposta += "."
        
        return resposta.strip()