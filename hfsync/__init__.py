
import os
from fileio import File
from . import auth
from hfsync.auth import GCSAuth, AZAuth, S3Auth
from smart_open import open_uri as sopen
from smart_open import s3
import logging

_known_files = ['config.json', 'flex_model.msgpack', 'pytorch_model.bin', 'rust_model.ot', 'tf_model.h5', 'tokenizer.json', 'tokenizer_config.json', 'vocab.txt', 'merges.txt', 'spiece.model']
logger = logging.getLogger(__name__)

class FIO:
    def __init__(self, auth_client):
        self.auth_client = auth_client
    
    def read(self, url_or_path):
        return sopen(url_or_path, mode='rb', transport_params=self.auth_client())
    
    def write(self, url_or_path):
        return sopen(url_or_path, mode='wb', transport_params=self.auth_client())
    
    def copy(self, src_file, dest_directory):
        dest_fn = os.path.join(os.path.basename(src_file), dest_directory)
        with self.read(src_file) as r, self.write(dest_fn) as f:
            for chunk in r:
                f.write(chunk)
            f.close()
        return dest_fn
    
    def copy_file(self, src_file, dest_file):
        with self.read(src_file) as r, self.write(dest_file) as f:
            for chunk in r:
                f.write(chunk)
            f.close()
        return dest_fn

    def list_s3(self, s3_dir):
        s3_data = self.parse_s3(s3_dir)
        return [
            os.path.join(s3_dir, key)
            for key, _ in s3.iter_bucket(
                s3_data['bucket'],
                prefix=s3_data['prefix'],
                accept_key=lambda key: os.path.basename(key) in _known_files,
                workers=2,
            )
        ]
    
    def list_gcs(self, gcs_dir):
        if not gcs_dir.endswith('/'):
            gcs_dir += '/*'
        elif not gcs_dir.endswith('*'):
            gcs_dir += '*'
        filenames = File.glob(gcs_dir)
        filenames = [f for f in filenames if os.path.basename(f) in _known_files]
        return filenames
    
    def list_az(self, az_dir):
        return NotImplementedError
    
    @classmethod
    def parse_s3(cls, s3_url):
        if 's3' in s3_url:
            s3_url = s3_url.split('://')[-1].strip()
        sp = s3_url.split('/')
        bucket = sp.pop(0)
        prefix = ('/').join(sp)
        return {'bucket': bucket, 'prefix': prefix}

class Sync:
    def __init__(self, local_path, cloud_path=None, auth_client=None):
        self.local_path = local_path
        self.cloud_path = cloud_path
        self.auth_client = auth_client
        self.get_prefix()
        self.check_auth()
        self.f = FIO(self.auth_client)

    def set_paths(self, local_path=False, cloud_path=False):
        if local_path:
            self.local_path = local_path
        if cloud_path is not False:
            self.cloud_path = cloud_path

    def copy_pretrained(self, source='local', local_path=None, cloud_path=None, overwrite=False):
        assert source in ['local', 'cloud']
        local_path = local_path or self.local_path
        cloud_path = cloud_path or self.cloud_path
        if source == 'local' and cloud_path:
            filenames = File.glob(local_path + '/*')
            copy_path = cloud_path
        elif source == 'cloud' and local_path:
            File.mkdirs(local_path)
            filenames = self.get_filenames(cloud_path)
            copy_path = local_path
        else:
            logger.info(f'No Valid Paths Set. Source = {source}. Local = {local_path}. Cloud = {cloud_path}')
            return
        res = {}
        logger.info(f'Syncing {len(filenames)} Files from {source} to {copy_path}. Overwrite = {overwrite}')
        for fn in filenames:
            if (source == 'cloud' and not File.exists(File.join(File.base(copy_path), fn))) or overwrite:
                dest_fn = self.f.copy(fn, copy_path)
                logger.info(f'Src: {fn} -> Dest: {dest_fn}')
                res[fn] = dest_fn
            else:
                logger.info(f'Passing {fn} as it exists.')
        return res

    def save_pretrained(self, model, tokenizer=None, local_path=None, cloud_path=None):
        local_path = local_path or self.local_path
        cloud_path = cloud_path or self.cloud_path
        model.save_pretrained(local_path)
        if tokenizer:
            tokenizer.save_pretrained(local_path)
        res = {}
        if cloud_path:
            filenames = File.glob(local_path + '/*')
            logger.info(f'Syncing {len(filenames)} Files from Local = {local_path} to Cloud = {cloud_path}')
            for fn in filenames:
                dest_fn = self.f.copy(fn, cloud_path)
                logger.info(f'Src: {fn} -> Dest: {dest_fn}')
                res[fn] = dest_fn
        return res
    
    def copy_file(self, src_path, dest_path):
        return self.f.copy_file(src_path, dest_path)
    
    def copy(self, src_path, dest=None):
        if not dest:
            dest = self.cloud_path if self.is_local(src_path) else self.local_path
        if os.path.isdir(dest):
            return self.f.copy(src_path, dest)
        return self.copy_file(src_path, dest)
    
    def is_local(self, file_path):
        return os.path.exists(file_path)

    def sync_to_local(local_path=None, cloud_path=None, overwrite=False):
        return self.copy_pretrained('cloud', local_path, cloud_path, overwrite)

    def get_prefix(self):
        self.obs = self.cloud_path.split('://')[0]

    def check_auth(self):
        if self.auth_client:
            return
        if self.obs == 'gs':
            self.auth_client = GCSAuth()
        elif self.obs == 's3':
            self.auth_client = S3Auth()
        elif self.obs == 'azure':
            self.auth_client == AZAuth()

    def get_filenames(self, path):
        if self.obs == 'gs':
            return self.f.list_gcs(path)
        elif self.obs == 's3':
            return self.f.list_s3(path)
        elif self.obs == 'azure':
            return self.f.list_az(path)