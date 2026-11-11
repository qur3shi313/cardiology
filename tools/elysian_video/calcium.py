"""Illustrate distinct calcium preparation mechanisms without procedure settings."""
from math import exp, sin, cos, pi
import json

import skia

from . import access, angiogram, coating, imaging, restenosis, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

TEXT={
 'P01':('Why hard calcium matters','A stiff section can limit stent expansion'),
 'P03':('Why preparation may help','The team chooses how to prepare the narrowing'),
 'P04':('A specialised balloon','Scoring elements concentrate force against plaque'),
 'P05':('Intravascular lithotripsy','Pressure waves can fracture calcium in selected lesions'),
 'P06':('Atherectomy is another option','A rotating element can modify hard plaque'),
 'P07':('Checking the treated section','The team checks expansion and downstream flow'),
}

def calcified(c,ident,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e8f1e9'))
    after=ident=='P07'
    expansion=1 if after else .19
    lumen=art.artery(c,expansion)
    s=art.Motion(1126,-280,12,-280,14,expansion,1)
    art.blood_flow(c,t,s,lumen)
    x0=art.LESION
    if not after:
        xs=range(x0-154,x0+155,4)
        high=[(x,art.center(x)-113) for x in xs]
        low=[(x,art.center(x)-113+61*exp(-abs((x-x0)/111)**2.7)) for x in xs]
        c.drawPath(art.enclosed(high,low),art.gradient(505,245,775,339,['#f0d8a7','#a0805c']))
    if ident in ('P01','P03','P07'):
        opened=access.smooth(p/.45)
        rad=lambda x:16+opened*(100-(65*exp(-abs((x-x0)/100)**2.6) if not after else 0))
        art.stent(c,x0,rad,False)
        if p<.62:
            art.wire(c,1126)
        art.stent(c,x0,rad,True)
    elif ident in ('P04','P05'):
        r=13+70*access.smooth((p-.18)/.47)
        art.wire(c,1126)
        art.balloon(c,x0,r)
        if ident=='P04':
            # Conceptual scoring element on the specialty balloon's exterior.
            x1,x2=x0-151,x0+151
            a=[(x,art.center(x)-r) for x in range(x1,x2+1,5)]
            art.line(c,a,'#e8dcbd',5.5)
            art.line(c,a,'#fff1cd',2.2)
        elif p>.45:
            # The waves are symbolic. No energy, pulse number or settings shown.
            for i in range(4):
                rr=29+((t*54+i*24)%85)
                q=access.solid('#d5ead7',round(156*(1-(rr-29)/85)))
                q.setStyle(skia.Paint.kStroke_Style); q.setStrokeWidth(3.3)
                c.drawCircle(x0,art.center(x0),rr,q)
            if p>.61:
                for i in (-1,0,1):
                    x=x0+i*51
                    y=art.center(x)-107
                    art.line(c,[(x,y),(x-8,y+17),(x+8,y+32),(x+2,y+41)],'#635442',3.4)
    elif ident=='P06':
        art.wire(c,1126)
        x=364+(x0-333)*access.smooth((p-.21)/.65)
        y=art.center(x)-7
        art.line(c,[(0,art.center(0)),(x-39,y)],'#69968d',8.5)
        c.drawOval(skia.Rect.MakeXYWH(x-37,y-22,74,44),access.solid('#c7bca1'))
        for i in range(6):
            q=(i/6+t*3)%1
            dx=26*sin(q*2*pi)
            access.line(c,[(x+dx-3,y-16),(x+dx+3,y+16)],'#898578',2.8)
        c.drawOval(skia.Rect.MakeXYWH(x-27,y-17,23,10),access.solid('#e6dac0',145))
    title,detail=TEXT[ident]
    angiogram.header(c,title,'CALCIFIED ARTERY')
    access.text(c,detail,56,675,31,'#245b4e')

def draw(c,ident,p,t):
    if ident=='P02':
        if p<.45:
            angiogram.imaging(c,'P29',p/.45,t,0)
        else:
            imaging.slice_view(c,(p-.45)/.55,t,'IVUS',calcium=True)
    elif ident=='P07' and p>.65:
        coating.summary(c,'P06',.55+.45*(p-.65)/.35,t)
    elif ident=='P08':
        restenosis.card(c,'Clinical sources','Calcified coronary lesions',
                        ('SCAI expert consensus','ACC, AHA and SCAI guidance'),'list',p,t)
    else:
        calcified(c,ident,p,t)

def render():
    ep=SERIES/'episode-13'
    visual=ep/'visuals'; visual.mkdir(exist_ok=True)
    timeline=json.loads((ep/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-calcium-film.mp4'
        tmp=visual/f'{ident}-calcium-film.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'calcium-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
