"""Differentiate IVUS and OCT with original, timed vessel cross-sections."""
from math import sin, cos, pi
import json

import skia

from . import access, angiogram, restenosis, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

def slice_view(c,p,t,mode,*,stent=False,waist=False,calcium=True):
    access.rect(c,0,0,1280,720,access.solid('#102c2b'))
    cx,cy=729,388
    for radius,shade in ((236,'#593b48'),(220,'#a47878'),(190,'#774957'),(168,'#181d27')):
        angiogram.dot(c,cx,cy,radius,shade)
    if calcium:
        x,y=cx-104,cy-110
        c.drawOval(skia.Rect.MakeXYWH(x-50,y-32,100,64),access.solid('#e1c69a'))
        if mode=='IVUS':
            # A sector beyond the bright calcium is obscured, not absent.
            c.drawPath(access.path([(x-51,y-23),(x+12,y-34),(cx-98,cy-234),
                                     (cx-184,cy-159)],True),access.solid('#151c24',238))
    if stent:
        for i in range(20):
            a=i*2*pi/20
            r=147 if not waist else 117+23*sin(a)
            x,y=cx+r*cos(a),cy+r*sin(a)
            c.drawRoundRect(skia.Rect.MakeXYWH(x-5,y-4,11,8),2,2,access.solid('#e7d9bf'))
    # Sensor direction is an illustration of the modality, not a scan setting.
    angiogram.dot(c,cx,cy,22,'#a5c5bb')
    angle=t*4
    aperture=skia.Rect.MakeXYWH(cx-167,cy-167,334,334)
    sweep=skia.Path()
    sweep.moveTo(cx,cy)
    sweep.arcTo(aperture,angle*180/pi-58,58,False)
    sweep.close()
    c.drawPath(sweep,access.solid('#f2d39c' if mode=='OCT' else '#9dcfd1',95))
    if mode=='IVUS':
        for j in range(3):
            r=27+(t*55+j*47)%134
            pen=access.solid('#9dcfd1',round(165*(1-(r-27)/134)))
            pen.setStyle(skia.Paint.kStroke_Style); pen.setStrokeWidth(3)
            c.drawCircle(cx,cy,r,pen)
    elif mode=='OCT':
        access.line(c,[(cx,cy),(cx+163*cos(angle),cy+163*sin(angle))],'#f2d39c',7)
        x,y=cx+163*cos(angle),cy+163*sin(angle)
        angiogram.dot(c,x,y,6,'#f7e2b9')
    angiogram.header(c,'A cross-section from inside the artery','ILLUSTRATED SCAN',True)
    access.text(c,{'IVUS':'IVUS: sound','OCT':'OCT: light','SCAN':'Conceptual slice'}[mode],
                61,388,39,'#e8f6e7')
    if waist:
        access.text(c,'A section remains narrower than intended',56,668,29,'#c6e8d7')
    elif calcium and mode=='IVUS':
        access.text(c,'Dense calcium can obscure the tissue behind it',56,668,29,'#c6e8d7')
    elif stent:
        access.text(c,'The scan can show individual stent struts',56,668,29,'#c6e8d7')
    else:
        access.text(c,'Vessel wall and open channel',56,668,29,'#c6e8d7')

def sweep(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e5eee7'))
    s=art.Motion(1126,-290,12,-290,12,.16,1)
    lumen=art.artery(c,.16)
    art.blood_flow(c,t,s,lumen)
    restenosis.trace_channel(c,t,lumen,.16)
    art.wire(c,1126)
    x=360+(870-360)*access.smooth((p-.18)/.66)
    y=art.center(x)
    access.line(c,[(x,y-107),(x,y+106)],'#adddd0',8)
    c.drawRoundRect(skia.Rect.MakeXYWH(x-18,y-11,36,22),6,6,access.solid('#558e82'))
    angiogram.header(c,'Planning treatment from a series of slices','INSIDE-ARTERY IMAGING')
    access.text(c,'Study the segment length, wall and calcium',57,673,31,'#265e52')

def draw(c,ident,p,t):
    if ident in ('P01','P02'):
        split=.34 if ident=='P01' else .52
        if p<split:
            angiogram.imaging(c,'P25',p/split,t,0)
        else:
            slice_view(c,(p-split)/(1-split),t,'SCAN',calcium=ident=='P02')
        return
    if ident=='P03':
        slice_view(c,p,t,'IVUS',calcium=p>.33)
        return
    if ident=='P04':
        slice_view(c,p,t,'OCT',stent=p>.64,calcium=False)
        return
    if ident=='P05':
        sweep(c,p,t)
        return
    if ident=='P06':
        slice_view(c,p,t,'SCAN',stent=True,waist=p>.38,calcium=False)
        return
    if ident=='P07':
        restenosis.card(c,'When imaging adds useful detail','One more view for a decision',
                        ('The team matches the findings to','the anatomy and clinical situation'),'check',p,t)
        return
    restenosis.card(c,'Clinical sources','Inside-artery imaging',
                    ('ACC, AHA and SCAI guidance','EAPCI expert consensus'),'list',p,t)

def render():
    ep=SERIES/'episode-12'
    visual=ep/'visuals'; visual.mkdir(exist_ok=True)
    timeline=json.loads((ep/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-inside-imaging.mp4'
        tmp=visual/f'{ident}-inside-imaging.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'inside-imaging-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
