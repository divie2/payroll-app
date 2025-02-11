
from django.urls import path
from . import views



urlpatterns = [

    path("register", views.register, name='registration'),
    path("login/token", views.CustomTokenObtainPairView.as_view(), name="token_access"),
    path("logout", views.logout, name = "logout"),

    # password reset and confirmation
    path("reset/<uidb64>/<token>", views.password_reset_link_confirmation, name="password_reset_confirm"),
    path("confirm_password", views.password_confirmation, name= 'password_confirmation'),

    path("forget_password", views.click_to_reset_password, name="forget_password"),



    # group creation and role assignment to groups
    path("groups/create", views.create_group, name = "create-group"),
    path('add-user-to-group/', views.add_user_to_group, name='add-user-to-group'),
]

