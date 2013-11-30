from setuptools import setup, find_packages


setup(
    name='skadi',
    version='1.0',
    description='Fast, full Dota 2 game replay parser.',
    long_description=open('README.md').read(),
    author='Joshua Morris',
    author_email='onethirtyfive@skadistats.com',
    zip_safe=True,
    url='https://github.com/skadistats/skadi',
    license='MIT',
    packages=find_packages(),
    keywords='dota replay parser',
    install_requires=[
      'protobuf==2.5',
      'python-snappy==0.5',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        "Programming Language :: Python :: 2.7",
        "Topic :: Database"
    ]
)