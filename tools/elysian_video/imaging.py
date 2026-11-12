"""Differentiate IVUS and OCT with original, timed vessel cross-sections."""
from math import sin, cos, pi
import json

import skia

from . import access, angiogram, restenosis, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

def slice_view(c,p,t,mode,*,stent=False,narrower=False,calcium=True,compare_sections=False):
    access.rect(c,0,0,1280,720,access.solid('#102c2b'))
    cx,cy=729,388
    lumen_radius = 124 if narrower else 168
    for radius,shade in ((236,'#593b48'),(220,'#a47878'),(190,'#774957'),(lumen_radius,'#181d27')):
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
            r=lumen_radius-5
            x,y=cx+r*cos(a),cy+r*sin(a)
            c.drawRoundRect(skia.Rect.MakeXYWH(x-5,y-4,11,8),2,2,access.solid('#e7d9bf'))
    if mode == 'OCT':
        # The same struts are visible only while the imaging field is clear.
        clearing = access.smooth((t - 10.15) / 4.35)
        c.drawCircle(cx, cy, lumen_radius+5, access.solid('#673949', round(255 * (1 - clearing))))
        if clearing < .999:
            field=skia.Path()
            field.addCircle(cx,cy,lumen_radius-2)
            c.save()
            c.clipPath(field,doAntiAlias=True)
            # Illustrative blood cells move past the imaging plane before the
            # field clears. The dots and beam carry no acquisition settings.
            for i in range(36):
                x=cx-184+(53*i+t*(64+11*(i%4)))%368
                y=cy-167+(i*89)%335+10*sin(t*1.7+i)
                w=19+5*(i%4)
                tone='#a46265' if i%3 else '#ad6b6e'
                c.drawOval(skia.Rect.MakeXYWH(x-w,y-9,w*2,18),
                           access.solid(tone,round(216*(1-clearing))))
            c.restore()
    # Sensor direction is an illustration of the modality, not a scan setting.
    angiogram.dot(c,cx,cy,22,'#a5c5bb')
    angle=t*4
    reach = 48 + 115 * clearing if mode == 'OCT' else lumen_radius - 1
    aperture = skia.Rect.MakeXYWH(cx - reach, cy - reach, 2 * reach, 2 * reach)
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
        x, y = cx + reach * cos(angle), cy + reach * sin(angle)
        access.line(c, [(cx, cy), (x, y)], '#f2d39c', 7)
        if clearing > .9:
            angiogram.dot(c,x,y,6,'#f7e2b9')
    angiogram.header(c,'A cross-section from inside the artery','ILLUSTRATED SCAN',True)
    if compare_sections:
        access.text(c,'Same stent, two sections',61,343,31,'#c6e8d7')
        access.text(c,'Narrower section' if narrower else 'Adjacent section',61,400,39,'#e8f6e7')
        access.line(c,[(86,464),(359,464)],'#527873',5)
        for x in (86,359):
            selected = (x==359) == narrower
            angiogram.dot(c,x,464,13 if selected else 8,'#e7d9bf' if selected else '#527873')
    else:
        access.text(c,{'IVUS':'IVUS: sound','OCT':'OCT: light','SCAN':'Conceptual slice'}[mode],
                    61,388,39,'#e8f6e7')
    if narrower:
        access.text(c,'A section remains narrower than intended',56,668,29,'#c6e8d7')
    elif calcium and mode=='IVUS':
        access.text(c,'Dense calcium can obscure the tissue behind it',56,668,29,'#c6e8d7')
    elif mode == 'OCT' and t < 10.15:
        access.text(c,'Near-infrared light shows fine surface detail',56,668,29,'#c6e8d7')
    elif mode == 'OCT' and t < 14.5:
        access.text(c,'Blood briefly clears from the imaging area',56,668,29,'#c6e8d7')
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

def decision_views(c,t):
    """Put the simulated angiogram and matching conceptual stent slice side by side."""
    access.rect(c,0,0,1280,720,access.solid('#e5eee7'))
    angiogram.header(c,'Two views help the team decide','INSIDE-ARTERY IMAGING')
    angiogram.block(c,55,170,561,440,24,access.solid('#1b3e37'))
    angiogram.block(c,664,170,561,440,24,access.solid('#163632'))
    access.text(c,'Simulated angiogram',83,223,34,'#e2f3e6')
    access.text(c,'Illustrated cross-section',692,223,34,'#e2f3e6')

    q=access.smooth((t-1.06)/5.52)*(1-access.smooth((t-13.5)/5.5))
    phase=(t%6.75)/6.75
    fill=access.smooth(phase/.42)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(79,248,592,541))
    c.translate(75,248)
    c.scale(.405,.405)
    c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kLinear))
    angiogram.contrast_paths(c,'left',fill,round(247-73*access.smooth((phase-.78)/.22)),-14,True)
    # The marker moves from an adjacent slice to the narrower part, then back.
    branch=angiogram.tree('left')[0][1][0]
    u,v=angiogram.project(branch[round((len(branch)-1)*(.35+.12*q))],-14)
    x,y=222+3.48*u,101+1.88*v
    edge=access.solid('#ffe6a9')
    edge.setStyle(skia.Paint.kStroke_Style)
    edge.setStrokeWidth(5)
    if fill>.55:
        c.drawCircle(x,y,29,edge)
    c.restore()
    access.text(c,'The contrast shows the artery’s path',82,580,28,'#cce6d7')

    cx,cy=944,390
    lumen=111-31*q
    for radius,tone in ((137,'#ba8d83'),(127,'#774957'),(lumen,'#1c2c32')):
        angiogram.dot(c,cx,cy,radius,tone)
    for i in range(18):
        a=i*2*pi/18
        x,y=cx+(lumen-4)*cos(a),cy+(lumen-4)*sin(a)
        c.drawRoundRect(skia.Rect.MakeXYWH(x-4,y-3,9,7),2,2,access.solid('#eddec4'))
    scan=skia.Path()
    scan.moveTo(cx,cy)
    scan.arcTo(skia.Rect.MakeXYWH(cx-lumen,cy-lumen,2*lumen,2*lumen),t*92,42,False)
    scan.close()
    c.drawPath(scan,access.solid('#b8dfcb',92))
    angiogram.dot(c,cx,cy,11,'#b9dfcb')
    access.text(c,'Narrower section' if q>.65 else 'Adjacent section',691,580,28,'#cce6d7')
    note=('The patient’s condition, artery anatomy and goals all matter.' if t>=14.53 else
          'In complex cases, imaging can guide treatment.' if t>=5.05 else
          'The cross-section adds detail that the angiogram alone cannot show.')
    access.text(c,note,55,677,30,'#22594e')


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
        slice_view(c,p,t,'OCT',stent=True,calcium=False)
        return
    if ident=='P05':
        sweep(c,p,t)
        return
    if ident=='P06':
        slice_view(c,p,t,'SCAN',stent=True,narrower=t>=7.77,calcium=False,compare_sections=True)
        return
    if ident=='P07':
        decision_views(c,t)
        return
    angiogram.clinical_credits(c,'INSIDE-ARTERY IMAGING',(
        'ACC, AHA and partner societies · Acute coronary syndromes',
        'EAPCI · Expert consensus on intracoronary imaging',
        'SCAI · Expert consensus on calcified coronary lesions'),
        'Calcified arteries and complex PCI')

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
