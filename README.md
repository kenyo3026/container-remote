# Container-Remote 🤖

🤖 **Container-Remote** – AI agent execution bridge that encapsulates tasks in Docker containers, enabling local AI agents to remotely execute and solve problems in isolated container environments

A powerful Python utility that creates secure Docker container bridges for AI agents, providing isolated execution environments with automatic file mounting and remote command execution capabilities. Perfect for AI agent ecosystems that need secure, reproducible task execution in containerized environments.

> **Note**: This project provides a secure bridge between local AI agents and remote Docker containers, enabling complex task execution while maintaining isolation and reproducibility.

## ✨ Key Features

- **🤖 AI Agent Bridge**: Seamlessly connect local AI agents to remote Docker containers
- **🐳 Docker Integration**: Full Docker container lifecycle management with python-on-whales
- **📁 Smart Mounting**: Automatic file mounting with intelligent path concentration and staging
- **🔒 Secure Isolation**: Isolated execution environments for each task
- **⚡ Remote Execution**: Execute commands remotely in containers with full shell access
- **🧹 Auto Cleanup**: Automatic cleanup of containers and staging directories
- **📊 Logging Support**: Comprehensive logging for debugging and monitoring
- **🔧 Configurable**: YAML-based configuration for easy setup and customization

## 🚀 Quick Start

### Installation

#### From Source
```bash
# Clone the repository
git clone https://github.com/kenyo3026/container-remote.git
cd container-remote

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

#### Install directly from GitHub
```bash
# Install the latest version
pip install git+https://github.com/kenyo3026/container-remote.git

# Or install a specific branch/tag
pip install git+https://github.com/kenyo3026/container-remote.git@main
```

**Dependencies:**
- Python 3.8+
- python-on-whales
- PyYAML
- pathlib (built-in)
- logging (built-in)

### Basic Usage

#### **1. Simple Container Environment**
```python
from lib.docker import DockerEnvRemote
from lib.utils.logger import enable_default_logger

# Setup logger
logger = enable_default_logger()

# Create remote environment
remote_env = DockerEnvRemote(
    image="python:3.9-slim",
    mounts=["/path/to/local/files"],
    logger=logger
)

# Execute remote commands
result = remote_env.remote("python --version")
print(result)

# Cleanup
remote_env.remote_env.remove_container()
remote_env.mount_space.remove_staging()
```

#### **2. AI Agent Task Execution** 🧠
```python
# Perfect for AI agents that need to execute tasks in isolated environments
# Each task gets its own container with mounted files

class AIAgentExecutor:
    def __init__(self, base_image="python:3.9-slim"):
        self.base_image = base_image
        self.logger = enable_default_logger()
    
    def execute_task(self, task_files, task_command):
        """Execute AI agent task in isolated container"""
        try:
            # Create isolated environment for this task
            remote_env = DockerEnvRemote(
                image=self.base_image,
                mounts=task_files,
                logger=self.logger
            )
            
            # Execute the task
            result = remote_env.remote(task_command)
            
            return {
                'success': True,
                'result': result,
                'container_id': remote_env.remote_container.id
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            # Always cleanup
            if 'remote_env' in locals():
                remote_env.remote_env.remove_container()
                remote_env.mount_space.remove_staging()

# Example usage for AI agent
agent = AIAgentExecutor()

# Execute a Python analysis task
task_result = agent.execute_task(
    task_files=["/path/to/data", "/path/to/scripts"],
    task_command="python analyze_data.py --input data.csv --output results.json"
)

print(f"Task completed: {task_result['success']}")
```

#### **3. Configuration-Based Setup**
```python
import yaml
from lib.docker import DockerEnvRemote

# Load configuration
with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create environment from config
docker_config = config.get('docker', {})
mount_list = config.get('mounts', [])

remote_env = DockerEnvRemote(
    mounts=mount_list,
    logger=enable_default_logger(),
    **docker_config
)

# Interactive remote shell
try:
    while True:
        cmd = input("Remote command (type 'exit' to quit): ")
        if cmd.strip().lower() == 'exit':
            break
        
        output = remote_env.remote(cmd)
        print(output)
        
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    remote_env.remote_env.remove_container()
    remote_env.mount_space.remove_staging()
```

## 📖 Configuration

The system supports YAML-based configuration for easy setup:

```yaml
# configs/config.yaml
mounts:
  - /Users/username/project/src
  - /Users/username/project/data

docker:
  image: python:3.9-slim
  command: ['sleep', '300']
  name: ai-agent-container
  detach: true
  interactive: true
  tty: true
  workdir: /remote_root
  volumes: []
  environment:
    - PYTHONPATH=/remote_root
```

## 🧪 Testing

```bash
# Run the example directly
python lib/docker.py

# This will start an interactive remote environment
# based on your config.yaml file
```

## 📚 API Reference

### DockerEnvRemote Class

```python
class DockerEnvRemote:
    def __init__(
        self,
        image: str,
        mounts: Union[str, List[str]] = [],
        remote_root: str = None,
        logger: logging.getLogger = None,
        **other_flags
    )
```

**Parameters:**
- `image`: Docker image to use for the container
- `mounts`: List of local paths to mount into the container
- `remote_root`: Remote directory where files are mounted (default: '/remote_root')
- `logger`: Logger instance for debugging and monitoring
- `**other_flags`: Additional Docker run flags

**Key Methods:**
- `remote(cmd)`: Execute command in remote container
- `set_remote_cwd(cwd)`: Set working directory in remote container

### DockerEnv Class

```python
class DockerEnv:
    def __init__(self, image: str, logger=None, **flags)
    def run_container(self, force_rerun: bool = True)
    def remove_container(self, container_or_info=None)
```

**Features:**
- Automatic container lifecycle management
- Force rerun capabilities
- Safe container cleanup

### MountSpace Class

```python
class MountSpace:
    def __init__(self, name: str = None, unique: bool = True, logger=None)
    def init_staging(self)
    def add(self, source: str)
    def remove_staging(self)
```

**Features:**
- Automatic staging directory management
- Unique naming for concurrent operations
- Safe file mounting and cleanup

### Mounted Class

```python
class Mounted:
    def __init__(self, mounted: Dict = {})
    def add(self, key, value)
    def concentrate(self)
```

**Features:**
- Path concentration for cleaner mounting
- Automatic subdirectory optimization

## 🔧 Advanced Features

### Smart File Mounting
The system automatically handles file mounting with intelligent staging:

```python
# Multiple source directories
mounts = [
    "/path/to/source/code",
    "/path/to/data/files",
    "/path/to/config"
]

# System automatically:
# 1. Creates unique staging directories
# 2. Copies files to staging
# 3. Mounts staging to container
# 4. Cleans up after execution
```

### Container Lifecycle Management
```python
# Automatic container management
remote_env = DockerEnvRemote(image="python:3.9-slim")

# Container is automatically created and managed
# No need to manually start/stop containers

# Cleanup is automatic when using context managers
# or explicit cleanup calls
```

### Logging and Monitoring
```python
# Comprehensive logging support
logger = enable_default_logger()

# All operations are logged:
# - Container creation/destruction
# - File mounting operations
# - Command execution
# - Error handling
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with python-on-whales for robust Docker integration
- Designed for AI agent ecosystems and secure task execution
- Thanks to the Docker and Python communities for excellent tooling

---

Made with ❤️ for the AI agent community
