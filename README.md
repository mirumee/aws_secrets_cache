```python
sec = Secrets(client=boto3.client('secretsmanager'))
# Set secret
sec['name'] = value
# Get secret
value = sec['name']
```
