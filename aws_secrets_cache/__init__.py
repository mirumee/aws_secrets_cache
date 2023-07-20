import time

import botocore


class CacheEntry:

    __slots__ = ('value', 'ctime')

    def __init__(self, value):
        self.value = value
        self.ctime = time.monotonic()

    def needs_refresh(self, ttl):
        now = time.monotonic()
        return (now - self.ctime) > ttl


class Secrets:

    __slots__ = ('client', 'kms_key_id', 'cache', 'ttl', 'prefix')

    def __init__(
        self,
        client,
        kms_key_id='alias/aws/secretsmanager',
        ttl=300,
        prefix="",
    ):
        self.client = client
        self.kms_key_id = kms_key_id
        self.cache = dict()
        self.ttl = ttl
        self.prefix = prefix

    def __setitem__(self, key, val):
        key = self.prefix + key
        secret_type = 'SecretBinary' if type(val) == bytes else 'SecretString'
        try:
            self.client.put_secret_value(**{'SecretId': key, secret_type: val})
        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                self.client.create_secret(**{
                    'Name': key,
                    secret_type: val,
                    'KmsKeyId': self.kms_key_id
                })
            else:
                raise err
        self.cache[key] = CacheEntry(value=val)

    def fetch_secret(self, key):
        key = key
        found = self.client.get_secret_value(SecretId=key)
        value = found.get('SecretString') or found['SecretBinary']
        return CacheEntry(value=value)

    def __getitem__(self, key):
        key = self.prefix + key
        try:
            found = self.cache[key]
            if found.needs_refresh(self.ttl):
                self.cache[key] = self.fetch_secret(key)
            return found.value
        except KeyError:
            found = self.fetch_secret(key)
            self.cache[key] = found
            return found.value
