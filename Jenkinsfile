pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'develop',
                    credentialsId: 'github-credentials',
                    url: 'https://github.com/manjusanjay/temp.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    pip3 install pytest flask google-generativeai \
                        chromadb sentence-transformers \
                        --break-system-packages --quiet
                '''
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh '''
                    python3 -m pytest test_it_helpdesk.py \
                        -v --tb=short \
                        --junit-xml=${WORKSPACE}/test-results.xml
                '''
            }
        }
    }

    post {
        always {
            junit 'test-results.xml'
        }
    }
}