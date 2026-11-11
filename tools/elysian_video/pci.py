"""The narrated PCI episode's connected guidewire, balloon, and stent scenes."""
import json

import skia

from .__main__ import ROOT, SERIES, FPS
from .access import HEADING, LOGO
from .encode import encode_scene
from . import stent as art

TITLE = {
    'P05': ('The guidewire crosses first', 'The wire stays beyond the narrowing'),
    'P06': ('A separate balloon prepares the artery', 'Preparation depends on the narrowing'),
    'P07': ('The first balloon comes out', 'The guidewire remains in place'),
    'P08': ('The stent arrives on a folded balloon', 'The mesh and balloon travel together'),
    'P09': ('The balloon opens the stent', 'The expanded mesh stays in the artery'),
    'P10': ('A drug-eluting coating releases medicine', 'The mesh supports the treated section'),
}

def state(ident,p):
    lesion=art.LESION
    e=art.ease
    wire=1126
    delivery=-280
    delivery_r=12
    mesh=-280
    mesh_r=14
    lumen=0
    flow=1.
    if ident=='P05':
        wire=80+1046*e(p,.17,.70)
    elif ident=='P06':
        delivery=-280+(lesion+280)*e(p,.24,.56)
        x=e(p,.61,.93)
        delivery_r=12+75*x
        lumen=.49*x
        flow=1-.80*x
    elif ident=='P07':
        x=e(p,.04,.24)
        delivery_r=87-75*x
        delivery=lesion-(lesion+280)*e(p,.28,.59)
        lumen=.49-.13*x
        flow=.20+.80*x
    elif ident=='P08':
        delivery=-280+(lesion+280)*e(p,.30,.86)
        mesh=delivery
        lumen=.36
    elif ident=='P09':
        x=e(p,.02,.35)
        collapsed=e(p,.58,.75)
        delivery=lesion-(lesion+280)*e(p,.77,.97)
        delivery_r=12+104*x*(1-collapsed)
        mesh,mesh_r=lesion,14+102*x
        lumen=.36+.64*x
        flow=1-.93*x*(1-collapsed)
    elif ident=='P10':
        lumen=1
        mesh,mesh_r=lesion,116
    return art.Motion(wire,delivery,delivery_r,mesh,mesh_r,lumen,flow)

def draw(c,ident,p,t):
    s=state(ident,p)
    c.drawRect(skia.Rect.MakeWH(1280,720),
               art.gradient(0,0,1280,720,['#f9faf3','#e2eee5','#d5e4dc'],[0,.6,1]))
    lumen=art.artery(c,s.expansion)
    art.blood_flow(c,t,s,lumen)
    has_mesh=s.stent_x+art.MESH_HALF>art.X0
    if has_mesh: art.stent(c,s.stent_x,s.stent_radius,False)
    art.wire(c,s.wire_tip)
    if s.delivery_x+art.BALLOON_HALF>art.X0:
        art.balloon(c,s.delivery_x,s.delivery_radius)
    if has_mesh: art.stent(c,s.stent_x,s.stent_radius,True)
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(49,22,57,57),skia.SamplingOptions(skia.FilterMode.kLinear))
    art.text(c,'Elysian Biomedical LLP',122,60,33,'#23574c')
    title,detail=TITLE[ident]
    art.text(c,title,49,134,48,'#123b33',HEADING)
    art.text(c,detail,49,688,33,'#163f36')
    if ident=='P05' and p>.64:
        art.marker(c,915,255,(s.wire_tip,art.center(s.wire_tip)),'Parked wire tip')
    elif ident=='P08' and p>.70:
        x=s.stent_x+100
        art.marker(c,721,254,(x,art.center(x)-s.stent_radius),'Mounted stent')
    elif ident=='P09' and p>.79:
        x=s.stent_x+100
        art.marker(c,721,218,(x,art.center(x)-s.stent_radius),'Stent stays')
    elif ident=='P10':
        # Conceptual transfer into the nearby wall, without dose or time claims.
        for i in range(14):
            phase=(p*3+i*.123)%1
            x=art.LESION-130+(i*39)%264
            y=art.center(x)-116-phase*18
            c.drawCircle(x,y,3.8,art.paint('#f4dc9c',round(185*(1-phase))))

def render():
    episode=SERIES/'episode-06'
    visual=episode/'visuals'
    visual.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    overrides={}
    for scene in timeline['scenes']:
        ident=scene['id']
        if ident not in TITLE: continue
        n=scene['end_frame']-scene['start_frame']
        final=visual/f'{ident}-coronary-cutaway.mp4'
        temporary=visual/f'{ident}-coronary-cutaway.part.mp4'
        if not final.is_file():
            encode_scene(temporary,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            temporary.replace(final)
        overrides[ident]={'path':final.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                          'reference_only':False,'native_composition':True}
        (visual/'clinical-overrides.json').write_text(json.dumps(overrides,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
