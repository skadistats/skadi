from setuptools import setup, find_packages
from Cython.Build import cythonize


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
        'cython>=0.19.1'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        "Programming Language :: Python :: 2.7",
        "Topic :: Database"
    ],
    ext_modules=cythonize([
        "skadi_ext/decoder/dt.pyx",
        "skadi_ext/decoder/packet_entities.pyx",
        "skadi_ext/decoder/string_table.pyx",
        "skadi_ext/decoder/recv_prop/carray.pyx",
        "skadi_ext/decoder/recv_prop/cfloat.pyx",
        "skadi_ext/decoder/recv_prop/cint.pyx",
        "skadi_ext/decoder/recv_prop/cint64.pyx",
        "skadi_ext/decoder/recv_prop/cstring.pyx",
        "skadi_ext/decoder/recv_prop/cvector.pyx",
        "skadi_ext/decoder/recv_prop/cvectorxy.pyx",
        "skadi_ext/index/embed/dem_packet.pyx",
        "skadi_ext/index/generic.pyx",
        "skadi_ext/index/prologue.pyx",
        "skadi_ext/io/util.pyx",
        "skadi_ext/io/demo.pyx",
        "skadi_ext/io/embed.pyx",
        "skadi_ext/io/stream/generic.pyx",
        "skadi_ext/io/stream/entity.pyx",
        "skadi_ext/state/recv_table.pyx",
        "skadi_ext/state/send_table.pyx",
        "skadi_ext/state/collection/entities.pyx"
    ])
)
