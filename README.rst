Base Skeleton to start your application using Flask-AppBuilder
--------------------------------------------------------------

- Install it::

	pip install flask-appbuilder
	git clone https://github.com/dpgaspar/Flask-AppBuilder-Skeleton.git

- Run it::

    $ export FLASK_APP=app
    # Create an admin user
    $ flask fab create-admin
    # Run dev server
    $ flask run


- Registration
    pip install flask-mail
    
    start smtp server: 
        python -m smtpd -n -c DebuggingServer localhost:2525

    register user
    click on activation link in smtp server terminal