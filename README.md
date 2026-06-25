# GIF Stickers

> A skill and helper scripts for making WeChat-ready animated sticker packs from photos or generated sheets.

GIF Stickers packages the practical route from a person/reference image to platform-valid animated stickers. It includes exact-face photo puppet mode, AI likeness sheet mode, kinetic captions, GIF assembly, and verification helpers.

## Examples

<p><img src="examples/images/male-business-preview-sheet.png" alt="Male business mentor preview sheet" width="100%"><br><sub>Male business mentor preview sheet</sub></p>
<p><img src="examples/images/male-business-animated-preview.gif" alt="Animated preview" width="100%"><br><sub>Animated preview</sub></p>
<p><img src="examples/images/polite-greetings-preview-sheet.png" alt="Polite greetings realistic preview" width="100%"><br><sub>Polite greetings realistic preview</sub></p>

## What It Does

- Create WeChat-sized 240x240 looping GIF stickers under size constraints.
- Choose between B-photo-puppet for exact face pixels and A-face-anchor for richer AI-redrawn motion.
- Cut 1x4 or 2x4 generated sheets into frames and add dynamic Chinese captions.
- Verify platform specs such as frame count, loop behavior, and file size.

## Install

Clone this repository into your local Codex skills folder:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/Alexsun1one/gif-stickers.git ~/.codex/skills/gif-stickers
```

If your agent expects a nested skill directory instead of a direct clone, copy the folder that contains `SKILL.md` into its skills directory.

## Use

Example request:

```text
Use gif-stickers with the attached portrait. Make 3 WeChat GIFs: 早安呀, 辛苦啦, 谢谢你. Use A-smoke first unless I explicitly approve a full pack.
```

The skill entry point is [`SKILL.md`](SKILL.md). Supporting rules live in [`references/`](references/) when this repo includes them; helper scripts live in [`scripts/`](scripts/) when available.

## Quality Bar

- The image must explain a concrete idea, not merely decorate the page.
- Chinese text should be readable at the actual publishing size.
- The output should keep a stable style system across a set while letting each image fit its topic.
- Generated examples are prompts and visual references, not fixed templates.

## WeChat

More writeups, examples, and AI workflow notes are published on my WeChat official account. This is the real QR/search card used for the account, included as a normal bitmap asset rather than a stylized fake code.

<p align="center">
  <img src="assets/wechat-official-account.png" alt="微信搜一搜：正在逐渐AI化" width="720">
</p>

## License

MIT. See [`LICENSE`](LICENSE).

## Notice

This is an original open-source skill package by Sun Wuyuan / Alexsun1one. It is not affiliated with OpenAI, GitHub, WeChat, or any referenced platform. Avoid using it to imitate protected characters, living artists, or third-party brand assets without permission.
