"""Original home, rehabilitation, and warning-sign illustrations for ICU recovery."""

from math import cos, pi, sin

import skia

from . import access as art
from . import angiogram
from . import cabg_graft as gfx
from . import cabg_recovery as recovery


INK = '#18493e'
MUTED = '#406d5f'
CREAM = '#edf5ee'
TOPIC = 'CARDIAC SURGERY'
WINE = '#692e36'
WINE_INK = '#743740'


def header(canvas, label, dark=False):
    angiogram.header(canvas, label, TOPIC, dark)


def round_box(canvas, x, y, w, h, r, shade, opacity=255):
    gfx.rounded(canvas, x, y, w, h, r, shade, opacity)


def shape(canvas, points, shade):
    canvas.drawPath(art.path(points, True), art.solid(shade))


def draw_window(canvas, seconds):
    round_box(canvas, 70, 192, 413, 303, 10, '#8eb4a3')
    glass = skia.Rect.MakeXYWH(83, 207, 387, 271)
    canvas.drawRect(glass, art.grad(90, 225, 449, 477, ['#daecdb', '#eff1d0', '#accbb4']))
    daylight = (seconds*.17)%1
    sun_x = 91 + daylight*288
    gfx.oval(canvas, sun_x, 236+(1-daylight)*48, 82, 82, art.solid('#f6d585', 202))
    shape(canvas, ((84, 429), (146, 403), (239, 425), (314, 386), (373, 402), (470, 375),
                   (470, 477), (84, 477)), '#b1cbbc')
    art.line(canvas, ((276, 205), (276, 477)), '#e6f3e8', 8)
    art.line(canvas, ((84, 340), (470, 340)), '#e5f1e6', 7)
    edge = 294 + 210*daylight
    shape(canvas, ((94, 480), (434, 480), (edge+226, 546), (edge-94, 546)), '#e5e8b2')


def seated_patient(canvas, x, y, seconds):
    """A covered, anonymous patient facing the window or clinician."""
    sway = 14*sin(seconds*1.72)
    shoulder = y+71+sway
    round_box(canvas, x-122, y+18, 115, 211, 37, '#9bbbad')
    round_box(canvas, x-110, y+204, 223, 51, 18, '#82a799')
    art.line(canvas, ((x-92, y+245), (x-112, y+320)), '#679285', 17)
    art.line(canvas, ((x+84, y+245), (x+92, y+320)), '#679285', 17)
    art.line(canvas, ((x+23, y+193), (x+86, y+242), (x+100, y+301)), '#4a6b65', 50)
    art.line(canvas, ((x+102, y+301), (x+141, y+301)), '#274944', 23)
    body = gfx.ANATOMY.curve((x-62, shoulder+103),
                             ((x-82, shoulder+62),(x-65,shoulder+16),(x-35,shoulder)),
                             ((x+18,shoulder-20),(x+56,shoulder+9),(x+65,shoulder+53)),
                             ((x+82,shoulder+87),(x+47,shoulder+108),(x-62,shoulder+103)))
    canvas.drawPath(art.path(body, True),
                    art.grad(x-68, shoulder, x+63, shoulder+112, ['#d5dbc2', '#a6ad87', '#78866b']))
    gfx.oval(canvas, x-48, y-18+sway, 104, 115, art.solid('#ba967b'))
    gfx.oval(canvas, x-48, y-24+sway, 103, 62, art.solid('#7d9883'))
    art.line(canvas, ((x-40, y+56+sway), (x-37, shoulder+17)), '#77917f', 15)
    reach = 28 + 25*sin(seconds*2.65)
    art.line(canvas, ((x+32, shoulder+20),(x+57,shoulder+55),(x+66+reach,shoulder+58)),
             '#95a486', 27)
    angiogram.dot(canvas, x+67+reach, shoulder+57, 10, '#c8a386')


def home_scene(canvas, seconds, progress, stage):
    art.rect(canvas, 0, 0, 1280, 720,
             art.grad(43, 164, 1128, 667, ['#faf9ed', '#e7f1e5', '#b7d2c2']))
    art.rect(canvas, 0, 492, 1280, 228, art.solid('#c4d9ce'))
    for x in range(85, 1280, 153):
        art.line(canvas, ((620+(x-620)*.47, 492), (x, 654)), '#d7e7db', 2.2)
    draw_window(canvas, seconds)
    if stage == 'walk':
        recovery.covered_walker(canvas, 541+264*progress, 606, seconds,
                                ('#7f9072', '#bfc8a9'))
        round_box(canvas, 948, 233, 249, 256, 22, '#3d7666')
        round_box(canvas, 963, 248, 219, 226, 16, '#ecf6eb')
        art.text(canvas, 'MY PLAN', 988, 302, 32, INK)
        for i, line in enumerate(('Activity', 'Medicines')):
            y = 367 + 54*i
            art.line(canvas, ((988, y-6), (998, y+4), (1016, y-12)), '#59987f', 6)
            art.text(canvas, line, 1025, y+3, 28, MUTED)
    else:
        seated_patient(canvas, 684, 270, seconds)
        round_box(canvas, 870, 512, 265, 30, 7, '#6e9484')
        art.line(canvas, ((893, 540),(880, 608)), '#648c7c', 15)
        art.line(canvas, ((1108, 540),(1119, 608)), '#648c7c', 15)
        gfx.oval(canvas, 916, 477, 111, 42, art.solid('#a2b7aa'))
        gfx.oval(canvas, 923, 477, 96, 36, art.solid('#f3f3e4'))
        gfx.oval(canvas, 943, 488, 55, 13, art.solid('#cba36e'))
        round_box(canvas, 1041, 452, 62, 65, 10, '#e9f1de')
        art.line(canvas, ((1063, 451),(1076, 436+6*sin(seconds)),(1062, 419)), '#f6f7e9', 3, 175)
    header(canvas, 'Recovery continues at home')
    if stage == 'rest':
        gfx.footer(canvas, 'Tell your team if tiredness, appetite, sleep or mood changes persist')
    else:
        gfx.footer(canvas, 'Build activity gradually and follow your individual plan')


def rehabilitation(canvas, seconds, progress):
    recovery.mobility(canvas, seconds, art.smooth(progress), True)
    header(canvas, 'Cardiac rehabilitation')
    gfx.footer(canvas, 'Supervised activity, heart-health education and support')


def consultation(canvas, seconds, progress, caption):
    gfx.studio_light(canvas)
    seated_patient(canvas, 243, 257, seconds)
    gfx.consultation_figure(canvas, 1052, 220, 1.75,
                            ('#82b49e', '#5c907c', '#376958'), -1, seconds+.7)
    shape(canvas, ((334, 450),(852, 429),(1136, 556),(1112, 603),(260, 603)), '#b5d0c0')
    art.line(canvas, ((334, 450),(852, 429),(1136, 556)), '#deeee1', 5)
    canvas.save()
    canvas.translate(636, 477)
    canvas.rotate(-11 + 20*progress)
    round_box(canvas, -164, -141, 344, 238, 18, '#729c89')
    round_box(canvas, -177, -154, 344, 238, 18, '#f3f8ef')
    art.text(canvas, 'FOLLOW-UP', -126, -94, 32, INK)
    for i, label in enumerate(('Symptoms', 'Prevention plan')):
        y = -34 + 61*i
        length = 150 * ((seconds*.44 + .30*i)%1)
        art.line(canvas, ((-129, y+20),(-129+length, y+20)), '#a2cab5', 5)
        art.text(canvas, label, -129, y, 27, MUTED)
    canvas.restore()
    if caption:
        header(canvas, 'Follow-up after bypass')
        gfx.footer(canvas, caption)


def at_home(canvas, progress, seconds, cues):
    activity = cues.get('activity', .28)
    rehab = cues.get('rehab', .53)
    follow = cues.get('follow', .79)
    if progress < activity:
        home_scene(canvas, seconds, progress/activity, 'rest')
    elif progress < rehab:
        home_scene(canvas, seconds, (progress-activity)/(rehab-activity), 'walk')
    elif progress < follow:
        rehabilitation(canvas, seconds, (progress-rehab)/(follow-rehab))
    else:
        consultation(canvas, seconds, (progress-follow)/(1-follow),
                     'Ask about local rehabilitation and review your long-term plan')


def emergency_banner(canvas):
    """One fixed action across all emergency symptom examples."""
    art.rect(canvas, 0, 605, 1280, 115, art.solid(WINE))
    art.text(canvas, 'Call your local emergency number now', 56, 676, 51, '#fff6ed')


def call_promptly(canvas, progress, seconds):
    recovery.dressing(canvas, progress, seconds)
    # The source dressing scene illustrates a covered wound. Replace its
    # editorial footer with this episode's stronger, stable care-team instruction.
    art.rect(canvas, 0, 607, 1280, 113, art.solid('#e3eee2'))
    art.text(canvas, 'Contact your care team promptly', 55, 657, 45, INK)
    art.text(canvas, 'Use your urgent contact instructions if the team is unavailable',
             56, 697, 28, MUTED, art.REGULAR)


def breath_figure(canvas, seconds, zoom):
    # Broad breathing movement through a high-neck sweater, with the shoulders
    # visibly moving. The illustration makes no diagnosis or oxygen reading.
    x, y = 935, 348
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(zoom, zoom)
    canvas.translate(-x, -y)
    lift = 19*(.5+.5*cos(seconds*4.3))
    body = gfx.ANATOMY.curve((x-179, y+233),
                            ((x-171,y+108),(x-131,y+52-lift),(x-48,y+38-lift)),
                            ((x+37,y+21-lift),(x+161,y+41),(x+178,y+233)))
    canvas.drawPath(art.path(body, True),
                    art.grad(x-144, y+21, x+158, y+230, ['#a5c3b2', '#638e7e', '#426b60']))
    round_box(canvas, x-49, y+11-lift*.5, 100, 49, 21, '#51796c')
    gfx.oval(canvas, x-63, y-133, 126, 161,
             art.grad(x-64,y-132,x+64,y+35,['#e1c3a5','#bf9a81','#997965']))
    gfx.oval(canvas, x-68, y-144, 138, 85, art.solid('#799c8a'))
    gfx.oval(canvas, x+6, y-9, 22, 14+9*sin(seconds*4.3)**2, art.solid('#93625b'))
    for i in range(3):
        sweep = ((seconds*.94+i*.25)%1)
        arch = gfx.ANATOMY.curve((x+45,y-2+16*i),
                                ((x+86+sweep*35,y-2+14*i),(x+109+sweep*55,y+7+14*i),
                                 (x+135+sweep*59,y+19+14*i)))
        art.line(canvas, arch, '#ae726a', 6+3*(1-sweep), round(157*(1-sweep)))
    canvas.restore()


def emergency_example(canvas, seconds, progress, kind):
    art.rect(canvas, 0, 0, 1280, 720,
             art.grad(0, 0, 1280, 720, ['#fcf8ee', '#eee7df', '#dac6be']))
    header(canvas, 'When to get emergency help')
    if kind == 'breathing':
        breath_figure(canvas, seconds, 1 + .24*art.smooth(progress))
        lines = ('Severe trouble', 'breathing')
        sign = ''
    else:
        phase = {'face': 0, 'arm': 1, 'speech': 2, 'stroke': 0}.get(kind, 0)
        canvas.save()
        canvas.translate(938, 375)
        zoom = 1+.25*art.smooth(progress)
        canvas.scale(zoom, zoom)
        canvas.translate(-938, -375)
        recovery.symptom_figure(canvas, seconds, 'chest' if kind == 'chest' else 'stroke', phase)
        canvas.restore()
        if kind == 'chest':
            lines = ('Sudden chest pressure', 'that does not go away')
            sign = ''
        else:
            lines = ('Possible stroke',)
            sign = {'stroke':'Any one sign is enough', 'face':'Drooping face',
                    'arm':'Sudden arm weakness', 'speech':'Difficulty speaking'}[kind]
    for i, line in enumerate(lines):
        art.text(canvas, line, 54, 312 + i*66, 55 if len(lines)==1 else 48,
                 WINE_INK, art.HEADING)
    if sign:
        art.text(canvas, sign, 55, 403, 40, WINE_INK)
    emergency_banner(canvas)


def get_help(canvas, progress, seconds, cues):
    emergency = cues.get('emergency', .33)
    breathing = cues.get('breathing', .54)
    stroke = cues.get('stroke', .63)
    face = cues.get('face', .67)
    arm = cues.get('arm', .75)
    speech = cues.get('speech', .82)
    any_sign = cues.get('any', .90)
    if progress < emergency:
        call_promptly(canvas, progress/emergency, seconds)
        return
    marks = (emergency, breathing, stroke, face, arm, speech, any_sign, 1.)
    options = ('chest','breathing','stroke','face','arm','speech','stroke')
    shot = min(len(options)-1, sum(progress >= mark for mark in marks[1:]))
    length = max(.001, marks[shot+1]-marks[shot])
    emergency_example(canvas, seconds, min(1, (progress-marks[shot])/length), options[shot])


def credits(canvas):
    art.rect(canvas, 0, 0, 1280, 720, art.solid('#183d34'))
    header(canvas, 'Clinical sources', True)
    lines = ('NHLBI and NHS · Recovery after bypass',
             'Leeds Teaching Hospitals · Recovery and activity',
             'ERAS Cardiac Society and STS · Perioperative care',
             'American Heart Association · Prevention after bypass',
             'NHS and CDC · Warning signs')
    for i, label in enumerate(lines):
        art.text(canvas, label, 55, 219+48*i, 31, '#e2f2e6')
    art.line(canvas, ((55, 453),(1200, 453)), '#6e9b8b', 2)
    art.text(canvas, 'Original educational animation · Synthetic English narration',
             54, 509, 30, '#c2dfd1', art.REGULAR)
    art.text(canvas, 'Next in the series', 54, 564, 28, '#c2dfd1', art.REGULAR)
    art.text(canvas, 'Surgical aortic valve replacement', 54, 617, 40, '#f0f7ec', art.HEADING)


def recap(canvas, progress, seconds, cues):
    move = cues.get('move', .18)
    contact = cues.get('contact', .36)
    next_episode = cues.get('next', .52)
    nominal_duration = seconds/progress if progress else 25.
    source = cues.get('credits', max(0, (nominal_duration-8)/nominal_duration))
    if progress >= source:
        credits(canvas)
        return
    if progress < move:
        recovery.bedside(canvas, seconds, True)
        title = 'What are you watching?'
    elif progress < contact:
        recovery.mobility(canvas, seconds, (progress-move)/(contact-move), False)
        title = 'What can I safely do next?'
    else:
        consultation(canvas, seconds, min(1, (progress-contact)/(source-contact)),
                     None)
        title = ('Whom do I call?' if progress < next_episode else
                 'Next in the series')
        caption = ('Keep your own discharge instructions close by' if progress < next_episode
                   else 'Surgical aortic valve replacement')
        gfx.footer(canvas, caption)
    # The matching footage is held; only its recap title changes with the voice.
    art.rect(canvas, 0, 0, 1280, 153, art.solid(CREAM))
    header(canvas, title)


SCENES = {'P07': at_home, 'P08': get_help, 'P09': recap}


def draw(canvas, ident, progress, seconds, *, cues=None):
    """Draw one complete scene with optional narration-derived fractional cues."""
    SCENES[ident](canvas, progress, seconds, cues or {})
