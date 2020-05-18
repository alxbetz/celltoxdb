from setuptools import setup

setup(
    name='Celltox database',
    version='0.7',
    long_description=__doc__,
    packages=['celltox_db'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask',
    'Flask-SQLAlchemy',
    'Flask-WTF',
    'WTForms',
    'SQLAlchemy',
    'dash',
    'pandas',
    'numpy',
    'Flask-Migrate',
    'Flask-SQLAlchemy']
)