pipeline {
    agent any

    triggers {
        pollSCM 'H/5 * * * *'
    }

    environment {
        DOCKERHUB_CREDENTIALS = credentials ('angelomakory-dockerhub')
    }

    stages {
        stage('Check Python and PIP') {
            steps {
                echo "Checking py and pip versions"
                sh "python3 --version"
                sh "pip3 --version"
                
            }
        }
         stage('Install Py Dependencies') {
            steps {
                echo "Installing Flask and otherdependencies.."
                sh 'pip3 install -r requirements.txt'
                
            }
        }
        // stage('Test') {
        //     steps {
        //         echo "Testing.."
        //         sh 'pytest tests'
        // }
        // stage('Build') {
        //     steps {
        //         echo 'Building....'
        //         sh 'npm run build'
        //         archiveArtifacts artifacts: 'dist/**', fingerprint: true
        //     }
        // }
       stage('Building Docker Image for Backend') {
            steps {
                echo 'Building....'
                sh 'docker build -t angelomakory/pdf_back:$BUILD_ID .'
               
            }
        }
    //   stage('login') {
    //       steps {
    //           sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
    //       }
    //   }
      stage('Login to DockerHub') {
        steps {
        sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
    }
}
        stage('run on 5000'){
            steps{
                sh 'docker run -d -p 5000:5000 angelomakory/pdf_back'
            }
        }
      stage ('push'){
          steps {
            sh 'docker push angelomakory/pdf_back:$BUILD_ID'
           }  
         }
    }
    post {
        always {
            echo "LOgging out of Docker session"
            sh 'docker logout'
        }
    }
}
