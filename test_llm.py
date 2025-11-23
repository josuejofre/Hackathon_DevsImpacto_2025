# test_sabia.py
from llm_service import LLMService
import time

def test_sabia():
    print("🧪 Testando Sabiá-7B...")
    
    inicio = time.time()
    llm = LLMService()
    tempo_carregamento = time.time() - inicio
    
    print(f"⏱️ Tempo de carregamento: {tempo_carregamento:.2f}s")
    
    if not llm.inicializado:
        print("❌ Sabiá-7B não inicializado")
        return
    
    # Testes com propostas reais do seu banco
    testes = [
        {
            "contexto": "Altera o Decreto-Lei nº 2.848, de 7 de dezembro de 1940 (Código Penal), para prever o processamento mediante ação penal pública incondicionada para o crime de dano em contexto de violência doméstica contra a mulher.",
            "perguntas": [
                "Quem se beneficia com esta lei?",
                "Como isso afeta as vítimas de violência doméstica?",
                "O que significa 'ação penal pública incondicionada'?",
                "Esta lei aumenta as penas para o crime de dano?"
            ]
        },
        {
            "contexto": "Altera a Lei nº 9.394, de 20 de dezembro de 1996 (Lei de Diretrizes e Bases da Educação Nacional), e a Lei nº 14.645, de 2 de agosto de 2023, para considerar os povos indígenas e quilombolas na oferta de educação profissional e tecnológica.",
            "perguntas": [
                "Como esta lei ajuda comunidades indígenas?",
                "Quais são os benefícios para a educação profissional?",
                "Isso gera custos para o governo?",
                "Quando essa lei entra em vigor?"
            ]
        }
    ]
    
    for i, teste in enumerate(testes, 1):
        print(f"\n{'='*60}")
        print(f"📋 TESTE {i}: {teste['contexto'][:100]}...")
        print(f"{'='*60}")
        
        for pergunta in teste['perguntas']:
            print(f"\n❓ Pergunta: {pergunta}")
            
            inicio_resposta = time.time()
            resposta = llm.responder_duvida(pergunta, teste['contexto'])
            tempo_resposta = time.time() - inicio_resposta
            
            print(f"💡 Resposta ({tempo_resposta:.2f}s): {resposta}")
            print("-" * 50)

if __name__ == "__main__":
    test_sabia()