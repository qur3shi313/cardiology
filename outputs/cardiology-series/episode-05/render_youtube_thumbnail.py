"""Draw the original Wrist vs Groin Access thumbnail at 1280×720."""

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONTS = ROOT / 'outputs/website-v2/elysian-corporate/assets/fonts'
WIDTH, HEIGHT, SS = 1280, 720, 2
GREEN, INK, ACCENT = '#004b3d', '#263832', '#00835b'


def xy(point):
    x, y = point
    return round(x*SS), round(y*SS)


def box(values):
    left, top, right, bottom = values
    return (*xy((left, top)), *xy((right, bottom)))


@lru_cache(maxsize=None)
def font(size, title=False):
    filename = 'josefin-sans-variable.ttf' if title else 'fira-sans-semibold.ttf'
    face = ImageFont.truetype(str(FONTS / filename), size*SS)
    if title:
        face.set_variation_by_axes([680])
    return face


def curve(first, segments, steps=20):
    points = [first]
    previous = first
    for a, b, end in segments:
        for i in range(1, steps+1):
            t = i/steps
            q = 1-t
            points.append(tuple(q**3*x+3*q*q*t*y+3*q*t*t*z+t**3*w
                                for x,y,z,w in zip(previous,a,b,end)))
        previous = end
    return points


def line(draw, points, color, width):
    draw.line([xy(p) for p in points], fill=color, width=round(width*SS), joint='curve')


def backdrop():
    y,x=np.ogrid[:HEIGHT*SS,:WIDTH*SS]
    x,y=x/SS,y/SS
    fog=np.exp(-(((x-760)/720)**2+((y-690)/370)**2))
    glow=np.exp(-(((x-330)/490)**2+((y-100)/270)**2))
    values=[np.clip(a-b*fog+c*glow,0,255) for a,b,c in zip((247,250,245),(27,12,16),(9,6,9))]
    return Image.fromarray(np.uint8(np.stack(values,axis=2)),'RGB')


def rounded_panel(image, bounds):
    shadow=Image.new('RGBA',image.size)
    l,t,r,b=bounds
    ImageDraw.Draw(shadow).rounded_rectangle(box((l,t+9,r,b+10)),radius=30*SS,fill=(31,73,56,37))
    shadow=shadow.filter(ImageFilter.GaussianBlur(13*SS))
    image.paste(shadow,(0,0),shadow)
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle(box(bounds),radius=30*SS,fill='#f7fbf8',outline='#c3d8cc',width=2*SS)


def shading(image, polygon, base, shade, highlight, focus, extent):
    points=[xy(p) for p in polygon]
    left,top=min(p[0] for p in points),min(p[1] for p in points)
    right,bottom=max(p[0] for p in points)+1,max(p[1] for p in points)+1
    mask=Image.new('L',(right-left,bottom-top))
    ImageDraw.Draw(mask).polygon([(x-left,y-top) for x,y in points],fill=255)
    yy,xx=np.ogrid[top:bottom,left:right]
    x,y=xx/SS,yy/SS
    fx,fy=focus
    sx,sy=extent
    glow=np.exp(-(((x-fx)/sx)**2+((y-fy)/sy)**2))
    shadow=np.clip((y-(fy+25))/(sy*1.5),0,1)
    color=[np.clip(a+(b-a)*shadow+(c-a)*glow,0,255) for a,b,c in zip(base,shade,highlight)]
    layer=Image.fromarray(np.uint8(np.stack(color,axis=2)),'RGB')
    blurred=mask.filter(ImageFilter.GaussianBlur(11*SS))
    image.paste('#b7c7ba',(left+1*SS,top+7*SS,right+1*SS,bottom+7*SS),blurred)
    image.paste(layer,(left,top),mask)
    ImageDraw.Draw(image).line(points+[points[0]],fill='#b98775',width=2*SS,joint='curve')


def artery(draw, points, highlight=True, width=13):
    if highlight:
        line(draw,points,'#e1a99a',width+7)
        line(draw,points,'#8a4450',width)
        line(draw,points,'#c86c70',width-4)
        line(draw,[(x-.8,y-1.2) for x,y in points],'#e69a8c',2.0)
    else:
        line(draw,points,'#c6867a',width)
        line(draw,points,'#e9a99b',width-4)


def site(draw, point):
    x,y=point
    draw.ellipse(box((x-20,y-20,x+20,y+20)),outline='#5e9f85',width=2*SS)
    draw.ellipse(box((x-13,y-13,x+13,y+13)),fill=GREEN,outline='#fbfffa',width=3*SS)
    draw.ellipse(box((x-3,y-3,x+3,y+3)),fill='#bde8ca')


def right_wrist(image):
    # Right palm up, fingers left and thumb above the wrist centerline.
    first=(1564,213)
    outline=curve(first,[
        ((1520,213),(1450,214),(1423,214)),
        ((1410,205),(1400,199),(1383,194)),
        ((1368,190),(1339,190),(1311,184)),
        ((1300,181),(1296,187),(1308,194)),
        ((1318,198),(1337,201),(1347,204)),
        ((1334,206),(1299,202),(1283,201)),
        ((1274,200),(1272,209),(1285,211)),
        ((1309,215),(1330,217),(1346,221)),
        ((1333,224),(1300,219),(1283,221)),
        ((1276,223),(1278,232),(1289,232)),
        ((1310,233),(1337,233),(1350,237)),
        ((1334,243),(1307,238),(1298,243)),
        ((1294,249),(1301,254),(1312,254)),
        ((1335,255),(1352,256),(1368,263)),
        ((1379,267),(1390,272),(1394,281)),
        ((1404,306),(1415,305),(1418,290)),
        ((1420,279),(1410,263),(1427,258)),
        ((1446,256),(1516,263),(1564,267)),
    ])

    def place(point):
        x,y=point
        return 100+(x-1273)*1.61, 469+(220-y)*1.85-(x-1273)*.29

    shading(image,[place(p) for p in outline],(231,182,151),(196,141,119),(255,220,185),(308,405),(188,99))
    draw=ImageDraw.Draw(image)
    for controls in (
        [(1368,231),(1399,216),(1417,234),(1417,252)],
        [(1361,215),(1379,221),(1390,228),(1398,241)],
        [(1419,224),(1432,221),(1443,226),(1451,228)],
    ):
        line(draw,[place(p) for p in curve(controls[0],[tuple(controls[1:])])],'#c69579',1.8)

    trail=curve((1563,250),[((1521,247),(1478,249),(1444,249)),((1433,250),(1428,253),(1420,259))])
    artery(draw,[place(p) for p in trail],width=11)
    mark=place((1444,249))
    line(draw,[mark,(mark[0]-25,557),(235,557)],'#4e8873',2)
    site(draw,mark)


def right_groin(image):
    # Anterior view. The patient's right is on the viewer's left.
    outline=curve((828,258),[
        ((867,270),(1013,270),(1052,258)),
        ((1062,307),(1089,333),(1118,354)),
        ((1153,385),(1163,428),(1160,476)),
        ((1159,516),(1154,546),(1148,565)),
        ((1119,569),(1066,570),(1030,562)),
        ((1015,542),(997,510),(968,485)),
        ((953,472),(927,472),(911,485)),
        ((884,509),(867,545),(850,563)),
        ((812,568),(758,567),(731,562)),
        ((722,529),(719,489),(720,453)),
        ((719,409),(731,378),(760,353)),
        ((790,330),(817,305),(828,258)),
    ])
    shading(image,outline,(231,185,162),(187,132,122),(254,224,193),(938,351),(192,116))
    draw=ImageDraw.Draw(image)
    left_ligament=curve((779,380),[((813,398),(846,408),(893,429))])
    right_ligament=curve((1099,380),[((1066,398),(1033,408),(986,429))])
    line(draw,left_ligament,'#be8a78',2.4)
    line(draw,right_ligament,'#be8a78',2.4)
    line(draw,curve((940,290),[((937,310),(942,326),(940,348))]),'#d8a58c',2)
    line(draw,curve((940,432),[((937,446),(939,459),(940,471))]),'#d8a58c',2)

    trunk=curve((940,285),[((939,310),(940,330),(939,348))])
    opposite=curve((939,348),[((967,359),(997,365),(1020,388)),((1041,409),(1050,456),(1051,478)),((1053,510),(1052,537),(1059,558))])
    common=curve((939,348),[((914,358),(877,369),(858,388)),((841,408),(836,435),(832,454)),((830,466),(831,474),(829,483))])
    main=curve((829,483),[((823,506),(818,533),(815,559))])
    deep=curve((829,483),[((846,494),(858,515),(860,540))])
    artery(draw,opposite,False,12)
    artery(draw,trunk,width=18)
    artery(draw,common,width=14)
    artery(draw,main,width=12)
    artery(draw,deep,width=8)
    mark=(832,454)
    line(draw,[mark,(799,556),(770,556)],'#4e8873',2)
    site(draw,mark)


def centered(draw, at, words, size, color, title=False):
    draw.text(xy(at),words,font=font(size,title),fill=color,anchor='mm')


def scene():
    image=backdrop()
    draw=ImageDraw.Draw(image)
    original=Image.open(ROOT / 'work/company-logo-original-686.jpg').convert('RGB')
    logo=original.resize((57*SS,57*SS),Image.Resampling.LANCZOS)
    mask=Image.new('L',logo.size)
    ImageDraw.Draw(mask).ellipse((0,0,logo.width-1,logo.height-1),fill=255)
    image.paste(logo,xy((48,32)),mask)
    draw.text(xy((121,51)),'Elysian Biomedical LLP',font=font(27),fill=GREEN,anchor='lt')
    centered(draw,(640,151),'Wrist or groin?',88,GREEN,True)

    rounded_panel(image,(48,219,623,665))
    rounded_panel(image,(657,219,1232,665))
    right_wrist(image)
    right_groin(image)
    draw=ImageDraw.Draw(image)
    line(draw,[(88,582),(583,582)],'#cfdfd4',1.5)
    line(draw,[(697,582),(1192,582)],'#cfdfd4',1.5)
    centered(draw,(335,620),'Right radial artery',38,GREEN)
    centered(draw,(944,620),'Right common femoral artery',35,GREEN)
    return image.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)


if __name__=='__main__':
    output=HERE / 'wrist-vs-groin-youtube-thumbnail.png'
    scene().save(output,optimize=True)
    print(output)
