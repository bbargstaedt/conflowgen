from typing import Dict

from conflowgen.domain_models.distribution_repositories.truck_arrival_distribution_repository import \
    TruckArrivalDistributionRepository


class TruckArrivalDistributionManager:
    """
    This manager allows to set and get the weekly arrival rates of trucks. When the truck arrival time is drawn from
    this distribution, first a slice for the minimum and maximum dwell time is created and the arrival time of the truck
    is drawn from that period.
    """

    def __init__(self):
        self.truck_arrival_distribution_repository = TruckArrivalDistributionRepository()

    def get_truck_arrival_distributions(self) -> Dict[int, float]:
        """
        Returns: The truck arrival distribution.
            Each key represents the hour in the week and each value represents the
            probability of a truck to arrive between that hour and the start of the next time slot (the successor
            is the nearest key larger than the current key).
        """
        return self.truck_arrival_distribution_repository.get_distribution()

    def set_truck_arrival_distributions(self, distribution: Dict[int, float]) -> None:
        """

        Args:
            distribution: The truck arrival distribution.
                Each key represents the hour in the week and each value represents the
                probability of a truck to arrive between that hour and the start of the next time slot (the successor is
                the nearest key larger than the current key).
        """
        self.truck_arrival_distribution_repository.set_distribution(distribution)
