"""Context, recovery and aftercare artwork for the access comparison."""

from math import cos, sin

from render_comparison import (
    INK, JADE, LIGHT, TEAL, WARN, anatomy, artery, beat, body, brand,
    curve, easing, ellipse, field, glove, gradient, groin_surface, lerp, line, marker,
    note, path_part, pulse, rectangle, shape, solid, words, wrist, wrist_surface,
)


def pictogram(c,name,x,y,s=1,tone=TEAL):
    c.save()
    c.translate(x,y)
    c.scale(s,s)
    if name in ("bleed","drainage"):
        p=curve((0,-48),((-15,-25),(-41,2),(-37,21)),((-29,55),(28,51),(36,19)),
                ((43,-1),(16,-28),(0,-48)))
        shape(c,p,tone)
        line(c,curve((-14,16),((-14,27),(-7,32),(-1,33))),"#f7e8dc",4.5)
    elif name in ("pain","swelling"):
        line(c,curve((-58,29),((-31,29),(-28,-18),(0,-19)),((28,-18),(31,29),(58,29))),tone,7)
        line(c,((0,-54),(0,-35)),tone,6)
        line(c,((-10,-45),(0,-55),(10,-45)),tone,6)
    elif name=="fever":
        rectangle(c,-12,-55,24,90,tone,11)
        ellipse(c,0,35,24,24,tone)
        rectangle(c,-4,-46,8,73,"#faede1",4)
        ellipse(c,0,34,12,12,"#faede1")
    elif name=="chest":
        pts=curve((0,-25),((-32,-62),(-66,-27),(-46,4)),((-32,25),(-10,37),(0,55)),
                  ((17,34),(48,21),(54,-8)),((58,-35),(18,-52),(0,-25)))
        shape(c,pts,tone)
        line(c,((-37,4),(-19,4),(-10,-13),(0,16),(11,-4),(36,-4)),"#faede1",4)
    elif name=="breath":
        line(c,((0,-49),(0,-9),(-12,4)),tone,9)
        line(c,((0,-9),(12,4)),tone,9)
        left=curve((-10,-24),((-21,-50),(-51,-9),(-56,13)),
                   ((-60,37),(-40,48),(-20,42)),((-10,40),(-9,9),(-10,-24)))
        shape(c,left,tone)
        shape(c,tuple((-a,b) for a,b in left),tone)
    elif name=="artery":
        artery(c,curve((-53,4),((-22,-19),(9,-15),(54,17))),21,"#ba6d70")
    elif name=="heart":
        pts=curve((0,-26),((-26,-61),(-61,-29),(-48,-1)),((-37,24),(-18,33),(0,53)),
                  ((20,34),(48,23),(54,-6)),((57,-32),(18,-54),(0,-26)))
        shape(c,pts,gradient(-42,-35,44,46,["#d1817d","#ad596a","#733a50"]), "#874c56")
    elif name=="phone":
        line(c,curve((-40,-45),((-59,-22),(-29,19),(-5,36)),((15,54),(38,57),(48,40))),tone,19)
        line(c,((-42,-44),(-28,-23)),tone,17)
        line(c,((48,41),(23,27)),tone,17)
    c.restore()


def cutaway(c,t,y=-148,sy=1.42):
    c.save()
    c.translate(0,y)
    c.scale(1,sy)
    wrist.vessel(c)
    wrist.flow(c,t)
    c.restore()


def p04(c,row,n):
    j,p,t=beat(row,n)
    field(c,"forest")
    cutaway(c,t,-163+t*3.05,1.48)
    heading="Stable coronary disease and PCI" if j==3 else "Acute coronary syndrome and PCI"
    note(c,heading,63,110,dark=True)
    icon,label=(
        ("artery","Wrist preferred when feasible"),
        ("bleed","Lower bleeding and vessel risk"),
        ("heart","Lower risk of death in this group"),
        ("artery","Fewer entry-site vessel problems and less bleeding"),
    )[j]
    x=1040+35*(1-easing(p,0,.42))
    ellipse(c,x,402,82,82,"#eff9eb",222)
    pictogram(c,icon,x,402,.97+easing(p,0,.44)*.10,TEAL)
    note(c,label,63,650,dark=True)


CURVATURE=curve((-75,446),((78,427),(200,346),(318,350)),
                ((458,355),(533,524),(643,536)),((727,546),(758,361),(852,343)),
                ((958,322),(1118,443),(1362,397)))


def difficult_path(c,t,p):
    artery(c,CURVATURE,104,"#b36470")
    line(c,CURVATURE,"#693846",66)
    line(c,tuple((x,y-22) for x,y in CURVATURE),"#d78a84",6,185)
    for k in range(26):
        fraction=((k*.056+t*.084)%1.0)
        point=path_part(CURVATURE,fraction)[-1]
        ellipse(c,point[0],point[1]+((k*17)%38-19),5.5,3.2,"#e78f88",155)
    into=easing(p,0,.68)
    stop=path_part(CURVATURE,.15+.38*into)
    line(c,stop,"#173c40",13)
    line(c,stop,"#9ad8ca",7.5)
    ellipse(c,*stop[-1],6,6,"#fff1c9")
    return stop[-1]


def p05(c,row,n):
    j,p,t=beat(row,n)
    field(c)
    if j==0:
        groin_surface(c,410,329,1.71)
        x=lerp(1110,957,easing(p))
        tool=curve((x-201,469),((x-155,445),(x-43,378),(x+95,307)))
        line(c,tool,"#216458",48)
        line(c,tool,"#68a99a",37)
        line(c,tuple((a,b-8) for a,b in tool),"#bde8d6",8,175)
        ellipse(c,x+94,306,13,17,"#214b47")
        pictogram(c,"heart",1094,521,.98+sin(t*4)*.06)
        note(c,"Larger equipment",1218,122,align="right")
    elif j==1:
        tip=difficult_path(c,t,p)
        pulse(c,*tip,t)
        note(c,"Arterial anatomy",68,135)
    else:
        c.save()
        c.translate(415+22*easing(p),327)
        c.scale(1.18,1.18)
        c.translate(-330,-295)
        artery(c,anatomy.AORTA,43,"#ab6470")
        shape(c,anatomy.MYOCARDIUM,gradient(155,170,492,497,["#d98e86","#ad6370","#774055"]),
              "#96545f")
        for path in (anatomy.LEFT_MAIN,anatomy.LAD,anatomy.LCX,anatomy.RCA):
            artery(c,path,10,"#c07477")
        bypass=curve((323,130),((385,116),(415,175),(416,229)),((418,302),(398,340),(354,368)))
        artery(c,bypass,10,"#b4976b")
        line(c,path_part(bypass,easing(p)), "#f9e8ac",4.4)
        c.restore()
        wrist_surface(c,1.15,711+32*(1-easing(p)),102)
        note(c,"Previous bypass or planned graft",640,646,align="center")


def patient(c,x,y,s,pose,t=0,band=False):
    c.save()
    c.translate(x,y)
    c.scale(s,s)
    cloth=gradient(-20,-70,181,218,["#b5d6c8","#77b2a2","#3c8277"])
    leg=gradient(0,15,120,184,["#b6c7ba","#85a496","#628477"])
    shadow=solid("#6a9186",80)
    head="#d8ac91"
    cap="#355d56"
    if pose=="seated":
        ellipse(c,111,230,224,27,shadow)
        line(c,((-26,-20),(-13,151),(136,154)), "#81ab9c",29)
        line(c,((3,129),(8,230)), "#81ab9c",17)
        line(c,((119,139),(126,228)), "#81ab9c",17)
        rectangle(c,-40,-30,55,174,"#b2cec0",16)
        rectangle(c,-15,121,178,44,"#9ebfb0",13)
        shape(c,curve((10,94),((64,86),(138,117),(178,137)),((211,157),(175,200),(201,214)),
                        ((241,215),(250,231),(228,238)),((211,243),(185,241),(178,228)),
                        ((166,195),(173,171),(152,166)),((96,171),(52,158),(18,135))),
              leg,"#648779")
        shape(c,curve((15,-14),((36,-48),(83,-45),(110,-17)),((137,17),(114,61),(134,110)),
                        ((105,134),(69,143),(27,130)),((8,97),(-4,29),(15,-14))),cloth,"#4a8a7b")
        ellipse(c,58,-60,39,44,head)
        shape(c,curve((19,-61),((13,-103),(81,-124),(97,-81)),((92,-65),(57,-70),(19,-61))),cap)
        rectangle(c,65,81,166,20,"#c3dcd0",10)
        line(c,curve((79,13),((98,34),(108,61),(145,70)),((166,70),(190,67),(222,73))), "#52988c",32)
        line(c,((207,71),(226,73)),head,15)
        if band:
            rectangle(c,203,57,16,30,"#266e62",4)
    elif pose=="flat":
        ellipse(c,175,138,325,30,shadow)
        rectangle(c,-120,52,646,40,"#b1cebf",18)
        rectangle(c,-99,89,604,28,"#8cb2a3",9)
        line(c,((-49,106),(-47,154)), "#6b9b8a",14)
        line(c,((456,106),(454,154)), "#6b9b8a",14)
        rectangle(c,-88,10,120,46,"#e1eee1",23)
        shape(c,curve((235,26),((293,16),(373,25),(414,21)),((442,20),(462,4),(478,8)),
                        ((500,14),(497,36),(478,44)),((451,53),(333,58),(238,56))),leg,"#668f82")
        shape(c,curve((43,47),((47,11),(85,-4),(127,2)),((192,-4),(230,2),(270,20)),
                        ((283,26),(280,51),(267,56)),((224,65),(100,60),(43,47))),cloth,"#4b8f82")
        ellipse(c,22,19,29,34,head)
        shape(c,curve((-9,20),((-19,-15),(34,-30),(48,-10)),((51,0),(45,7),(44,12)),
                        ((27,9),(9,12),(-9,20))),cap)
        line(c,((116,22),(161,37),(195,35)), "#5d9b8d",22)
        line(c,((200,35),(220,35)), "#8ab2a5",14)
    else:
        shape(c,curve((-40,-14),((-28,-52),(20,-52),(42,-12)),((62,29),(55,75),(50,111)),
                        ((25,130),(-26,129),(-50,110)),((-61,68),(-63,21),(-40,-14))),cloth,"#4a8a7b")
        ellipse(c,0,-48,31,39,head)
        shape(c,curve((-32,-52),((-29,-91),(21,-98),(32,-56)),((16,-45),(-11,-53),(-32,-52))),cap)
        shift=8*sin(t*4)
        if pose=="staff_check":
            arm=curve((33,6),((71,13),(67,49),(93,70)),((113,76),(129,78),(134,87+shift)))
        else:
            arm=curve((33,6),((62,25),(65,40),(95,30+shift)),((107,27),(126,12+shift),(133,1+shift)))
        line(c,arm,"#6fa99a",23)
        ellipse(c,*arm[-1],11,8,"#98c8b8")
    c.restore()


def p06(c,row,n):
    j,p,t=beat(row,n)
    field(c)
    if j==0:
        tip=difficult_path(c,t,p)
        pulse(c,*tip,t)
        note(c,"A difficult arterial path",73,128)
    elif j==1:
        body(c,370,367,1.10,[],t)
        b=body(c,924,367,1.10,[("groin",easing(p,.32,1))],t)
        if p<.57:
            pulse(c,370+(525-293)*1.10,367+(397-282)*1.10,t)
            note(c,"The other wrist",347,651,align="center")
        else:
            pulse(c,*b[1],t)
            note(c,"The groin",931,651,align="center")
    else:
        patient(c,466,340,1.35,"staff_check",t)
        patient(c,284,411+13*(1-easing(p)),1.43,"flat",t)
        pulse(c,619,462,t)
        pulse(c,531,457,t+.35)
        note(c,"Staff check both sites if used",640,654,align="center")


def p08(c,row,n):
    j,p,t=beat(row,n)
    field(c)
    if j==0:
        x=408+lerp(-46,34,easing(p))
        patient(c,x,339,1.65,"seated",t,True)
        marker(c,(x+211*1.65,458),"Wrist band",920,209)
        note(c,"Often able to sit up sooner",69,661)
    elif j==1:
        patient(c,230+44*easing(p),403,1.69,"flat",t)
        note(c,"May need to lie flat with the leg straight",73,161)
    else:
        patient(c,712,244,1.60,"staff",t)
        patient(c,250+26*easing(p),401,1.56,"flat",t)
        note(c,"Staff assess when you can walk" if j==2 else "Wait until staff say it is safe",640,669,align="center")


def paper(c,x,y,entries,check_count):
    rectangle(c,x+13,y+16,525,435,solid("#719b8c",95),25)
    rectangle(c,x,y,525,435,gradient(x,y,x+525,y+435,["#fcfff3","#e9f3e4"]),25)
    rectangle(c,x+168,y-15,193,48,"#6ba696",9)
    words(c,"Your discharge plan",x+45,y+90,43,INK,title=True)
    for i,label in enumerate(entries):
        if i>=check_count:
            break
        yy=y+160+i*55
        ellipse(c,x+60,yy-9,14,14,"#cee6d5")
        line(c,((x+53,yy-8),(x+59,yy-2),(x+68,yy-17)),TEAL,3.5)
        words(c,label,x+91,yy,30,INK)


def car(c,x,y,s):
    c.save()
    c.translate(x,y)
    c.scale(s,s)
    ellipse(c,6,58,131,19,"#aac9bb")
    pts=curve((-123,28),((-126,-3),(-81,-16),(-65,-22)),((-40,-51),(31,-62),(64,-30)),
              ((71,-21),(79,-11),(97,-8)),((120,-2),(129,15),(127,34)),((95,46),(-82,48),(-123,28)))
    shape(c,pts,gradient(-99,-48,112,50,["#a6cfb8","#70ab99","#4a8f81"]),"#437b70",2.5)
    shape(c,curve((-49,-18),((-24,-43),(22,-46),(49,-24)),((56,-16),(63,-12),(67,-7)),
                    ((31,0),(-17,1),(-54,-4))),"#e4f4e6","#74a99a")
    for a in (-74,73):
        ellipse(c,a,39,19,20,"#395d56")
        ellipse(c,a,39,7,7,"#c8ded3")
    c.restore()


def p09(c,row,n):
    j,p,t=beat(row,n)
    field(c)
    if j==0:
        paper(c,117+65*easing(p),129,("Dressing care",),1)
        car(c,858+143*easing(p),437,1.55)
        note(c,"Possible same-day discharge",72,661)
    elif j==1:
        patient(c,239+39*easing(p),404,1.63,"flat",t)
        rectangle(c,834,113,353,164,"#345e58",13)
        points=[(851+i*2,198+13*sin((i*2-t*74)*.088)+23*max(0,cos((i*2-t*74)*.092))**10) for i in range(157)]
        line(c,points,"#b9efc6",3.4)
        note(c,"More monitoring if needed",73,661)
    else:
        details=("Dressing care","Medicines") if p<.50 else ("Lifting, driving and work","Who to call")
        paper(c,151+32*easing(p),129,details,1 if p%.50<.13 else 2)
        car(c,911+84*easing(p),396,1.38)


def advice(c,heading,icon,label,t,p, *, emergency=False):
    field(c,"forest" if emergency else "paper")
    text="#f7fff3" if emergency else INK
    main="#f6d4c2" if emergency else "#326f61"
    words(c,heading,65,137,52,text,title=True)
    x=382+38*easing(p)
    ellipse(c,x,389,167,167,"#efddcb" if emergency else "#d3eadd",248)
    pictogram(c,icon,x,389,2.18+easing(p,0,.55)*.12,WARN if emergency else TEAL)
    pulse(c,x+81,462,t,main)
    for i,entry in enumerate(label):
        words(c,entry,638,340+i*57,38,text)


def p10(c,row,n):
    j,p,t=beat(row,n)
    if j==0:
        field(c)
        if p<.53:
            wrist_surface(c,2.17,115+32*easing(p),100,bruise=True)
        else:
            groin_surface(c,673,355,1.61+easing(p,.53,1)*.18,bruise=True)
        note(c,"Small bruise or mild soreness",640,662,align="center")
        return
    if p<.42:
        icon,label,local="pain",("Increasing pain,","redness or swelling"),p/.42
    elif p<.74:
        icon,label,local="drainage",("Fluid draining","from the site"),(p-.42)/.32
    else:
        icon,label,local="fever",("Fever",),(p-.74)/.26
    advice(c,"Contact your care team promptly",icon,label,t,local)


def p11(c,row,n):
    j,p,t=beat(row,n)
    header="Call your local emergency number"
    if j==0:
        field(c,"forest")
        groin_surface(c,650,345,1.43)
        glove(c,776,397-66*easing(p),.89,-1)
        words(c,header,65,129,52,LIGHT,title=True)
        note(c,"Apply firm pressure if bleeding",640,662,dark=True,align="center")
    elif j==1:
        if p<.58:
            advice(c,header,"bleed",("Heavy bleeding or","bleeding that won't stop"),t,p/.58,emergency=True)
        else:
            advice(c,header,"swelling",("Rapidly growing swelling",),t,(p-.58)/.42,emergency=True)
    elif p<.56:
        field(c,"forest")
        words(c,header,65,129,52,LIGHT,title=True)
        wrist_surface(c,1.30,-12+14*easing(p,0,.55),152,cool=True)
        words(c,"Suddenly cold, pale or",682,363,36,LIGHT)
        words(c,"numb hand or foot",682,413,36,LIGHT)
    elif p<.76:
        advice(c,header,"chest",("Severe chest pain",),t,(p-.56)/.20,emergency=True)
    else:
        advice(c,header,"breath",("Sudden trouble breathing",),t,(p-.76)/.24,emergency=True)


CREDIT_ARC=curve((28,712),((353,668),(443,621),(669,551)),((881,490),(1092,489),(1290,391)))


def p12(c,row,n):
    _,p,t=beat(row,n)
    field(c,"forest")
    line(c,CREDIT_ARC,"#3d756b",69)
    line(c,CREDIT_ARC,"#70aa99",32)
    line(c,path_part(CREDIT_ARC,easing(p,0,.94)),"#c7e8ca",7.8)
    for k in range(8):
        dot=path_part(CREDIT_ARC,(k*.151+t*.18)%1)[-1]
        ellipse(c,*dot,4.5,4.5,"#d5f1d5",200)
    brand(c,75,66,dark=True)
    words(c,"Cardiology Education Series",74,177,45,LIGHT,title=True)
    words(c,"Next episode",75,265,29,"#b6dfca")
    words(c,"What the sheath, guidewire,",74,332,41,LIGHT,title=True)
    words(c,"catheter and contrast each do",74,390,41,LIGHT,title=True)
    words(c,"Clinical sources in the description",75,481,30,"#d2edda")


SCENES={"P04":p04,"P05":p05,"P06":p06,"P08":p08,"P09":p09,"P10":p10,"P11":p11,"P12":p12}
