import time

import boto3
import botocore

client = boto3.client('secretsmanager')

class CacheEntry:

    __slots__ = ('value', 'ctime')

    def __init__(self, value):
        self.value = value
        self.ctime = time.monotonic()

    def needs_refresh(self, ttl):
        now = time.monotonic()
        return (now - self.ctime) > ttl


class Secrets:

    def __init__(self, client, kms_key_id='alias/aws/secretsmanager', ttl=300):
        self.client = client
        self.kms_key_id = kms_key_id
        self.cache = dict()
        self.ttl = ttl

    def __setitem__(self,key,val):
        secret_type = 'SecretBinary' if type(b'') == bytes else 'SecretString'
        try:
            client.put_secret_value(**{'SecretId':key, secret_type:val})
        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                self.client.create_secret(**{'Name':key, secret_type:val, 'KmsKeyId':self.kms_key_id})
            else:
                raise err
        self.cache[key] = CacheEntry(value=val)

    def fetch_secret(self, key):
        found = self.client.get_secret_value(SecretId=key)
        value = found['SecretString'] or found['SecretBinary']
        return CacheEntry(value=value)

    def __getitem__(self, key):
        try:
            found = self.cache[key]
            if found.needs_refresh(self.ttl):
                self.cache[key] = self.fetch_secret(key)
            return found.value
        except KeyError:
            found = self.fetch_secret(key)
            self.cache[key] = found
            return found.value
