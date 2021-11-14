from collections import OrderedDict
from utilities import date_range, duration_months, ds_days, update_df, timeit
import pdb
import pandas as pd
# import numpy as np
from pyxirr import xirr as py_xirr
from datetime import datetime
import logging
logging.debug("This is a warning")


class Loan:
    facility_columns = [
        "funding date",
        "days btwn periods",
        "opening balance",
        "arrangement fee",
        "interest",
        "capital",
        "non-utilisation fee",
        "repayment",
        "closing balance",
        "exit fee",
        "cashflow",
        "facility used cumul"
    ]
    funding_columns = [
        "funding date",
        "funding required",
        "equity capital funding",
        "debt capital funding"
    ]
    max_headroom = 50000
    round_to = 50000

    def __init__(self,
                 arrangement_fee_pct,
                 interest_pct,
                 non_utilisation_fee_pct,
                 exit_fee_pct,
                 ltv_covenant,
                 ltc_covenant,
                 start_date=datetime.now(),
                 maturity_date=datetime.now(),
                 facility_schedule=pd.DataFrame(columns=facility_columns),
                 funding_schedule=pd.DataFrame(columns=funding_columns),
                 equity_required=0,
                 facility_amount=0,
                 collateral=[],
                 funding_required=pd.Series()):

        self.arrangement_fee_pct = arrangement_fee_pct
        self.interest_pct = interest_pct
        self.non_utilisation_fee_pct = non_utilisation_fee_pct
        self.exit_fee_pct = exit_fee_pct
        self.ltv_covenant = ltv_covenant
        self.ltc_covenant = ltc_covenant

        # attributes defined dynamically
        self.start_date = start_date
        self.maturity_date = maturity_date
        self.facility_schedule = facility_schedule
        self.funding_schedule = funding_schedule
        self._equity_required = equity_required
        self._facility_amount = facility_amount
        self.collateral = collateral
        self.funding_required = funding_required

    @property
    def facility_amount(self):
        return self._facility_amount

    @facility_amount.setter
    def facility_amount(self, new_facility_amount):
        self._facility_amount = new_facility_amount
        self.facility_schedule__refresh()
        self.equity_required = self.equity_required - self.headroom

    @property
    def equity_required(self):
        return self._equity_required

    @equity_required.setter
    def equity_required(self, new_equity_required):
        self._equity_required = new_equity_required
        self.funding_schedule__refresh()
        self.facility_schedule__refresh()

    @property
    def total_hard_costs(self):
        return self.funding_required.sum()

    @property
    def collateral_value(self):
        return sum([el.value for el in self.collateral if self.collateral])

    @property
    def term_months(self):
        return duration_months(self.start_date, self.maturity_date)

    @property
    def arrangement_fee(self):
        return self.facility_schedule["arrangement fee"].sum()

    @property
    def interest(self):
        return self.facility_schedule["interest"].sum()

    @property
    def capital(self):
        return self.facility_schedule["capital"].sum()

    @property
    def non_utilisation_fee(self):
        return self.facility_schedule["non-utilisation fee"].sum()

    @property
    def repayment(self):
        return abs(self.facility_schedule["repayment"].sum())

    @property
    def exit_fee(self):
        return self.facility_schedule["exit fee"].sum()

    @property
    def profit(self):
        return self.facility_schedule["cashflow"].sum()

    @property
    def xirr(self):
        dates = self.facility_schedule["funding date"]
        amounts = self.facility_schedule["cashflow"]
        return py_xirr(dates, amounts)

    @property
    def em(self):
        return (self.capital + self.profit) / self.capital

    @property
    def coc(self):
        return ((self.em - 1) / self.term_months) * 12

    @property
    def finance_costs_capitalised(self):
        finance_costs_capitalised = [
            self.arrangement_fee,
            self.interest,
            self.non_utilisation_fee
        ]
        return sum(finance_costs_capitalised)

    @property
    def total_funded_costs(self):
        total_funded_costs = [
            self.finance_costs_capitalised,
            self.capital
        ]
        return sum(total_funded_costs)

    @property
    def total_fundable_costs(self):
        return self.finance_costs_capitalised + self.total_hard_costs

    def ltc(self):
        return self.facility_amount / self.total_fundable_costs

    def ltv(self):
        return self.facility_amount / self.collateral_value

    @property
    def headroom(self):
        return self.facility_amount - self.total_funded_costs

    def reporting(self):
        print("\n\n",
              "Loan terms:",
              "\n", "- Facility amount:", "{:,.0f}".format(
                  self.facility_amount),
              "\n", "- Capital committed:", "{:,.0f}".format(
                  self.capital),
              "\n", "- Loan headroom:", "{:,.0f}".format(
                  self.headroom),
              "\n", "- Equity required:", "{:,.0f}".format(
                  self.equity_required),
              "\n", "- Duration:", "{:,.1f} months".format(
                  self.term_months),
              "\n", "- Arrangement Fee:", "{:.2%}".format(
                  self.arrangement_fee_pct),
              "\n", "- Interest:", "{:.2%}".format(
                  self.interest_pct),
              "\n", "- Non Utilisation Fee:", "{:.2%}".format(
                  self.non_utilisation_fee_pct),
              "\n", "- Exit Fee:", "{:.2%}".format(
                  self.exit_fee_pct),

              "\n\n",
              "Leverage metrics:",
              "\n", "- Loan-to-value:",  "{:.1%}".format(
                  self.ltv()),
              "\n", "- Loan-to-cost:", "{:.1%}".format(self.ltc()),

              "\n\n",
              "Returns:",
              "\n", "- Profit:", "{:,.0f}".format(self.profit),
              "\n", "- XIRR:", "{:.1%}".format(self.xirr),
              "\n", "- Equity Multiple:", "{:,.2f}x".format(self.em),
              "\n", "- Cash on Cash yield:", "{:.2%}".format(self.coc),
              )

    def add_nb(self, df, nb):
        # print(df["opening balance"] + nb)
        df["opening balance"] = df["opening balance"] + nb
        print(df)
        return df

    @timeit
    def facility_schedule__refresh(self):
        # CONTINUE HERE !! ========>>>
        schedule = self.facility_schedule

        # reset values to zero
        re_set_columns = [col for col in list(schedule.columns) if col not in [
            "days btwn periods", "capital", "funding date"]]
        schedule[re_set_columns] = 0

        for index, row in schedule.iterrows():
            days = row["days btwn periods"]

            # opening balance
            schedule.at[index,
                        "opening balance"] = (0 if index == 0 else schedule.at[index-1, "closing balance"])

            # arrangement fee
            if index == 0:
                schedule.at[index,
                            "arrangement fee"] = self.arrangement_fee_pct * self.facility_amount

            # interest
            schedule.at[index,
                        "interest"] = self.interest_pct * schedule.at[index, "opening balance"] * days / 365

            # non utilisation fee
            facility_used_cumul_previous = (
                0 if index == 0 else schedule.at[index-1, "facility used cumul"])
            schedule.at[index,
                        "non-utilisation fee"] = self.non_utilisation_fee_pct * max(0, self.facility_amount - facility_used_cumul_previous) * days / 365

            # facility used cumul
            facility_used = sum([schedule.at[index, "arrangement fee"],
                                 schedule.at[index, "interest"],
                                 row["capital"],
                                 schedule.at[index, "non-utilisation fee"]])
            schedule.at[index, "facility used cumul"] = facility_used + \
                facility_used_cumul_previous

            # repayment and exit fee
            if index == len(schedule.index)-1:
                schedule.at[index, "exit fee"] = self.exit_fee_pct * \
                    self.facility_amount
                schedule.at[index, "repayment"] = - sum([
                    schedule.at[index, "opening balance"],
                    schedule.at[index, "interest"],
                    row["capital"],
                    schedule.at[index, "non-utilisation fee"]
                ])

            # closing balance
            schedule.at[index, "closing balance"] = sum([
                schedule.at[index, "opening balance"],
                schedule.at[index, "arrangement fee"],
                schedule.at[index, "interest"],
                row["capital"],
                schedule.at[index, "non-utilisation fee"],
                schedule.at[index, "repayment"]
            ])

        # cashflow
        schedule["cashflow"] = - schedule["capital"] - \
            schedule["repayment"] - schedule["exit fee"]

    def facility_capped(self):
        return min(self.ltv_covenant * self.collateral_value, self.ltc_covenant * self.total_fundable_costs)

    def facility_schedule__initialise(self):
        schedule = self.facility_schedule

        # funding dates to take into account standard of end of month for payment of interest
        schedule["funding date"] = date_range(
            self.start_date, self.maturity_date)

        # set index of schedule as funding dates, to be able to combine with the Series funding_required
        schedule.index = schedule["funding date"]

        # define total funding required
        schedule["capital"] = self.funding_required

        # reset index such that index shows period number
        schedule.reset_index(inplace=True, drop=True)
        schedule.index.name = "period"

        # days between periods
        schedule["days btwn periods"] = ds_days(schedule, "funding date")

        schedule.fillna(0, inplace=True)

        schedule["facility used cumul"] = schedule["capital"].cumsum()

        # refresh finance costs now that funding required is defined
        self.facility_schedule__refresh()

    def funding_schedule__initialise(self):
        schedule = self.funding_schedule

        schedule["funding required"] = self.funding_required
        schedule["funding date"] = schedule.index

        # reset index such that index shows period number
        schedule.reset_index(inplace=True, drop=True)
        schedule.index.name = "period"

        # all funding initially from debt

        update_df(
            df_to_update=schedule,
            df_updating=self.facility_schedule,
            col_to_update="debt capital funding",
            col_updating="capital",
            join_on="funding date"
        )

        # set values of columns to zero
        schedule.fillna(0, inplace=True)

    def facility_amount__initialise(self):
        self.facility_amount = self.repayment
        while int(self.headroom) != 0:
            self.facility_amount = self.repayment

        self.facility_schedule__refresh()

    def funding_schedule__refresh(self):
        schedule = self.funding_schedule
        equity = self.equity_required

        # initialise funders invested amount
        schedule["equity capital funding"] = 0
        schedule["debt capital funding"] = 0

        # all periods
        for i in range(0, len(schedule)):
            equity_available = equity - schedule["equity capital funding"].sum()

            schedule.loc[i, "equity capital funding"] = min(
                schedule.loc[i, "funding required"], equity_available
            )

        # debt capital funding
        schedule["debt capital funding"] = schedule["funding required"] - \
            schedule["equity capital funding"]

        # update facility_schedule with the new spread of costs
        update_df(
            df_to_update=self.facility_schedule,
            df_updating=self.funding_schedule,
            col_to_update="capital",
            col_updating="debt capital funding",
            join_on="funding date"
        )
        self.facility_schedule__refresh()

    def facility_amount__size(self):
        # resize loan and define equity required based on loan leverage covenants
        while int(self.headroom) != 0:
            self.facility_amount = self.facility_capped()

    def facility_amount__round(self):
        self.facility_amount = int(
            self.facility_amount / self.round_to) * self.round_to
        self.facility_schedule__refresh()
        while int(self.headroom) != 0:
            self.equity_required = self.equity_required - self.headroom
        if self.headroom < 0:
            self.equity_required = self.equity_required + self.headroom

    def add_headroom(self):
        while int(self.headroom) != self.max_headroom:
            self.equity_required = self.equity_required + self.max_headroom - self.headroom
