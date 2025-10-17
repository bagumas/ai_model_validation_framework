pipeline {
  agent {
    docker {
      image 'python:3.11-slim'
      args '--add-host=host.docker.internal:host-gateway -v $HOME/.cache/pip:/root/.cache/pip'
    }
  }

  options {
    skipDefaultCheckout(true)   // <— stop the implicit checkout
  }

  environment {
    PYTHONUNBUFFERED = '1'
    MLFLOW_TRACKING_URI = 'http://host.docker.internal:5000'
  }

  stages {
    stage('Checkout') {
      steps {
        deleteDir()             // <— clean workspace
        checkout scm            // <— do a full checkout now
      }
    }

    stage('Setup Python') {
      steps {
        sh '''
          python -m pip install --upgrade pip setuptools wheel
          pip install -r requirements.txt
        '''
      }
    }

    stage('Train Sample Model') {
      steps { sh 'python scripts/train_sample_model.py' }
    }

    stage('Validate (Policy Gates)') {
      steps {
        sh '''
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
      // When earlier stages abort, ensure we still have a node/workspace context
      script {
        sh 'ls -R mlruns || true'
        archiveArtifacts artifacts: 'mlruns/**/*, **/report.txt', allowEmptyArchive: true
      }
    }
  }
}

