#!groovy
@Library('shared-incu') _

// This is needed if you want to use ci checks defined in ci_check.yaml file
/*
def checks_file = "checks.yaml"
def get_checks(file){
    checks = readYaml file: file
    return checks.checks
}
*/

def projectName = 'votebot'
def repoName = 'votebot'
def registryUrl = "europe-central2-docker.pkg.dev"
def projectGCP = "gc-prod-it-main"
def chartRepo = "https://gitlab.intra.codilime.com/admins/sandbox-manifests/votebot"
def chartStagingBranch = "staging"
def chartProdBranch = "prod"

pipeline {
    agent any
    stages {
        // This stage is advised to guarantee that all requirements for ci checks are satisfied.
        // All CI checks will be executed inside that image.
        stage('Create CI image') {
            steps {
                script {
                    env.GIT_COMMIT = sh(script: "git log -1 --pretty=format:%h", returnStdout: true).trim()
                    // Choose approach that fits you better. Separate dockerfile or target for multistage dockerfiles.
                    docker.build("${projectName}:${GIT_COMMIT}", "--target tests .")
                }
            }
        }
        
/*
        // This stage executes check read from checks.yaml file
        stage("CI checks") {
            steps {
                script {
                    def checks = readYaml file:'checks.yaml'
                    checks = checks['checks']
                    if (checks) {
                        for (int i = 0; i < checks.size(); i++) {
                            stage(checks[i].name) {
                                // If you decided not to build docker image, you should remove docker.image().inside(){} wrapper
                                docker.image("${projectName}:${GIT_COMMIT}").inside("""--entrypoint=''""") {
                                    runWithStatus(checks[i].name, env.GIT_URL, "${projectName}_gitToken") {
                                        sh """#!/bin/bash
                                        |${checks[i].command}""".stripMargin()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
*/
        // This stage builds image based on Dockerfile in repository root and pushes it to GCP Artifact Registry.
        // This image will be used for deployment.
        
        stage('Build image') {
            steps {
                script {
                    withCredentials([file(credentialsId: "${projectName}_registry", variable: 'KEYSTORE')]) {
                    sh"""
                    cat $KEYSTORE | docker login -u _json_key --password-stdin "https://${registryUrl}"

                    docker build -f Dockerfile -t image --target production . 
                    docker tag image "${registryUrl}/${projectGCP}/${projectName}/votebot:${GIT_COMMIT}"

                    docker build -f nginx/Dockerfile -t image .
                    docker tag image "${registryUrl}/${projectGCP}/${projectName}/proxy:${GIT_COMMIT}"

                    docker push "${registryUrl}/${projectGCP}/${projectName}/votebot:${GIT_COMMIT}"
                    docker push "${registryUrl}/${projectGCP}/${projectName}/proxy:${GIT_COMMIT}"
                    """
                    }
                }
            }
        }
        
        // This stage changes the image tag in the Manifest repo Staging branch
        // To use with Sandbox version 2
        stage("Change tag in the project Manifest repo Staging branch") {
            steps {
                cleanWs()
                script {
                    reponame = getRepoName(chartRepo)
                    withCredentials([usernamePassword(credentialsId: "${projectName}_manifestGitToken", usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
                        #!/bin/bash -e
                        clean_url=`echo $chartRepo |sed "s%https\\?:\\/\\/\\|git@%%"`
                        git clone -b $chartStagingBranch https://$GIT_USERNAME:$GIT_PASSWORD@\$clean_url
                        cd ${reponame}
                        git config --global user.email "sanbox-inku-k8s@codilime.com"
                        git config --global user.name "SandBox"
                        yq -i '.deployments.deployment-votebot.image.tag = "${GIT_COMMIT}"' values.yaml
                        yq -i '.deployments.deployment-proxy.image.tag = "${GIT_COMMIT}"' values.yaml
                        git commit -am 'updating image TAG ${GIT_COMMIT}'
                        git push --set-upstream origin ${chartStagingBranch} -o merge_request.create -o merge_request.description="Merging Staging Branch. -o merge_request.source_branch=${chartStagingBranch} -omerge_request.target_branch=${chartProdBranch} -o merge_request.remove_source_branch = false"
                        """
                    }
                }
            }
        }
        
        // This stage executes end-to-end checks defined by Developers
        /*
        stage('E2E Checks') {
            steps {
                // Define checks
            }
        }
        */
        // This stage changes the image tag in the Manifest repo Production branch
        // To use with Sandbox version 2
        /*
        stage("Change tag in the project Manifest repo Production branch") {
            when { expression { env.CHANGE_ID == null }}
            steps {
                cleanWs()
                script {
                    reponame = getRepoName(chartRepo)
                    withCredentials([usernamePassword(credentialsId: "${projectName}_gitManifestToken", usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
                        #!/bin/bash -e
                        clean_url=`echo $chartRepo |sed "s%https\\?:\\/\\/\\|git@%%"`
                        git clone -b $chartProdBranch https://$GIT_USERNAME:$GIT_PASSWORD@\$clean_url
                        cd ${reponame}
                        git config --global user.email "sanbox-inku-k8s@codilime.com"
                        git config --global user.name "SandBox"
                        yq -i '.deployments.deployment-*.image.tag = "${GIT_COMMIT}"' values.yaml
                        git commit -am 'updating image TAG ${GIT_COMMIT}'
                        cd ${reponame} && git push --set-upstream origin ${chartProdBranch} -o merge_request.create -o merge_request.description="Merging Production Branch."
                        """
                    }
                }
            }
        }
        */
    }
    post {
        always {
            cleanWs()
        }
    }
}
