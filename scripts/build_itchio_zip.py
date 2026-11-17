"""Gera arquivo ZIP opcional com a página de apresentação para itch.io.

O jogo multiplayer reside no servidor Blefe Color, não dentro do ZIP.
Leia marketing/ITCH_IO.md antes de publicar.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'marketing'/'itch_launcher'/'index.html'
OUTPUT=ROOT/'marketing'/'blefe-color-itch-launcher.zip'
if __name__=='__main__':
    with ZipFile(OUTPUT,'w',compression=ZIP_DEFLATED) as archive:
        archive.write(SOURCE,arcname='index.html')
    print('Arquivo de apresentação preparado:',OUTPUT)
