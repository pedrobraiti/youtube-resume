## 🎬 YouTube Resume

Projeto que resume vídeos do YouTube e permite engajar em uma discussão sobre o conteúdo através da API da OpenAI.

### 🌟 Características

- ✅ **Suporte multilíngue**: Funciona com vídeos em **qualquer idioma** (português, inglês, espanhol, etc.)
- ✅ **Detecção automática**: Identifica e usa automaticamente as legendas disponíveis
- ✅ **Legendas automáticas e manuais**: Prioriza legendas manuais (mais precisas), mas aceita automáticas
- ✅ **Todos os formatos**: Aceita qualquer formato de legenda disponível no YouTube
- ✅ **Chat interativo**: Faça perguntas sobre o vídeo após o resumo
- ✅ **Sem STT pago**: Usa apenas legendas do YouTube (gratuito) + API OpenAI para resumos

### 📋 Requisitos

```bash
pip install -r requirements.txt
```

### ⚙️ Configuração

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` e adicione sua chave da OpenAI:
```
OPENAI_API_KEY=sua-chave-aqui
MODEL=gpt-4o-mini
```

### 🚀 Como Usar

```bash
python3 yt-resume.py
```

Depois cole a URL do vídeo (em qualquer idioma):
```
📎 Cole a URL do vídeo: https://youtu.be/WeFMVaunezk
```

O programa irá:
1. 🎥 Extrair informações do vídeo
2. 🌍 Detectar idiomas disponíveis
3. ✅ Baixar as legendas automaticamente
4. 🤖 Gerar resumo com IA
5. 💬 Permitir perguntas sobre o conteúdo

### 📝 Exemplos

**Vídeo em português:**
```
https://youtu.be/WeFMVaunezk?si=0nd7-KuczQgcdGg8
```

**Vídeo em inglês:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Múltiplos vídeos (separados por vírgula):**
```
https://youtu.be/video1, https://youtu.be/video2
```

### 🔧 Melhorias Recentes

- ✨ Detecção automática de **qualquer idioma** disponível
- ✨ Aceitação de **todos os formatos** de legenda (não apenas srv3/srv2/srv1)
- ✨ Priorização inteligente: português-BR → português → inglês → outros idiomas
- ✨ Logs informativos mostrando o progresso em cada etapa
- ✨ Validação de legendas vazias ou muito curtas
- ✨ Tratamento melhorado de erros com mensagens claras
- ✨ Decodificação de entidades HTML nas legendas

### ❓ FAQ

**P: Funciona com vídeos sem legendas?**
R: Não. O vídeo precisa ter legendas (automáticas ou manuais) disponíveis no YouTube.

**P: Preciso especificar o idioma do vídeo?**
R: Não! O programa detecta automaticamente e escolhe o melhor idioma disponível.

**P: Quais APIs pagas são usadas?**
R: Apenas a API da OpenAI para gerar os resumos. As legendas são extraídas gratuitamente do YouTube.

**P: Funciona com vídeos privados?**
R: Não, apenas vídeos públicos com legendas disponíveis.
