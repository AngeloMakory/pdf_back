pipeline {
    agent any

    triggers {
        pollSCM 'H/5 * * * *'
    }

    environment {
        DOCKERHUB_CREDENTIALS = credentials('angelomakory-dockerhub')
    }

    stages {
        stage('Build Docker Image for Backend') {
            steps {
                echo 'Building Docker image...'
                sh 'docker build -t angelomakory/pdf_back:$BUILD_ID .'
            }
        }

        stage('Run Docker Container') {
            steps {
                echo 'Running container on port 5000...'
                sh 'docker run -d -p 5000:5000 angelomakory/pdf_back:$BUILD_ID'
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo 'Logging into DockerHub...'
                sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
                echo 'Pushing image...'
                sh 'docker push angelomakory/pdf_back:$BUILD_ID'
            }
        }
    }

    post {
        always {
            echo "Logging out of Docker session"
            sh 'docker logout'
        }
    }
}
