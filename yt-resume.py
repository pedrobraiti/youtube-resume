import yt_dlp
import openai
import os
import warnings
import re
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

warnings.filterwarnings("ignore")
load_dotenv()

def extrair_video_id(url):
    """Extrai o ID do vídeo de uma URL do YouTube"""
    import re
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'embed\/([0-9A-Za-z_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def limpar_nome_arquivo(nome):
    """Remove caracteres inválidos do nome do arquivo"""
    caracteres_invalidos = '<>:"|?*\\/'

    for char in caracteres_invalidos:
        nome = nome.replace(char, '')

    nome = nome.strip()[:200]
    return nome

def processar_video(url_video):
    """Processa vídeo e extrai texto limpo das legendas usando youtube-transcript-api"""

    print("🎥 Extraindo informações do vídeo...")

    # Extrair ID do vídeo
    video_id = extrair_video_id(url_video)
    if not video_id:
        print("❌ Não foi possível extrair o ID do vídeo da URL.")
        return False

    print(f"🆔 ID do vídeo: {video_id}")

    try:
        # Listar todas as transcrições disponíveis
        print("🔍 Buscando legendas disponíveis...")
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Coletar todos os idiomas disponíveis
        idiomas_manuais = []
        idiomas_automaticos = []

        for transcript in transcript_list:
            if transcript.is_generated:
                idiomas_automaticos.append(transcript.language_code)
            else:
                idiomas_manuais.append(transcript.language_code)

        print(f"🌍 Legendas manuais: {idiomas_manuais if idiomas_manuais else 'Nenhuma'}")
        print(f"🤖 Legendas automáticas: {idiomas_automaticos if idiomas_automaticos else 'Nenhuma'}")

        # Priorizar idiomas
        idiomas_prioritarios = ['pt', 'pt-BR', 'pt-PT', 'en', 'en-US', 'en-GB']
        transcript = None
        idioma_usado = None
        tipo_legenda = None

        # Tentar idiomas prioritários primeiro nas legendas manuais
        for idioma in idiomas_prioritarios:
            if idioma in idiomas_manuais:
                try:
                    transcript = transcript_list.find_transcript([idioma])
                    idioma_usado = idioma
                    tipo_legenda = "manual"
                    break
                except:
                    continue

        # Se não encontrou, tentar idiomas prioritários nas automáticas
        if not transcript:
            for idioma in idiomas_prioritarios:
                if idioma in idiomas_automaticos:
                    try:
                        transcript = transcript_list.find_transcript([idioma])
                        idioma_usado = idioma
                        tipo_legenda = "automática"
                        break
                    except:
                        continue

        # Se ainda não encontrou, pegar a primeira disponível (manual ou automática)
        if not transcript:
            for t in transcript_list:
                try:
                    transcript = t
                    idioma_usado = t.language_code
                    tipo_legenda = "manual" if not t.is_generated else "automática"
                    break
                except:
                    continue

        if not transcript:
            print("❌ Nenhuma legenda pôde ser carregada.")
            return False

        print(f"✅ Usando legendas em: {idioma_usado} ({tipo_legenda})")
        print(f"📝 Idioma completo: {transcript.language}")

        # Baixar a transcrição
        print("⬇️  Baixando legendas...")
        transcript_data = transcript.fetch()

        # Extrair texto limpo
        texto_limpo = ' '.join([entry['text'] for entry in transcript_data])

        # Limpar texto
        texto_limpo = texto_limpo.strip()

        if not texto_limpo or len(texto_limpo.strip()) < 50:
            print("⚠️  Aviso: Legenda parece estar vazia ou muito curta.")
            return False

        # Salvar arquivo
        with open("legenda.txt", 'w', encoding='utf-8') as f:
            f.write(texto_limpo)

        print(f"✅ Legenda extraída com sucesso! ({len(texto_limpo)} caracteres)\n")
        return True

    except TranscriptsDisabled:
        print("❌ As legendas estão desabilitadas para este vídeo.")
        return False
    except NoTranscriptFound:
        print("❌ Nenhuma legenda encontrada para este vídeo.")
        return False
    except Exception as e:
        print(f"❌ Erro ao processar vídeo: {e}")
        print("💡 Tentando método alternativo com yt-dlp...")
        return processar_video_fallback(url_video)

def processar_video_fallback(url_video):
    """Método alternativo usando yt-dlp (fallback)"""

    opcoes = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    try:
        print("🔄 Usando método alternativo (yt-dlp)...")
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
        print(f"❌ Erro ao processar vídeo com método alternativo: {e}")
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