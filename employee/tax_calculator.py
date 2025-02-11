from django.conf import settings

tax_charge = {
    "f_300000": float(settings.F_300000),
    "n_300000": float(settings.N_300000),
    "n_500000": float(settings.N_500000),
    "nf_500000": float(settings.NF_500000),
    "n_1600000": float(settings.N_1600000),
    "a_3200000": float(settings.A_3200000)
}

allowances = {
    "transport_allowance_rate":float(settings.TRANSPORT_ALLOWANCE_RATE),
    "housing_allowance_rate":float(settings.HOUSING_ALLOWANCE_RATE)
}

cra_relief_map = {
    "pension":float(settings.PENSION),
    "nhf":float(settings.NHF),
    "CRA":float(settings.CRA),
    "top_cra":float(settings.TOP_CRA)
}

def calculate_tax(montly_payment: float) -> float:
    """
    This calculate the tax base on the monthly salary
    monthly_payment: float (This is the employee monthly)
    """
    gross_payment = montly_payment * 12

    # get the less i.e non taxable income to have a redefined annual pay to remove consolidated relief allowance from
    less = 0

    # get the reliefs
    total_allowance = 0
    for allowance_rate in allowances.values():
        total_allowance += float(allowance_rate) * gross_payment

    # main allowances needed for pension, nhf and nhis
    transport_allowance = float(allowances.get("transport_allowance_rate", 0)) * gross_payment
    housing_allowance = float(allowances.get("transport_allowance_rate", 0)) * gross_payment
    basic_pay = gross_payment - total_allowance

    pension = cra_relief_map.get("pensions")
    if pension:
        # update the less
        less += cra_relief_map.get("pension") * (basic_pay + transport_allowance + housing_allowance)


    nhf = cra_relief_map.get("nhfs")
    if nhf:
        # update the less
        less += cra_relief_map.get("nhf") * housing_allowance # basic_pay

    # TODO: implement NHIS

    # Get the redefined annual pay i.e the gross payment
    redefined_annual_pay = gross_payment - less

    # Get the CRA: consolidated relief allowance
    top_cra = 200000 if (cra_relief_map.get("top_cra") * redefined_annual_pay) < 200000 else (cra_relief_map.get("top_cra") * redefined_annual_pay)
    CRA = (cra_relief_map.get("CRA") * redefined_annual_pay) + top_cra + less

    real_tax_charge = 0.0

    # Get the national income tax: This is to determine if tax will be removed or not
    national_annual_income = float(settings.NATIONAL_MINIMUM_WAGE) * 12
    taxable_annual_income = gross_payment - CRA
    old_taxable_annual_income = taxable_annual_income
    """
    a new  proviso  was  inserted  in  Section  37  of  PITA  which
    provides that, minimum tax shall not apply to any person who earns in any
    year of assessment national minimum wage or less from an employment. .
    """

    if int(national_annual_income) >= redefined_annual_pay:
        # no tax is to be deducted
        return 0, 0

    above_charge_tax_amount = int(settings.ABOVE_CHARGE_TAX_AMOUNT) # this is the highest rate to be charged
    for tax_, tax_percent in tax_charge.items():
        amount_to_tax_on = int(tax_.split('_')[1])
        # check if the rate is the last and charge the excess only
        if list(tax_charge.keys())[-1].split("_")[-1] == above_charge_tax_amount:
            excess_amount = old_taxable_annual_income - above_charge_tax_amount
            real_tax_charge += tax_percent * excess_amount
            break
        if taxable_annual_income > amount_to_tax_on:
            real_tax_charge += tax_percent * amount_to_tax_on
            taxable_annual_income -= amount_to_tax_on
        else:
            real_tax_charge += tax_percent * taxable_annual_income
            break

    return round(real_tax_charge,2), round(real_tax_charge/12, 2)
