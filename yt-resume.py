import yt_dlp
import openai
import os
import warnings
import re
import requests
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

def limpar_nome_arquivo(nome):
    """Remove caracteres inválidos do nome do arquivo"""
    caracteres_invalidos = '<>:"|?*\\/'
    
    for char in caracteres_invalidos:
        nome = nome.replace(char, '')
    
    nome = nome.strip()[:200]
    return nome

def processar_video(url_video):
    """Processa vídeo e extrai texto limpo das legendas"""

    opcoes = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,  # Necessário para ambientes com problemas de SSL
    }

    try:
        print("🎥 Extraindo informações do vídeo...")
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url_video, download=False)

            titulo = info.get('title', 'Sem título')
            print(f"📹 Vídeo: {titulo}")

            # Tentar legendas manuais primeiro (mais precisas)
            legendas = info.get('subtitles', {})
            tipo_legenda = "manual"

            # Se não houver legendas manuais, usar automáticas
            if not legendas:
                legendas = info.get('automatic_captions', {})
                tipo_legenda = "automática"

            if not legendas:
                print("❌ Nenhuma legenda encontrada para este vídeo.")
                return False

            # Mostrar idiomas disponíveis
            idiomas_disponiveis = list(legendas.keys())
            print(f"🌍 Idiomas disponíveis ({tipo_legenda}): {', '.join(idiomas_disponiveis)}")

            # Priorizar idiomas comuns, mas aceitar qualquer um disponível
            idiomas_prioritarios = ['pt-BR', 'pt-br', 'pt', 'pt-PT', 'en', 'en-US', 'en-GB']
            idioma_escolhido = None

            # Primeiro tentar idiomas prioritários
            for idioma in idiomas_prioritarios:
                if idioma in legendas:
                    idioma_escolhido = idioma
                    break

            # Se não encontrou nenhum prioritário, pegar o primeiro disponível
            if not idioma_escolhido and idiomas_disponiveis:
                idioma_escolhido = idiomas_disponiveis[0]

            if idioma_escolhido:
                print(f"✅ Usando legendas em: {idioma_escolhido}")
                legenda_info = legendas[idioma_escolhido]

                # Tentar qualquer formato disponível
                url_legenda = None
                for formato in legenda_info:
                    # Pegar qualquer formato que tenha URL
                    if formato.get('url'):
                        url_legenda = formato.get('url')
                        formato_nome = formato.get('ext', 'desconhecido')
                        print(f"📝 Formato da legenda: {formato_nome}")
                        break

                if url_legenda:
                    print("⬇️  Baixando legendas...")
                    # Baixar conteúdo da legenda
                    response = requests.get(url_legenda)
                    conteudo_legenda = response.text

                    # Extrair texto limpo
                    texto_limpo = extrair_texto_das_legendas(conteudo_legenda)

                    if not texto_limpo or len(texto_limpo.strip()) < 50:
                        print("⚠️  Aviso: Legenda parece estar vazia ou muito curta.")
                        return False

                    # Salvar arquivo
                    with open("legenda.txt", 'w', encoding='utf-8') as f:
                        f.write(texto_limpo)

                    print(f"✅ Legenda extraída com sucesso! ({len(texto_limpo)} caracteres)\n")
                    return True
                else:
                    print("❌ Não foi possível encontrar URL da legenda.")
            else:
                print("❌ Nenhum idioma compatível encontrado.")

    except Exception as e:
        print(f"❌ Erro ao processar vídeo: {e}")
        return False

    return False

def extrair_texto_das_legendas(conteudo_xml):
    """Extrai texto limpo do XML/JSON das legendas do YouTube"""

    # Remover tags XML e manter só o texto
    texto = re.sub(r'<[^>]+>', '', conteudo_xml)

    # Decodificar entidades HTML comuns
    texto = texto.replace('&amp;', '&')
    texto = texto.replace('&lt;', '<')
    texto = texto.replace('&gt;', '>')
    texto = texto.replace('&quot;', '"')
    texto = texto.replace('&#39;', "'")
    texto = texto.replace('&nbsp;', ' ')

    # Remover quebras de linha e espaços extras
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Remover caracteres especiais de controle
    texto = re.sub(r'[\r\n\t]', ' ', texto)

    return texto

def gerar_resumo_gpt():
    """Gera resumo usando GPT"""
    try:
        print("🤖 Gerando resumo com IA...")
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        model = os.getenv('MODEL')

        # Ler arquivos
        with open('memory.txt', 'r', encoding='utf-8') as file:
            memory = file.read()

        with open('legenda.txt', 'r', encoding='utf-8') as file:
            legenda = file.read()

        historico = [{"role": "system", "content": memory}]
        historico.append({"role": "user", "content": legenda})

        print("\n📝 Resumo:\n" + "="*50)
        resposta = ""

        response = client.chat.completions.create(
            model=model,
            messages=historico,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                print(delta, end="", flush=True)
                resposta += delta

        print("\n" + "="*50 + "\n")
        historico.append({"role": "assistant", "content": resposta})

        print("💬 Você pode fazer perguntas sobre o vídeo agora!\n")
        return historico

    except Exception as e:
        print(f"❌ Erro ao gerar resumo: {e}")
        return None

def chat_interativo(historico):
    """Mantém chat interativo com GPT"""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    model = os.getenv('MODEL')
    
    while True:
        pergunta = input("Você: ").strip()
        
        if not pergunta:
            continue
        
        print()
        historico.append({"role": "user", "content": pergunta})
        
        resposta = ""
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=historico,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    print(delta, end="", flush=True)
                    resposta += delta
            
            print("\n")
            historico.append({"role": "assistant", "content": resposta})
            
        except Exception as e:
            print(f"Erro: {e}")
            continue

# Programa principal
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🎬 YouTube Resume - Resumidor de Vídeos")
    print("="*60 + "\n")

    urls = input("📎 Cole a URL do vídeo (ou várias separadas por vírgula): ").strip()

    if not urls:
        print("❌ Nenhuma URL fornecida!")
        exit(1)

    lista_urls = [url.strip() for url in urls.split(',')]

    print(f"\n🔍 Processando {len(lista_urls)} vídeo(s)...\n")

    # Processar vídeos
    sucesso = False
    for i, url in enumerate(lista_urls, 1):
        if len(lista_urls) > 1:
            print(f"\n--- Vídeo {i}/{len(lista_urls)} ---")

        if processar_video(url):
            sucesso = True
            break
        else:
            if i < len(lista_urls):
                print("⚠️  Tentando próximo vídeo...\n")

    if sucesso:
        # Gerar resumo
        historico = gerar_resumo_gpt()

        if historico:
            # Iniciar chat interativo
            chat_interativo(historico)
        else:
            print("❌ Erro ao inicializar chat.")
    else:
        print("\n❌ Não foi possível processar legendas de nenhum dos vídeos.")
        print("💡 Dica: Verifique se o vídeo possui legendas disponíveis no YouTube.")