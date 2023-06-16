### Use AWS Secrets Manager as dict.

This package provides convenient way of using secrets manager as a dict. You can
configure underlying cache time with `ttl` parameter. If you want to use non
default kms key id pass it with `kms_key_id` parameter.

```python
sec = Secrets(client=boto3.client('secretsmanager'))
# Set secret
sec['name'] = value
# Get secret
value = sec['name']
```
