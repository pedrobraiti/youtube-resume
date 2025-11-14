#!/usr/bin/env python3
"""Script de teste para verificar extração de legendas"""

import yt_dlp
import requests
import re

def extrair_texto_das_legendas(conteudo_xml):
    """Extrai texto limpo do XML/JSON das legendas do YouTube"""
    texto = re.sub(r'<[^>]+>', '', conteudo_xml)
    texto = texto.replace('&amp;', '&')
    texto = texto.replace('&lt;', '<')
    texto = texto.replace('&gt;', '>')
    texto = texto.replace('&quot;', '"')
    texto = texto.replace('&#39;', "'")
    texto = texto.replace('&nbsp;', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()
    texto = re.sub(r'[\r\n\t]', ' ', texto)
    return texto

def testar_video(url):
    """Testa extração de legendas de um vídeo"""
    opcoes = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,  # Necessário para ambientes com problemas de SSL
    }

    print(f"\n{'='*60}")
    print(f"Testando URL: {url}")
    print(f"{'='*60}\n")

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=False)

            titulo = info.get('title', 'Sem título')
            print(f"📹 Vídeo: {titulo}\n")

            # Verificar legendas manuais
            legendas = info.get('subtitles', {})
            tipo_legenda = "manual"

            if legendas:
                print(f"✅ Legendas manuais encontradas: {', '.join(legendas.keys())}\n")

            # Se não houver legendas manuais, usar automáticas
            if not legendas:
                legendas = info.get('automatic_captions', {})
                tipo_legenda = "automática"
                if legendas:
                    print(f"✅ Legendas automáticas encontradas: {', '.join(legendas.keys())}\n")

            if not legendas:
                print("❌ Nenhuma legenda encontrada!\n")
                return False

            # Mostrar idiomas disponíveis
            idiomas_disponiveis = list(legendas.keys())

            # Tentar pt-BR primeiro
            idiomas_prioritarios = ['pt-BR', 'pt-br', 'pt', 'pt-PT']
            idioma_escolhido = None

            for idioma in idiomas_prioritarios:
                if idioma in legendas:
                    idioma_escolhido = idioma
                    break

            if not idioma_escolhido and idiomas_disponiveis:
                idioma_escolhido = idiomas_disponiveis[0]

            if idioma_escolhido:
                print(f"✅ Usando legendas em: {idioma_escolhido} (tipo: {tipo_legenda})\n")
                legenda_info = legendas[idioma_escolhido]

                # Mostrar formatos disponíveis
                print("📝 Formatos disponíveis:")
                for formato in legenda_info:
                    print(f"   - {formato.get('ext', 'desconhecido')}: {formato.get('url', 'sem URL')[:80]}...")
                print()

                # Tentar baixar
                url_legenda = None
                for formato in legenda_info:
                    if formato.get('url'):
                        url_legenda = formato.get('url')
                        formato_nome = formato.get('ext', 'desconhecido')
                        break

                if url_legenda:
                    print("⬇️  Baixando legendas...")
                    response = requests.get(url_legenda)
                    conteudo_legenda = response.text

                    # Extrair texto
                    texto_limpo = extrair_texto_das_legendas(conteudo_legenda)

                    print(f"✅ Legenda extraída! ({len(texto_limpo)} caracteres)\n")
                    print("📄 Primeiros 500 caracteres:")
                    print("-" * 60)
                    print(texto_limpo[:500])
                    print("-" * 60)

                    # Salvar
                    with open("legenda_teste.txt", 'w', encoding='utf-8') as f:
                        f.write(texto_limpo)
                    print("\n✅ Legenda salva em 'legenda_teste.txt'\n")

                    return True

    except Exception as e:
        print(f"❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    return False

if __name__ == "__main__":
    # URL em português fornecida pelo usuário
    url_pt = "https://youtu.be/WeFMVaunezk?si=0nd7-KuczQgcdGg8"

    # URL em inglês para teste comparativo
    url_en = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print("\n🧪 TESTE DE EXTRAÇÃO DE LEGENDAS\n")

    # Testar URL em português
    print("🇧🇷 Testando vídeo em PORTUGUÊS:")
    sucesso_pt = testar_video(url_pt)

    # Testar URL em inglês
    print("\n🇺🇸 Testando vídeo em INGLÊS:")
    sucesso_en = testar_video(url_en)

    # Resumo
    print(f"\n{'='*60}")
    print("RESUMO DOS TESTES")
    print(f"{'='*60}")
    print(f"Português: {'✅ SUCESSO' if sucesso_pt else '❌ FALHOU'}")
    print(f"Inglês: {'✅ SUCESSO' if sucesso_en else '❌ FALHOU'}")
    print(f"{'='*60}\n")
