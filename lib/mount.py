import os
import hashlib
import logging
import pathlib
import shutil
import time

from dataclasses import dataclass, field
from typing import Dict, Union


TMP_ROOT = '/tmp'

@dataclass
class Mounted:
    mounted:Dict[str, str] = field(default_factory={})

    def __init__(self, mounted:Dict[Union[str, pathlib.PosixPath], Union[str, pathlib.PosixPath]]={}):
        self.mounted = {pathlib.Path(source):pathlib.Path(staging) for source, staging in mounted.items()}

    def add(self, key:Union[str, pathlib.PosixPath], value:Union[str, pathlib.PosixPath]):
        if not isinstance(key, pathlib.PosixPath):
            key = pathlib.Path(key)
        if not isinstance(value, pathlib.PosixPath):
            value = pathlib.Path(value)
        self.mounted[key] = value
        self.concentrate()

    def concentrate(self):
        """Remove subdirectories that are covered by parent directories."""
        source_list = sorted(self.mounted.keys(), key=lambda p: p.resolve())

        checked_paths = []
        for i in range(len(source_list)):
            if not checked_paths or not source_list[i].resolve().is_relative_to(checked_paths[-1].resolve()):
                checked_paths.append(source_list[i])

        self.mounted = {path: self.mounted[path] for path in checked_paths}

class MountSpace:

    def __init__(
        self,
        name:str=None,
        uniqle:bool=True,
        logger:logging.Logger=None,
    ):
        self.logger = logger

        if uniqle:
            uniqle_tag = hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:8]
            name = (name or 'tmp') + f'_{uniqle_tag}'
        self.staging_root = os.path.join(TMP_ROOT, name)
        if self.logger:
            self.logger.info(f'Set staging_root: \'{self.staging_root}\'')

        self.mounted = Mounted()

    def __del__(self):
        self.remove_staging()

    def init_staging(self):
        if os.path.exists(self.staging_root):
            if self.logger:
                self.logger.info(f'Conflicting staging directory {self.staging_root} found during initialization -> cleaning up')
            shutil.rmtree(self.staging_root)
        if self.logger:
            self.logger.info(f'Staging directory \'{self.staging_root}\' init -> create')
        os.makedirs(self.staging_root)

    def remove_staging(self):
        if os.path.exists(self.staging_root):
            if self.logger:
                self.logger.info(f'Staging directory \'{self.staging_root}\' found -> remove')
            shutil.rmtree(self.staging_root)
        else:
            if self.logger:
                self.logger.info(f'Staging directory \'{self.staging_root}\' not found -> skip')

    def add(self, source:str):
        source = pathlib.Path(source)
        source_abspath = source.resolve().__str__()

        staging = os.path.join(self.staging_root, source.name)
        staging = pathlib.Path(staging)
        staging_abspath = staging.resolve().__str__()
        shutil.copytree(source_abspath, staging_abspath)

        self.mounted.add(source_abspath, staging_abspath)
        if self.logger:
            self.logger.info(f'Add source \'{source}\' to staging \'{staging}\'')

    def lock(self):
        # TODO
        ...

    def unlock(self):
        # TODO
        ...