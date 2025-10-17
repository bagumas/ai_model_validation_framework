pipeline {
  agent {
    docker {
      image 'python:3.11-slim'
      // allow container to reach MLflow on host; no host bind mounts needed
      args '--add-host=host.docker.internal:host-gateway'
    }
  }

  options {
    // We do a clean, explicit checkout in a stage
    skipDefaultCheckout(true)
    // nice console
    timestamps()
  }

  environment {
    PYTHONUNBUFFERED        = '1'
    // Point to your MLflow server (from earlier docker-compose setup)
    MLFLOW_TRACKING_URI     = 'http://host.docker.internal:5000'
    MLFLOW_EXPERIMENT_NAME  = 'model-validation'
    RUN_CONTEXT             = "jenkins:${env.JOB_NAME}#${env.BUILD_NUMBER}"

    // Silence GitPython warning if git is missing (we also install git below)
    GIT_PYTHON_REFRESH      = 'quiet'

    // Cache pip to your Jenkins workspace (persisted via volumes-from)
    PIP_CACHE_DIR           = "${env.WORKSPACE}/.pip-cache"

    // Set to "true" in Jenkins (or here) to enable the jailbreak gate
    ENABLE_JAILBREAK        = 'false'

    // Optional: set a Slack channel in job/env to enable notifications
    // SLACK_CHANNEL        = '#builds'
  }

  stages {

    stage('Checkout') {
      steps {
        deleteDir()
        checkout scm
        sh 'git rev-parse --short HEAD || true'
      }
    }

    stage('Setup Python') {
      steps {
        sh '''
          set -eux
          # Install git so MLflow can record commit SHA
          apt-get update
          apt-get install -y --no-install-recommends git
          git --version

          python -m pip install --upgrade pip setuptools wheel
          pip install -r requirements.txt
        '''
      }
    }

    stage('Train Sample Model') {
      steps {
        sh 'python scripts/train_sample_model.py'
      }
    }

    stage('Validate (Policy Gates)') {
      steps {
        sh '''
          set -eux
          export PYTHONPATH=src

          # Base suite
          SUITE="f1,latency_p95,pii"

          # Optionally add jailbreak gate if requested
          if [ "${ENABLE_JAILBREAK}" = "true" ]; then
            SUITE="${SUITE},jailbreak"
          fi

          # Pass experiment name + tags into runner via env (runner will read them)
          python src/runner.py \
            --model-path models/iris_logreg.pkl \
            --data-path data/iris.csv \
            --suite "${SUITE}" \
            --policy policy.yaml
        '''
      }
    }
  }

  post {
    success {
      echo '✅ Validation passed — all policy gates met.'
      script {
        if (env.SLACK_CHANNEL) {
          try {
            slackSend channel: env.SLACK_CHANNEL, message: "✅ ${env.JOB_NAME} #${env.BUILD_NUMBER} passed"
          } catch (err) {
            echo "Slack notify skipped: ${err}"
          }
        }
      }
    }
    failure {
      echo '❌ Validation failed — at least one policy gate did not pass.'
      script {
        if (env.SLACK_CHANNEL) {
          try {
            slackSend channel: env.SLACK_CHANNEL, message: "❌ ${env.JOB_NAME} #${env.BUILD_NUMBER} failed — check logs"
          } catch (err) {
            echo "Slack notify skipped: ${err}"
          }
        }
      }
    }
    always {
      archiveArtifacts artifacts: 'mlruns/**/*, **/report.txt', allowEmptyArchive: true
    }
  }
}

