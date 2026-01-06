# quant-start

一个极简的量化回测示例：基于 510300 ETF 的 MA20 策略，生成交易记录与净值曲线。

## 功能
- 获取 510300 ETF 日线数据（akshare）
- 生成 MA20 信号
- 单标的极简回测（手续费、滑点、全仓/空仓）
- 输出交易记录与指标，绘制净值曲线

## 目录结构
- quant/run_ma20.py：主流程，计算信号并回测
- quant/strategy/ma20_signal.py：MA20 信号
- quant/backtest/simple_bt.py：极简回测引擎
- quant/data/get_510300.py：拉取并保存 510300 数据
- quant/data/510300.csv：样例数据（可重新拉取）

## 环境依赖
- Python 3.11+
- numpy
- pandas
- matplotlib
- akshare

示例安装：
```bash
pip install numpy pandas matplotlib akshare
```

## 快速开始
在项目根目录执行：
```bash
cd code/quant
```

1) 拉取数据（可选）
```bash
python data/get_510300.py
```

2) 运行回测
```bash
python run_ma20.py
```

输出：
- 终端打印指标
- 交易记录保存到 `quant/result_trades.csv`
- 弹出净值曲线图

## 数据格式
回测脚本要求 CSV 至少包含以下列：
`date`, `open`, `high`, `low`, `close`, `volume`

如果你使用自己的数据，请确保字段名一致。

## 备注
本项目为教学/演示用途，回测逻辑做了简化，不代表真实交易结果。
