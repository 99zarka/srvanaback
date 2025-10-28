pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "srvanaback-app"
        DOCKER_REGISTRY = "your-docker-registry.com" // Replace with your Docker registry
        DOCKER_CREDENTIALS_ID = "docker-hub-credentials" // Replace with your Docker credentials ID in Jenkins
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE}:${env.BUILD_NUMBER} ."
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    // Run tests inside a temporary container
                    sh "docker run --rm ${DOCKER_IMAGE}:${env.BUILD_NUMBER} python manage.py test"
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                        sh "docker tag ${DOCKER_IMAGE}:${env.BUILD_NUMBER} ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
                        sh "docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD} ${DOCKER_REGISTRY}"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Deployment logic goes here. For example, using Kubernetes, SSH, etc."
                echo "Image to deploy: ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
                // Example: sh "kubectl apply -f kubernetes-deployment.yaml"
            }
        }
    }

    post {
        always {
            echo "Pipeline finished."
        }
        success {
            echo "Pipeline succeeded!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
