"""Native angiogram imaging and editorial scenes, keyed to episode 01 narration."""
from bisect import bisect_right
from functools import lru_cache
from math import cos, sin, pi, radians, hypot
import importlib.util
import json
from random import Random

import skia

from .__main__ import ROOT, SERIES, LEGACY_FFMPEG, FPS, WIDTH, HEIGHT
from .access import color, solid, grad, path, line, text, rect, HEADING, BOLD, REGULAR, LOGO, smooth
from .encode import encode_scene

LEGACY = ROOT/'outputs/cardiology-series/episode-01/production/vascular_art.py'
art_spec=importlib.util.spec_from_file_location('angiography_anatomy',LEGACY)
art=importlib.util.module_from_spec(art_spec)
art_spec.loader.exec_module(art)

def block(c,x,y,w,h,r,brush):
    c.drawRoundRect(skia.Rect.MakeXYWH(x,y,w,h),r,r,brush)

def dot(c,x,y,r,fill,alpha=255):
    c.drawCircle(x,y,r,solid(fill,alpha))

def header(c,title,tag='CORONARY ANGIOGRAPHY', dark=False):
    tone,sub=('#effbf4','#b1d6c7') if dark else ('#123e35','#276b5a')
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(55,27,44,44),skia.SamplingOptions(skia.FilterMode.kLinear))
    text(c,'Elysian Biomedical LLP',115,57,24,sub)
    text(c,tag,878,57,24,sub)
    text(c,title,55,132,48,tone,HEADING)

def stroke_var(c,pts,weights,shade,opacity):
    for (a,b),w in zip(zip(pts,pts[1:]),weights):
        line(c,[a,b],shade,w,opacity)

@lru_cache(maxsize=4)
def tree(side):
    out=[]
    for points,thickness in (art.ANGIO_LEFT if side=='left' else art.ANGIO_RIGHT):
        lengths=[0.]
        for a,b in zip(points,points[1:]):
            lengths.append(lengths[-1]+hypot(b[0]-a[0],b[1]-a[1]))
        entry=0.
        if out:
            x,y=points[0]
            _,entry=min((hypot(x-u,y-v),begin+local)
                        for parent, distances, begin, _ in out
                        for (u,v),local in zip(parent,distances))
        out.append((points,lengths,entry,thickness))
    return out,max(origin+lengths[-1] for _,lengths,origin,_ in out)

def project(pt,angle):
    x,y=pt
    q=radians(angle)
    depth=22*sin(y/60)+(x-108)*.17
    return (x-128)*cos(q)+depth*sin(q)+128,y+.20*depth*sin(q)

def contrast_paths(c,side,fill,alpha,angle,narrow):
    branches,max_distance=tree(side)
    head=fill*max_distance
    def xy(pt):
        u,v=project(pt,angle)
        return (222+3.48*u,101+1.88*v)
    for k,(points,lengths,entry,thickness) in enumerate(branches):
        visible=min(lengths[-1],head-entry)
        if visible<=0: continue
        j=max(1,bisect_right(lengths,visible)-1)
        segment=list(points[:j+1])
        if j<len(points)-1 and visible>lengths[j]:
            a,b=points[j:j+2]
            f=(visible-lengths[j])/(lengths[j+1]-lengths[j])
            segment.append((a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f))
        weights=[]
        for i in range(len(segment)-1):
            u=i/(len(points)-1)
            width=(thickness*2.18)*(1-.49*u)
            if narrow and k==1:
                width*=1-.76*max(0,1-abs(u-.47)/.10)
            weights.append(max(2.4,width))
        at=[xy(pt) for pt in segment]
        stroke_var(c,at,[w+4.1 for w in weights],'#505856',int(alpha*.6))
        stroke_var(c,at,weights,'#18201f',alpha)
    a=xy(branches[0][0][0])
    guide=[(a[0]-150,146),(a[0]-91,144),(a[0]-40,a[1]-23),a]
    line(c,guide,'#344444',7)
    line(c,guide,'#687470',2)
    return xy(branches[1][0][round((len(branches[1][0])-1)*.47)])

GRAIN=[(r.randrange(123,1157),r.randrange(129,664),r.choice([1,1.5,2]),r.randrange(8,26))
       for r in [Random(721)] for _ in range(1060)]

def draw_radiograph(c):
    rect(c,0,0,1280,720,grad(0,0,1210,720,['#102323','#1b3432','#0b1e20']))
    c.drawOval(skia.Rect.MakeXYWH(106,148,1068,508),
               grad(0,161,1280,690,['#2b3938','#a1aeaa','#798785','#394c49'],[0,.26,.69,1]))
    block(c,103,150,1074,504,64,grad(270,148,1070,670,['#99a5a0','#cad0c8','#9aa6a1','#5c736f']))
    c.drawOval(skia.Rect.MakeXYWH(394,191,506,402),solid('#dce2d7',112))
    for i in range(7):
        x=194+i*17
        y=174+i*62
        line(c,[(x,y+41),(378,y+9),(619,y),(851,y+16),(1093,y+62)],'#dce2d8',11,44)
    for x,y,r,a in GRAIN:
        dot(c,x,y,r,'#38423d',a)
    line(c,[(110,647),(1170,647)],'#b1cec1',2,135)

@lru_cache(maxsize=1)
def radiograph_plate():
    surface=skia.Surface(WIDTH,HEIGHT)
    canvas=surface.getCanvas()
    canvas.scale(2,2)
    draw_radiograph(canvas)
    return surface.makeImageSnapshot()

IMAGING={'P01':('left','Coronary angiogram'), 'P25':('left','The left coronary arteries'),
         'P28':('right','The right coronary artery'), 'P29':('left','What a narrowing looks like')}

def imaging(c,ident,p,t,duration):
    side,title=IMAGING[ident]
    c.drawImageRect(radiograph_plate(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    if ident=='P01':
        q=smooth(p/.31)
        tip=contrast_paths(c,side,q,244,4,True)
        if t>=5:
            header(c,title,'SIMULATED X-RAY',True)
            block(c,54,589,283,46,12,solid('#1a3934',231))
            text(c,'Wrist or groin access',68,621,24,'#e7f2eb')
        else:
            text(c,'SIMULATED CORONARY X-RAY',56,64,25,'#e1f0e8')
    elif ident=='P29':
        spot=contrast_paths(c,side,smooth(p/.24),242,-13,True)
        if p>.32:
            x,y=spot
            r=23+1.2*cos(p*8*pi)
            edge=solid('#ffe6aa',232); edge.setStyle(skia.Paint.kStroke_Style); edge.setStrokeWidth(3.6)
            c.drawCircle(x,y,r,edge)
            line(c,[(x+r,y-12),(x+111,y-52),(x+233,y-52)],'#ffe6aa',3)
            text(c,'Narrowing',x+125,y-64,29,'#fff1cf')
        header(c,title,'SIMULATED X-RAY',True)
    else:
        # Separate injections at the selected ostium. Keep the image projection
        # still during each injection; show the new projection on the next run.
        if p<.50:
            w=(p/.5); angle=-19 if side=='right' else 7
        else:
            w=(p-.5)/.5; angle=26 if side=='right' else -14
        fill=smooth((w-.03)/.47)
        opacity=round(245*(1-smooth((w-.78)/.21)))
        contrast_paths(c,side,fill,opacity,angle,False)
        header(c,title,'SIMULATED X-RAY',True)
        block(c,54,587,294,49,11,solid('#132d2a',229))
        text(c,('First projection' if p<.50 else 'Second projection'),70,620,26,'#e6f3e9')

CARDS={
    'P02':('Why an angiogram is done',(
        ('Open artery','Blood travels through the channel','open'),
        ('Narrowed artery','Plaque can reduce the opening','narrow'),
        ('Planned or urgent','Symptoms and other tests guide timing','pulse'))),
    'P03':('Preparing for the test',(
        ('Review your medicines','Mention previous contrast reactions','medicine'),
        ('Check kidney health','The team reviews the results','check'),
        ('Follow your instructions','Food, drink and medicines','list'))),
    'P30':('What the results can lead to',(
        ('Medicines','Manage symptoms and reduce risk','medicine'),
        ('Further tests','Clarify the meaning of a narrowing','check'),
        ('Angioplasty','A balloon may widen the artery','balloon'),
        ('Bypass surgery','An option the team may discuss','vessel'))),
    'P37':('Observation and discharge',(
        ('Same-day discharge','Possible after an uncomplicated test','clock'),
        ('Longer observation','Some people need more checks','pulse'))),
    'P38':('At home after an angiogram',(
        ('Follow your written plan','Dressing, activity, medicines, follow-up','list'),
        ('What you may notice','A small bruise or mild soreness','band'),
        ('Contact your care team','Increasing pain, redness, drainage or fever','call'))),
    'P39':('When to get emergency help',(
        ('Heavy or persistent bleeding','Call local emergency services','band'),
        ('Growing swelling or a cold hand','Call local emergency services','call'),
        ('Chest pressure or breathlessness','Call local emergency services','pulse'))),
    'P40':('Know your result and recovery plan',(
        ('Clinical sources','AHA  •  SCAI  •  Guy’s and St Thomas’ NHS','check'),)),
}
# These transitions correspond to complete clauses in the selected Alexander
# narration. The surrounding scene time comes from the frame-locked manifest.
MARKS={'P02':(.0,.29,.59),'P03':(.0,.40,.64),'P30':(.0,.35,.49,.73),
       'P37':(.0,.65),'P38':(.0,.42,.67),'P39':(.0,.40,.73),'P40':(.0,)}

def icon(c,kind,p,t):
    cx,cy=929,380
    q=smooth(p/.45)
    base=grad(726,209,1133,565,['#143c36','#0d2728','#071e21'])
    block(c,683,190,505,406,42,base)
    if kind in ('open','narrow'):
        for radius,sh in ((141,'#723641'),(126,'#c77270'),(108,'#e5a38c'),(91,'#572637')):
            c.drawCircle(cx,cy,radius,solid(sh))
        if kind=='narrow':
            c.drawPath(path([(cx-77,cy-51),(cx-23,cy-85),(cx-11,cy-37),(cx-15,cy+7),
                             (cx+1,cy+52),(cx-31,cy+85),(cx-70,cy+59),(cx-90,cy+5)],True),
                       grad(cx-70,cy-74,cx,cy+75,['#e8c59a','#b67963']))
        for j in range(16):
            dx=((j*29+t*62)%132)-66
            dy=((j*37)%134)-67
            if hypot(dx,dy)<76 and (kind=='open' or dx>4):
                dot(c,cx+dx,cy+dy,3.8,'#e19a90',147)
    elif kind=='pulse':
        route=[(730,415),(812,415),(844,380),(885,453),(927,305),(981,413),(1139,413)]
        line(c,route,'#285a55',10)
        part=min(len(route),max(2,int(1+(len(route)-1)*q)))
        line(c,route[:part],'#a0e8cc',7)
        x,y=route[part-1]
        dot(c,x,y,8,'#eeffeb')
    elif kind in ('balloon','vessel'):
        block(c,729,307,413,133,65,solid('#8c414c'))
        block(c,741,327,389,94,45,solid('#5f3040'))
        if kind=='balloon':
            h=13+57*q
            block(c,838,374-h/2,192,h,min(h/2,27),solid('#76b8b2',212))
            line(c,[(736,374),(1125,374)],'#d7e9cb',4)
        else:
            line(c,[(743,386),(829,385),(888,285),(1000,287),(1108,370)],'#cf9b83',17)
            line(c,[(743,386),(829,385),(888,285),(1000,287),(1108,370)],'#6eaca1',8)
    elif kind=='band':
        block(c,762,331,329,115,43,solid('#9cbdb2'))
        block(c,875,309,99,160,16,solid('#d8e4d3'))
        block(c,900,356,49,65,7,solid('#648a7e'))
        line(c,[(867,479),(982,479)],'#a7d5c5',4,round(225*q))
    elif kind=='clock':
        dot(c,cx,cy,131,'#c6dfce'); dot(c,cx,cy,119,'#244741')
        line(c,[(cx,cy),(cx,cy-73)],'#d9f4e3',8)
        a=pi*.62+q*pi*.65
        line(c,[(cx,cy),(cx+76*cos(a),cy+76*sin(a))],'#81b9a9',8)
        dot(c,cx,cy,9,'#c8e7d8')
    elif kind=='medicine':
        for j in range(2):
            c.save()
            c.rotate(-35,cx+(j-0.5)*101,cy)
            block(c,cx-29+(j-.5)*101,cy-87,58,174,29,solid('#dce7d6'))
            block(c,cx-29+(j-.5)*101,cy-1,58,88,29,solid('#80ad9d'))
            c.restore()
    elif kind=='call':
        block(c,852,246,156,259,28,solid('#7ab19e'))
        block(c,865,259,130,217,17,solid('#173934'))
        for i in range(3):
            r=18+i*19+(t*11)%19
            edge=solid('#aee2cf',84); edge.setStyle(skia.Paint.kStroke_Style); edge.setStrokeWidth(3)
            c.drawCircle(cx,cy,r,edge)
        dot(c,cx,cy,20,'#8dd1ba')
    else:
        block(c,818,235,228,292,19,solid('#e2eee3'))
        block(c,880,220,102,48,13,solid('#84baaa'))
        for j in range(3):
            y=312+j*69
            line(c,[(887,y),(1002,y)],'#698b80',4)
            if q*3>=j+.25:
                line(c,[(841,y-2),(851,y+8),(869,y-13)],'#25836f',5)

def cards(c,ident,p,t,duration):
    urgent=ident=='P39'
    rect(c,0,0,1280,720,grad(0,0,1240,715,['#fbfcf6','#e9f3eb','#bad5c6']))
    title,entries=CARDS[ident]
    header(c,title,'PATIENT RECOVERY' if ident in ('P37','P38','P39','P40') else 'TEST AND RESULTS')
    stops=MARKS[ident]
    i=bisect_right(stops,p)-1
    local=(p-stops[i])/((stops[i+1] if i<len(stops)-1 else 1.0)-stops[i])
    title,detail,kind=entries[i]
    icon(c,kind,local,t)
    block(c,55,238,8,194,4,solid('#a34f4e' if urgent else '#00835b'))
    text(c,title,85,324,40,'#713737' if urgent else '#004b3d')
    text(c,detail,85,385,27,'#333b39',REGULAR)
    if ident=='P40':
        text(c,'Next: Wrist versus groin access',85,472,28,'#235e50')
    for j in range(len(entries)):
        block(c,86+59*j,568,40,7,4,solid('#226956' if j==i else '#adcabe'))
    text(c,'Follow the advice of your own care team',57,663,25,'#2f5e52',REGULAR)

ROOT_SCENES={
    'P24':'At the left coronary opening',
    'P26':'The left catheter withdraws',
    'P27':'At the right coronary opening',
}

def root_outline():
    return art.curve(
        (1086,331),((1087,380),(1094,443),(1074,466)),((1035,512),(1030,558),(1050,597)),
        ((1076,659),(1125,681),(1157,680)),((1208,678),(1256,651),(1276,595)),
        ((1293,544),(1281,497),(1253,468)),((1229,440),(1233,378),(1232,331)),
    )

def root_lumen():
    return art.curve(
        (1111,334),((1111,393),(1120,450),(1095,482)),((1066,522),(1060,565),(1075,595)),
        ((1097,639),(1133,650),(1157,650)),((1201,649),(1233,627),(1250,591)),
        ((1269,545),(1247,503),(1229,477)),((1205,443),(1210,390),(1206,334)),
    )

ROOT_OUTLINE,ROOT_LUMEN=root_outline(),root_lumen()
NEUTRAL=(1142,518)
LEFT=(1253,516)
RIGHT=(1067,521)
WIRE=(1145,577)

def root_coord(p):
    return (665+(p[0]-1147)*2.65,183+(p[1]-334)*1.31)

def root_trace(p):
    return list(map(root_coord,p))

def blend_point(a,b,q):
    return tuple(u+(v-u)*q for u,v in zip(a,b))

def instrument_path(tip, bend=0):
    tx,ty=tip
    return art.curve(
        (1146,294),((1143,371),(1140,409),(1136,453)),
        ((1134,500+bend),(tx+(1142-tx)*.36,ty+bend),tip),
    )

def show_root(c,ident,p,t,duration):
    rect(c,0,0,1280,720,grad(0,0,1220,720,['#f4faf3','#dcece5','#b5d2c6']))
    # The coronary ostia are shown above the valve plane. This view follows
    # the original source illustration's left/right anatomical orientation.
    for origin,end in ((RIGHT,(972,550)),(LEFT,(1344,549))):
        x,y=origin; xx,yy=end
        branch=root_trace(art.curve(origin,((x+(xx-x)*.38,y+1),((x+xx)*.5,yy+7),end)))
        line(c,branch,'#863e52',63)
        line(c,branch,'#bc7776',52)
        line(c,branch,'#e5a78b',34)
    c.drawPath(path(root_trace(ROOT_OUTLINE),True),
               grad(398,186,895,611,['#b57273','#a15261','#653641']))
    c.drawPath(path(root_trace(ROOT_LUMEN),True),
               grad(394,216,848,596,['#f0bba0','#d8958b','#a46571']))
    for i in range(16):
        py=335+(i*19+t*40)%269
        px=1146+((i*27)%88)-44
        if py>536: px=1154+((i*31)%154)-77
        x,y=root_coord((px,py))
        dot(c,x,y,3.6,'#eacbb2',135)
    for p0 in (LEFT,RIGHT):
        x,y=root_coord(p0)
        c.drawOval(skia.Rect.MakeXYWH(x-19,y-12,38,24),solid('#71384e'))
    valve=root_trace(art.curve((1071,604),((1109,596),(1120,614),(1158,629)),
                              ((1193,614),(1218,601),(1258,603))))
    line(c,valve,'#75364a',16)
    line(c,valve,'#edb394',8)
    wire,catheter=[],[]
    if ident=='P24':
        tip=blend_point(NEUTRAL,LEFT,smooth((p-.48)/.44))
        catheter=instrument_path(tip)
        wire=art.trace(instrument_path(WIRE),1-smooth((p-.05)/.39))
    elif ident=='P26':
        tip=blend_point(LEFT,NEUTRAL,smooth((p-.15)/.24))
        catheter=art.trace(instrument_path(tip),1-smooth((p-.41)/.46))
    else:
        wire=art.trace(instrument_path(WIRE),smooth((p-.03)/.23)*(1-smooth((p-.59)/.15)))
        tip=blend_point(NEUTRAL,RIGHT,smooth((p-.76)/.21))
        catheter=art.trace(instrument_path(tip,-8),smooth((p-.27)/.29))
    coords=root_trace(catheter)
    line(c,coords,'#1c514d',20)
    line(c,coords,'#76aba3',13)
    line(c,coords,'#d2eee0',3)
    line(c,root_trace(wire),'#755032',7)
    line(c,root_trace(wire),'#f6d99f',4)
    # Occlude the long tool proximal to the top of the enlarged field.
    rect(c,0,0,1280,160,grad(0,0,1220,720,['#f4faf3','#dcece5','#b5d2c6']))
    header(c,ROOT_SCENES[ident])
    active=RIGHT if ident=='P27' else LEFT
    tx,ty=root_coord(active)
    left_side=ident=='P27'
    ax=66 if left_side else 963
    line(c,[(tx,ty),(332 if left_side else 961,ty-43),(ax+(225 if left_side else 1),ty-43)],
         '#175749',2.6)
    dot(c,tx,ty,5,'#d0ead6')
    text(c,'Right coronary opening' if left_side else 'Left coronary opening',ax,ty-58,27,'#164c40')
    line(c,[(625,554),(569,619),(490,619)],'#195b4d',2.7)
    text(c,'Aortic valve',331,630,27,'#174b40')
    if ident=='P26':
        text(c,'The access sheath remains in place.',55,677,25,'#255d51',REGULAR)
    else:
        text(c,'Aortic root  /  Enlarged cutaway',55,677,25,'#255d51',REGULAR)

def build():
    folder=SERIES/'episode-01'
    assets=folder/'visuals'
    assets.mkdir(exist_ok=True)
    data=json.loads((folder/'timeline.json').read_text(encoding='utf-8-sig'))
    by_id={}
    for row in data['scenes']:
        ident=row['id']
        if ident not in IMAGING and ident not in CARDS and ident not in ROOT_SCENES: continue
        n=row['end_frame']-row['start_frame']
        target=assets/f'{ident}-angiogram-visual.mp4'
        tmp=assets/f'{ident}-angiogram-visual.part.mp4'
        if not target.exists():
            draw=imaging if ident in IMAGING else show_root if ident in ROOT_SCENES else cards
            encode_scene(tmp,n,lambda c,f:draw(c,ident,f/max(1,n-1),f/FPS,n/FPS))
            tmp.replace(target)
        by_id[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                      'reference_only':False,'native_composition':True}
        (assets/'angiogram-overrides.json').write_text(json.dumps(by_id,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    build()
