#!/usr/bin/env bash
# Mostra a lista de atalhos
rofi -dmenu -i -p "atalhos" -no-custom <<'LISTA' >/dev/null
Super (sozinho)        abrir/fechar menu de apps
Super + R              executar comando (igual Win+R)
Shift + Vol +/-        volume só do Spotify
Super + Alt + ↑/↓      volume só do Spotify
Super + Enter          terminal
Super + B              navegador
Super + E              arquivos
Super + D              mostrar área de trabalho (igual Win+D)
Super + Q              fechar janela
Alt + F4               fechar janela (igual Windows)
Super + F              tela cheia
Super + M              maximizar
Super + T              janela flutuante (solta)
Super + C              centralizar janela flutuante
Super + V              histórico do copiar/colar
Super + .              emojis
Super + Shift + S      print de uma área e editar
Print                  print de uma área
Shift + Print          print da tela inteira
Super + Shift + C      pegar cor da tela
Super + N              luz noturna
Super + L              bloquear tela
Super + Esc            menu de desligar / sair
Super + setas          mudar o foco entre janelas
Super + Shift + setas  mover janela
Super + 1..6           ir pra área de trabalho
Super + Shift + 1..6   mandar janela pra área de trabalho
Super + Tab            área de trabalho anterior
Alt + Tab              próxima janela (todas, até as minimizadas)
Alt + Shift + Tab      janela anterior
Super + S              mostrar/esconder área secreta
Super + Alt + S        mandar janela pra área secreta
Super + arrastar       mover janela com o mouse
Super + botão direito  redimensionar com o mouse
Super + /              esta lista
LISTA
