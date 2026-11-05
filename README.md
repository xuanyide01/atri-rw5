# 《ATRI》· 小米手环 8 Pro

作者 xuanyide。移植、资源转换与构建工具由 OpenAI Codex 完成。维护者已确认 **0.1.2** 实机测试通过。

[下载 小米手环 8 Pro 0.1.2](https://github.com/xuanyide01/atri-rw5/releases/tag/band8pro-v0.1.2) · [安装说明](docs/INSTALL.md) · [REDMI Watch 5 版](https://github.com/xuanyide01/atri-rw5/releases/tag/v0.1.8)

## 0.1.2 更新

- 清理移除人物后残留的背景小窗边框，包括凛凛花登场时右侧的异常方框。检查 12,172 段剧情，修正 284 处背景引用，移除 66 张带可见残框的背景副本。
- 核对 418 张独立立绘和 5,065 处引用，全部属于亚托莉。原作 CG 中的人物随 CG 保留。
- 累计修复手环字体方框，调整圆形图标至 96 × 96，正文从左上方起排并自动换行。
- 所有选项都可点，前两次选择仍影响结局。
- 保留 30 个存档栏位、三档自动播放、安全跳章与 31 组／71 张 CG 差分。包名、签名和存档格式沿用前版。

![模拟器中的修复场景](docs/scene-fix.png)

## 功能与流程

- 336 × 480 界面。上方显示原作背景、CG 和亚托莉独立立绘，下方显示对白。可点正文或画面推进，长对白支持滚动。
- 阅读菜单可设置字号、即时／逐字显示、慢速／标准／快速自动播放。自动播放在选项处暂停，选择后继续。“下一章”也会停在选项处。
- 可自行选择 30 个存档栏位。CG 鉴赏将同场景差分分组，点图切换。
- 从 START 开始。依次选择“亚托莉先放在我这”“吻她”“捡起鞋子”即可进入好结局。坏结局与好结局均完成后，返回标题可进入 TRUE END。
- 本版采用静态画面，省略语音、BGM、视频和动态演出。

## 构建与验证

预转换资源在 `src/`。构建需要 Node.js 和 npm，编译器版本为 aiot-toolkit 1.1.0。

```sh
npm ci --prefix tools/compat-toolkit --ignore-scripts
npm run build
npm test
node tools/test-auto-reader.cjs
```

正式发布包沿用原有兼容封装和签名。维护者实机反馈、包体校验和模拟器验证分别记在 [验证报告](reports/VALIDATION.json) 中。

## 原作与致谢

原作 [《ATRI -My Dear Moments-》官网](https://atri-mdm.com/)。感谢 [@liuyuze61 的移植](https://github.com/liuyuze61/ATRI-miband)、[《ATRI》1.5.1 分享](https://api.bandbbs.cn/wftools/bandbbs.html?code=A&state=1820673)、[《星空列车与白的旅行》1.0.0 分享](https://api.bandbbs.cn/wftools/bandbbs.html?code=A&state=1841662)及 [表盘自定义工具相关团队](https://www.bandbbs.cn/)。

自编代码采用 [MIT](LICENSE)。原作剧情、美术、标志及截图归原权利人，字体和第三方工具见 [授权说明](licenses/THIRD_PARTY_NOTICES.md)。

问题反馈请使用[仓库 Issues](https://github.com/xuanyide01/atri-rw5/issues)。联系邮箱沿用仓库原有的公开地址 [shining237841@gmail.com](mailto:shining237841@gmail.com)。
