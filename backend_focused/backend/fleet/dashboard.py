import json
from decimal import Decimal

from unfold.components import BaseComponent, register_component

from fleet.queries import (
    active_vehicles_by_office,
    maintenance_cost_by_month,
    top_mechanic_workloads,
)


def _chart(labels, dataset):
    return json.dumps({"labels": labels, "datasets": [dataset]})


def _number(value):
    if isinstance(value, Decimal):
        return float(value.quantize(Decimal("0.01")))
    return value


@register_component
class ActiveVehiclesChart(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offices = list(active_vehicles_by_office())
        labels = [str(office) for office in offices]
        values = [office.active_count for office in offices]
        if not labels:
            labels, values = ["No offices"], [0]
        context.update(
            {
                "height": 320,
                "data": _chart(
                    labels,
                    {
                        "label": "Active vehicles",
                        "data": values,
                        "backgroundColor": "var(--color-primary-700)",
                        "displayYAxis": True,
                    },
                ),
            }
        )
        return context


@register_component
class MaintenanceCostChart(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        months = maintenance_cost_by_month()
        context.update(
            {
                "height": 320,
                "data": _chart(
                    [month.strftime("%b %Y") for month, _cost in months],
                    {
                        "label": "Maintenance cost",
                        "data": [_number(cost) for _month, cost in months],
                        "borderColor": "var(--color-primary-600)",
                        "backgroundColor": "var(--color-primary-200)",
                        "type": "line",
                        "displayYAxis": True,
                        "suffixYAxis": "$",
                        "maxTicksXLimit": 13,
                    },
                ),
            }
        )
        return context


@register_component
class MechanicWorkloadChart(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = list(top_mechanic_workloads())
        labels = [mechanic.name for mechanic in rows]
        values = [mechanic.maintenance_count for mechanic in rows]
        if not labels:
            labels, values = ["No mechanics"], [0]
        context.update(
            {
                "height": 320,
                "data": _chart(
                    labels,
                    {
                        "label": "Jobs this year",
                        "data": values,
                        "backgroundColor": "var(--color-primary-500)",
                        "displayYAxis": True,
                    },
                ),
            }
        )
        return context
