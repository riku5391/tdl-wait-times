#!/usr/bin/env python3
"""Fetch existing Commons-licensed ride photo candidates into local GitHub Pages assets.
Source metadata is retained for attribution and license review; no unverified substitutions.
"""
import json, pathlib, urllib.parse, urllib.request, time, sys
root=pathlib.Path(__file__).resolve().parents[1]
source=json.loads((root/'scripts/photo_sources.json').read_text())
out=root/'assets/attractions';out.mkdir(parents=True,exist_ok=True)
results=[]
headers={'User-Agent':'TDLPersonalGuidePhotoCollector/1.0 (educational personal project; Wikimedia Commons API)'}
for idx,name in enumerate(source['files']):
    key=f'ride-{idx:02d}.jpg'; dest=out/key
    record={'file':name,'local':'assets/attractions/'+key,'status':'failed'}
    try:
        query=urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':330,'titles':'File:'+name})
        req=urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+query,headers=headers)
        with urllib.request.urlopen(req,timeout=25) as resp: data=json.load(resp)
        page=next(iter(data.get('query',{}).get('pages',{}).values()))
        info=page.get('imageinfo',[None])[0]
        if not info: raise RuntimeError('Commons file not found')
        url=info.get('thumburl') or info.get('url')
        meta=info.get('extmetadata',{})
        record.update({'source_page':info.get('descriptionurl'),'license':meta.get('LicenseShortName',{}).get('value',''),'artist_html':meta.get('Artist',{}).get('value','')})
        if not url:raise RuntimeError('No image URL')
        request=urllib.request.Request(url,headers=headers)
        with urllib.request.urlopen(request,timeout=30) as resp: content=resp.read()
        if len(content)<1000 or not (content.startswith(b'\xff\xd8') or content.startswith(b'\x89PNG') or content.startswith(b'RIFF')):raise RuntimeError('Invalid image data')
        ext='.png' if content.startswith(b'\x89PNG') else '.webp' if content.startswith(b'RIFF') else '.jpg'
        record['local']='assets/attractions/ride-%02d%s'%(idx,ext)
        dest=out/('ride-%02d%s'%(idx,ext));dest.write_bytes(content)
        record.update({'status':'downloaded','bytes':len(content)})
    except Exception as e:record['error']=str(e)[:250]
    results.append(record)
    print(record['status'],name,flush=True)
    time.sleep(.2)
(root/'scripts/photo_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
manifest={r['file']:r['local'] for r in results if r['status']=='downloaded'}
(root/'scripts/photo_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Downloaded',len(manifest),'of',len(results),'unique candidates')
