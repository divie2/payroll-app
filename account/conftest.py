import pytest


@pytest.fixture(scope="session")
def sample_reg_data():
    data = {
        "jira_ticket_id": "IS-21",
        "base_pay": 200,
        "job_role": "Data Migration Expert",
        "job_type": "Full Time",
        "pay_deno": "Naira",
        "phone": "12345",
        "start_date": "2025-01-13",
        "dob": "2025-01-13",
        "fullname": "January Born",
        "email": "jan@alluvium.net",
        "acct_num": "123",
        "acct_name": "Jan Alluv",
        "bank_name": "Alluv Bank LTD",
        "address": "ADO NG",
        "team_name": "QA",
        "jira_employee_id": "QA-21",
        "id_type": "NIN",
        "nok_name": "Don't Know",
        "nok_address": "Sambisa",
        "nok_phone": "234"
    }

    return data