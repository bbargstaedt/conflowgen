from __future__ import annotations

import abc
from typing import NamedTuple, Union, Dict

from conflowgen.domain_models.data_types.mode_of_transport import ModeOfTransport


class ContainersAndTEUContainerFlowPair(NamedTuple):
    """
    This is a pair of two container flows, i.e. the number of containers moving from A to B within a given time window.
    First, it is reported in containers which is important for reporting the efficiency at the interfaces,
    e.g. moves per hour for the ship-to-shore gantry cranes.
    Second, it is reported in TEU which is important for the yard capacity.
    """
    containers: Dict[ModeOfTransport, Dict[ModeOfTransport, Union[int, float]]]
    TEU: Dict[ModeOfTransport, Dict[ModeOfTransport, Union[int, float]]]


class AbstractPosthocAnalysis(abc.ABC):

    def __init__(
            self,
            transportation_buffer: float | None = None
    ):
        """

        Args:
            transportation_buffer: The buffer, e.g. 0.2 means that 20% more containers (in TEU) can be put on a vessel
                compared to the amount of containers it had on its inbound journey - as long as the total vehicle
                capacity would not be exceeded.
        """
        self.transportation_buffer: float | None = None
        self.update(
            transportation_buffer=transportation_buffer
        )

    def update(
            self,
            transportation_buffer: float | None
    ):
        """
        As the transportation buffer is not stored in the database, for some analyses it needs to be provided.

        Args:
            transportation_buffer: The buffer, e.g. 0.2 means that 20% more containers (in TEU) can be put on a vessel
                compared to the amount of containers it had on its inbound journey - as long as the total vehicle
                capacity would not be exceeded.
        """
        if transportation_buffer is not None:
            assert transportation_buffer > -1
            self.transportation_buffer = transportation_buffer
