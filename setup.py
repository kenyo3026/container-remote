from setuptools import setup


LIBRARY_NAME = "container_remote"
PACKAGE_DIR = 'lib'

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name=LIBRARY_NAME,
    version="0.1.0",
    packages=[LIBRARY_NAME],
    package_dir={LIBRARY_NAME: PACKAGE_DIR},
    install_requires=install_requires,
    author="kenyo3026",
    author_email="kenyo3026@gmail.com",
    description="🤖 container-remote – 🐳 Docker container bridge for AI agents to remotely execute tasks and solve problems in isolated environments, providing secure task encapsulation and remote execution capabilities",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kenyo3026/container-remote",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.10",
    keywords="docker, container, ai-agent, remote-execution, isolation, mounting, python-on-whales, containerization, devops, automation",
    project_urls={
        "Bug Reports": "https://github.com/kenyo3026/container-remote/issues",
        "Source": "https://github.com/kenyo3026/container-remote",
    },
)