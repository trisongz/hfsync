import os
import boto3
import botocore
import botocore.client
from google.cloud.storage import Client
from google.auth.credentials import Credentials
from azure.storage.blob import BlobServiceClient

cloud_envs = {
    'GCS': {
        'token': 'GOOGLE_API_TOKEN',
        'service_account': 'GOOGLE_APPLICATION_CREDENTIALS'
    },
    'AZ': {
        'client': 'AZURE_STORAGE_CONNECTION_STRING'
    },
    'S3': {
        'aws_access_key_id': 'AWS_ACCESS_KEY_ID',
        'aws_secret_access_key': 'AWS_SECRET_ACCESS_KEY',
        'aws_session_token': 'AWS_SESSION_TOKEN',
    }
}


class S3Auth:
    def __init__(self, access_key=None, secret_key=None, session_token=None, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.auth_params = cloud_envs['S3'].copy()
        if access_key and secret_key:
            self.auth_params.update({'aws_access_key_id': access_key, 'aws_secret_access_key': secret_key, {'aws_session_token': session_token}})
            self.set_env()
        else:
            self.check_env()
        self.create_auth()
    
    def create_auth(self):
        if self.auth_params['aws_access_key_id'] and self.auth_params['aws_secret_access_key']:
            self.sess = boto3.Session(**self.auth_params)
        else:
            self.kwargs['config'] = botocore.client.Config(signature_version=botocore.UNSIGNED)
            self.sess = boto3.Session()
        self.client = self.sess.client('s3', endpoint_url=self.kwargs.get('endpoint_url', None), config=self.kwargs.get('config', None))

    def check_env(self):
        for key, env in self.auth_params.items():
            self.auth_params[key] = os.environ.get(env, None)
        
    def set_env(self):
        for key, val in self.auth_params.items():
            os.environ[key] = val
    
    def __call__(self):
        return dict(client=self.client)
            


class GCSAuth:
    def __init__(self, service_account=None, token=None, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.auth_params = cloud_envs['GCS'].copy()
        if not service_account or token:
            self.check_env()
        else:
            self.auth_params.update({'service_account': service_account, 'token': token})
            self.set_env()
        self.create_auth()
    
    def create_auth(self):
        if self.auth_params['service_account']:
            self.client = Client.from_service_account_json(self.auth_params['service_account'])
        elif self.auth_params['token']:
            self.sess = Credentials(token=self.auth_params['token'])
            self.client = Client(credentials=self.sess)
        else:
            self.client = None

    def check_env(self):
        for key, env in self.auth_params.items():
            self.auth_params[key] = os.environ.get(env, None)
        
    def set_env(self):
        for key, val in self.auth_params.items():
            os.environ[key] = val
    
    def __call__(self):
        return dict(client=self.client)


class AZAuth:
    def __init__(self, connection_string=None, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.auth_params = cloud_envs['AZ'].copy()
        if not connection_string:
            self.check_env()
        else:
            self.auth_params.update({'connection_string': connection_string})
            self.set_env()
        self.create_auth()
    
    def create_auth(self):
        if self.auth_params['connection_string']:
            self.client = BlobServiceClient.from_connection_string(self.auth_params['connection_string'])
        else:
            self.client = None

    def check_env(self):
        for key, env in self.auth_params.items():
            self.auth_params[key] = os.environ.get(env, None)
        
    def set_env(self):
        for key, val in self.auth_params.items():
            os.environ[key] = val
    
    def __call__(self):
        return dict(client=self.client)
