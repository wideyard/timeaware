---
dataset_info:
- config_name: documents
  features:
  - name: chunk_id
    dtype: string
  - name: chunk
    dtype: string
  splits:
  - name: train
    num_bytes: 3968308
    num_examples: 5502
  - name: validation
    num_bytes: 399556
    num_examples: 555
  - name: test
    num_bytes: 1263082
    num_examples: 1750
  download_size: 3462955
  dataset_size: 5630946
- config_name: queries
  features:
  - name: og_query
    dtype: string
  - name: query
    dtype: string
  - name: chunk_id
    dtype: string
  - name: answer
    dtype: string
  splits:
  - name: train
    num_bytes: 6371715.290749214
    num_examples: 27953
  - name: validation
    num_bytes: 664723.0
    num_examples: 2919
  - name: test
    num_bytes: 1970467.8313323231
    num_examples: 8575
  download_size: 3619450
  dataset_size: 9006906.122081537
configs:
- config_name: documents
  data_files:
  - split: train
    path: documents/train-*
  - split: validation
    path: documents/validation-*
  - split: test
    path: documents/test-*
- config_name: queries
  data_files:
  - split: train
    path: queries/train-*
  - split: validation
    path: queries/validation-*
  - split: test
    path: queries/test-*
---
# ConTEB - NarrativeQA

This dataset is part of *ConTEB* (Context-aware Text Embedding Benchmark), designed for evaluating contextual embedding model capabilities. It stems from the widely used [NarrativeQA](https://huggingface.co/datasets/deepmind/narrativeqa) dataset.

## Dataset Summary

NarrativeQA (literature), consists of long documents, associated to existing sets of question-answer pairs. To build the corpus, we start from the pre-existing collection documents, extract the text, and chunk them (using [LangChain](https://github.com/langchain-ai/langchain)'s RecursiveCharacterSplitter with a threshold of 1000 characters). Since chunking is done a posteriori without considering the questions, chunks are not always self-contained and eliciting document-wide context can help build meaningful representations. We use GPT-4o to annotate which chunk, among the gold document, best contains information needed to answer the query. 

This dataset provides a focused benchmark for contextualized embeddings. It includes a set of original documents, chunks stemming from them, and queries.

*   **Number of Documents:** 355 
*   **Number of Chunks:** 1750 
*   **Number of Queries:** 8575
*   **Average Number of Tokens per Chunk:** 151.9

## Dataset Structure (Hugging Face Datasets)
The dataset is structured into the following columns:

*   **`documents`**: Contains chunk information:
    *   `"chunk_id"`:  The ID of the chunk, of the form `doc-id_chunk-id`, where `doc-id` is the ID of the original document and `chunk-id` is the position of the chunk within that document. 
    *   `"chunk"`:  The text of the chunk
*   **`queries`**: Contains query information:
    *   `"query"`: The text of the query.
    *   `"answer"`: The answer relevant to the query, from the original dataset.
    *   `"chunk_id"`: The ID of the chunk that the query is related to, of the form `doc-id_chunk-id`, where `doc-id` is the ID of the original document and `chunk-id` is the position of the chunk within that document.

## Usage

Use the `train` split for training, and the `test` split for evaluation.
We will upload a Quickstart evaluation snippet soon.

## Citation

We will add the corresponding citation soon.

## Acknowledgments

This work is partially supported by [ILLUIN Technology](https://www.illuin.tech/), and by a grant from ANRT France.

## Copyright

All rights are reserved to the original authors of the documents.