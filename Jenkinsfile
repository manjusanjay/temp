pipeline {
    agent any

    stages {
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
            success {
            sh '''
                PR_NUMBER=$(echo ${JOB_NAME} | grep -oP '(?<=PR-)\\d+')
                curl -X POST http://172.17.0.1:5678/webhook-test/cicd-gate \
                -H "Content-Type: application/json" \
                -d "{
                    \\"job_name\\": \\"${JOB_NAME}\\",
                    \\"build_number\\": \\"${BUILD_NUMBER}\\",
                    \\"build_status\\": \\"SUCCESS\\",
                    \\"branch\\": \\"develop\\",
                    \\"developer\\": \\"${GIT_AUTHOR_NAME}\\",
                    \\"tests_passed\\": \\"40\\",
                    \\"tests_failed\\": \\"0\\",
                    \\"pr_action\\": \\"merge\\",
                    \\"repo\\": \\"manjusanjay/it-helpdesk-agent_\\",
                    \\"base_branch\\": \\"release\\",
                    \\"head_branch\\": \\"develop\\",
                    \\"pr_number\\": \\"${PR_NUMBER}\\"
                }" || true
            '''
            echo 'Tests passed — asking n8n agent to merge PR!'
        }
        failure {
            sh '''
                PR_NUMBER=$(echo ${JOB_NAME} | grep -oP '(?<=PR-)\\d+')
                curl -X POST http://172.17.0.1:5678/webhook-test/cicd-gate \
                -H "Content-Type: application/json" \
                -d "{
                    \\"job_name\\": \\"${JOB_NAME}\\",
                    \\"build_number\\": \\"${BUILD_NUMBER}\\",
                    \\"build_status\\": \\"FAILURE\\",
                    \\"branch\\": \\"develop\\",
                    \\"developer\\": \\"${GIT_AUTHOR_NAME}\\",
                    \\"tests_passed\\": \\"0\\",
                    \\"tests_failed\\": \\"40\\",
                    \\"pr_action\\": \\"close\\",
                    \\"repo\\": \\"manjusanjay/it-helpdesk-agent_\\",
                    \\"base_branch\\": \\"release\\",
                    \\"head_branch\\": \\"develop\\",
                    \\"pr_number\\": \\"${PR_NUMBER}\\"
                }" || true
            '''
            echo 'Tests failed — asking n8n agent to close PR!'
        }
    }
}