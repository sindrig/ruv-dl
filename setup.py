import os

from setuptools import setup, find_packages

VERSION = '0.5.1'

ROOT = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(ROOT, 'README.md')) as f:
    readme = f.read()


setup(
    name='ruv-dl',
    version=VERSION,
    description='Downloader/organizer for ruv programs',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/sindrig/ruv-dl',
    author='Sindri Guðmundsson',
    author_email='sindrigudmundsson@gmail.com',
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.6.0',
    install_requires=[
        'requests==2.22.0',
        'click==7.0',
    ],
    entry_points={
        'console_scripts': [
            'ruv-dl=ruv_dl:main',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
