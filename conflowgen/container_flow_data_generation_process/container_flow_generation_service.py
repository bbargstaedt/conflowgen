import datetime
import logging

from conflowgen.application_models.container_flow_statistics_report import ContainerFlowStatisticsReport
from conflowgen.application_models.repositories.container_flow_generation_properties_repository import \
    ContainerFlowGenerationPropertiesRepository
from conflowgen.container_flow_data_generation_process.assign_destination_to_container_service import \
    AssignDestinationToContainerService
from conflowgen.container_flow_data_generation_process.large_scheduled_vehicle_creation_service import \
    LargeScheduledVehicleCreationService
from conflowgen.domain_models.container import Container
from conflowgen.domain_models.vehicle import LargeScheduledVehicle, Truck
from conflowgen.container_flow_data_generation_process.allocate_space_for_containers_delivered_by_truck_service import \
    AllocateSpaceForContainersDeliveredByTruckService
from conflowgen.container_flow_data_generation_process.large_scheduled_vehicle_for_onward_transportation_manager \
    import LargeScheduledVehicleForOnwardTransportationManager
from conflowgen.container_flow_data_generation_process.truck_for_export_containers_manager import \
    TruckForExportContainersManager
from conflowgen.container_flow_data_generation_process.truck_for_import_containers_manager import \
    TruckForImportContainersManager


class ContainerFlowGenerationService:

    def __init__(self):
        self.logger = logging.getLogger("conflowgen")
        self.truck_for_import_containers_manager = TruckForImportContainersManager()
        self.truck_for_export_containers_manager = TruckForExportContainersManager()
        self.large_scheduled_vehicle_creation_service = LargeScheduledVehicleCreationService()
        self.large_scheduled_vehicle_for_onward_transportation_manager = \
            LargeScheduledVehicleForOnwardTransportationManager()
        self.allocate_space_for_containers_delivered_by_truck_service = \
            AllocateSpaceForContainersDeliveredByTruckService()
        self.assign_destination_to_container_service = AssignDestinationToContainerService()

    def _update_generation_properties_and_distributions(self):
        self.container_flow_generation_properties_manager = ContainerFlowGenerationPropertiesRepository()
        container_flow_generation_properties = self.container_flow_generation_properties_manager.\
            get_container_flow_generation_properties()

        self.container_flow_start_date: datetime.date = container_flow_generation_properties.start_date
        self.container_flow_end_date: datetime.date = container_flow_generation_properties.end_date
        assert self.container_flow_start_date < self.container_flow_end_date

        self.minimum_dwell_time_of_import_containers_in_hours: int = container_flow_generation_properties \
            .minimum_dwell_time_of_import_containers_in_hours
        self.maximum_dwell_time_of_import_containers_in_hours: int = container_flow_generation_properties \
            .maximum_dwell_time_of_import_containers_in_hours
        assert (self.minimum_dwell_time_of_import_containers_in_hours
                < self.maximum_dwell_time_of_import_containers_in_hours)

        self.minimum_dwell_time_of_export_containers_in_hours: int = container_flow_generation_properties \
            .minimum_dwell_time_of_export_containers_in_hours
        self.maximum_dwell_time_of_export_containers_in_hours: int = container_flow_generation_properties \
            .maximum_dwell_time_of_export_containers_in_hours
        assert (self.minimum_dwell_time_of_export_containers_in_hours
                < self.maximum_dwell_time_of_export_containers_in_hours)

        self.minimum_dwell_time_of_transshipment_containers_in_hours: int = container_flow_generation_properties \
            .minimum_dwell_time_of_transshipment_containers_in_hours
        self.maximum_dwell_time_of_transshipment_containers_in_hours: int = container_flow_generation_properties \
            .maximum_dwell_time_of_transshipment_containers_in_hours
        assert (self.minimum_dwell_time_of_transshipment_containers_in_hours
                < self.maximum_dwell_time_of_transshipment_containers_in_hours)

        self.transportation_buffer: float = container_flow_generation_properties.transportation_buffer
        assert -1 < self.transportation_buffer

        self.large_scheduled_vehicle_for_onward_transportation_manager.reload_properties(
            minimum_dwell_time_of_import_containers_in_hours=
            self.minimum_dwell_time_of_import_containers_in_hours,
            minimum_dwell_time_of_export_containers_in_hours=
            self.minimum_dwell_time_of_export_containers_in_hours,
            minimum_dwell_time_of_transshipment_containers_in_hours=
            self.minimum_dwell_time_of_transshipment_containers_in_hours,
            maximum_dwell_time_of_import_containers_in_hours=
            self.maximum_dwell_time_of_import_containers_in_hours,
            maximum_dwell_time_of_export_containers_in_hours=
            self.maximum_dwell_time_of_export_containers_in_hours,
            maximum_dwell_time_of_transshipment_containers_in_hours=
            self.maximum_dwell_time_of_transshipment_containers_in_hours,
            transportation_buffer=self.transportation_buffer
        )
        self.allocate_space_for_containers_delivered_by_truck_service.reload_distribution(
            transportation_buffer=self.transportation_buffer
        )
        self.truck_for_import_containers_manager.reload_distribution(
            minimum_dwell_time_in_hours=self.minimum_dwell_time_of_import_containers_in_hours,
            maximum_dwell_time_in_hours=self.maximum_dwell_time_of_import_containers_in_hours
        )
        self.truck_for_export_containers_manager.reload_distribution(
            minimum_dwell_time_in_hours=self.minimum_dwell_time_of_export_containers_in_hours,
            maximum_dwell_time_in_hours=self.maximum_dwell_time_of_export_containers_in_hours
        )
        self.large_scheduled_vehicle_creation_service.reload_properties(
            container_flow_start_date=self.container_flow_start_date,
            container_flow_end_date=self.container_flow_end_date
        )
        self.assign_destination_to_container_service.reload_distribution()

    @staticmethod
    def clear_previous_container_flow():
        Container.delete().execute()  # pylint: disable=no-value-for-parameter

        # Due to cascading foreign keys, Train, Feeder etc. are also deleted
        LargeScheduledVehicle.delete().execute()  # pylint: disable=no-value-for-parameter

        Truck.delete().execute()  # pylint: disable=no-value-for-parameter

    def generate(self):
        self.logger.info("Remove previous data...")
        self.clear_previous_container_flow()
        self.logger.info("Reloading properties and distributions...")
        self._update_generation_properties_and_distributions()

        self.logger.info("Create fleet including their delivered containers for given time range for each schedule...")
        self.large_scheduled_vehicle_creation_service.create()

        self.logger.info("Loading status of vehicles adhering to a schedule:")
        report = ContainerFlowStatisticsReport(transportation_buffer=self.transportation_buffer)
        report.generate()
        self.logger.info(report.get_text_representation())

        self.logger.info("Assign containers arriving by vehicles adhering a schedule for onward transportation...")
        self.large_scheduled_vehicle_for_onward_transportation_manager.choose_departing_vehicle_for_containers()
        number_assigned_containers = (self.large_scheduled_vehicle_for_onward_transportation_manager
                                      .number_assigned_containers)
        number_not_assignable_containers = (self.large_scheduled_vehicle_for_onward_transportation_manager
                                            .number_not_assignable_containers)
        assigned_as_fraction = number_assigned_containers / (
                    number_assigned_containers + number_not_assignable_containers)
        self.logger.info(
            f"Containers for which no outgoing vehicle could be found: {(assigned_as_fraction * 100):.2f}%")

        self.logger.info("Loading status of vehicles adhering to a schedule:")
        report = ContainerFlowStatisticsReport(transportation_buffer=self.transportation_buffer)
        report.generate()
        self.logger.info(report.get_text_representation())

        self.logger.info("Generate trucks that pick up containers...")
        self.truck_for_import_containers_manager.generate_trucks_for_picking_up()

        self.logger.info("Generate containers that are delivered by trucks...")
        self.allocate_space_for_containers_delivered_by_truck_service.allocate()

        self.logger.info("Loading status of vehicles adhering to a schedule:")
        report = ContainerFlowStatisticsReport(transportation_buffer=self.transportation_buffer)
        report.generate()
        self.logger.info(report.get_text_representation())

        self.logger.info("Generate trucks that deliver containers...")
        self.truck_for_export_containers_manager.generate_trucks_for_delivering()

        self.logger.info("Assign containers to next destinations...")
        self.assign_destination_to_container_service.assign()

        self.logger.info("Container flow generation finished")

        self.logger.info("Final capacity status of vehicles adhering to a schedule:")
        report = ContainerFlowStatisticsReport(transportation_buffer=self.transportation_buffer)
        report.generate()
        self.logger.info(report.get_text_representation())
