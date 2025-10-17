pipeline {
  agent {
    docker {
      image 'python:3.11-slim'
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
    cron('H H * * *')
  }

  parameters {
    string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Branch to build')
    booleanParam(name: 'ENABLE_JAILBREAK', defaultValue: false, description: 'Include jailbreak gate')
    string(name: 'SUITE', defaultValue: 'f1,latency_p95,pii', description: 'Validation evaluators (comma-separated)')
    string(name: 'POLICY', defaultValue: 'policy.yaml', description: 'Policy file path')
  }

  environment {
    MLFLOW_TRACKING_URI = 'http://host.docker.internal:5000'
    PYTHONUNBUFFERED    = '1'
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    DEBIAN_FRONTEND     = 'noninteractive'

    // 👇 Explicitly map params -> env so they exist in the container
    GIT_BRANCH          = "${params.GIT_BRANCH}"
    ENABLE_JAILBREAK    = "${params.ENABLE_JAILBREAK}"
    SUITE               = "${params.SUITE}"
    POLICY              = "${params.POLICY}"
  }

  stages {

    stage('Checkout') {
      steps {
        deleteDir()
        checkout([$class: 'GitSCM',
          branches: [[name: "*/${params.GIT_BRANCH}"]],
          userRemoteConfigs: [[url: 'https://github.com/bagumas/ai_model_validation_framework.git']]
        ])
        // Ensure git is available inside the container (some images don’t have it)
        sh '''
          set -euo pipefail
          apt-get update
          apt-get install -y --no-install-recommends git
          git --version || true
        '''
      }
    }

    stage('Setup Python') {
      steps {
        sh '''
          set -euo pipefail
          python -m pip install --upgrade pip setuptools wheel
          pip install -r requirements.txt
        '''
      }
    }

    stage('Train Sample Model') {
      steps {
        sh '''
          set -euo pipefail
          python scripts/train_sample_model.py
        '''
      }
    }

    stage('Validate (Policy Gates)') {
      steps {
        sh '''
          set -euo pipefail
          export PYTHONPATH=src

          # Safe defaults even with `set -u`
          SUITE_VAL="${SUITE:-f1,latency_p95,pii}"
          POLICY_FILE="${POLICY:-policy.yaml}"
          ENABLE_JB="${ENABLE_JAILBREAK:-false}"

          if [ "${ENABLE_JB}" = "true" ]; then
            SUITE_VAL="${SUITE_VAL},jailbreak"
          fi
          echo "Using suite: ${SUITE_VAL}"
          echo "Using policy: ${POLICY_FILE}"

          # Tag run with Git + Jenkins metadata (readable by MLflow)
          COMMIT=$(git rev-parse --short HEAD || echo "unknown")
          export MLFLOW_TAG_GIT_SHA="${COMMIT}"
          export MLFLOW_TAG_JOB="${JOB_NAME:-validation}"
          export MLFLOW_TAG_BUILD="${BUILD_NUMBER:-0}"

          # Run validation and capture output so we can extract the MLflow run URL
          python src/runner.py \
            --model-path models/iris_logreg.pkl \
            --data-path data/iris.csv \
            --suite "${SUITE_VAL}" \
            --policy "${POLICY_FILE}" 2>&1 | tee runner_output.log

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

