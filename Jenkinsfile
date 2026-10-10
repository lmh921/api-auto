// ============================================================
// 接口自动化测试框架 - Jenkins声明式流水线
//
// 前置要求（见 README 第13节）：
//   1. Jenkins 安装插件：Email Extension（邮件通知）、（可选）Allure
//   2. Jenkins 全局配置好 SMTP 发件账号（Manage Jenkins -> System -> Extended E-mail Notification）
//   3. 运行节点为 Windows（步骤用 bat），且能访问 python / allure（默认走 PATH，
//      找不到时把下方 PYTHON_EXE / ALLURE_EXE 改成绝对路径）
//
// agent 说明：
//   方式一（推荐，Jenkins与项目同机）：保持下方 customWorkspace 指向项目目录，任务里直接粘贴本文件内容即可，无需 git
//   方式二（代码入 git 后）：删除 customWorkspace 两行，任务改用 "Pipeline script from SCM" 从仓库读取本文件
// ============================================================
pipeline {
    agent {
        node {
            label ''
            customWorkspace 'D:\\pythontest\\ziufileApi'
        }
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    // 定时自动执行：每天上午8点左右（Jenkins cron语法，H为散列扰动避免整点拥堵；按需修改/删除）
    // 当前已暂停（旧产品用例归档期间）；恢复每日自动执行时取消下行注释，并在Jenkins任务里同步更新脚本
    // triggers { cron('H 8 * * *') }

    parameters {
        choice(
            name: 'ENV',
            choices: ['client-dev', 'station-dev', 'client-prod', 'station-prod'],
            description: '测试环境（见 config/config.yaml 的 environments 段）'
        )
        booleanParam(
            name: 'CONFIRM_PROD',
            defaultValue: false,
            description: '正式环境（prod: true）必须勾选才会执行'
        )
        text(
            name: 'RECIPIENTS',
            defaultValue: '',
            description: '邮件收件人，多个用英文逗号分隔；留空则发给构建触发人/任务订阅者'
        )
        string(
            name: 'PYTEST_ARGS',
            defaultValue: '',
            description: '附加pytest参数，如 -k smoke 或指定用例文件（可选）'
        )
    }

    environment {
        // Jenkins服务账户的PATH与桌面不同，找不到命令时改为绝对路径：
        // PYTHON_EXE = 'D:\\tools\\python\\python.exe'
        // ALLURE_EXE = 'D:\\work\\dev\\allure-2.36.0\\bin\\allure.bat'
        PYTHON_EXE = 'python'
        ALLURE_EXE = 'allure'
        PIP_INDEX   = 'https://pypi.tuna.tsinghua.edu.cn/simple'
    }

    stages {
        stage('准备依赖') {
            steps {
                bat '''
                    %PYTHON_EXE% -m venv .venv-ci
                    .venv-ci\\Scripts\\python.exe -m pip install -r requirements.txt -q -i %PIP_INDEX%
                    .venv-ci\\Scripts\\python.exe -m pip list
                '''
            }
        }

        stage('运行测试') {
            steps {
                script {
                    // returnStatus：用例失败不中断流水线，保证报告与邮件仍然生成
                    env.TEST_RC = bat(
                        returnStatus: true,
                        script: """
                            .venv-ci\\Scripts\\python.exe -m pytest testcases/test_executor.py ^
                              --env ${params.ENV} ${params.CONFIRM_PROD ? '--confirm-prod' : ''} ^
                              --alluredir=reports/allure-results --clean-alluredir -v ${params.PYTEST_ARGS}
                        """
                    )
                }
            }
        }

        stage('生成Allure报告') {
            steps {
                bat returnStatus: true, script: '%ALLURE_EXE% generate reports/allure-results -o reports/allure-report --clean'
            }
        }

        stage('生成邮件摘要') {
            steps {
                bat returnStatus: true, script: """
                    if not exist reports\\allure-results mkdir reports\\allure-results
                    .venv-ci\\Scripts\\python.exe utils/result_summary.py --results reports/allure-results --out-dir reports --env ${params.ENV}
                """
            }
        }

        stage('归档产物') {
            steps {
                bat '''
                    if exist reports\\allure-report (
                        powershell -Command "Compress-Archive -Path reports/allure-report/* -DestinationPath reports/allure-report.zip -Force"
                    )
                '''
                archiveArtifacts artifacts: 'reports/email_summary.txt,reports/email_summary.html,reports/allure-report.zip,logs/api_test.log',
                                 allowEmptyArchive: true
            }
        }

        stage('标记构建结果') {
            steps {
                script {
                    if (env.TEST_RC != '0') {
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
    }

    post {
        always {
            // 邮件正文内嵌纯文本摘要，附件带HTML明细、Allure报告压缩包与执行日志
            emailext(
                subject: "[接口自动化][${params.ENV}] 构建#${BUILD_NUMBER} - ${currentBuild.currentResult}",
                body: '''${FILE,path="reports/email_summary.txt"}''',
                attachmentsPattern: 'reports/email_summary.html,reports/allure-report.zip,logs/api_test.log',
                mimeType: 'text/plain;charset=UTF-8',
                to: "${params.RECIPIENTS}",
                recipientProviders: [requestor(), developers()]
            )
        }
        cleanup {
            // CI专用虚拟环境每次构建重建，保持环境干净（重建约1分钟）
            bat 'if exist .venv-ci rmdir /s /q .venv-ci'
            // 注意：customWorkspace 直接指向真实项目目录，绝不能调用 deleteDir()，否则会删除整个项目
        }
    }
}
