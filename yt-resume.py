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
    }
    
    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url_video, download=False)
            
            titulo = info.get('title', 'Sem título')
            
            # Tentar legendas originais primeiro
            legendas = info.get('subtitles', {})
            if not legendas:
                legendas = info.get('automatic_captions', {})
            
            if legendas:
                # Procurar por português ou inglês
                idioma_escolhido = None
                for idioma in ['pt', 'pt-BR', 'pt-PT', 'en']:
                    if idioma in legendas:
                        idioma_escolhido = idioma
                        break
                
                if idioma_escolhido:
                    legenda_info = legendas[idioma_escolhido]
                    
                    # Procurar formato que funcione
                    url_legenda = None
                    for formato in legenda_info:
                        if formato.get('ext') in ['srv3', 'srv2', 'srv1']:
                            url_legenda = formato.get('url')
                            break
                    
                    if url_legenda:
                        # Baixar conteúdo da legenda
                        response = requests.get(url_legenda)
                        conteudo_legenda = response.text
                        
                        # Extrair texto limpo
                        texto_limpo = extrair_texto_das_legendas(conteudo_legenda)
                        
                        # Salvar arquivo
                        with open("legenda.txt", 'w', encoding='utf-8') as f:
                            f.write(texto_limpo)
                        
                        return True
                        
    except Exception as e:
        return False
    
    return False

def extrair_texto_das_legendas(conteudo_xml):
    """Extrai texto limpo do XML das legendas do YouTube"""
    
    # Remover tags XML e manter só o texto
    texto = re.sub(r'<[^>]+>', '', conteudo_xml)
    
    # Remover quebras de linha e espaços extras
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # Remover caracteres especiais de controle
    texto = re.sub(r'[\r\n\t]', ' ', texto)
    
    return texto

def gerar_resumo_gpt():
    """Gera resumo usando GPT"""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        model = os.getenv('MODEL')
        
        # Ler arquivos
        with open('memory.txt', 'r', encoding='utf-8') as file:
            memory = file.read()
        
        with open('legenda.txt', 'r', encoding='utf-8') as file:
            legenda = file.read()
        
        historico = [{"role": "system", "content": memory}]
        historico.append({"role": "user", "content": legenda})
        
        print("Resumo: ", end="", flush=True)
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
        
        print("\n")
        historico.append({"role": "assistant", "content": resposta})
        
        return historico
        
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
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
    urls = input("URLs: ")
    
    lista_urls = [url.strip() for url in urls.split(',')]
    
    # Processar vídeos
    sucesso = False
    for url in lista_urls:
        if processar_video(url):
            sucesso = True
            break
    
    if sucesso:
        # Gerar resumo
        historico = gerar_resumo_gpt()
        
        if historico:
            # Iniciar chat interativo
            chat_interativo(historico)
        else:
            print("Erro ao inicializar chat.")
    else:
        print("Erro ao processar legendas dos vídeos.")
        