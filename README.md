Como funciona:

Toda terça e quinta às 19:00 o bot rodará o código.
Ele olhará os posts da página alvo e pegará o mais recente.
Verificará se o post já foi postado pelo bot no Log.
- Se já foi, ele olhará o próximo post (do mais recente ao mais antigo).
- Se não foi, ele pega o ID deste post.
Com o ID, o bot baixará o arquivo na pasta Media.
- Se for imagem: joga pra edição de imagem.
- Se for vídeo, cortará o vídeo em 30 segundos, separará áudio do vídeo, editará o vídeo e depois juntará o áudio novamente (a edição de vídeo remove áudio, por isso se torna necessário)
- Com o arquivo editado, ele segue 2 caminhos:
  1. Se for imagem -> posta no imgBB
  2. Se for vídeo  -> joga no catbox
Ambas as alternativas devolvem o link do arquivo.
O link do arquivo é enviado para a Meta para ser postado com todos os parâmetros preenchidos.
O arquivo é postado.
O log é atualizado com o ID do arquivo já postado, evitando que seja postado novamente.

(Nota: diversas ações possuem time.sleep para tempo de processamento, evitando erros).
(Nota 2: caso o arquivo não seja postado por qualquer tipo de erro, ele tentará o mesmo arquivo 3 vezes em intervalos de 5 minutos antes de desistir).
(Nota 3: a cada processo do arquivo de vídeo, o arquivo anterior é deletado fazendo com que só sobre um arquivo de vídeo, e não 4).


Como usar:

O usuário deverá ter em mãos:
- App ativo no Meta for Developers linkado à conta do Facebook com vínculo à conta do Instagram. (tutorial em breve)
- Conta no instagram profissional (business).
- Short Token do API Graph Explorer do App com as devidas permissões.
- ID do App (Meta for Developers).
- App Secret (Meta for Developers).
- Conta e chave de API do ImgBB.
- ID da sua conta profissionl do Instagram.
- @ do usuário alvo.

Abra teste.py
Preencha o arquivo com ID do app, app secret e a short token.
Rode 'python teste.py', o terminal devolverá sua permanent key token.
Abra bot.py
Preencha com:
- Sua nova permanent key token
- Seu ID do Instagram
- O @ da conta alvo
- O token do ImgBB

Rode bot.py e deixe o programa aberto e funcionando.

Próximas atualizações:
- Interface
- Inputs para inserção de dados
- Substituição do ImgBB
- Arquivo executável
- Versão em inglês
- Edição/alteração/remoção/adição de data e hora de postagem.

Criado por: @tortoruuu
Para uso de: @purplehaze_banda
