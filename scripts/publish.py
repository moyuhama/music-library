#!/usr/bin/env python3
"""Index a local audio folder and publish only new audio to GitHub Releases."""
import argparse, hashlib, json, pathlib, shutil, subprocess, tempfile, urllib.parse, concurrent.futures
ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = 'moyuhama/music-library'
TAG = 'audio-v1'
AUDIO = {'.mp3','.m4a','.flac','.wav','.ogg','.opus','.aac','.aiff','.webm'}
def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)
def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024), b''): h.update(part)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=pathlib.Path)
    parser.add_argument('--publish', action='store_true', help='Upload new audio; then atomically publish index by pushing Git')
    args=parser.parse_args(); folder=args.folder.resolve()
    if not folder.is_dir(): parser.error('Audio folder does not exist')
    tracks=[]; uploads={}
    for file in sorted(folder.rglob('*')):
        if not file.is_file() or file.is_symlink() or file.suffix.lower() not in AUDIO: continue
        relative=file.relative_to(folder).as_posix()
        identifier='bundled-'+hashlib.sha256(relative.encode()).hexdigest()[:24]
        mediahash=digest(file); asset=mediahash+file.suffix.lower()
        probe=run('ffprobe','-v','quiet','-print_format','json','-show_format',str(file),capture_output=True)
        info=json.loads(probe.stdout).get('format',{}); tags=info.get('tags',{})
        title=tags.get('title') or file.stem
        artist=tags.get('artist') or ('郭德纲 / 于谦' if '郭德纲' in file.stem and '于谦' in file.stem else '郭德纲' if '郭德纲' in file.stem else '未知歌手')
        row={'id':identifier,'title':title,'artist':artist,'album':tags.get('album') or (file.parent.name if file.parent!=folder else '本地音乐'),'path':relative,'url':f'https://github.com/{REPO}/releases/download/{TAG}/{asset}','sha256':mediahash,'bytes':file.stat().st_size,'duration':float(info.get('duration',0)), 'hosted':True}
        cover=next((file.parent/name for name in ['cover.jpg','cover.png','folder.jpg','cover.webp'] if (file.parent/name).is_file()),None)
        if cover:
            name=digest(cover)+cover.suffix.lower(); target=ROOT/'covers'/name; target.parent.mkdir(exist_ok=True)
            if not target.exists(): shutil.copy2(cover,target)
            row['cover']=f'https://raw.githubusercontent.com/{REPO}/main/covers/{name}'
        subtitles=[]
        for fmt in ['lrc','srt','vtt','txt']:
            sidecar=file.with_suffix('.'+fmt)
            if sidecar.exists():
                text=sidecar.read_text(encoding='utf-8-sig')
                if fmt=='lrc': row['lyricText']=text
                else: subtitles.append({'text':text,'format':fmt})
        if subtitles: row['subtitles']=subtitles
        tracks.append(row); uploads[asset]=file
    if not tracks: parser.error('No audio files found; existing index left unchanged')
    catalog={'version':1,'repository':f'https://github.com/{REPO}','tracks':tracks}
    if args.publish:
        result=subprocess.run(['gh','release','view',TAG,'--repo',REPO],capture_output=True)
        if result.returncode: run('gh','release','create',TAG,'--repo',REPO,'--title','音乐资源 · audio-v1','--notes','播放器音频资源。索引见仓库 catalog.json，文件名使用内容哈希，已发布音频链接保持稳定。','--target','main')
        assets=json.loads(run('gh','release','view',TAG,'--repo',REPO,'--json','assets',capture_output=True).stdout)['assets']
        existing={a['name'] for a in assets}
        pending=[(name,file) for name,file in uploads.items() if name not in existing]
        def upload(item):
            name,file=item
            with tempfile.TemporaryDirectory() as temp:
                target=pathlib.Path(temp)/name; target.symlink_to(file)
                run('gh','release','upload',TAG,str(target),'--repo',REPO,capture_output=True)
            print('Uploaded:',file.name,flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: list(pool.map(upload,pending))
        # Never replace the public index when an upload has failed.
        (ROOT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
        run('git','-C',str(ROOT),'add','catalog.json','covers')
        changed=subprocess.run(['git','-C',str(ROOT),'diff','--cached','--quiet']).returncode
        if changed: run('git','-C',str(ROOT),'commit','-m',f'Update music catalog ({len(tracks)} tracks)')
        run('git','-c','http.version=HTTP/1.1','-C',str(ROOT),'push')
    else:
        (ROOT/'catalog.preview.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(tracks)} tracks, {sum(t["bytes"] for t in tracks)/1024**2:.1f} MiB',flush=True)
if __name__=='__main__': main()
