# 数据集下载指南

## 已完成的数据集

### ✅ TempReason
- **状态**: 已下载
- **路径**: `data/TempReason/tempreason_data/`
- **格式**: JSONL
- **数据文件**:
  - `train_l1.json` (63.32 MB) - Level 1 训练集
  - `train_l2.json` (157.89 MB) - Level 2 训练集
  - `train_l3.json` (140.17 MB) - Level 3 训练集
  - `val_l1.json`, `val_l2.json`, `val_l3.json` - 验证集
  - `test_l1.json`, `test_l2.json`, `test_l3.json` - 测试集
- **样本格式**:
```json
{
  "question": "What is the time 1 year and 7 month after Mar, 1873",
  "date": "March 26, 1873",
  "text_answers": {"text": ["Oct, 1874"]},
  "id": "0",
  "context": ""
}
```

### ✅ NarrativeQA
- **状态**: 已转换，答案已填充
- **路径**: `converted_data/narrativeqa.jsonl`
- **样本数**: 5,000
- **答案状态**: 全部已填充

---

## 待下载的数据集

### ⏳ Winogrande
- **HuggingFace ID**: `allenai/winogrande`
- **状态**: 网络连接问题，需要手动下载

#### 方法 1: 使用 Python 脚本（推荐）
```python
from datasets import load_dataset
import json
from pathlib import Path

# 设置代理（如需要）
import os
os.environ['HTTP_PROXY'] = 'http://your-proxy:port'
os.environ['HTTPS_PROXY'] = 'http://your-proxy:port'

# 下载数据集
dataset = load_dataset('allenai/winogrande', 'winogrande_debiased')

output_dir = Path('data/winogrande')
output_dir.mkdir(parents=True, exist_ok=True)

for split in dataset.keys():
    output_file = output_dir / f'winogrande_debiased_{split}.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in dataset[split]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f'{split}: {len(dataset[split])} samples saved')
```

#### 方法 2: 使用 HuggingFace 镜像
如果网络访问 HuggingFace 有问题，可以使用镜像站点：

```python
# 使用 HF-Mirror
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from datasets import load_dataset
dataset = load_dataset('allenai/winogrande', 'winogrande_debiased')
```

#### 方法 3: 直接下载
从以下地址手动下载文件：
- https://huggingface.co/datasets/allenai/winogrande

下载后解压到 `data/winogrande/` 目录。

---

## 数据集下载命令汇总

### TempReason（已下载）
```bash
cd data/TempReason
git lfs install
git clone https://huggingface.co/datasets/tonytan48/TempReason tempreason_data
```

### Winogrande（待下载）
```bash
# 使用 pip 安装 datasets
pip install datasets

# 运行下载脚本
python download_datasets.py --winogrande
```

或使用 HuggingFace CLI:
```bash
pip install huggingface_hub
huggingface-cli download allenai/winogrande --repo-type dataset --local-dir data/winogrande
```

---

## 数据集配置文件

项目中已创建 `download_datasets.py` 脚本用于批量下载：

```bash
# 下载所有数据集
python download_datasets.py --all

# 单独下载
python download_datasets.py --winogrande
python download_datasets.py --tempreason
python download_datasets.py --narrativeqa
```

---

## 网络问题解决方案

如果遇到 `[WinError 10060]` 或 `[WinError 10061]` 连接问题：

### 方案 1: 使用代理
```python
import os
os.environ['HTTP_PROXY'] = 'http://your-proxy:port'
os.environ['HTTPS_PROXY'] = 'http://your-proxy:port'
```

### 方案 2: 使用 HuggingFace 镜像
```python
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
```

### 方案 3: 手动下载
1. 访问数据集页面: https://huggingface.co/datasets/allenai/winogrande
2. 点击 "Files and versions"
3. 下载数据文件
4. 解压到 `data/winogrande/` 目录

---

## 更新记录

| 日期 | 数据集 | 状态 |
|------|--------|------|
| 2026-03-30 | TempReason | ✅ 已下载 |
| 2026-03-30 | NarrativeQA | ✅ 答案已填充 |
| 2026-03-30 | Winogrande | ⏳ 网络问题，待处理 |