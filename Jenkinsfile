pipeline {
  agent {
    docker {
      image 'python:3.11-slim'
      // Optional: mount a pip cache between builds for speed
      args '-v $HOME/.cache/pip:/root/.cache/pip'
    }
  }

  environment {
    PYTHONUNBUFFERED = '1'
    // Uncomment if you add MLflow server creds or API keys later:
    // MLFLOW_TRACKING_URI = credentials('mlflow-tracking-uri')  // Jenkins Credentials ID
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Setup Python') {
      steps {
        sh '''
          python -m pip install --upgrade pip setuptools wheel
          # If you’re using MLflow in requirements.txt, this will pull manylinux wheels incl. pyarrow
          pip install -r requirements.txt
        '''
      }
    }

    stage('Train Sample Model') {
      steps {
        sh 'python scripts/train_sample_model.py'
      }
    }

    stage('Validate Model (Policy Gates)') {
      steps {
        sh '''
          # Ensure package imports resolve
          export PYTHONPATH=src
          python src/runner.py \
            --model-path models/iris_logreg.pkl \
            --data-path data/iris.csv \
            --suite f1,latency_p95,pii \
            --policy policy.yaml
        '''
      }
    }
  }

  post {
    always {
      // Archive MLflow runs (if MLflow local dir exists) and text report if present
      sh 'ls -R mlruns || true'
      archiveArtifacts artifacts: 'mlruns/**/*, **/report.txt', allowEmptyArchive: true
    }
    failure {
      echo '❌ Validation failed — one or more policy gates were not met.'
    }
    success {
      echo '✅ Validation passed — all policy gates met.'
    }
  }
}

