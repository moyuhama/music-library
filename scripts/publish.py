#!/usr/bin/env python3
"""Index music/<type>/<artist>/<album>/ and optionally commit/push to GitHub."""
import argparse,hashlib,json,pathlib,subprocess,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parent.parent
RAW='https://raw.githubusercontent.com/moyuhama/music-library/main/'
AUDIO={'.mp3','.m4a','.flac','.wav','.ogg','.opus','.aac','.aiff','.webm'}
def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def raw(file):return RAW+urllib.parse.quote(file.relative_to(ROOT).as_posix(),safe='/')
def run(*args,**kw):return subprocess.run(args,check=True,text=True,**kw)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publish',action='store_true');args=parser.parse_args();rows=[]
    previous=json.loads((ROOT/'catalog.json').read_text()) if (ROOT/'catalog.json').exists() else {'tracks':[]}
    known={t.get('sha256'):t for t in previous['tracks']}
    by_path={t.get('path'):t for t in previous['tracks']}
    used=set()
    for file in sorted((ROOT/'music').rglob('*')):
        if not file.is_file() or file.is_symlink() or file.suffix.lower() not in AUDIO:continue
        if file.stat().st_size>=100*1024**2:parser.error(f'{file.name} exceeds GitHub single-file limit')
        info=json.loads(run('ffprobe','-v','quiet','-print_format','json','-show_format',str(file),capture_output=True).stdout).get('format',{})
        tags=info.get('tags',{});checksum=digest(file);relative=file.relative_to(ROOT).as_posix()
        old=by_path.get(relative) or known.get(checksum,{})
        identifier=old.get('id')
        if not identifier or identifier in used:identifier='bundled-'+hashlib.sha256(relative.encode()).hexdigest()[:24]
        used.add(identifier)
        row={'id':identifier,'title':tags.get('title') or file.stem,'artist':tags.get('artist') or old.get('artist') or file.parent.parent.name,'album':tags.get('album') or file.parent.name,'path':relative,'url':raw(file),'sha256':checksum,'bytes':file.stat().st_size,'duration':float(info.get('duration',0)),'hosted':True}
        cover=next((file.parent/name for name in ['cover.jpg','cover.png','folder.jpg','cover.webp'] if (file.parent/name).is_file()),None)
        if cover:row['cover']=raw(cover)
        subtitles=[]
        for fmt in ['lrc','srt','vtt','txt']:
            sidecar=file.with_suffix('.'+fmt)
            if sidecar.is_file():
                text=sidecar.read_text(encoding='utf-8-sig')
                if fmt=='lrc':row['lyricText']=text
                else:subtitles.append({'text':text,'format':fmt})
        if subtitles:row['subtitles']=subtitles
        rows.append(row)
    if not rows:parser.error('No music found; existing index left unchanged')
    catalog={'version':1,'repository':'https://github.com/moyuhama/music-library','tracks':rows}
    (ROOT/('catalog.json' if args.publish else 'catalog.preview.json')).write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(rows)} tracks, {sum(t["bytes"] for t in rows)/1024**2:.1f} MiB',flush=True)
    if args.publish:
        run('git','-C',str(ROOT),'add','music','catalog.json')
        if subprocess.run(['git','-C',str(ROOT),'diff','--cached','--quiet']).returncode:run('git','-C',str(ROOT),'commit','-m',f'Update organized music library ({len(rows)} tracks)')
        run('git','-c','http.version=HTTP/1.1','-C',str(ROOT),'push')
if __name__=='__main__':main()
