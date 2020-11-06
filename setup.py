"""
Flask-CognitoLogin
-------------

Flask-Login and Cognito integration make easy.
"""
from setuptools import setup


# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='Flask-CognitoLogin',
    version='0.0.1',
    url='http://github.com/ybenitezf/flask-cognitologin/',
    license='GPL-3.0-or-later',
    author='Yoel Benítez Fonseca',
    author_email='ybenitezf@gmail.com',
    description='Flask-Login and Cognito integration make easy',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['flask_cognitologin'],
    zip_safe=False,
    include_package_data=True,
    python_requires=">= 3.6",
    platforms='any',
    install_requires=[
        'Flask', 'python-jose', 'requests'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
