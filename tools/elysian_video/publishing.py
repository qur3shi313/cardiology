"""Prepare factual episode metadata from the locked release and source records."""
import json
import re

from .__main__ import SERIES

def chapters(timeline):
    fps=timeline['fps']
    last=-1000
    result=[]
    for scene in timeline['scenes']:
        start=scene['start_frame']//fps
        if start-last<10 or timeline['duration_frames']/fps-start<10:
            continue
        result.append(f'{start//60:02}:{start%60:02} {scene["title"]}')
        last=start
    return result

def sources(episode):
    text=(episode/'SOURCES.md').read_text(encoding='utf-8-sig')
    out=[]
    seen=set()
    for title,url in re.findall(r'\[([^\]\n]+)\]\((https?://[^\s)]+)\)',text):
        if url in seen: continue
        seen.add(url)
        out.append(f'{title}\n{url}')
    if not out: raise ValueError(f'No public clinical source links for {episode.name}')
    return out[:7]

def create():
    ledger=json.loads((SERIES/'schedule.json').read_text(encoding='utf-8-sig'))
    for row in ledger['targets']:
        number=row['topic']
        if number==1:continue
        episode=SERIES/row['episode']
        timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
        if (episode/'youtube-metadata.json').exists():
            continue
        opener=timeline['scenes'][0]['narration']
        section='\n'.join(chapters(timeline))
        refs='\n'.join(sources(episode))
        description=(f'{opener}\n\n{section}\n\n'
            'This educational animation uses original illustrations and synthetic English narration. '
            'Any X-ray, ultrasound or CT views shown are illustrative. Procedures and recovery plans vary. '
            'Follow your own care team’s advice.\n\n'
            f'Clinical sources:\n{refs}\n\n'
            f'Cardiology Education Series · Episode {number}\nElysian Biomedical LLP\n')
        if len(description)>5000: raise ValueError(f'Description too long for {episode.name}')
        title=row['title']
        branded=f'{title} | Elysian Biomedical LLP'
        title=branded if len(branded)<=100 else title
        metadata={'title':title,'description_file':'youtube-description.txt',
                  'tags':['cardiology education','cardiology explained','Elysian Biomedical LLP',row['title']],
                  'language':'en','planned_release':row['target'],'timezone':ledger['timezone'],
                  'studio_release_verified':False,'watch_url':None}
        (episode/'youtube-description.txt').write_bytes(description.encode('utf-8'))
        (episode/'youtube-metadata.json').write_bytes((json.dumps(metadata,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))

if __name__=='__main__':
    create()
