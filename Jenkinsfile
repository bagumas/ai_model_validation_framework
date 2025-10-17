pipeline {
  agent {
    docker {
      image 'python:3.11-slim'
      // Lets the container talk to MLflow running on your host via Docker Desktop
      args '--add-host=host.docker.internal:host-gateway'
      reuseNode true
    }
  }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    skipDefaultCheckout(true)
  }

  triggers {
    // Nightly run (hashed hour) so the job validates regularly
    cron('H H * * *')
  }

  environment {
    // Point training/validation to your local MLflow server
    MLFLOW_TRACKING_URI = 'http://host.docker.internal:5000'
    PYTHONUNBUFFERED    = '1'
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    DEBIAN_FRONTEND     = 'noninteractive'
  }

  parameters {
    string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch to build')
    booleanParam(name: 'ENABLE_JAILBREAK', defaultValue: false, description: 'Include jailbreak gate')
    string(name: 'SUITE', defaultValue: 'f1,latency_p95,pii', description: 'Validation evaluators (comma-separated)')
    string(name: 'POLICY', defaultValue: 'policy.yaml', description: 'Policy file path')
  }

  stages {

    stage('Checkout') {
      steps {
        deleteDir()
        checkout([$class: 'GitSCM',
          branches: [[name: "*/${params.GIT_BRANCH}"]],
          userRemoteConfigs: [[url: 'https://github.com/bagumas/ai_model_validation_framework.git']]
        ])
        // If Jenkins tried git outside the container earlier, this guarantees we have git here
        sh '''
          set -eux
          apt-get update
          apt-get install -y --no-install-recommends git
          git --version || true
        '''
      }
    }

    stage('Setup Python') {
      steps {
        sh '''
          set -eux
          python -m pip install --upgrade pip setuptools wheel
          pip install -r requirements.txt
        '''
      }
    }

    stage('Train Sample Model') {
      steps {
        sh '''
          set -eux
          python scripts/train_sample_model.py
        '''
      }
    }

    stage('Validate (Policy Gates)') {
      steps {
        sh '''
          set -eux

          export PYTHONPATH=src

          # Compose suite (optionally append jailbreak)
          SUITE="${SUITE}"
          if [ "${ENABLE_JAILBREAK}" = "true" ]; then
            SUITE="${SUITE},jailbreak"
          fi
          echo "Using suite: ${SUITE}"

          # Tag run with Git + Jenkins metadata (readable by MLflow)
          COMMIT=$(git rev-parse --short HEAD || echo "unknown")
          export MLFLOW_TAG_GIT_SHA="${COMMIT}"
          export MLFLOW_TAG_JOB="${JOB_NAME}"
          export MLFLOW_TAG_BUILD="${BUILD_NUMBER}"

          # Run validation and capture output so we can extract the MLflow run URL
          python src/runner.py \
            --model-path models/iris_logreg.pkl \
            --data-path data/iris.csv \
            --suite "${SUITE}" \
            --policy "${POLICY}" 2>&1 | tee runner_output.log

          # Best-effort: extract the run URL from MLflow client logs
          awk -F'at: ' '/View run/ {print $2}' runner_output.log | sed 's/[[:space:]]*\\.*$//' | tail -n1 > mlflow_run_url.txt || true
          echo "MLflow run URL (if found): $(cat mlflow_run_url.txt 2>/dev/null || echo 'n/a')"
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'models/**,data/**,reports/**/*,runner_output.log,mlflow_run_url.txt,mlruns/**', allowEmptyArchive: true
    }
    success {
      script {
        def url = fileExists('mlflow_run_url.txt') ? readFile('mlflow_run_url.txt').trim() : null
        if (url) {
          currentBuild.description = "MLflow: ${url}"
          echo "✅ Validation passed — all policy gates met. MLflow: ${url}"
        } else {
          echo "✅ Validation passed — all policy gates met."
        }
      }
    }
    failure {
      echo '❌ Validation failed — one or more policy gates were not met.'
    }
  }
}

