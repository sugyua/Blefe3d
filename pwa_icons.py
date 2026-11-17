"""Gera ícones PNG estáticos por solicitação, sem dependências externas."""
from functools import lru_cache
import math
import struct
import zlib


def _card(x,y,cx,cy,w,h,theta):
    dx,dy=x-cx,y-cy
    c,si=math.cos(theta),math.sin(theta)
    u,v=dx*c+dy*si,-dx*si+dy*c
    if abs(u)>w/2 or abs(v)>h/2:return 0
    if max(abs(u)-(w/2-.025),0)**2+max(abs(v)-(h/2-.025),0)**2>.025**2:return 0
    return 1 if min(w/2-abs(u),h/2-abs(v))<.018 else 2


@lru_cache(maxsize=4)
def icon_png(size):
    if size not in (180,192,512):raise ValueError('Ícone fora dos tamanhos permitidos')
    glyph=('001111100','011000110','110000011','000000011','000000110','000001100','000011000','000110000','000110000','000000000','000110000','000110000','000000000')
    scan=[]
    for row in range(size):
        y=(row+.5)/size
        line=bytearray([0])
        for col in range(size):
            x=(col+.5)/size
            light=max(0,1-math.hypot(x-.5,y-.5)*.7)
            r,g,b=int(12+15*(1-y)*light),int(23+36*(1-y)*light),int(41+44*(1-y)*light)
            a=_card(x,y,.4,.5,.36,.55,-.31)
            if a:r,g,b=(255,240,205) if a==1 else (194,57,78)
            a=_card(x,y,.62,.51,.35,.53,.29)
            if a:r,g,b=(255,240,205) if a==1 else (37,111,181)
            dx,dy=x-.62,y-.48
            c,si=math.cos(.29),math.sin(.29)
            u,v=dx*c+dy*si,-dx*si+dy*c
            gx,gy=int((u+.115)/.23*9),int((v+.165)/.33*13)
            if 0<=gx<9 and 0<=gy<13 and glyph[gy][gx]=='1':r,g,b=255,230,151
            line.extend((r,g,b,255))
        scan.append(bytes(line))
    def chunk(tag,body):
        return struct.pack('>I',len(body))+tag+body+struct.pack('>I',zlib.crc32(tag+body)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(scan),6))+chunk(b'IEND',b'')
