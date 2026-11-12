"""Attach an approved episode's exact files to its GitHub release."""
from hashlib import sha256
from http.client import HTTPSConnection
import argparse
import json
import mimetypes
import os
from pathlib import Path
import subprocess
from urllib.parse import urlencode

from .__main__ import ROOT, SERIES

OWNER,REPO='qur3shi313','cardiology'
REPO_PATH=f'/repos/{OWNER}/{REPO}'

def hash_file(path):
    with path.open('rb') as f:
        return sha256_file(f)

def sha256_file(f):
    h=sha256()
    for block in iter(lambda:f.read(1024*1024),b''):
        h.update(block)
    return h.hexdigest()

def credential(repo):
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
    command=['git','-C',str(repo)]
    remote=subprocess.run(command+['remote','get-url','origin'],capture_output=True,text=True,
                          check=True,env=env).stdout.strip()
    if remote.rstrip('/') not in (f'https://github.com/{OWNER}/{REPO}.git',
                                  f'https://github.com/{OWNER}/{REPO}'):
        raise ValueError('This delivery tool is scoped to the authorised cardiology repository')
    data=f'protocol=https\nhost=github.com\nusername={OWNER}\n\n'
    r=subprocess.run(command+['credential','fill'],input=data,capture_output=True,text=True,env=env)
    if r.returncode: raise RuntimeError('The existing GitHub credential is unavailable')
    for line in r.stdout.splitlines():
        if line.startswith('password='):
            return line.split('=',1)[1]
    raise RuntimeError('No usable GitHub token from the configured credential helper')

class GitHub:
    def __init__(self,token):
        self.token=token

    def request(self,method,host,path,payload=None,asset=None):
        if host not in ('api.github.com','uploads.github.com') or not path.startswith(REPO_PATH):
            raise ValueError('Refusing to send an authenticated request outside this repository')
        headers={'Authorization':f'Bearer {self.token}','Accept':'application/vnd.github+json',
                 'X-GitHub-Api-Version':'2026-03-10','User-Agent':'Elysian-Cardiology-Delivery'}
        conn=HTTPSConnection(host,timeout=180)
        try:
            if asset:
                headers['Content-Type']=mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
                headers['Content-Length']=str(asset.stat().st_size)
                with asset.open('rb') as body:
                    conn.request(method,path,body=body,headers=headers)
            else:
                body=None if payload is None else json.dumps(payload).encode('utf-8')
                if body:
                    headers['Content-Type']='application/json'
                conn.request(method,path,body=body,headers=headers)
            response=conn.getresponse()
            body=response.read()
            if method == 'DELETE' and response.status == 204:
                return None
            if response.status not in (200,201):
                raise RuntimeError(f'GitHub returned HTTP {response.status} for this repository action')
            return json.loads(body)
        finally:
            conn.close()

def files(episode,qa):
    if qa.get('status')!='pass' or qa.get('halal_review')!='pass' or qa.get('errors'):
        raise ValueError('Publish only a fully reviewed delivery package')
    delivery=episode/'delivery'
    paths=[delivery/qa['input']]
    if hash_file(paths[0])!=qa['sha256']:
        raise ValueError('The master changed after review')
    for k in ('1080p','short','thumbnail'):
        artifact=qa['deliverables'][k]
        p=delivery/artifact['file']
        if hash_file(p)!=artifact['sha256']:
            raise ValueError(f'The {k} file changed after review')
        paths.append(p)
    t=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    return paths+[episode/t.get('caption_file','captions.en.srt'),episode/'chapters.txt',episode/'QA.json']

def release(number,repo,package=None):
    episode_name=f'episode-{number:02}'
    episode=package.resolve() if package else SERIES/episode_name
    if episode.name!=episode_name or not episode.is_relative_to(SERIES.resolve()):
        raise ValueError('The package must be for this episode inside the series directory')
    report=json.loads((episode/'QA.json').read_text(encoding='utf-8-sig'))
    sources=files(episode,report)
    for path in sources:
        if not 0<path.stat().st_size<2*1024**3:
            raise ValueError(f'Invalid GitHub release asset size: {path.name}')
    metadata=json.loads((episode/'youtube-metadata.json').read_text(encoding='utf-8-sig'))
    api=GitHub(credential(repo))
    request=lambda method,path,body=None:api.request(method,'api.github.com',REPO_PATH+path,body)
    tag=f'cardiology-v2-episode-{number:02}'
    existing=request('GET','/releases?per_page=100')
    matches=[x for x in existing if x['tag_name']==tag]
    if len(matches)>1:
        raise ValueError(f'Ambiguous existing release for {tag}')
    if matches:
        current=matches[0]
    else:
        current=request('POST','/releases',{'tag_name':tag,'target_commitish':'main',
                 'name':metadata['title'],'draft':True,'prerelease':False,
                 'body':'Completed education film, captioned vertical edit, and exact media review record.'})
    id=current['id']
    prior={x['name']:x for x in request('GET',f'/releases/{id}/assets?per_page=100')}
    for p in sources:
        before=prior.get(p.name)
        digest='sha256:'+hash_file(p)
        if before:
            if before.get('digest') == digest and before.get('state') == 'uploaded':
                continue
            if not current['draft'] or before.get('state') != 'starter' or before.get('digest'):
                raise ValueError(f'Existing asset differs from the approved file: {p.name}')
            # GitHub can leave an incomplete placeholder when a transfer is interrupted.
            request('DELETE', f"/releases/assets/{before['id']}")
            print(f'Restarting incomplete draft transfer for {p.name}', flush=True)
        response=api.request('POST','uploads.github.com',
            REPO_PATH+f'/releases/{id}/assets?'+urlencode({'name':p.name}),asset=p)
        if response.get('digest')!=digest or response.get('size')!=p.stat().st_size:
            raise ValueError(f'GitHub did not verify the exact uploaded bytes: {p.name}')
        print(f'Verified {p.name}',flush=True)
    if current['draft']:
        current=request('PATCH',f'/releases/{id}',{'draft':False})
    if current.get('draft'):
        raise RuntimeError('GitHub did not publish the release')
    verified=request('GET',f'/releases/{id}/assets?per_page=100')
    record={'tag':tag,'release_url':current['html_url'],
            'assets':[{'name':x['name'],'size':x['size'],'digest':x['digest'],'url':x['browser_download_url']}
                      for x in verified]}
    (episode/'github-release.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
    print(record['release_url'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('episode',type=int,choices=range(1,21))
    p.add_argument('--repo',type=Path,default=ROOT/'work/github-cardiology')
    p.add_argument('--package',type=Path,help='Use a reviewed revision of this episode')
    args=p.parse_args()
    release(args.episode,args.repo.resolve(),args.package)
