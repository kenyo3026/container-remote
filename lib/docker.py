import os
import re
import hashlib
import logging
import pathlib
import shlex
import shutil
import time
import yaml

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Union

from python_on_whales import docker, Container


def load_yaml(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

class DockerEnv:
    def __init__(
        self,
        image:str,
        logger=None,
        **flags
    ):
        self.logger = logger
        self.flags = flags | {'image':image}
        self.container:Container = None
        self.container_info:dict = {}
        if name := self.flags.get('name'):
            self.container_info['name'] = name
        self.run_container()

    def run_container(self, force_rerun:bool=True):
        if self.container_info:
            existing = docker.ps(all=True, filters=self.container_info)
            if existing:
                if force_rerun:
                    # Remove existing containers and create new one
                    docker.remove(containers=existing, force=True)
                elif len(existing)==1:
                    # Use existing container
                    self.container = existing[0]
                    return
                else:
                    raise RuntimeError(f"Multiple containers found with same filter: {len(existing)}")

        # Remove current container if force_rerun
        if force_rerun and self.container:
            docker.remove(containers=self.container, force=True)

        # Create new container only if needed
        if force_rerun or not self.container:
            self.container = docker.run(**self.flags)

    def remove_container(
            self,
            container_or_info:Union[str, Container, Sequence[Container]]=None
        ):
        target = container_or_info or self.container
        if target:
            try:
                docker.remove(containers=target, force=True)
                # Only reset self.container if we removed it
                if target == self.container:
                    self.container = None
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to remove container: {e}")
                return False
        return True

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

class DockerEnvRemote:

    def __init__(
        self,
        image:str,
        mounts:Union[str, List[str]]=[],
        remote_root:str = None,
        logger:logging.getLogger=None,
        **other_flags,
    ):
        self.image = image
        self.remote_root = remote_root or '/remote_root'
        self.logger = logger

        # setup mount space
        _mount_space_name = image.split(':')[0]
        self.mount_space = MountSpace(name=_mount_space_name, logger=logger)
        self.mount_space.init_staging()
        for mount in mounts:
            self.mount_space.add(mount)

        # setup container
        self.flags = other_flags
        self.flags['image'] = image
        self.flags['volumes'] = self.flags.get('volumes', [])
        self.flags['volumes'].append([self.mount_space.staging_root, self.remote_root])
        self.remote_env = DockerEnv(**self.flags)
        self.remote_container = self.remote_env.container
        self.set_remote_cwd(self.remote_root)

    def set_remote_cwd(self, cwd:str):
        self.remote_cwd = cwd

    def remote(self, cmd:Union[str, Sequence[str]]):
        if isinstance(cmd, str):
            pattern = r"/bin/bash\s*-c\s*[\"'](.*?)['\"]"
            if not re.search(pattern, cmd):
                cmd = f'/bin/bash -c \"{cmd}\"'
            cmd = shlex.split(cmd)
        elif isinstance(cmd, Sequence):
            if len(cmd) > 2 and cmd[0].strip()=='/bin/bash' and cmd[1].strip()=='-c':
                ...
            else:
                cmd = ['/bin/bash', '-c'] + cmd
        return self.remote_container.execute(cmd)

if __name__ == '__main__':
    from utils.logger import enable_default_logger

    logger = enable_default_logger()

    config = load_yaml('../configs/config.yaml')
    docker_config = config.get('docker', {})
    mount_list = config.get('mounts', [])

    self = DockerEnvRemote(**docker_config, mounts=mount_list, logger=logger)

    try:
        while True:
            cmd = input("Enter remote command (type 'exit' to quit): ")
            if cmd.strip().lower() == 'exit':
                print("Exiting remote environment...")
                break
            try:
                output = self.remote(cmd)
                print(output)
            except Exception as e:
                logger.error(f"Failed to execute command: {cmd}, Error: {e}")
    finally:
        self.remote_env.remove_container()
        self.mount_space.remove_staging()
        print("Docker environment and mount space cleaned up.")