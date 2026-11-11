"""Opening, final assessment, and recovery scenes for the complete PCI film."""
from bisect import bisect_right

from . import access, angiogram, stent as art

SCENES={
 'P01':('Coronary angioplasty and stent placement',
        (('A coronary narrowing','The artery channel is narrower here','narrow'),
         ('One possible treatment','Angioplasty can widen the channel','balloon'))),
 'P02':('Why the artery narrows',
        (('An open coronary artery','The artery carries blood to heart muscle','open'),
         ('Plaque can narrow the channel','Plaque builds in the artery wall','narrow'),
         ('An acute clot is different','A clot can suddenly limit blood flow','pulse'))),
 'P03':('From diagnosis to treatment',
        (('The images show the channel','Contrast outlines the coronary arteries','check'),
         ('Treatment depends on the findings','Options may include medicines or a procedure','medicine'),
         ('Same session or planned later','The treating team decides what fits','list'))),
 'P04':('The guide catheter',
        (('An access sheath stays at the entry','Wrist or groin access','band'),
         ('The guide catheter reaches the ostium','The coronary opening is above the valve','vessel'))),
 'P11':('Checking the treated segment',
        (('Check the contrast flow','Look at the artery beyond the stent','open'),
         ('Inside-the-artery imaging','Selected cases: assess how the mesh opened','check'))),
 'P12':('Removing the equipment',
        (('The wire and catheter come out','The expanded stent stays in place','vessel'),
         ('Wrist compression','A band helps control bleeding','band'),
         ('Groin closure','The method depends on the access site','check'))),
 'P13':('Recovery and discharge',
        (('Checks after the procedure','Pulse, blood pressure and the access site','pulse'),
         ('Your individual discharge plan','Activity, dressing, medicines and follow-up','list'),
         ('Timing varies','Ask your team about your recovery','clock'))),
 'P14':('Why antiplatelet medicines are used',
        (('Platelets can form a clot','Antiplatelets make them less likely to clump','vessel'),
         ('Your care team chooses the plan','It accounts for your situation and bleeding risk','medicine'),
         ('Ask before changing medicines','Follow the prescription you receive','call'))),
 'P15':('Aftercare and urgent symptoms',
        (('Follow the written instructions','Ask about activity and wound care','list'),
         ('Get emergency help for severe symptoms','Persistent chest pain, bleeding, or a cold limb','call'),
         ('Discuss follow-up','Ask about cardiac rehabilitation','pulse'))),
 'P16':('What treatment changes',
        (('One section receives support','The stent stays in the treated segment','vessel'),
         ('Coronary disease still needs care','Confirm medicines, activity and follow-up','check'))),
 'P17':('Clinical sources',
        (('Coronary angioplasty and stenting','American Heart Association','vessel'),
         ('Recovery and patient information','NHS coronary angioplasty guidance','list'),
         ('Device sequence','FDA-hosted coronary stent labeling','check'))),
}
MARKS={
 'P01':(.0,.36),'P02':(.0,.26,.64),'P03':(.0,.34,.64),'P04':(.0,.52),
 'P11':(.0,.62),'P12':(.0,.39,.70),'P13':(.0,.34,.69),'P14':(.0,.40,.70),
 'P15':(.0,.27,.75),'P16':(.0,.44),'P17':(.0,.33,.66),
}

def wire_out(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e5efe7'))
    s=art.Motion(1126-(1126+90)*access.smooth(p),-280,12,art.LESION,116,1,1)
    lumen=art.artery(c,1)
    art.blood_flow(c,t,s,lumen)
    art.stent(c,art.LESION,116,False)
    art.wire(c,s.wire_tip)
    art.stent(c,art.LESION,116,True)
    angiogram.header(c,'The wire comes out','CORONARY ANGIOPLASTY')
    access.text(c,'The expanded stent stays in place',55,677,33,'#245c50')

def draw(c,ident,p,t):
    title,beats=SCENES[ident]
    stops=MARKS[ident]
    i=bisect_right(stops,p)-1
    a,b=stops[i],stops[i+1] if i+1<len(stops) else 1
    local=(p-a)/(b-a)
    label,detail,icon=beats[i]
    if ident=='P01' and i==0:
        # The hook is a moving contrast view of the narrowed example.
        angiogram.imaging(c,'P29',p/.36,t,0)
        return
    if ident=='P03' and i==0:
        angiogram.imaging(c,'P25',p/.34,t,0)
        return
    if ident=='P04' and i==1:
        angiogram.show_root(c,'P24',.49+.51*local,t,0)
        access.rect(c,0,71,1280,72,access.solid('#eaf4eb'))
        access.text(c,'Guide catheter at the coronary opening',55,132,48,'#153e36',access.HEADING)
        return
    if ident=='P11':
        from .coating import summary
        summary(c,'P06',local*.55 if i==0 else .55+.45*local,t)
        return
    if ident=='P12' and i==0:
        if local<.55:
            wire_out(c,local/.55,t)
        else:
            angiogram.show_root(c,'P26',(local-.55)/.45,t,0)
        return
    if ident=='P12' and i==1:
        access.scene(c,'P35',local,t)
        return
    access.rect(c,0,0,1280,720,access.solid('#e9f2eb'))
    angiogram.header(c,title,'CORONARY ANGIOPLASTY')
    angiogram.block(c,680,190,511,407,37,access.solid('#183d36'))
    angiogram.icon(c,icon,local,t)
    access.text(c,label,55,314,32,'#004b3d')
    access.text(c,detail,55,375,25,'#333b39',access.REGULAR)
    for j in range(len(beats)):
        angiogram.block(c,57+j*58,552,41,7,4,access.solid('#287665' if j==i else '#a9c7b9'))
    access.text(c,('Next: How drug-eluting stents work' if ident=='P17' else 'Follow your own care team’s advice'),
                55,665,28,'#2d6154',access.REGULAR)
