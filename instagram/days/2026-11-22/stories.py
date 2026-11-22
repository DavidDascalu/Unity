import os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FD="/usr/share/fonts/opentype/inter/"
F=lambda n,s: ImageFont.truetype(FD+n+".otf",s)
LIME=(199,240,130); INK=(8,30,22); WHITE=(255,255,255); MUTED=(170,196,182)
yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt(((xx-W/2)/W)**2+((yy-H*.4)/H)**2); k=np.clip(r/.8,0,1)[...,None]
BG=Image.fromarray((np.array([22,78,56])*(1-k)+np.array([5,22,16])*k).astype(np.uint8),"RGB")
logo=Image.open("/home/user/Unity/instagram/engine/logo.png").convert("RGBA").resize((90,90))
def wrap(d,t,f,mw):
    o=[];l=""
    for w in t.split():
        s=(l+" "+w).strip()
        if d.textlength(s,font=f)<=mw: l=s
        else: o.append(l); l=w
    o.append(l); return o
def frame(lines, box=None, name=""):
    im=BG.convert("RGBA"); d=ImageDraw.Draw(im)
    im.alpha_composite(logo,(90,260)); d.text((200,305),"@jurnalul.alimentar",font=F("Inter-SemiBold",38),fill=MUTED,anchor="lm")
    y=460
    for txt,font,col in lines:
        for l in wrap(d,txt,font,860): d.text((90,y),l,font=font,fill=col); y+=font.size*1.12
        y+=30
    im.convert("RGB").save(name)
P="0 - Duminica 22 nov - STORIES cadru"
frame([("Ghicește:",F("InterDisplay-Black",110),LIME),("care prăjitură Zoomserie are cele mai multe calorii la 100 g?",F("InterDisplay-Bold",80),WHITE)],
      "pune aici stickerul QUIZ: Kornet / Tiramisu / Bueno Profiterol", f"{P} 1.png")
frame([("Răspuns:",F("InterDisplay-Black",110),LIME),("Tort Bueno Profiterol, 390 kcal la 100 g.",F("InterDisplay-Bold",80),WHITE),("Kornet are 256. Toate cele 5 sunt în postarea nouă.",F("Inter-Medium",50),MUTED)],
      "pune aici stickerul cu postarea nouă (distribuie caruselul în story)", f"{P} 2.png")
frame([("Săptămâna asta",F("InterDisplay-Black",110),LIME),("ce vrei să urmărești: caloriile, proteinele sau dulciurile?",F("InterDisplay-Bold",80),WHITE)],
      "pune aici stickerul ÎNTREBARE", f"{P} 3.png")
