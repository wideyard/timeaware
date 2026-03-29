"""arch package - 统一时间推理框架

基于 arich.md 的设计，提供：
1. 统一的数据格式和任务定义 (task_schema)
2. 数据集适配器 (dataset_adapter)
3. 五大任务生成器 (task_generators)
4. 三层评测模块 (evaluation)
"""

from .task_schema import (
    TemporalSample,
    TaskType,
    DifficultyLevel,
    SubTaskConfig,
    ALL_SUBTASKS,
    get_task_description,
    get_task_metrics,
)

from .task_generators import (
    BaseTaskGenerator,
    T1TemporalCalculationGenerator,
    T2StateTrackingGenerator,
    T3ConcurrencyGenerator,
    T4LongTermMemoryGenerator,
    T5CounterfactualGenerator,
    TaskGeneratorFactory,
    TaskConfig,
)

from .dataset_adapter import (
    DatasetAdapter,
    MCTACOAdapter,
    UDSTDurationQAAdapter,
    TimeDialAdapter,
    TRACIEAdapter,
    SituatedGenAdapter,
    UDSTAdapter,
    DatasetConverter,
    convert_all_datasets,
)

from .qasper_adapter import (
    QASPerAdapter,
    load_qasper_data,
)

from .winogrande_adapter import (
    WinograndeAdapter,
    load_winogrande_data,
)

from .new_adapters import (
    DROPAdapter,
    TimeQAAdapter,
    BABiAdapter,
    ProParaAdapter,
    SocialIQAAdapter,
    CosmosQAAdapter,
    PIQAAdapter,
    LongBenchAdapter,
    ATOMICAdapter,
    TRIPAdapter,
    NarrativeQAAdapter,
    load_drop_data,
    load_timeqa_data,
    load_socialiqa_data,
    load_cosmosqa_data,
    load_piqa_data,
    load_atomic_data,
    load_trip_data,
    load_narrativeqa_data,
)

from .evaluation import (
    EvaluationResult,
    AnswerLevelEvaluator,
    StateLevelEvaluator,
    ChainLevelEvaluator,
    TemporalBenchmarkEvaluator,
)

from .main import (
    generate_tasks,
    load_converted_data,
    run_model_prediction,
    run_evaluation,
    run_comparison_experiment,
)

__all__ = [
    "TemporalSample",
    "TaskType",
    "DifficultyLevel",
    "TaskConfig",
    "SubTaskConfig",
    "ALL_SUBTASKS",
    "get_task_description",
    "get_task_metrics",
    "DatasetAdapter",
    "MCTACOAdapter",
    "UDSTDurationQAAdapter",
    "TimeDialAdapter",
    "TRACIEAdapter",
    "SituatedGenAdapter",
    "UDSTAdapter",
    "DatasetConverter",
    "convert_all_datasets",
    "QASPerAdapter",
    "load_qasper_data",
    "WinograndeAdapter",
    "load_winogrande_data",
    "DROPAdapter",
    "TimeQAAdapter",
    "BABiAdapter",
    "ProParaAdapter",
    "SocialIQAAdapter",
    "CosmosQAAdapter",
    "PIQAAdapter",
    "LongBenchAdapter",
    "ATOMICAdapter",
    "TRIPAdapter",
    "NarrativeQAAdapter",
    "load_drop_data",
    "load_timeqa_data",
    "load_socialiqa_data",
    "load_cosmosqa_data",
    "load_piqa_data",
    "load_atomic_data",
    "load_trip_data",
    "load_narrativeqa_data",
    "BaseTaskGenerator",
    "T1TemporalCalculationGenerator",
    "T2StateTrackingGenerator",
    "T3ConcurrencyGenerator",
    "T4LongTermMemoryGenerator",
    "T5CounterfactualGenerator",
    "TaskGeneratorFactory",
    "EvaluationResult",
    "AnswerLevelEvaluator",
    "StateLevelEvaluator",
    "ChainLevelEvaluator",
    "TemporalBenchmarkEvaluator",
    "generate_tasks",
    "load_converted_data",
    "run_model_prediction",
    "run_evaluation",
    "run_comparison_experiment",
]
