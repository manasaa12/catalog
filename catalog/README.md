# TelevisionsCart
### By Manasa Morla
This is one of the project for the Udacity [FSND Course](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).

### Project Overview
This applications shows different categories with respective categorical items,here any user can view the item details but only authenticated people can add, update, delete the items. 


### Why This Project?
Modern web applications perform a variety of functions and provide amazing features and utilities to their users; but deep down, it’s really all just creating, reading, updating and deleting data. In this project, you’ll combine your knowledge of building dynamic websites with persistent data storage to create a web application that provides a compelling service to your users.

### What Will I Learn?
  * Develop a RESTful web application using the Python framework Flask.
  * Implementing Login mechanisam using third-party OAuth authentication.
  * Implementing CRUD (create, read, update and delete) operations on favourite database.

## Skills Required
1. Python
2. HTML
3. CSS
4. OAuth
5. Flask Framework
6. flask_sqlalchemy

#### Requirements
  * [Python](https://www.python.org/downloads)
  * [Vagrant](https://www.vagrantup.com/)
  * [VirtualBox](https://www.virtualbox.org/)
  * [Git](https://git-scm.com/downloads) - for windows
  
#### Project Setup:
  1. Install Vagrant 
  2. Install VirtualBox
  3. Download or Clone [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) repository.
  4. Unzip the above vagrant zip folder and open it
  5. Move the TelevisionsCart folder into above vagrant folder
  
#### Running Project
  1. open git bash from vagrant folder
  2. Launch the Vagrant by using the command:
  `
    $ vagrant up
  `
  3. Log into Vagrant by using the command:
  `
    $ vagrant ssh
  `
  4. Move to server side vagrant folder by using the commmand:
  `
    $ cd /vagrant
  `
  5. Move to Project folder i.e, TelevisionsCart by using the command:
  `
    $ cd TelevisionsCart
  `
  6. Run the project by using the command:
  `
    $ python finalproject.py
  `
  7. open our application by visiting from your favourite browser[http://localhost:5000](http://localhost:5000).
  ### JSON end points
  in this application we created json end points for multi purpose using REST architecture 
#### urls:
`
http://localhost:5000/items/JSON
`
`
http://localhost:5000/categories/JSON
`
`
http://localhost:5000/category/1/items/JSON
`
  