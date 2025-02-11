import pytest
from django.urls import reverse
from .models import Account
from employee.models import Employee, Team, NextOfKin

# Create your tests here.

def test_registration_url_resolves():
    registration_url = reverse("registration")
    assert registration_url == "/account/register"


def test_regsitration_endpoint_allow_only_post_requests(client):
    registration_url = reverse("registration")
    response = client.get(registration_url)
    assert response.status_code == 405
    assert response.json() == {'detail': 'Method "GET" not allowed.'}

@pytest.mark.django_db
def test_registration_view_response(client, sample_reg_data):
    registration_url = reverse("registration")
    response = client.post(registration_url, data=sample_reg_data)
    assert response.json() == {"success": "Employee added successfully"}
    assert response.status_code == 201

    # count number of employee
    new_account = Account.objects.filter(email = sample_reg_data['email'])
    assert new_account.count() == 1
    assert Employee.objects.filter(account = new_account.first()).count() == 1
    assert Team.objects.count() == 1
    assert NextOfKin.objects.count() == 1



# @pytest.mark.django_db



# def test_user_count_after_registration(client, db):
#     registration_url = reverse("registration")
#     response = client.get(registration_url)