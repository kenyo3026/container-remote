import re
import logging
import shlex
import yaml
from typing import List, Sequence, Union

from python_on_whales import docker, Container

from .mount import MountSpace


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

# 如需直接執行，請使用專案根目錄的 run_docker.py