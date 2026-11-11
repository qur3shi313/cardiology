"""Reusable conceptual aortic valve and root geometry for structural-heart films.

Long-axis coordinates are relative to the annulus center. Negative y follows
the ascending aorta and positive y leads through the LVOT into the ventricle.
The short-axis view is a separate look down the same outlet.
"""

from math import cos, exp, pi, sin

import skia

from .access import grad, line, path, solid


ANNULUS = (0, 0)
LVOT = (0, 42)
AORTIC_ROOT = (0, -114)
LEFT_VENTRICLE = (-29, 170)
FLOW_TONES = ('#ffe2a3', '#f3b590', '#ffcda4')


def mix(a,b,p):
    return a+(b-a)*p


def smooth(p):
    p=max(0.,min(1.,p))
    return p*p*(3-2*p)


def beat(t, period=1.82):
    """Return illustrative opening and contraction during one shared cycle."""
    p=(t/period)%1
    opening=smooth((p-.05)/.14)*(1-smooth((p-.40)/.15))
    contraction=smooth((p-.025)/.23)*(1-smooth((p-.45)/.29))
    return p,opening,contraction


def spline(start, sections, close=False):
    out=skia.Path()
    out.moveTo(*start)
    for a,b,end in sections:
        out.cubicTo(*a,*b,*end)
    if close:
        out.close()
    return out


def cubic_point(start,a,b,end,p):
    q=1-p
    return tuple(q**3*u+3*q*q*p*v+3*q*p*p*w+p**3*x for u,v,w,x in zip(start,a,b,end))


def ring(c,x,y,radius,tone,width=2.6,alpha=255):
    pen=solid(tone,alpha)
    pen.setStyle(skia.Paint.kStroke_Style)
    pen.setStrokeWidth(width)
    c.drawCircle(x,y,radius,pen)


def polar(radius,angle):
    return radius*cos(angle),radius*sin(angle)


def calcific_deposits(c, pts, amount, monochrome=False):
    if amount <= 0:
        return
    for i,(x,y,r) in enumerate(pts):
        r*=.44+.56*amount
        out=[]
        for j in range(7):
            a=j*2*pi/7
            spread=.77+.23*sin((i+2)*1.6+j*2.1)
            out.append((x+r*spread*cos(a),y+r*.73*spread*sin(a)))
        c.drawPath(path(out,True),solid('#eee9d6' if monochrome else '#ebcc8c'))
        c.drawCircle(x-r*.13,y-r*.12,r*.32,solid('#fffcdd',184))


def valve_deposits(middle,spread,aperture):
    for j in range(8):
        p=(j-3.5)/7
        a=middle+p*spread*.62
        radius=50+48*aperture+8*sin(j*2.6)
        x,y=polar(radius,a)
        yield x,y,4.1+(j%3)*1.7


def valve_deposit_point(cx,cy,radius,*,opening,calcium):
    x,y,_=tuple(valve_deposits(-pi/2,2*pi/3,opening*(1-.72*calcium)))[4]
    return cx+x*radius/145,cy+y*radius/145


def draw_valve_face(c,cx,cy,radius,*,opening=1.,calcium=0.,cusps=3,monochrome=False):
    """Draw a short-axis native valve with fixed commissures and mobile free edges."""
    if cusps not in (2,3):
        raise ValueError('The conceptual model supports two or three cusps.')
    c.save()
    c.translate(cx,cy)
    c.scale(radius/145,radius/145)
    aorta,lip,inside=('#6b7772','#b7c2b9','#303d39') if monochrome else ('#743b49','#c77b7a','#421f34')
    c.drawCircle(5,8,148,solid('#233c37',53))
    c.drawCircle(0,0,145,grad(-112,-132,130,143,[lip,aorta,'#593344' if not monochrome else '#344840']))
    c.drawCircle(0,0,122,solid(inside))
    ring(c,0,0,129,'#efafa0' if not monochrome else '#dce4d9',3.3,178)
    aperture=opening*(1-.72*calcium)
    spread=2*pi/cusps
    for i in range(cusps):
        middle=-pi/2+i*spread
        start=middle-spread/2
        end=middle+spread/2
        points=[polar(121,start+spread*j/22) for j in range(23)]
        a,b=points[0],points[-1]
        tip=polar(94*aperture,middle)
        shoulder=50+46*aperture
        ca=polar(shoulder,middle-.42*spread)
        cb=polar(shoulder,middle+.42*spread)
        left_tip=polar(94*aperture,middle-.15*spread)
        right_tip=polar(94*aperture,middle+.15*spread)
        cusp=path(points)
        cusp.cubicTo(*cb,*right_tip,*tip)
        cusp.cubicTo(*left_tip,*ca,*a)
        cusp.close()
        light='#dbded3' if monochrome else '#f4b4a0'
        mid='#909f97' if monochrome else '#bf7978'
        shade='#53685f' if monochrome else '#8c475b'
        c.drawPath(cusp,grad(a[0],a[1],b[0],b[1],[shade,light,mid]))
        edge=spline(b,((cb,right_tip,tip),(left_tip,ca,a)))
        pen=solid('#f3eee1' if monochrome else '#ffdac2',221)
        pen.setStyle(skia.Paint.kStroke_Style)
        pen.setStrokeWidth(2.1+3.1*calcium)
        c.drawPath(edge,pen)
        if calcium>0:
            c.save()
            c.clipPath(cusp,doAntiAlias=True)
            calcific_deposits(c,valve_deposits(middle,spread,aperture),calcium,monochrome)
            c.restore()
    if aperture>.11 and not monochrome:
        c.drawCircle(0,0,4+12*aperture,solid('#ffe1a5',round(28+37*opening)))
    c.restore()


def root_wall():
    return spline((-102,-259),(
        ((-110,-210),(-101,-170),(-131,-127)),
        ((-169,-69),(-138,-24),(-107,3)),
        ((-98,35),(-122,53),(-166,92)),
        ((-232,152),(-222,230),(-180,279)),
        ((-130,332),(-61,342),(-15,333)),
        ((84,318),(153,239),(166,153)),
        ((177,95),(121,50),(104,3)),
        ((142,-26),(161,-84),(138,-126)),
        ((111,-169),(112,-215),(110,-259)),
    ),True)


def root_lumen(contraction,hypertrophy):
    squeeze=25*contraction+31*hypertrophy
    apex=289-14*contraction-16*hypertrophy
    return spline((-74,-260),(
        ((-80,-209),(-75,-169),(-102,-127)),
        ((-126,-92),(-119,-52),(-77,-3)),
        ((-70,33),(-103,60),(-137+squeeze*.65,103)),
        ((-187+squeeze,156),(-177+squeeze,217),(-142+squeeze*.79,249)),
        ((-105+squeeze*.48,apex),(-56,apex+13),(-22,apex+6)),
        ((63-squeeze*.35,apex-3),(110-squeeze,229),(127-squeeze,156)),
        ((138-squeeze,100),(98,58),(75,-3)),
        ((119,-41),(134,-92),(106,-127)),
        ((81,-172),(85,-212),(81,-260)),
    ),True)


def leaflet(c,sign,opening,calcium,displacement,monochrome):
    aperture=opening*(1-.72*calcium)
    end_x=sign*mix(0,59,aperture)
    end_y=mix(-8,-101,aperture)
    end_x=mix(end_x,sign*102,displacement)
    end_y=mix(end_y,-94,displacement)
    start=(sign*76,-3)
    tip=(end_x,end_y)
    shoulder=(sign*mix(42,91,aperture+displacement*(1-aperture)),mix(-34,-58,aperture))
    under=(sign*mix(47,98,aperture+displacement*(1-aperture)),mix(-6,-28,aperture))
    return_shoulder=(shoulder[0]+sign*6,shoulder[1]+7+6*calcium)
    return_under=(under[0]+sign*4,under[1]+8)
    leaf=spline(start,((under,shoulder,tip),(return_shoulder,return_under,(sign*78,5))),True)
    c.drawPath(leaf,grad(start[0],start[1],tip[0],tip[1],
                         ['#777f76','#e4e6d7','#bac8ba'] if monochrome else ['#934b5c','#f2c2a4','#ffd6b1']))
    front=spline(start,((under,shoulder,tip),))
    pen=solid('#eee6d4' if monochrome else '#ffe1b8')
    pen.setStyle(skia.Paint.kStroke_Style)
    pen.setStrokeWidth(3.8+6.0*calcium)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    c.drawPath(front,pen)
    if calcium>0:
        points=[]
        for i,f in enumerate((.23,.37,.48,.61,.73)):
            x,y=cubic_point(start,under,shoulder,tip,f)
            x+=sign*2.4
            y+=4.5
            points.append((x,y,4.7+(i%3)*2.15))
        c.save()
        c.clipPath(leaf,doAntiAlias=True)
        calcific_deposits(c,points,calcium,monochrome)
        c.restore()


def forward_flow(c,t,opening,calcium,monochrome):
    if opening<.13:
        return
    aperture=opening*(1-.72*calcium)
    for i in range(18 if calcium<.3 else 12):
        s=(i/18+t*(.92+.66*calcium))%1
        y=mix(215,-245,s)
        level=exp(-((y+6)/72)**2)
        offset=((i*23)%67-33)
        x=offset*mix(.68,.44*aperture,level)
        if y>55:
            x-=15*min(1,(y-55)/100)
        length=7.8+7.5*calcium+4.2*opening
        tone=('#e9eee1' if monochrome else FLOW_TONES[i%len(FLOW_TONES)])
        line(c,((x,y+length),(x-1.4,y)),tone,2.3+opening,round(177*opening))
    # Flow arrows point from ventricle toward the ascending aorta only.
    pen=('#e9f5e6' if monochrome else '#fff1bd')
    c.drawPath(path(((-8,-151),(0,-167),(8,-151)),True),solid(pen,round(191*opening)))


def draw_root(c,cx,cy,scale,*,opening=1.,calcium=0.,contraction=0.,hypertrophy=0.,
              displacement=0.,monochrome=False,flow=False,t=0.):
    """Draw LV below a native valve, with aorta above and fixed annular landmarks.

    Scale transforms the local coordinates and preserves all anatomy anchors.
    Displacement moves old cusps outward for separately authored TAVI sequences.
    """
    c.save()
    c.translate(cx,cy)
    c.scale(scale,scale)
    wall=root_wall()
    cavity=root_lumen(contraction,hypertrophy)
    tissue=['#57665f','#929d91','#3d514b'] if monochrome else ['#d89287','#a55562','#6b324c']
    blood=['#26322e','#4a5d54','#263b36'] if monochrome else ['#6d3346','#a4545b','#642a42']
    c.drawPath(wall,grad(-200,-191,183,313,tissue))
    edge=solid('#cbd8ca' if monochrome else '#f4b3a0',191)
    edge.setStyle(skia.Paint.kStroke_Style)
    edge.setStrokeWidth(2.6)
    c.drawPath(wall,edge)
    c.drawPath(cavity,grad(-176,81,125,235,blood))
    inner=solid('#d8ddd0' if monochrome else '#f19a91',185)
    inner.setStyle(skia.Paint.kStroke_Style)
    inner.setStrokeWidth(2.8)
    c.drawPath(cavity,inner)
    if flow:
        c.save()
        c.clipPath(cavity,doAntiAlias=True)
        forward_flow(c,t,opening,calcium*(1-displacement),monochrome)
        c.restore()
    for side in (-1,1):
        leaflet(c,side,opening,calcium,displacement,monochrome)
    c.restore()


def draw_valve_frame(c,cx,cy,scale,*,expansion=1.,tone='#39786b',leaflets=True):
    """Conceptual generic valve frame, centered on the annular landing point."""
    c.save()
    c.translate(cx,cy)
    c.scale(scale,scale)
    width=mix(17,84,expansion)
    top,bottom=-115,35
    for j in range(7):
        x=mix(-width,width,j/6)
        drift=width*.115
        line(c,[(x,top),(x+drift,-78),(x-drift,-42),(x+drift,-6),(x,bottom)],tone,3.5)
        if j<6:
            neighbor=mix(-width,width,(j+1)/6)
            line(c,[(x,-78),(neighbor,-42),(x,-6)],tone,2.5)
    line(c,[(-width,top),(width,top)],tone,2.7)
    line(c,[(-width,bottom),(width,bottom)],tone,2.7)
    if leaflets:
        light=spline((-width*.76,-5),(((-width*.57,-35),(-width*.24,-22),(0,-13)),
                     ((width*.25,-22),(width*.59,-35),(width*.78,-4))))
        stroke=solid('#f2d0a2')
        stroke.setStyle(skia.Paint.kStroke_Style)
        stroke.setStrokeWidth(4.)
        c.drawPath(light,stroke)
    c.restore()
