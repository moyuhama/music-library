# Music Library

余音播放器的独立音乐资源库。音频、封面、歌词按文件夹保存并直接提交到此仓库；播放器使用 Raw 文件链接，不依赖 Releases。

- [曲库索引](https://raw.githubusercontent.com/moyuhama/music-library/main/catalog.json)
- [音乐文件](https://github.com/moyuhama/music-library/tree/main/music)
- [播放器](https://moyuhama.github.io/music/)

## 文件夹结构

```text
music/
  相声/
    郭德纲/
      郭德纲相声经典/
        cover.png
        歌曲.m4a
        歌曲.lrc
  音乐/
    歌手名/
      专辑名/
        cover.jpg
        歌曲.mp3
```

歌词与音频同名；支持 LRC、SRT、VTT、TXT。封面放在专辑目录，命名为 cover.jpg、cover.png、folder.jpg 或 cover.webp。不需要歌词占位文件。

## 添加资源

将有权分享的音频放入对应目录，安装 Python 3、FFmpeg（ffprobe）、Git，然后执行：

```sh
# 检查并生成预览，不修改正式索引
python3 scripts/publish.py
# 更新 catalog.json、提交音频和索引并推送
python3 scripts/publish.py --publish
```

播放器刷新或重新回到窗口后读取新索引，无需重新部署播放器。索引包含元数据、歌词、Raw 链接及 SHA-256。已有文件按校验值沿用 ID，调整文件夹时保留对应收藏。删除音乐文件后重新生成索引即可下架，Git 历史保留旧版本。

每个文件须小于 100 MiB。这个仓库会随音乐增加而增大，播放器仓库与部署包不会包含这些音频。

作品著作权属于各权利人。此仓库不授予作品再分发许可。
