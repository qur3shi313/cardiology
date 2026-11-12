"""Illustrate distinct calcium preparation mechanisms without procedure settings."""
from math import exp, sin, cos, pi
import json

import skia

from . import access, angiogram, imaging, restenosis, stent as art
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


def balloon_expanded_stent(c, ident, p, x0, after):
    # P03 rewinds to pre-treatment anatomy before the delivery system leaves.
    rewind = ident == 'P03'
    progress = p / .45 if rewind else p
    opening = access.smooth(progress / (.68 if rewind else .45))
    deflation = 0 if rewind else access.smooth((progress-.52)/.17)
    withdrawal = 0 if rewind else access.smooth((progress-.70)/.28)

    def mesh_radius(at):
        waist = 0 if after else 65*exp(-abs((at-x0)/100)**2.6)
        return 16 + opening*(art.OPEN_RADIUS-16-waist)

    def balloon_radius(at):
        # The balloon opens just inside the mesh. Collapsing it leaves the
        # expanded mesh at the treated section while the shaft withdraws.
        return 12 + (mesh_radius(at)-14)*(1-deflation)

    art.stent(c, x0, mesh_radius, False)
    art.wire(c, 1126)
    if withdrawal < .999:
        delivery_x = x0-(x0+art.BALLOON_HALF-art.X0+22)*withdrawal
        art.balloon(c, delivery_x, balloon_radius)
    art.stent(c, x0, mesh_radius, True)


def calcified(c,ident,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e8f1e9'))
    after=ident=='P07'
    expansion=1 if after else .19
    lumen=art.artery(c,expansion)
    s=art.Motion(1126,-280,12,-280,14,expansion,1)
    art.blood_flow(c,t,s,lumen)
    restenosis.trace_channel(c,t,lumen,expansion)
    x0=art.LESION
    if not after:
        xs=range(x0-154,x0+155,4)
        high=[(x,art.center(x)-113) for x in xs]
        low=[(x,art.center(x)-113+61*exp(-abs((x-x0)/111)**2.7)) for x in xs]
        c.drawPath(art.enclosed(high,low),art.gradient(505,245,775,339,['#f0d8a7','#a0805c']))
    if ident in ('P01','P07') or (ident == 'P03' and p < .45):
        balloon_expanded_stent(c, ident, p, x0, after)
    elif ident in ('P03','P04','P05'):
        progress = (p - .45) / .55 if ident == 'P03' else p
        r=13+70*access.smooth((progress-.12)/.52)
        def vessel_limited_radius(at):
            return min(r, art.lumen_radius(at, -1, expansion) - 4)
        art.wire(c,1126)
        art.balloon(c,x0,vessel_limited_radius)
        if ident=='P04':
            # Conceptual scoring element on the specialty balloon's exterior.
            x1,x2=x0-151,x0+151
            a=[(x,art.center(x)-art.balloon_profile(x,x0,vessel_limited_radius))
               for x in range(x1,x2+1,5)]
            art.line(c,a,'#e8dcbd',5.5)
            art.line(c,a,'#fff1cd',2.2)
        elif ident=='P05' and p>.45:
            # The waves are symbolic. No energy, pulse number or settings shown.
            for i in range(4):
                rr=29+((t*54+i*24)%85)
                q=access.solid('#d5ead7',round(156*(1-(rr-29)/85)))
                q.setStyle(skia.Paint.kStroke_Style); q.setStrokeWidth(7)
                c.drawCircle(x0,art.center(x0),rr,q)
            if p>.61:
                for i in (-1,0,1):
                    x=x0+i*51
                    y=art.center(x)-107
                    art.line(c,[(x,y),(x-8,y+17),(x+8,y+32),(x+2,y+41)],'#635442',3.4)
    elif ident=='P06':
        approach=access.smooth((p-.21)/.65)
        x=364+(x0-364)*approach
        def centerline(at):
            return art.center(at)-30*approach*exp(-abs((at-x0)/120)**2.6)
        y=centerline(x)
        wire=[(at,centerline(at)) for at in range(art.X0,1127,5)]
        shaft=[(at,centerline(at)) for at in range(art.X0,round(x-34)+1,5)]
        art.line(c,wire,'#331c29',6.6)
        art.line(c,wire,'#efd5a0',3.9)
        art.line(c,shaft+[(x-34,centerline(x-34))],'#69968d',8.5)
        c.drawOval(skia.Rect.MakeXYWH(x-37,y-22,74,44),access.solid('#c7bca1'))
        for i in range(6):
            q=(i/6+t*3)%1
            dx=26*sin(q*2*pi)
            access.line(c,[(x+dx-3,y-16),(x+dx+3,y+16)],'#898578',2.8)
        c.drawOval(skia.Rect.MakeXYWH(x-27,y-17,23,10),access.solid('#e6dac0',145))
        if approach>.99:
            access.line(c,[(x,y-22),(x+121,261),(x+251,261)],'#fff1cd',3)
            access.text(c,'Contact with calcium',x+127,247,28,'#fff1cd')
    title,detail=TEXT[ident]
    if ident == 'P03' and p >= .45:
        title,detail='Preparing the narrowing before a stent','The stiff section limits how far the balloon opens'
    angiogram.header(c,title,'CALCIFIED ARTERY')
    access.text(c,detail,56,675,31,'#245b4e')

def checked_result(c,p,t):
    if t<4.62:
        calcified(c,'P07',min(1,t/4.62),t)
        return
    if 9.3<=t<13.47:
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0,0,1280,638))
        imaging.slice_view(c,p,t,'SCAN',stent=True,calcium=False)
        c.restore()
        access.rect(c,0,638,1280,82,access.solid('#102c2b'))
        access.text(c,'The scan can show expansion and wall contact',56,674,31,'#c6e8d7')
        return
    local=t-4.62 if t<9.3 else (t-13.47)*.72
    c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    head=access.smooth(local/2.42)
    spot=angiogram.contrast_paths(c,'left',head,round(245-38*access.smooth((local-3)/1.7)),-13,False)
    if head>.54:
        x,y=spot
        edge=access.solid('#f5d78f',235)
        edge.setStyle(skia.Paint.kStroke_Style)
        edge.setStrokeWidth(3.5)
        c.drawCircle(x,y,22,edge)
    angiogram.header(c,'Checking flow beyond the treated section','SIMULATED X-RAY',True)
    access.text(c,'The angiogram shows where contrast travels',56,683,31,'#e1f0e7')


def draw(c,ident,p,t):
    if ident=='P02':
        if p<.45:
            angiogram.imaging(c,'P29',p/.45,t,0)
        else:
            imaging.slice_view(c,(p-.45)/.55,t,'IVUS',calcium=True)
    elif ident=='P07':
        checked_result(c,p,t)
    elif ident=='P08':
        angiogram.clinical_credits(c,'CALCIFIED ARTERY',(
            'SCAI · Expert consensus on calcified coronary lesions',
            'ACC, AHA and partner societies · Acute coronary syndromes'),
            'Heart attack and emergency PCI')
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
