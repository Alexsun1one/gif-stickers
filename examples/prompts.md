# 示例 Prompt

```text
用 gif-stickers 基于这张真人照片做 3 个微信 GIF：早安呀、辛苦啦、谢谢你。先走 A-smoke，不要一上来盲跑完整大包。
```

```text
用 gif-stickers 做一个中文发布场景示例。先说明视觉结构，再写最终生图提示词，最后按 Skill 的 QA checklist 自检。
```

## 1x4 帧表到真实 GIF

```text
用 gif-stickers 做一个原创纸灯笼角色的 240x240 微信 GIF。

要求：
- 先生成 1x4 frame sheet：同一个小纸灯笼，待机、前倾、挥手闪光、回到原位
- 不要在 frame sheet 里写文字
- 再用脚本切帧并叠短 caption：你好呀
- 输出真实 wechat.gif，并运行 verify_output.py --platform wechat
- 不要只交静态预览图
```
