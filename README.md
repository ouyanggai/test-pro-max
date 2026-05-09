# 接口编排自动化测试工具

Python 桌面端流程回归工具原型。

## 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

## 启动工作台

```bash
./scripts/run_workbench.sh
```

默认读取项目根目录 `.env`。也可以指定环境文件：

```bash
./scripts/run_workbench.sh /path/to/.env
```

## 启动验证

无界面环境下验证 Qt 工作台能创建、展示并自动退出：

```bash
./scripts/verify_startup.sh
```

## 测试

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest
```
