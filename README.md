# Music Library

余音播放器的独立音乐资源库。曲目索引、封面、歌词保存在 Git；音频通过 GitHub Releases 发布，不进入 Git 历史。播放器从索引读取音频链接。

- 曲库索引：https://raw.githubusercontent.com/moyuhama/music-library/main/catalog.json
- 音频资源：https://github.com/moyuhama/music-library/releases/tag/audio-v1
- 播放器：https://moyuhama.github.io/music/

## 维护

本机 `media/专辑名/` 存放原始音频，不提交。支持同目录 `cover.jpg` / `cover.png` 和音频同名 `.lrc` / `.srt` / `.vtt` / `.txt`。索引保留曲名、歌手、专辑、时长、封面、歌词和文件校验值。

安装 Python 3、FFmpeg（ffprobe）、Git 和 GitHub CLI，登录有仓库写权限的账号后：

```sh
# 仅检查，生成 catalog.preview.json
python3 scripts/publish.py media
# 上传新增资源，成功后才更新并推送索引
python3 scripts/publish.py media --publish
```

音频以 SHA-256 命名，重复发布跳过已有文件。修改音频产生新地址，旧地址继续可用；稳定曲目 ID 来自相对路径，保持文件名和目录不变即可保留播放器收藏。封面按内容去重。删除本机文件后重新发布会移除其索引，已发布的旧资源不会自动删除。上传中断可重试，不需重传已成功的资源。

此库仅收集有权保存和分享的资源；作品著作权属于各权利人。本仓库不授予音频的再分发许可。
