#!/usr/bin/env python3
"""
Download missing datasets from HuggingFace
Downloads: 
- allenai/winogrande
- tonytan48/TempReason (or search for correct ID)
- deepmind/narrativeqa
"""

import os
import json
from pathlib import Path
from datasets import load_dataset
import argparse

DATA_DIR = Path("data")

def download_winogrande():
    """Download Winogrande dataset."""
    print("=" * 60)
    print("Downloading Winogrande...")
    print("=" * 60)
    
    output_dir = DATA_DIR / "winogrande"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Winogrande has multiple configurations
    configs = ['winogrande_debiased', 'winogrande_xl', 'winogrande_l', 
               'winogrande_m', 'winogrande_s', 'winogrande_xs']
    
    for config in configs:
        try:
            print(f"\nDownloading {config}...")
            dataset = load_dataset("allenai/winogrande", config, trust_remote_code=True)
            
            # Save each split
            for split in dataset.keys():
                output_file = output_dir / f"{config}_{split}.jsonl"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for item in dataset[split]:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                print(f"Saved {len(dataset[split])} samples to {output_file}")
                
        except Exception as e:
            print(f"Error downloading {config}: {e}")
            continue
    
    print("\nWinogrande download completed!")
    return True

def download_tempreason():
    """Download TempReason dataset."""
    print("=" * 60)
    print("Searching and Downloading TempReason...")
    print("=" * 60)
    
    output_dir = DATA_DIR / "TempReason" / "downloaded_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try different possible HuggingFace IDs
    possible_ids = [
        "tonytan48/TempReason",
        "tonytan48/preprocessed_tempreason",
        "utahnlp/tempreason",
        "PIPA/TempReason"
    ]
    
    for dataset_id in possible_ids:
        try:
            print(f"\nTrying {dataset_id}...")
            dataset = load_dataset(dataset_id, trust_remote_code=True)
            
            print(f"Success! Found dataset: {dataset_id}")
            print(f"Available splits: {list(dataset.keys())}")
            
            # Save each split
            for split in dataset.keys():
                output_file = output_dir / f"{split}.jsonl"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for item in dataset[split]:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                print(f"Saved {len(dataset[split])} samples to {output_file}")
            
            print("\nTempReason download completed!")
            return True
            
        except Exception as e:
            print(f"Not found at {dataset_id}: {e}")
            continue
    
    print("\nCould not find TempReason. Please check HuggingFace for the correct dataset ID.")
    return False

def download_narrativeqa():
    """Download NarrativeQA dataset."""
    print("=" * 60)
    print("Downloading NarrativeQA from HuggingFace...")
    print("=" * 60)
    
    output_dir = DATA_DIR / "narrative-qa" / "original"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # NarrativeQA on HuggingFace
        dataset = load_dataset("deepmind/narrativeqa", trust_remote_code=True)
        
        print(f"Available splits: {list(dataset.keys())}")
        
        # Save each split
        for split in dataset.keys():
            output_file = output_dir / f"{split}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in dataset[split]:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"Saved {len(dataset[split])} samples to {output_file}")
        
        print("\nNarrativeQA download completed!")
        return True
        
    except Exception as e:
        print(f"Error downloading NarrativeQA: {e}")
        print("Trying alternative source...")
        
        # Try alternative source from google-research-datasets
        print("Note: deepmind/narrativeqa may require authentication.")
        print("Please visit: https://huggingface.co/datasets/deepmind/narrativeqa")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download datasets from HuggingFace")
    parser.add_argument("--winogrande", action="store_true", help="Download Winogrande")
    parser.add_argument("--tempreason", action="store_true", help="Download TempReason")
    parser.add_argument("--narrativeqa", action="store_true", help="Download NarrativeQA")
    parser.add_argument("--all", action="store_true", help="Download all datasets")
    
    args = parser.parse_args()
    
    if not (args.winogrande or args.tempreason or args.narrativeqa or args.all):
        print("Usage:")
        print("  python download_datasets.py --winogrande")
        print("  python download_datasets.py --tempreason")
        print("  python download_datasets.py --narrativeqa")
        print("  python download_datasets.py --all")
        return
    
    if args.all:
        args.winogrande = True
        args.tempreason = True
        args.narrativeqa = True
    
    installed_packages = []
    try:
        import datasets
        installed_packages.append("datasets")
    except ImportError:
        print("Error: 'datasets' package not installed. Please install it:")
        print("pip install datasets")
        return
    
    if args.winogrande:
        download_winogrande()
    
    if args.tempreason:
        download_tempreason()
    
    if args.narrativeqa:
        download_narrativeqa()
    
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)

if __name__ == "__main__":
    main()