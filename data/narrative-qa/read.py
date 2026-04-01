# 将目录下的所有parquet文件转换为jsonl文件
import json
import os
import pandas as pd
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return obj.item()
        return super().default(obj)

def parquet_to_jsonl(parquet_file, jsonl_file):
    # 读取parquet文件
    df = pd.read_parquet(parquet_file)
    
    # 将DataFrame转换为字典列表
    records = df.to_dict(orient='records')
    
    # 将字典列表写入jsonl文件
    with open(jsonl_file, 'a') as f:
        for record in records:
            json_line = json.dumps(record, cls=NumpyEncoder)
            f.write(json_line + '\n')

if __name__ == "__main__":
    input_dir = 'D:\\workspace\\timeaware\\data\\narrative-qa\\queries'

    jsonl_file = 'D:\\workspace\\timeaware\\data\\narrative-qa\\queries.jsonl'
    
    # 获取目录下所有的parquet文件
    for filename in os.listdir(input_dir):
        if filename.endswith(".parquet"):
            parquet_file = os.path.join(input_dir, filename)
            parquet_to_jsonl(parquet_file, jsonl_file)