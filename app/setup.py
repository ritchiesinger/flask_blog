from setuptools import setup

setup(
    name='app',
    packages=[],
    include_package_data=True,
    install_requires=[
        'Flask==2.0.3',
        'passlib==1.7.4',
        'python-dotenv==0.20.0',
        'PyJWT==2.3.0',
        'Flask-Cors==3.0.10',
        'Flask-HTTPAuth==4.5.0',
        'Flask-Migrate==3.1.0',
        'Flask-SQLAlchemy==2.5.1'
    ],
)