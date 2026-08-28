"""Repository for SimulationPhoneNumber model — encapsulates all ORM access."""

from __future__ import annotations

from typing import Any

from simulate.models.simulation_phone_number import SimulationPhoneNumber


class PhoneNumberRepository:
    """Data access layer for SimulationPhoneNumber."""

    @staticmethod
    async def resolve_to_call_config(phone_number: str) -> dict[str, Any] | None:
        """Find an IN_USE phone number and return its linked call config.

        Returns None if no matching phone number is found or if it has
        no linked call execution.
        """
        try:
            phone = await SimulationPhoneNumber.objects.select_related(
                "current_call_execution"
            ).aget(
                phone_number=phone_number,
                status=SimulationPhoneNumber.PhoneStatus.IN_USE,
            )
        except SimulationPhoneNumber.DoesNotExist:
            return None

        if not phone.current_call_execution:
            return None

        ce = phone.current_call_execution
        return {
            "call_id": str(ce.id),
            "call_metadata": ce.call_metadata or {},
            "provider_call_data": ce.provider_call_data or {},
            "status": ce.status,
        }
