pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo 'Cloning repository...'
                    bat 'git clone https://github.com/99zarka/srvanaback .' // Clone into the current directory
                    echo 'Repository cloned.'
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    echo 'Ensuring virtual environment exists and installing dependencies...'
                    bat 'python -m venv venv'
                    bat 'call venv\\Scripts\\activate'
                    bat 'pip install -r requirements.txt'
                    echo 'Build stage complete.'
                }
            }
        }
        stage('Test') {
            steps {
                script {
                    echo 'Activating virtual environment and running tests...'
                    bat 'call venv\\Scripts\\activate'
                    bat 'python manage.py test api.tests.test_models --verbosity 2 --noinput --keepdb'
                    bat 'python manage.py test api.test_api_crud --verbosity 2 --noinput --keepdb'
                    echo 'Test stage complete.'
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    echo 'Deployment stage - activating venv and running server.'
                    bat 'call venv\\Scripts\\activate'
                    bat 'python manage.py runserver'
                    echo 'Deployment stage complete.'
                }
            }
        }
    }
}
