# hfsync
 Sync Huggingface Transformer Models to Cloud Storage (GCS/S3 + more soon)



## Quickstart

```python
!pip install --upgrade git+https://github.com/trisongz/hfsync.git
!pip install --upgrade hfsync

```

## Usage
```python
from hfsync import GCSAuth, S3Auth # AZAuth (not yet supported)
from hfsync import Sync

# Note: Only use one auth client.

# To have Auth picked up from env vars / implicitly
auth_client = GCSAuth()
auth_client = S3Auth()

# To set Auth directly / explicitly
auth_client = GCSAuth(service_account='service_account', token='gcs_token')
auth_client = S3Auth(access_key='access_key', secret_key='secret_key', session_token='token')

# Local and Cloud Paths
local_path = '/content/model'
cloud_path = 'gs://bucket/model/experiment' # or 's3://bucket/model/experiment'
sync_client = Sync(local_path=local_path, cloud_path=cloud_path, auth_client=auth_client)

# Or Implicitly without an auth_client to have it figure things out based on your cloud path
sync_client = Sync(local_path=local_path, cloud_path=cloud_path)

# After training loop, sync your pretrained model to both local and cloud. 
# You don't need to explicitly call model.save_pretrained(path) as this function will do that automatically
results = sync_client.save_pretrained(model, tokenizer)
# results = {
# '/content/model/pytorch_model.bin': 'gs://bucket/model/experiment/pytorch_model.bin'
# ...
# }

# Pull Down from your bucket to local
results = sync_client.sync_to_local(overwrite=False)
# results = {
# 'gs://bucket/model/experiment/pytorch_model.bin': '/content/model/pytorch_model.bin'
# ...
# }

# Or set explicit paths if you are changing paths, for example, different dirs for each checkpoint
new_local = '/content/model2'
results = sync_client.sync_to_local(local_path=new_local, cloud_path=cloud_path, overwrite=False)
# results = {
# 'gs://bucket/model/experiment/pytorch_model.bin': '/content/model2/pytorch_model.bin'
# ...
# }

# Or set paths to use
new_cloud = 'gs://bucket/model/experiment2'
sync_client.set_paths(local_path=new_local, cloud_path=new_cloud)
results = sync_client.save_pretrained(model, tokenizer)
# results = {
# '/content/model2/pytorch_model.bin': 'gs://bucket/model/experiment2/pytorch_model.bin'
# ...
# }


# You can also use the underlying filesystem to copy a file directly

# Implicitly & Explicitly
filename = '/content/model2/pytorch_model.bin'
sync_client.copy(filename) # Copies to the set cloud_path variable -> 'gs://bucket/model/experiment2/pytorch_model.bin'
sync_client.copy(filename, dest='gs://bucket/model/experiment3') # Copies to dest variable -> 'gs://bucket/model/experiment3/pytorch_model.bin'
sync_client.copy(filename, dest='gs://bucket/model/experiment3/model.bin') # Copies to dest variable -> 'gs://bucket/model/experiment3/model.bin'

filename = 'gs://bucket/model/experiment2/pytorch_model.bin'
sync_client.copy(filename) # Copies to the set local_path variable -> '/content/model2/pytorch_model.bin'
sync_client.copy(filename, dest='/content/model3') # Copies to dest variable -> '/content/model3/pytorch_model.bin'
sync_client.copy(filename, dest='/content/model3/model.bin') # Copies to dest variable -> '/content/model3/model.bin'

# Copy Explicitly
src_file = '/content/mydataset.pb'
dest_file = 's3://bucket/data/dataset.pb'
sync_client.copy(src_file, dest_file)

```
### Environment Variables Used

Google Cloud Storage
- `GOOGLE_API_TOKEN`
- `GOOGLE_APPLICATION_CREDENTIALS`

AWS S3
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`


### Limitations

While the library tries to respect and check prior to overwriting where `overwrite=false` is available, it's not currently supported agnostically across all cloud.
Support for other Cloud FS is WIP.

### Credits

- [file-io](https://github.com/trisongz/file_io)
- [smart-open](https://github.com/RaRe-Technologies/smart_open)