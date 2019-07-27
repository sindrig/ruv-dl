import os

from setuptools import setup

VERSION = '0.1.0'

ROOT = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(ROOT, 'README.md')) as f:
    readme = f.read()


setup(
    name='ruv-dl',
    version=VERSION,
    description='Command line interface for RUV (http://www.ruv.is)',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/hjalti/ruv-cli',
    author='Sindri Guðmundsson',
    author_email='sindrigudmundsson@gmail.com',
    license='GPLv3',
    packages=['ruv_dl'],
    python_requires='>=3.6.0',
    install_requires=[
        'requests==2.22.0',
    ],
    entry_points={
        'console_scripts': [
            'ruv-dl=ruv_dl:main',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v3 (LGPLv3)',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
