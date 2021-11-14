import pandas as pd
import pdb
from pprint import pprint
import logging
logging.debug("This is a warning")


class Building:

    def __init__(self, name, costs=[], value=0):
        self.name = name
        self.costs = costs
        self.value = value

    def __str__(self):
        return self.name

    @property
    def development_schedule(self):
        df = pd.concat(
            [cost.schedule for cost in self.costs],
            axis=1,
            keys=[cost.type for cost in self.costs]
        ).fillna(0)

        # add a total.
        df["total"] = df.sum(axis=1)

        return df

    @property
    def hard_cost_schedule(self):
        return pd.concat([cost.schedule for cost in self.costs], axis=1, keys=[
            cost.type for cost in self.costs]).fillna(0)

    @property
    def total_hard_costs(self):
        return self.hard_cost_schedule.values.sum()

    def reporting(self):
        print("Building:",
              "\n", "- name:", self.name,
              "\n", "- value:", "{:,.0f}".format(self.value),
              "\n", "- breakdown of development costs :",
              "\n", self.development_schedule.sum().to_string()
              )
