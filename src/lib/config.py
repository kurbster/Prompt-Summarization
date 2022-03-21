from typing import Any, Dict, List
from pathlib import Path
from dataclasses import dataclass, field

from omegaconf import OmegaConf
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig

def get_output_dir() -> Path:
    hydra_config = HydraConfig.get()
    return Path(hydra_config.output_subdir).resolve()

def is_initial_job() -> bool:
    hydra_config = HydraConfig.get()
    return hydra_config.job.num == 0

@dataclass
class APIConfig:
    engine: str
    top_p: float = 0.0
    temperature: float = 0.0

    n: int = 1
    logprobs: int = 0
    max_tokens: int = 512

    stop: List[str] = field(default_factory=list)
    logit_bias: Dict[str, float] = field(default_factory=dict)
    
@dataclass
class Studio21APIConfig(APIConfig):
    def convert_to_studio21_kwargs(self) -> OmegaConf:
        """Method for converting the snake_case arguments into camelCase
        to match Studio21AI's API

        Returns:
            OmegaConf: The dictionary containing the arguments
        """
        conf = dict()
        # All of the options that need to be converted
        conf['topP'] = self.top_p
        conf['maxTokens'] = self.max_tokens
        conf['logitBias'] = self.logit_bias
        conf['numResults'] = self.n
        conf['topKReturn'] = self.logprobs
        conf['stopSequences'] = self.stop

        # Every other option
        conf['temperature'] = self.temperature

        conf_obj = OmegaConf.create(conf)
        return OmegaConf.to_container(conf_obj)

@dataclass
class OpenAIAPIConfig(APIConfig):
    echo: bool = False
    stream: bool = False

    presence_penalty: Any = 0.0
    frequency_penalty: Any = 0.0

    best_of: int = 1

    user: str = ""

@dataclass
class GenerationConfig:
    num_prompts: int = 0
    num_few_shot: int = 0
    ignore_intro: bool = False
    ignore_train: bool = False
    header: str = ""
    api_name: str = ""
    split_file: str = ""
    category_file: str = ""
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    prompt_manifest: str = ""
    few_shot_suffix: str = ""
    completion_prefix: str = ""
    completion_suffix: str = ""
    summary_types: List[str] = field(default_factory=list)

@dataclass
class CodexConfig(GenerationConfig):
    human_only: bool = False
    test_immediately: bool = False
    prompts_per_iter: int = 20

@dataclass
class ExperimentConfig:
    api_params: APIConfig
    generation_params: GenerationConfig

def register_configs():
    cs = ConfigStore.instance()
    cs.store(name="base_config", node=ExperimentConfig)
    cs.store(
        group="api_params",
        name="studio21_base",
        node=Studio21APIConfig
    )
    cs.store(
        group="api_params",
        name="openai_base",
        node=OpenAIAPIConfig
    )
    cs.store(
        group="generation_params",
        name="summary_base",
        node=GenerationConfig
    )
    cs.store(
        group="generation_params",
        name="codex_base",
        node=CodexConfig
    )