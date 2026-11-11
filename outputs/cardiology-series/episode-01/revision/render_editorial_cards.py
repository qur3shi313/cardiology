"""Render the shared 1080p editorial and educational cards for the two reviewed films."""
from pathlib import Path
from functools import lru_cache
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / 'editorial-scenes'
FONTDIR = ROOT / 'outputs/website-v2/elysian-corporate/assets/fonts'
sys.path.insert(0, str(HERE.parent / 'production'))
import vascular_art as geo

W,H = 1920,1080
INK = '#18312d'
DEEP = '#004b3d'
MUTED = '#466058'
LINE = '#c0d5ca'
WHITE = '#f8fbf7'
PALE = '#e9f3ee'

@lru_cache(None)
def font(size, kind='body'):
    path = {'body':'fira-sans-regular.ttf','bold':'fira-sans-semibold.ttf','title':'josefin-sans-variable.ttf'}[kind]
    f=ImageFont.truetype(str(FONTDIR / path),size)
    if kind=='title': f.set_variation_by_axes([650])
    return f

def write(d, x, y, value, size=28, kind='body', color=INK, maxwidth=None):
    f=font(size,kind)
    if maxwidth:
        lines=[]
        for part in value.split('\n'):
            line=''
            for word in part.split():
                candidate=(line+' '+word).strip()
                if line and d.textlength(candidate,font=f)>maxwidth:
                    lines.append(line);line=word
                else: line=candidate
            lines.append(line)
    else: lines=value.split('\n')
    for k,l in enumerate(lines):d.text((x,y+k*int(size*1.24)),l,font=f,fill=color,anchor='lt')
    return len(lines)*int(size*1.24)

@lru_cache(None)
def gradient(top,bottom):
    img=Image.new('RGB',(W,H)); d=ImageDraw.Draw(img)
    for y in range(H):
        t=y/(H-1); d.line((0,y,W,y),fill=tuple(round(a+(b-a)*t) for a,b in zip(top,bottom)))
    return img

def frame(route,title,kicker):
    im=gradient((248,251,246),(226,240,233)).copy();d=ImageDraw.Draw(im)
    logo=Image.open(ROOT/'work/company-logo-original-686.jpg').convert('RGB')
    logo=ImageOps.fit(logo,(68,68),method=Image.Resampling.LANCZOS)
    mask=Image.new('L',(68,68));ImageDraw.Draw(mask).ellipse((0,0,67,67),fill=255)
    im.paste(logo,(66,47),mask)
    write(d,152,47,'Elysian Biomedical LLP',31,'bold',DEEP)
    write(d,152,86,'Cardiology Education Series',22,'body',MUTED)
    route_name='RIGHT WRIST' if route=='radial' else 'RIGHT GROIN'
    d.text((1849,53),route_name,font=font(27,'bold'),fill=DEEP,anchor='ra')
    d.text((1849,89),kicker,font=font(22),fill=MUTED,anchor='ra')
    d.line((66,139,1850,139),fill=LINE,width=2)
    write(d,66,184,title,66,'title')
    d.line((66,1002,1850,1002),fill=LINE,width=2)
    write(d,66,1022,'CORONARY ANGIOGRAPHY',20,'bold',DEEP)
    return im,d

def panel(d,box,fill='#f8fcf8'):
    d.rounded_rectangle(box,radius=33,fill=fill,outline=LINE,width=2)

def bullet(d,x,y,tag,title,sub,maxwidth=640):
    d.rounded_rectangle((x,y,x+62,y+62),radius=17,fill='#dcece3')
    d.text((x+31,y+30),tag,font=font(22,'bold'),fill=DEEP,anchor='mm')
    write(d,x+83,y+2,title,31,'bold',INK,maxwidth)
    write(d,x+83,y+47,sub,25,'body',MUTED,maxwidth)

def heart(im, x, y, scale):
    def xy(points):return [(x+(a-140)*scale,y+(b-49)*scale) for a,b in points]
    shadow=Image.new('RGBA',im.size);sd=ImageDraw.Draw(shadow)
    sd.polygon([(a+15,b+18) for a,b in xy(geo.MYOCARDIUM)],fill=(67,37,33,58))
    im.paste(shadow.filter(ImageFilter.GaussianBlur(22)),(0,0),shadow.filter(ImageFilter.GaussianBlur(22)))
    d=ImageDraw.Draw(im)
    def artery(path,width,border,base,highlight):
        pts=xy(path);w=max(3,round(width*scale))
        d.line(pts,fill=border,width=w+5,joint='curve')
        d.line(pts,fill=base,width=w,joint='curve')
        d.line([(a-1.6*scale,b-1.3*scale) for a,b in pts],fill=highlight,width=max(2,round(w*.24)),joint='curve')
    artery(geo.AORTA,33,'#8e4d50','#b65e62','#d38884')
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(xy(geo.MYOCARDIUM),fill=255)
    tones=Image.new('RGB',im.size,'#b76266');td=ImageDraw.Draw(tones)
    colors=((128,53,61),(158,77,83),(180,95,98),(200,119,117),(213,145,134),(225,160,147))
    for i,c in enumerate(colors):
        shrink=1-i*.12
        pts=[(318+(a-318)*shrink,322+(b-322)*shrink) for a,b in geo.MYOCARDIUM]
        td.polygon(xy(pts),fill=c)
    im.paste(tones.filter(ImageFilter.GaussianBlur(35)),(0,0),mask)
    d.line(xy(geo.MYOCARDIUM),fill='#ad6768',width=3,joint='curve')
    for path,width in [(geo.RCA,8),(geo.LEFT_MAIN,10),(geo.LAD,8),(geo.LCX,8),*[(p,4) for p in geo.RCA_TWIGS],*[(p,4) for p in geo.LEFT_TWIGS]]:
        artery(path,width,'#a45957','#e4967d','#f5c3a6')

def section(route,index):
    route_label='Wrist' if route=='radial' else 'Groin'
    if index==0:
        im,d=frame(route,'Coronary angiography','Episode 01'+('A' if route=='radial' else 'B'))
        panel(d,(68,283,914,924))
        write(d,115,343,f'{route_label} access',65,'title',DEEP)
        write(d,115,437,'How the care team sees the coronary arteries and uses the images to guide what happens next.',42,'body',INK,725)
        d.line((116,682,864,682),fill=LINE,width=2)
        write(d,115,730,'ACCESS  /  IMAGING  /  RECOVERY',24,'bold',DEEP)
        heart(im,1056,294,1.36)
        write(d,1077,908,'Coronary arteries on the surface of the heart',24,'body',MUTED)
    elif index==1:
        im,d=frame(route,'Why the test is done','Illustrated artery cross-section')
        panel(d,(68,302,1850,909))
        for cx,label,blocked in [(564,'Open channel',False),(1335,'Narrowed channel',True)]:
            cy=555
            d.ellipse((cx-146,cy-146,cx+146,cy+146),fill='#b96265',outline='#87464a',width=6)
            d.ellipse((cx-116,cy-116,cx+116,cy+116),fill='#f0a28d')
            d.ellipse((cx-94,cy-94,cx+94,cy+94),fill='#862e41')
            if blocked:
                from math import cos,sin,radians
                arc=[(cx+94*cos(radians(q)),cy+94*sin(radians(q))) for q in range(-87,94,3)]
                arc+= [(cx+30,cy+79),(cx+8,cy+48),(cx-8,cy+4),(cx+4,cy-44),(cx+34,cy-80)]
                d.polygon(arc,fill='#e7c07f')
                d.line((cx+25,cy+14,cx+165,cy+83,cx+253,cy+83),fill=DEEP,width=3)
                write(d,cx+164,cy+96,'Plaque',24,'bold',DEEP)
            d.text((cx,765),label,font=font(36,'bold'),fill=INK,anchor='mm')
        d.line((950,385,950,790),fill=LINE,width=2)
        write(d,117,841,'An angiogram shows where the open channel of an artery becomes narrower.',28,'body',MUTED)
    elif index==2:
        im,d=frame(route,'Preparing for the test','Before and during the test')
        panel(d,(68,305,1850,925))
        bullet(d,124,374,'01','Talk with the care team','Review medicines, kidney health and prior reactions to contrast.',1350)
        bullet(d,124,538,'02','Follow your instructions','Ask about food, drink and medicines before the test.',1350)
        bullet(d,124,702,'03','Monitoring in the cath lab','The team checks heart rhythm and blood pressure. Most people are awake.',1350)
    elif index==3:
        im,d=frame(route,'At home after an angiogram','Follow your own discharge instructions')
        panel(d,(68,303,1850,926))
        bullet(d,122,369,'01','Use the written plan','Follow your care team’s advice on your dressing, activity, medicines and follow-up.',1450)
        bullet(d,122,540,'02','Know what can be expected','A small bruise or mild soreness can happen.',1450)
        bullet(d,122,708,'03','Contact the care team promptly','Report increasing redness or pain, drainage or fever.',1450)
    elif index==4:
        im,d=frame(route,'When to get emergency help','After your angiogram')
        panel(d,(68,305,1850,932),'#fbf7f3')
        write(d,122,364,'Call local emergency services',48,'bold','#813b35')
        extremity='hand' if route=='radial' else 'foot'
        signs=(('01','Heavy bleeding or bleeding that continues despite firm pressure'),('02',f'Rapidly growing swelling or a newly cold or numb {extremity}'),('03','New chest pressure or sudden shortness of breath'))
        for i,(num,sign) in enumerate(signs):
            y=486+i*123
            d.rounded_rectangle((122,y,183,y+60),radius=16,fill='#f0ded8')
            d.text((153,y+29),num,font=font(22,'bold'),fill='#813b35',anchor='mm')
            write(d,210,y+10,sign,31,'bold',INK,1480)
    elif index==5:
        im,d=frame(route,'What the test tells you','Before you leave')
        panel(d,(68,304,1070,932))
        bullet(d,113,370,'01',f'The {route_label.lower()} gives the team a route to the heart','A catheter carries contrast to the coronary openings.',855)
        bullet(d,113,535,'02','The images show the arteries','The findings help guide the next decision.',855)
        bullet(d,113,698,'03','Ask what your images showed','Make sure you understand recovery and follow-up.',855)
        heart(im,1170,328,1.18)
    else:
        im,d=frame(route,'Clinical sources','Educational animation')
        panel(d,(68,304,1850,925))
        bullet(d,120,365,'01','American Heart Association','Coronary angiogram',1400)
        bullet(d,120,505,'02','Society for Cardiovascular Angiography & Interventions','Vascular access and diagnostic guidance',1400)
        bullet(d,120,645,'03','Guy’s and St Thomas’ NHS Foundation Trust','After a coronary angiogram',1400)
        d.line((120,801,1798,801),fill=LINE,width=2)
        write(d,120,842,'Anatomical illustrations and simulated angiograms. Follow the instructions from your own care team.',25,'body',MUTED,1625)
    return im

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for route,numbers in [('radial',[1,2,3,23,24,25,26]),('femoral',[1,2,3,28,29,30,31])]:
        for i,n in enumerate(numbers):
            section(route,i).save(OUT / f'{route[0].upper()}{n:02d}.png',optimize=True)
    sheet=Image.new('RGB',(1536,864),'#fff')
    for i,name in enumerate(('R01','R02','R03','R23','R24','F29','F30','F31')):
        img=Image.open(OUT / f'{name}.png').resize((384,216),Image.Resampling.LANCZOS)
        sheet.paste(img,((i%4)*384,(i//4)*216))
    sheet.crop((0,0,1536,432)).save(OUT/'editorial-visual-check.jpg',quality=93)

if __name__=='__main__':main()
