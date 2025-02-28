from __future__ import annotations
import itertools

from conflowgen.posthoc_analysis.abstract_posthoc_analysis_report import AbstractPosthocAnalysisReport
from conflowgen.posthoc_analysis.container_flow_by_vehicle_type_analysis import ContainerFlowByVehicleTypeAnalysis


class ContainerFlowByVehicleTypeAnalysisReport(AbstractPosthocAnalysisReport):
    """
    This analysis report takes the data structure as generated by :class:`.ContainerFlowByVehicleTypeAnalysis`
    and creates a comprehensible representation for the user, either as text or as a graph.
    """

    def __init__(self):
        super().__init__()
        self.analysis = ContainerFlowByVehicleTypeAnalysis()

    def get_report_as_text(
            self
    ) -> str:
        inbound_to_outbound_flow = self.analysis.get_inbound_to_outbound_flow()

        # create string representation
        report = "\n"
        report += "vehicle type (from) "
        report += "vehicle type (to) "
        report += "transported capacity (in TEU)"
        report += "\n"
        for vehicle_type_from, vehicle_type_to in itertools.product(self.order_of_vehicle_types_in_report, repeat=2):
            vehicle_type_from_as_text = str(vehicle_type_from).replace("_", " ")
            vehicle_type_to_as_text = str(vehicle_type_to).replace("_", " ")
            report += f"{vehicle_type_from_as_text:<19} "
            report += f"{vehicle_type_to_as_text:<18} "
            report += f"{inbound_to_outbound_flow[vehicle_type_from][vehicle_type_to]:>28.1f}"
            report += "\n"

        report += "(rounding errors might exist)\n"
        return report

    def get_report_as_graph(self) -> object:
        """
        The container flow is represented by a Sankey diagram.

        Returns: The plotly figure of the Sankey diagram.

        .. note::
            At the time of writing, plotly comes with some shortcomings.

            * Sorting the labels on either the left or right side without recalculating the height of each bar is not
              possible, see https://github.com/plotly/plotly.py/issues/1732.
            * Empty nodes require special handling, see https://github.com/plotly/plotly.py/issues/3003 and the
              coordinates need to be $0 < x,y < 1$ (no equals!), see https://github.com/plotly/plotly.py/issues/3002.

            However, it seems to be the best available library for plotting Sankey diagrams that can be visualized e.g.
            in a Jupyter Notebook.
        """

        import plotly.graph_objects as go  # pylint: disable=import-outside-toplevel

        inbound_to_outbound_flow = self.analysis.get_inbound_to_outbound_flow()

        vehicle_types = [str(vehicle_type).replace("_", " ") for vehicle_type in inbound_to_outbound_flow.keys()]
        source_ids = list(range(len(vehicle_types)))
        target_ids = list(range(len(vehicle_types), 2 * len(vehicle_types)))
        value_ids = list(itertools.product(source_ids, target_ids))
        source_ids_with_duplication = [source_id for (source_id, _) in value_ids]
        target_ids_with_duplication = [target_id for (_, target_id) in value_ids]
        value = [
            inbound_to_outbound_flow[inbound_vehicle_type][outbound_vehicle_type]
            for inbound_vehicle_type in inbound_to_outbound_flow.keys()
            for outbound_vehicle_type in inbound_to_outbound_flow[inbound_vehicle_type].keys()
        ]
        inbound_labels = [
            str(inbound_vehicle_type).replace("_", " ").capitalize() + ":<br>Inbound: " + str(
                round(sum(inbound_to_outbound_flow[inbound_vehicle_type].values()), 2))
            for inbound_vehicle_type in inbound_to_outbound_flow.keys()
        ]
        to_outbound_flow = [0 for _ in range(len(inbound_to_outbound_flow.keys()))]
        for inbound_vehicle_type, inbound_capacity in inbound_to_outbound_flow.items():
            for i, outbound_vehicle_type in enumerate(inbound_to_outbound_flow[inbound_vehicle_type].keys()):
                to_outbound_flow[i] += inbound_capacity[outbound_vehicle_type]
        outbound_labels = [
            str(outbound_vehicle_type).replace("_", " ").capitalize() + ":<br>Outbound: " + str(
                round(to_outbound_flow[i], 2))
            for i, outbound_vehicle_type in enumerate(inbound_to_outbound_flow.keys())
        ]
        fig = go.Figure(
            data=[
                go.Sankey(
                    arrangement='perpendicular',
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(
                            color="black",
                            width=0.5
                        ),
                        label=inbound_labels + outbound_labels,
                        color="dimgray",
                    ),
                    link=dict(
                        source=source_ids_with_duplication,
                        target=target_ids_with_duplication,
                        value=value
                    )
                )
            ]
        )

        fig.update_layout(
            title_text="Container flow from vehicle type A to vehicle type B as defined by generated containers",
            font_size=10,
            width=900,
            height=700
        )
        return fig
