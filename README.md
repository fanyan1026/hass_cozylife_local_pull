## CozyLife Local Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/fanyan1026/cozylife_local?include_prereleases)](https://github.com/fanyan1026/cozylife_local/releases)
[![License](https://img.shields.io/github/license/fanyan1026/cozylife_local)](LICENSE)
[![HACS Compatible](https://img.shields.io/badge/HACS-Compatible-green.svg)](https://hacs.xyz/)

`cozylife_local` 是一个为 Home Assistant 设计的自定义集成，用于**本地控制** CozyLife 品牌的智能设备，如智能灯泡、开关和插座。

通过此集成，你可以在 Home Assistant 中直接发现并控制你的 CozyLife 设备，无需依赖云服务，从而实现更快的响应速度和更高的隐私安全性。

## 特点

- **纯本地控制**：所有通信都在你的局域网内进行，不经过任何第三方服务器。
- **自动发现**：自动扫描局域网内的 CozyLife 设备，无需手动查找 IP 地址。
- **图形化配置**：通过 Home Assistant 的 UI 界面轻松完成集成设置，无需修改 `configuration.yaml` 文件。
- **异步架构**：采用 `asyncio` 异步编程，确保不会阻塞 Home Assistant 的主事件循环，性能更佳。
- **稳定的连接**：内置自动重连和心跳检测机制，即使网络波动也能快速恢复连接。
- **丰富的实体支持**：
  - **灯光**：支持开关、亮度、色温以及 RGB 颜色调节。
  - **开关**：支持开关控制。

## 安装

### 方法一：通过 HACS (推荐)

1. 确保你已安装 [HACS](https://hacs.xyz/)。
2. 在 Home Assistant 侧边栏中，进入 **HACS** -> **集成**。
3. 点击右下角的 **"..."** 按钮，选择 **"自定义存储库"**。
4. 在 **"存储库 URL"** 中输入 `https://github.com/fanyan1026/cozylife_local`，类别选择 **"集成"**，然后点击 **"添加"**。
5. 搜索 "CozyLife Local" 并点击 **"下载"**。
6. 重启 Home Assistant。

### 方法二：手动安装

1. 下载最新版本的 [发布包](https://github.com/fanyan1026/cozylife_local/releases)。
2. 解压下载的文件。
3. 将 `cozylife_local` 文件夹复制到你 Home Assistant 配置目录下的 `custom_components` 文件夹中（如果 `custom_components` 不存在，请手动创建）。
   - 路径示例: `/config/custom_components/cozylife_local/`
4. 重启 Home Assistant。

## 配置

1. 在 Home Assistant 侧边栏中，进入 **设置** -> **设备与服务**。
2. 点击右上角的 **"+ 添加集成"** 按钮。
3. 搜索并选择 **"CozyLife Local"**。
4. 系统将自动开始扫描局域网内的 CozyLife 设备。
5. 扫描完成后，你会看到所有发现的设备列表。选择你希望添加的设备，然后点击 **"提交"**。
6. 集成会自动为每个设备创建对应的实体（如 `light.cozylife_bulb_1234`）。

## 使用

添加完成后，你可以像使用 Home Assistant 中其他任何设备一样使用 CozyLife 设备：

- 在 **仪表板** 中添加卡片来控制设备。
- 在 **自动化** 和 **脚本** 中使用设备来创建复杂的场景。

## 故障排除

### 设备未被发现
- 确保你的 Home Assistant 服务器和 CozyLife 设备连接在**同一个局域网**下。
- 检查路由器的 AP 隔离功能是否关闭，这可能会阻止设备发现。
- 尝试重启 CozyLife 设备和 Home Assistant。

### 设备频繁离线或控制延迟
- 检查设备的 Wi-Fi 信号强度，弱信号可能导致连接不稳定。
- 确保 Home Assistant 所在的服务器资源充足（CPU/内存）。
- 尝试将 CozyLife 设备固件更新到最新版本。

### 查看日志
如果遇到问题，可以在 Home Assistant 的 **设置** -> **系统** -> **日志** 中查看详细的错误信息，这有助于定位问题根源。

## 贡献

如果你发现了 bug、有新的功能请求或想要改进代码，欢迎通过以下方式贡献：

1. Fork 本仓库。
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)。
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)。
4. 推送到分支 (`git push origin feature/amazing-feature`)。
5. 打开一个 Pull Request。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

**免责声明**：本项目与 CozyLife 品牌或其母公司无任何关联，仅为第三方爱好者开发的非官方集成工具。