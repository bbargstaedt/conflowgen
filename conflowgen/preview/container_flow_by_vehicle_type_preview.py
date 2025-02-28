from __future__ import annotations
import datetime
from typing import Dict

from conflowgen.preview.abstract_preview import AbstractPreview
from conflowgen.preview.inbound_and_outbound_vehicle_capacity_preview import \
    InboundAndOutboundVehicleCapacityPreview
from conflowgen.domain_models.data_types.mode_of_transport import ModeOfTransport
from conflowgen.domain_models.distribution_repositories.mode_of_transport_distribution_repository import \
    ModeOfTransportDistributionRepository
from conflowgen.domain_models.distribution_validators.mode_of_transport_distribution_validator import \
    ModeOfTransportDistributionValidator


class ContainerFlowByVehicleTypePreview(AbstractPreview):
    """
    This preview informs the user about from which vehicle type to which vehicle type how many containers are intended
    to be moved.

    The preview returns a data structure that can be used for generating reports (e.g., in text or as a figure)
    as it is the case with :class:`.ContainerFlowByVehicleTypePreviewReport`.
    The preview is intended to provide a first estimate before running the expensive
    :meth:`.ContainerFlowGenerationManager.generate` method.
    The preview does not consider all restrictions (such as container dwell times in combination with the schedules)
    into consideration, thus later deviations might exist.
    """

    def __init__(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            transportation_buffer: float
    ):
        """
        Args:
            start_date: The earliest day to consider when checking the vehicles that move according to schedules
            end_date: The latest day to consider when checking the vehicles that move according to schedules
            transportation_buffer: The fraction of how much more a vehicle takes with it on an outbound journey
                compared to an inbound journey as long as the total vehicle capacity is not exceeded.
        """
        super().__init__(
            start_date=start_date,
            end_date=end_date,
            transportation_buffer=transportation_buffer
        )

        self.mode_of_transport_distribution = ModeOfTransportDistributionRepository().get_distribution()
        self.inbound_and_outbound_vehicle_capacity_preview = InboundAndOutboundVehicleCapacityPreview(
            start_date=start_date,
            end_date=end_date,
            transportation_buffer=transportation_buffer
        )
        self.validator = ModeOfTransportDistributionValidator()

    def hypothesize_with_mode_of_transport_distribution(
            self,
            mode_of_transport_distribution: Dict[ModeOfTransport, Dict[ModeOfTransport, float]]
    ):
        self.validator.validate(mode_of_transport_distribution)
        self.mode_of_transport_distribution = mode_of_transport_distribution

    def get_inbound_to_outbound_flow(
            self
    ) -> Dict[ModeOfTransport, Dict[ModeOfTransport, int | float]]:
        """
        The estimated flow of containers from vehicles on their inbound journey to vehicles on their outbound journey
        based on the mode of transport distribution.

        Returns: A flow from vehicle type A to vehicle type B estimated in TEU.
        """
        inbound_to_outbound_flow: Dict[ModeOfTransport, Dict[ModeOfTransport, int | float]] = {
            vehicle_type_inbound:
                {
                    vehicle_type_outbound: 0
                    for vehicle_type_outbound in ModeOfTransport
                }
            for vehicle_type_inbound in ModeOfTransport
        }
        inbound_capacity_per_vehicle_type = self.inbound_and_outbound_vehicle_capacity_preview.\
            get_inbound_capacity_of_vehicles()

        for inbound_vehicle_type in inbound_capacity_per_vehicle_type.keys():
            inbound_capacity_of_vehicle_type = inbound_capacity_per_vehicle_type[inbound_vehicle_type]
            distribution_for_vehicle_type = self.mode_of_transport_distribution[inbound_vehicle_type]
            for outbound_vehicle_type, frequency in distribution_for_vehicle_type.items():
                outbound_capacity_from_inbound_to_outbound = inbound_capacity_of_vehicle_type * frequency
                inbound_to_outbound_flow[inbound_vehicle_type][outbound_vehicle_type] = \
                    outbound_capacity_from_inbound_to_outbound

        return inbound_to_outbound_flow
