#!/usr/bin/env python3
"""Resume Wikimedia Commons photo collection; keep prior verified files and attribution."""
import json, pathlib, urllib.parse, urllib.request, urllib.error, time
root=pathlib.Path(__file__).resolve().parents[1]
source=json.loads((root/'scripts/photo_sources.json').read_text())
out=root/'assets/attractions';out.mkdir(parents=True,exist_ok=True)
previous_path=root/'scripts/photo_results.json'
previous={r['file']:r for r in json.loads(previous_path.read_text())} if previous_path.exists() else {}
headers={'User-Agent':'TDLPersonalGuidePhotoCollector/1.1 (personal educational project; Wikimedia Commons)'}
results=[]
for idx,name in enumerate(source['files']):
    default='assets/attractions/ride-%02d.jpg'%idx
    old=previous.get(name,{})
    old_path=old.get('local',default)
    if old.get('status')=='downloaded' and (root/old_path).is_file() and (root/old_path).stat().st_size>1000:
        results.append(old);print('kept',name,flush=True);continue
    record={'file':name,'local':default,'status':'failed'}
    try:
        query=urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':330,'titles':'File:'+name})
        req=urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+query,headers=headers)
        with urllib.request.urlopen(req,timeout=35) as resp:data=json.load(resp)
        page=next(iter(data.get('query',{}).get('pages',{}).values()))
        info=page.get('imageinfo',[None])[0]
        if not info:raise RuntimeError('Commons file not found')
        meta=info.get('extmetadata',{})
        record.update({'source_page':info.get('descriptionurl'),'license':meta.get('LicenseShortName',{}).get('value',''),'artist_html':meta.get('Artist',{}).get('value','')})
        url=info.get('thumburl') or info.get('url')
        if not url:raise RuntimeError('No image URL')
        request=urllib.request.Request(url,headers=headers)
        with urllib.request.urlopen(request,timeout=35) as resp:content=resp.read()
        if len(content)<1000 or not (content.startswith(b'\xff\xd8') or content.startswith(b'\x89PNG') or content.startswith(b'RIFF')):raise RuntimeError('Invalid image data')
        ext='.png' if content.startswith(b'\x89PNG') else '.webp' if content.startswith(b'RIFF') else '.jpg'
        local='assets/attractions/ride-%02d%s'%(idx,ext)
        (root/local).write_bytes(content)
        record.update({'status':'downloaded','local':local,'bytes':len(content)})
    except Exception as e:
        record['error']=str(e)[:250]
        if isinstance(e,urllib.error.HTTPError) and e.code==429:
            results.append(record)
            print('rate limited; stop politely and retry on a later run',flush=True)
            for remaining in source['files'][idx+1:]:
                results.append(previous.get(remaining,{'file':remaining,'status':'pending','local':'assets/attractions/ride-%02d.jpg'%source['files'].index(remaining)}))
            break
    results.append(record)
    print(record['status'],name,flush=True)
    time.sleep(2)
(root/'scripts/photo_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
manifest={r['file']:r['local'] for r in results if r.get('status')=='downloaded' and (root/r['local']).is_file()}
(root/'scripts/photo_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Saved and retained',len(manifest),'of',len(source['files']),'candidates')
