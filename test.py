#!/usr/bin/env python

if __name__ == '__main__':
    from container_remote.docker import DockerEnvRemote, load_yaml
    from container_remote.utils.logger import enable_default_logger

    logger = enable_default_logger()

    config = load_yaml('./configs/config.yaml')
    docker_config = config.get('docker', {})
    mount_list = config.get('mounts', [])

    env = DockerEnvRemote(**docker_config, mounts=mount_list, logger=logger)

    try:
        while True:
            cmd = input("Enter remote command (type 'exit' to quit): ")
            if cmd.strip().lower() == 'exit':
                print("Exiting remote environment...")
                break
            try:
                output = env.remote(cmd)
                print(output)
            except Exception as e:
                logger.error(f"Failed to execute command: {cmd}, Error: {e}")
    finally:
        env.remote_env.remove_container()
        env.mount_space.remove_staging()
        print("Docker environment and mount space cleaned up.")
