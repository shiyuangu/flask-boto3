# sgu: pip 21.3.1 has issues of importing pip during `pip install -e .`
# Cf: https://github.com/pypa/pip/issues/10573
# https://stackoverflow.com/a/49837302
# try: # for pip >= 10
#     from pip._internal.req import parse_requirements
# except ImportError: # for pip <= 9.0.3
#     from pip.req import parse_requirements


from setuptools import setup

# Requirements
#install_reqs = parse_requirements('requirements.txt', session='dummy')
#reqs = [str(ir.req) for ir in install_reqs]

# sgu: use local version identifier: https://peps.python.org/pep-0440/#version-specifiers
version = '0.3.2+sgu.1' 

setup(
    name='Flask-Boto3',
    version=version,
    url='https://github.com/Ketouem/flask-boto3',
    license='MIT',
    author='Cyril "Ketouem" Thomas',
    author_email='ketouem@gmail.com',
    description='Flask extension that ties boto3 to the application',
    packages=['flask_boto3'],
    zip_safe=False,
    include_package_data=True,
    test_suite='tests',
    #install_requires=reqs,
    platforms='any',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
