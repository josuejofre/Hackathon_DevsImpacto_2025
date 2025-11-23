import pywhatkit
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.ultimo_envio = 0
        logger.info("✅ Serviço WhatsApp inicializado")
    
    def enviar_mensagem(self, telefone, mensagem):
        try:
            # Rate limiting - 10 segundos entre mensagens
            agora = time.time()
            if agora - self.ultimo_envio < 10:
                time.sleep(10 - (agora - self.ultimo_envio))
            
            # Formatar telefone
            tel_limpo = ''.join(filter(str.isdigit, telefone))
            if tel_limpo.startswith('55'):
                tel_limpo = tel_limpo[2:]
            
            logger.info(f"📤 Enviando mensagem para {tel_limpo}")
            
            # Enviar via pywhatkit
            pywhatkit.sendwhatmsg_instantly(
                f"+55{tel_limpo}", 
                mensagem,
                wait_time=15,
                tab_close=True
            )
            
            self.ultimo_envio = time.time()
            logger.info(f"✅ Mensagem enviada para {tel_limpo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False