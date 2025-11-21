\# 迁移指南 (v2.0 → 2.0.1)



\## 重要提醒

v2.0.1 是重大更新版本，\*\*不向后兼容\*\*。您需要重新配置设备。



\## 迁移步骤



\### 1. 备份配置

```yaml

\# 备份您的旧配置 (configuration.yaml)

hass\_cozylife\_local\_pull:

&nbsp; lang: 'en'

&nbsp; ip: 

&nbsp;   - '192.168.1.100'

&nbsp;   - '192.168.1.101'

