from concurrent.futures import ThreadPoolExecutor, as_completed

import structlog
from django.db import close_old_connections
from django.db.models import Q

from agentic_eval.core.embeddings.embedding_manager import EmbeddingManager
from tfc.telemetry import wrap_for_thread

logger = structlog.get_logger(__name__)
from model_hub.models.choices import CellStatus, DataTypeChoices
from model_hub.models.develop_dataset import Cell
from tfc.temporal import temporal_activity


@temporal_activity(time_limit=3600 * 3, queue="default")
def insert_embeddings_task(
    table_name="dataset_embeddings",
    batch_size=100,
    dataset_id=None,
    column_ids=None,
    cell_id=None,
):
    """
    Celery task to process cells without embeddings.
    This function will run periodically to check for cells that need embeddings.
    """
    try:
        close_old_connections()
        logger.info(
            f"Starting scheduled embedding task, batch_size: {batch_size}, dataset_id: {dataset_id}, column_ids: {column_ids}, cell_id: {cell_id}"
        )
        embedding_manager = EmbeddingManager()
        embedding_manager.db_client.create_table(table_name)

        query = Q()

        if cell_id is not None:
            query &= Q(id=cell_id)

        if column_ids is not None:
            query &= Q(column_id__in=column_ids)

        if dataset_id is not None:
            query &= Q(dataset_id=dataset_id)

        query &= Q(
            column__data_type__in=[
                DataTypeChoices.IMAGE.value,
                DataTypeChoices.AUDIO.value,
            ]
        )

        query &= Q(status=CellStatus.PASS.value) & ~Q(value__isnull=True) & ~Q(value="")

        # query &= (
        #     Q(column_metadata__embedding__isnull=True) |
        #     Q(column_metadata__embedding=False)
        # )

        cells = Cell.objects.filter(query).prefetch_related("column", "dataset")

        total_cells = cells.count()
        logger.info(f"Found {total_cells} cells that need embeddings")

        if total_cells == 0:
            logger.info("No cells need embeddings. Task complete.")
            return

        batches = []
        for i in range(0, total_cells, batch_size):
            batches.append(cells[i : i + batch_size])

        logger.info(f"Created {len(batches)} batches to insert embeddings")

        def process_batch(batch):
            vectors_data = embedding_manager.get_embedding_data(batch)

            if vectors_data:
                results = embedding_manager.bulk_insert_embeddings(
                    table_name=table_name,
                    vectors_data=vectors_data,
                    unique_key="cell_id",
                )

                return len(results)
            else:
                logger.warning("No valid vectors found in a batch")
                return 0

        # Wrap function with OTel context propagation for thread safety
        wrapped_process_batch = wrap_for_thread(process_batch)

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_batch = {
                executor.submit(wrapped_process_batch, batch): i
                for i, batch in enumerate(batches)
            }

            total_processed = 0
            for future in as_completed(future_to_batch):
                batch_index = future_to_batch[future]
                try:
                    processed_count = future.result()
                    total_processed += processed_count
                    logger.info(
                        f"Completed batch {batch_index + 1}/{len(batches)}, inserted {processed_count} vectors"
                    )
                except Exception as e:
                    logger.exception(f"Error processing batch {batch_index + 1}: {e}")

        logger.info(f"Completed embedding task. Total processed: {total_processed}")

    except Exception as e:
        logger.exception(f"Error in insert_embeddings_task: {e}")
    finally:
        close_old_connections()
