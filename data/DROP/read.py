# 将parquet文件转换为jsonl文件
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
    parquet_file_1 = 'D:\\workspace\\timeaware\\data\\DROP\\train-00000-of-00001.parquet'
    parquet_file_2 = 'D:\\workspace\\timeaware\\data\\DROP\\validation-00000-of-00001.parquet'
    jsonl_file = 'D:\\workspace\\timeaware\\data\\DROP\\DROP.jsonl'
    parquet_to_jsonl(parquet_file_1, jsonl_file)
    parquet_to_jsonl(parquet_file_2, jsonl_file)