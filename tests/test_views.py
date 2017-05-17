# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import pytest
from rest_framework.test import APIClient
from rest_friendship.serializers import get_user_serializer, UserSerializer
from friendship.models import Friend, FriendshipRequest
from tests.serializers import TestUserSerializer

from .factories import UserFactory


def test_settings_user_serializer():
    assert get_user_serializer() == UserSerializer


def test_settings_user_serializer_with_specific_settings(settings):
    settings.REST_FRIENDSHIP = {
        'USER_SERIALIZER': 'tests.serializers.TestUserSerializer'
    }
    assert get_user_serializer() == TestUserSerializer


@pytest.mark.django_db(transaction=True)
def test_list_friends():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()

    Friend.objects.add_friend(
        user2,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    Friend.objects.add_friend(
        user3,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    for friend_request in FriendshipRequest.objects.filter(to_user=user1):
        friend_request.accept()

    client = APIClient()
    client.force_authenticate(user=user1)
    response = client.get('/friends/')
    assert response.status_code == 200
    assert len(response.data) == 2


@pytest.mark.django_db(transaction=True)
def test_create_friend_request():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()

    client = APIClient()
    client.force_authenticate(user=user1)
    data = {'user_id': user2.id, 'message': 'Hi there!'}
    response = client.post('/friends/', data=data)
    assert response.status_code == 201
    assert response.data['from_user'] == user1.id
    assert response.data['to_user'] == user2.id
    assert response.data['message'] == 'Hi there!'
    assert FriendshipRequest.objects.filter(pk=response.data['id']).count() == 1


@pytest.mark.django_db(transaction=True)
def test_list_friend_requests():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()

    Friend.objects.add_friend(
        user2,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    Friend.objects.add_friend(
        user3,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    client = APIClient()
    client.force_authenticate(user=user1)
    response = client.get('/friends/requests/')
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['to_user'] == user1.id


@pytest.mark.django_db(transaction=True)
def test_list_sent_friend_requests():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()

    Friend.objects.add_friend(
        user2,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    Friend.objects.add_friend(
        user3,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    client = APIClient()
    client.force_authenticate(user=user2)
    response = client.get('/friends/sent_requests/')
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['to_user'] == user1.id


@pytest.mark.django_db(transaction=True)
def test_list_rejected_friend_requests():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()

    Friend.objects.add_friend(
        user2,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    Friend.objects.add_friend(
        user3,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    for friend_request in FriendshipRequest.objects.filter(to_user=user1):
        friend_request.reject()

    client = APIClient()
    client.force_authenticate(user=user1)
    response = client.get('/friends/rejected_requests/')
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['to_user'] == user1.id


@pytest.mark.django_db(transaction=True)
def test_accept_friend_request():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()

    Friend.objects.add_friend(
        user2,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    fr = FriendshipRequest.objects.filter(to_user=user1).first()

    client = APIClient()
    client.force_authenticate(user=user1)
    response = client.post('/friendrequests/{}/accept/'.format(fr.id))
    assert response.status_code == 201
    assert Friend.objects.are_friends(user1, user2)


@pytest.mark.django_db(transaction=True)
def test_reject_friend_request():

    # Create users
    user1 = UserFactory()
    user2 = UserFactory()

    Friend.objects.add_friend(
        user2,                               # The sender
        user1,                               # The recipient
        message='Hi! I would like to add you'
    )

    fr = FriendshipRequest.objects.filter(to_user=user1).first()

    client = APIClient()
    client.force_authenticate(user=user1)
    response = client.post('/friendrequests/{}/reject/'.format(fr.id))
    assert response.status_code == 201
    assert not Friend.objects.are_friends(user1, user2)
