from building import Building
from loan import Loan
from cost import Cost
from datetime import datetime
import pandas as pd
import numpy as np
import pdb
import logging
logging.debug("This is a warning")


def underwrite_process():
    # pandas formatting
    pd.set_option('display.max_columns', None)
    pd.options.display.float_format = '{:,.2f}'.format

    # define development costs
    cost1_start = datetime(2021, 6, 28)
    cost1 = Cost("Acquisition costs",
                 100000, cost1_start)

    cost2_start = datetime(2021, 7, 1)
    cost2_end = datetime(2023, 6, 28)
    cost2 = Cost("Construction costs",
                 5000000, cost2_start, cost2_end)

    cost3_start = datetime(2021, 7, 1)
    cost3_end = datetime(2023, 6, 28)
    cost3 = Cost("Professional fees",
                 250000, cost3_start, cost3_end)

    # define building parameters
    building = Building("Beautiful Point")
    building.value = (100000 + 5000000 + 250000) * 1.4
    building.costs = [cost1, cost2, cost3]

    # instantiate loan and define basic criteria
    loan = Loan(
        arrangement_fee_pct=0.01,
        interest_pct=0.06,
        non_utilisation_fee_pct=0.02,
        exit_fee_pct=0.015,
        ltv_covenant=0.75,
        ltc_covenant=0.85
    )

    # loan start date and maturity to match development duration in this case
    loan.start_date = min(building.hard_cost_schedule.index)
    loan.maturity_date = max(building.hard_cost_schedule.index)

    # define schedule of hard costs which require funding
    # loan.funding_required = building.hard_cost_schedule.sum(axis=1)
    loan.funding_required = building.development_schedule["total"]

    # initialise facility and funding schedule
    loan.facility_schedule__initialise()
    loan.funding_schedule__initialise()
    loan.facility_amount__initialise()

    # assign collateral to the loan and resize loan based on loan  covenants
    loan.collateral = [building]
    loan.facility_amount = loan.facility_capped()

    # size facility, within the covenant parameters
    loan.facility_amount__size()

    # round facility to the required rounding
    loan.facility_amount__round()

    # add headroom to the required level
    loan.add_headroom()

    return loan, building


def main():
    # underwrite loan
    loan, building = underwrite_process()

    # reporting
    print("\n")
    building.reporting()
    loan.reporting()


# Check to see if this file is being run as the main module
if __name__ == '__main__':
    main()
