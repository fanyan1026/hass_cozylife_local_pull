# CozyLife Local Integration


Home Assistant 本地集成，用于控制 CozyLife 智能设备。

## 🆕 新版本 v2.0.1 重大更新

### ✨ 全新特性
- 🎯 **可视化配置** - 通过 UI 界面添加设备，告别配置文件
- ⚡ **完全异步** - 性能大幅提升，不阻塞系统
- 🔍 **自动发现** - 自动扫描网络中的设备
- 🛡️ **智能错误处理** - 详细的错误提示和自动重试

### 🚀 快速开始

#### 安装方式
1. 通过 HACS 添加自定义仓库
2. 或手动复制文件到 `custom_components` 目录
3. 重启 Home Assistant

#### 添加设备
1. 进入 **设置** → **设备与服务** → **集成**
2. 点击 **+ 添加集成**
3. 搜索 **"CozyLife local"**
4. 选择发现的设备或手动输入 IP 地址

### 📋 支持设备

| 设备类型 | 功能支持 |
|---------|----------|
| 💡 智能灯光 | 开关、亮度、色温、颜色 |
| 🔌 智能开关 | 基础开关控制 |
| 🔍 自动识别 | 自动检测设备类型 |

### ⚠️ 重要提示

**v2.0.1 是重大更新，不向后兼容！**

如果您从旧版本升级：
1. 删除 `configuration.yaml` 中的旧配置
2. 通过集成界面重新添加设备
3. 查看 [迁移指南](MIGRATION.md) 获取详细说明

### 🔧 技术特性

- ✅ 完全基于 async/await 的异步架构
- ✅ 符合 Home Assistant 最新标准
- ✅ 完整的类型注解
- ✅ 自动重连和心跳保持
- ✅ 详细的调试日志

### ❓ 常见问题

**Q: 为什么我的旧配置不工作了？**  
A: v2.0.1 完全重构，请使用新的 UI 配置方式。

**Q: 如何手动指定设备 IP？**  
A: 在集成界面中选择"手动输入"选项。

**Q: 支持哪些设备功能？**  
A: 自动检测设备能力，支持灯光、开关等。

**Q: 遇到连接问题怎么办？**  
A: 检查设备 IP 和端口(默认5555)，确保网络连通。

### 📖 文档链接

- [更新日志](CHANGELOG.md) - 版本历史和新特性
- [迁移指南](MIGRATION.md) - 从旧版本升级说明
- [问题反馈](https://github.com/fanyan1026/cozylife_local/issues) - 报告问题和建议

### 🛠 开发信息

这是一个社区维护的项目，基于原 [cozylife/hass_cozylife_local_pull](https://github.com/cozylife/hass_cozylife_local_pull) 重构。

---

**如果这个集成对您有帮助，请给个 ⭐ 星标支持！**

# CozyLife & Home Assistant 

CozyLife Assistant integration is developed for controlling CozyLife devices using local net, officially 
maintained by the CozyLife Team.


## Supported Device Types

- RGBCW Light
- CW Light
- Switch & Plug


## Install

* A home assistant environment that can access the external network
* clone the repo to the custom_components directory
* configuration.yaml
```
hass_cozylife_local_pull:
   lang: en
   ip:
     - "192.168.1.99"
```


### Feedback
* Please submit an issue
* Send an email with the subject of hass support to info@cozylife.app

### Troubleshoot 
* Check whether the internal network isolation of the router is enabled
* Check if the plugin is in the right place
* Restart HASS multiple times
* View the output log of the plugin
* It is currently the first version of the plugin, there may be problems that cannot be found


### TODO
- Sending broadcasts regularly has reached the ability to discover devices at any time
- Support sensor device

### PROGRESS
- None
