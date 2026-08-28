from app.servable_models import EmbeddingModel, ModelServing
from app.servable_models.embedding_models import (
    AudioEmbeddingModel,
    ImageEmbeddingModel,
    ImageTextEmbeddingModel,
    SynDataEmbeddingModel,
    TextEmbeddingModel,
)
from app.servable_models.external_models import (
    HuggingFaceEmbeddingModel,
    OpenAIEmbeddingModel,
)

SUPPORTED_MODELS = [
    "embedding",
    "text_embedding",
    "image_embedding",
    "audio_embedding",
    "image_text_embedding",
    "syn_data_embedding",
    "openai",
    "huggingface",
]

MODEL_NAME_TO_CLASS_MAPPING = {
    "embedding": EmbeddingModel,
    "text_embedding": TextEmbeddingModel,
    "image_embedding": ImageEmbeddingModel,
    "audio_embedding": AudioEmbeddingModel,
    "image_text_embedding": ImageTextEmbeddingModel,
    "syn_data_embedding": SynDataEmbeddingModel,
    "openai": OpenAIEmbeddingModel,
    "huggingface": HuggingFaceEmbeddingModel,
}
