import structlog

logger = structlog.get_logger(__name__)
from model_hub.models.custom_models import CustomAIModel

update_model = True


def one_time_model_providers_update():
    global update_model
    if update_model:
        logger.info("Updating model providers...")
        CustomAIModel.objects.filter(provider__startswith="custom_").update(
            provider="custom"
        )
        update_model = False
        logger.info("Model providers updated.")
    logger.info("Model providers already updated.")
