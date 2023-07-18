import pytest
import moto
import boto3
import os
from unittest.mock import Mock

import aws_secrets_cache


@pytest.fixture()
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture()
def smclient(aws_credentials):
    with moto.mock_secretsmanager():
        client = boto3.client("secretsmanager")
        yield client


@pytest.mark.parametrize('value', ('string', b'byte_string'))
def test_set_then_get(value):
    smclient = Mock()
    secrets = aws_secrets_cache.Secrets(client=smclient)
    secrets['name'] = value
    assert value == secrets['name']
    # Assert that getting doesn't call boto.
    assert smclient.get_secret_value.call_count == 0


@pytest.mark.parametrize('kind,value', (
    ('SecretBinary', b'value'),
    ('SecretString', 'value'),
))
def test_set_string(smclient, kind, value):
    cache = aws_secrets_cache.Secrets(client=smclient)
    cache['name'] = value
    response = smclient.get_secret_value(SecretId='name')
    assert value == response[kind]


@pytest.mark.parametrize('kind,value', (
    ('SecretBinary', b'value'),
    ('SecretString', 'value'),
))
def test_get_string(smclient, kind, value):
    smclient.create_secret(**{'Name': 'name', kind: value})
    cache = aws_secrets_cache.Secrets(client=smclient)
    assert cache['name'] == value


def test_set_string_prefixed(smclient):
    cache = aws_secrets_cache.Secrets(client=smclient, prefix='/prefix/')
    cache['name'] = 'value'
    response = smclient.get_secret_value(SecretId='/prefix/name')
    assert 'value' == response['SecretString']
