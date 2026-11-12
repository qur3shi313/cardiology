"""Recovery and medicines scenes for the finished post-PCI episode."""
from math import sin, cos
import json

import skia

from . import access, angiogram, restenosis
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

CARDS={
    'P02':('What staff check in recovery',(
        ('Access site and circulation',('Staff check for bleeding and','look at the hand or foot used'),'band'),
        ('Pulse and blood pressure',('Timing depends on your situation',),'pulse'))),
    'P04':('Ask before changing medicines',(
        ('Talk to your care team',('Tell them about bleeding, side effects,','and any planned procedures'),'call'),
        ('Keep a current medicine list',('Follow the prescription you received',),'list'))),
    'P05':('Activity and the wound at home',(
        ('Check the written instructions',('Ask about the dressing and activity',),'band'),
        ('Instructions are individual',('Confirm when driving, lifting or work','can safely resume'),'list'))),
    'P06':('When to get emergency help',(
        ('Chest symptoms or breathing trouble',('Get emergency help for severe symptoms',),'pulse'),
        ('Persistent bleeding or a cold limb',('Get emergency help for serious changes',),'call'))),
    'P07':('Rehabilitation and follow-up',(
        ('Discuss your recovery plan',('Follow-up reviews symptoms and medicines',),'check'),
        ('Cardiac rehabilitation',('Ask how to join if it is recommended',),'pulse'))),
    'P08':('What to take home',(
        ('The result',('Ask what was treated',),'check'),
        ('Medicines and recovery',('Keep your written instructions',),'list'),
        ('Who to contact',('Know who to call if you need help',),'call'))),
    'P09':('Clinical sources',(
        ('Patient recovery guidance',('NHS coronary angioplasty recovery','AHA patient information'),'list'),
        ('Clinical practice',('ACC, AHA and SCAI guidelines',),'check'))),
}

def platelet_view(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e6f0e8'))
    angiogram.block(c,73,235,1125,330,102,access.solid('#863b4e'))
    angiogram.block(c,91,270,1089,260,84,access.solid('#602b40'))
    # Conceptual illustration. Platelets travel in the open channel.
    # Show the relative tendency to gather, never imply zero clot risk.
    relaxed=p>.58
    for i in range(22):
        x=115+((i*71+t*52)%1021)
        y=312+(i*53)%169
        q=(.62 if not relaxed else .12)*max(0,1-abs(x-785)/275)
        x=(1-q)*x+q*(775+36*sin(i))
        y=(1-q)*y+q*(425+34*cos(i))
        c.drawOval(skia.Rect.MakeXYWH(x-10,y-7,20,14),access.solid('#edc38e',223))
        c.drawOval(skia.Rect.MakeXYWH(x-5,y-4,8,5),access.solid('#f7d9ac',189))
    angiogram.header(c,'The medicine plan after a stent','RECOVERY AFTER PCI')
    access.text(c,'Platelets are less likely to clump with antiplatelet medicines',
                54,674,29,'#234f46')

def draw(c,ident,p,t):
    if ident=='P01':
        restenosis.lumen_view(c,t,'open')
        angiogram.header(c,'The stent stays inside the artery','RECOVERY AFTER PCI')
        access.text(c,'What happens after the procedure?',56,674,31,'#235d51')
        return
    if ident=='P03':
        platelet_view(c,p,t)
        return
    title,steps=CARDS[ident]
    i=min(len(steps)-1,int(p*len(steps)))
    sub,lines,icon=steps[i]
    restenosis.card(c,title,sub,lines,icon,p*len(steps)-i,t)

def render():
    episode=SERIES/'episode-10'
    visuals=episode/'visuals'
    visuals.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visuals/f'{ident}-pci-recovery.mp4'
        tmp=visuals/f'{ident}-pci-recovery.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visuals/'post-pci-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
