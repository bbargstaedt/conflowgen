from __future__ import annotations
import datetime
from typing import Dict, NamedTuple, Union

from conflowgen.preview.abstract_preview import AbstractPreview
from conflowgen.preview.container_flow_by_vehicle_type_preview import \
    ContainerFlowByVehicleTypePreview
from conflowgen.preview.inbound_and_outbound_vehicle_capacity_preview import \
    InboundAndOutboundVehicleCapacityPreview
from conflowgen.domain_models.data_types.mode_of_transport import ModeOfTransport
from conflowgen.domain_models.distribution_validators.mode_of_transport_distribution_validator import \
    ModeOfTransportDistributionValidator


class RequiredAndMaximumCapacityComparison(NamedTuple):
    """
    This is a tuple that maintains three separate values for a given vehicle type. First, the currently planned capacity
    is recorded. Second, the maximum capacity is noted. If more capacity is requested than available, the exceeded flag
    is true, otherwise false.
    """
    currently_planned: Union[int, float]
    maximum: Union[int, float]
    exceeded: bool


class VehicleCapacityExceededPreview(AbstractPreview):
    """
    The preview examines the outbound traffic and checks if the intended transportation demands can be satisfied by the
    existing transport capacities (per vehicle type).

    The preview returns a data structure that can be used for generating reports (e.g., in text or as a figure)
    as it is the case with :class:`.VehicleCapacityExceededPreviewReport`.
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

        self.inbound_and_outbound_vehicle_capacity_preview = InboundAndOutboundVehicleCapacityPreview(
            start_date=start_date,
            end_date=end_date,
            transportation_buffer=transportation_buffer
        )
        self.container_flow_by_vehicle_type_preview = ContainerFlowByVehicleTypePreview(
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
        self.inbound_and_outbound_vehicle_capacity_preview.hypothesize_with_mode_of_transport_distribution(
            mode_of_transport_distribution
        )
        self.container_flow_by_vehicle_type_preview.hypothesize_with_mode_of_transport_distribution(
            mode_of_transport_distribution
        )

    def compare(
            self
    ) -> Dict[ModeOfTransport, RequiredAndMaximumCapacityComparison]:
        """
        Compare the required capacity of vehicles on their outbound journey to transport all containers and the maximum
        capacity of the vehicles on their outbound journey. If the maximum capacity of the vehicles is exceeded, this
        mismatch is indicated (per vehicle type, in TEU).
        """
        comparison = {
            mode_of_transport: (0, 0, False)
            for mode_of_transport in ModeOfTransport
        }

        inbound_vehicle_capacities = self.inbound_and_outbound_vehicle_capacity_preview.\
            get_inbound_capacity_of_vehicles()
        _, outbound_maximum_capacities = self.inbound_and_outbound_vehicle_capacity_preview.\
            get_outbound_capacity_of_vehicles()
        flow = self.container_flow_by_vehicle_type_preview.get_inbound_to_outbound_flow()
        for outgoing_vehicle_type, maximum_capacity in outbound_maximum_capacities.items():
            container_capacity_to_pick_up = 0
            for incoming_vehicle_type, delivered_capacity in inbound_vehicle_capacities.items():
                container_capacity_destined_for_outgoing_vehicle_type = \
                    flow[incoming_vehicle_type][outgoing_vehicle_type]
                container_capacity_to_pick_up += container_capacity_destined_for_outgoing_vehicle_type

            vehicle_type_capacity_is_exceeded = container_capacity_to_pick_up > maximum_capacity
            if maximum_capacity == -1:
                # Special case: if a vehicle type has no maximum capacity, there cannot be any mismatch
                vehicle_type_capacity_is_exceeded = False

            comparison[outgoing_vehicle_type] = RequiredAndMaximumCapacityComparison(
                currently_planned=container_capacity_to_pick_up,
                maximum=maximum_capacity,
                exceeded=vehicle_type_capacity_is_exceeded
            )

        return comparison
