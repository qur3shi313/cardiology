"""Render the 1080p opener for Elysian's coronary angioplasty episode."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageOps

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'episode-01/revision'))
from render_editorial_cards import ROOT, gradient, write, font, panel, DEEP, INK, MUTED, LINE

im=gradient((248,251,246),(226,240,233)).copy()
d=ImageDraw.Draw(im)
logo=ImageOps.fit(Image.open(ROOT/'work/company-logo-original-686.jpg').convert('RGB'),(68,68),method=Image.Resampling.LANCZOS)
mask=Image.new('L',(68,68));ImageDraw.Draw(mask).ellipse((0,0,67,67),fill=255)
im.paste(logo,(66,47),mask)
write(d,152,47,'Elysian Biomedical LLP',31,'bold',DEEP)
write(d,152,86,'Cardiology Education Series',22,'body',MUTED)
d.text((1849,54),'EPISODE 02',font=font(27,'bold'),fill=DEEP,anchor='ra')
d.text((1849,89),'Educational illustration',font=font(22),fill=MUTED,anchor='ra')
d.line((66,139,1850,139),fill=LINE,width=2)
write(d,66,184,'Coronary angioplasty',66,'title')
panel(d,(66,301,1850,918))
write(d,125,373,'How a stent helps\nkeep an artery open',64,'title',DEEP)
write(d,125,566,'From the angiogram to treatment,\nthen a final X-ray check.',36,'body',INK)
d.line((126,728,804,728),fill=LINE,width=2)
write(d,125,775,'GUIDEWIRE  /  BALLOON  /  STENT',23,'bold',DEEP)

# A simplified longitudinal view of a coronary artery with an expanded stent.
x0,x1,cy=965,1741,570
for y in range(cy-125,cy+126):
    t=abs(y-cy)/125
    c=tuple(round(a+(b-a)*t) for a,b in zip((161,73,84),(202,130,125)))
    d.line((x0,y,x1,y),fill=c)
d.rounded_rectangle((x0-11,cy-125,x1+11,cy+125),radius=16,outline='#a65e60',width=4)
d.rectangle((x0,cy-71,x1,cy+71),fill='#8d394b')
d.line((x0,cy-72,x1,cy-72),fill='#d08a84',width=7)
d.line((x0,cy+72,x1,cy+72),fill='#d08a84',width=7)
for i in range(10):
    x=1119+i*47
    for a,b in (((x,cy-65),(x+47,cy)),((x,cy),(x+47,cy+65)),((x+47,cy-65),(x,cy)),((x+47,cy),(x,cy+65))):
        d.line((a,b),fill='#294f55',width=7)
        d.line((a,b),fill='#b5d5d2',width=4)
for x in (1119,1589):
    d.arc((x-17,cy-66,x+17,cy+66),0,360,fill='#b5d5d2',width=4)
d.line((1547,cy-46,1600,409,1721,409),fill=DEEP,width=3)
write(d,1610,365,'Expanded stent',24,'bold',DEEP)
write(d,965,759,'Illustrated section of a coronary artery',23,'body',MUTED)
d.line((66,1002,1850,1002),fill=LINE,width=2)
write(d,66,1022,'CORONARY ANGIOPLASTY AND STENT PLACEMENT',20,'bold',DEEP)
out=HERE/'assets';out.mkdir(exist_ok=True)
im.save(out/'episode-02-opening.png',optimize=True)
