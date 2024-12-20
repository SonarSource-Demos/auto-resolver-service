# Auto Resolver Service

Proof of concept tool to automatically apply AI CodeFix suggestions. The service listens for Sonarqube pull request
webhooks, pulls the issues and creates a pull request with the suggested fixes into the developers pr branch

## Setup
1. Create a personal access token with read/write repo permissions in GiHub
2. Create a user token in Sonarqube
3. Set the following environment variables in the container:
    - GITHUB_TOKEN: GitHub personal access token
    - SONARQUBE_TOKEN: Sonarqube user token
4. Deploy the container with a SonarQube accessible endpoint (use ngrok)
5. Create a global webhook in SonarQube -> pointing to the deployed https://{host}/v1/webhooks 
6. Trigger a PR scan in the GitHub repository

## Alternative Setup
1. Create local.env from example.env and set the following environment variables:
    - GITHUB_TOKEN: GitHub personal access token
    - SONARQUBE_TOKEN: Sonarq
2. Run `docker compose up`
3. Open the Swagger UI at http://localhost:8086/v1/ui/
4. Use the POST /v1/webhooks endpoint to simulate a SonarQube webhook

```json
{
  "serverUrl": "https://nautilus.sonarqube.org",
  "taskId": "4744377f-6f20-46d1-84f9-b86bf8e932d0",
  "status": "SUCCESS",
  "analysedAt": "2024-12-20T20:02:21+0000",
  "revision": "0b8fcf23194db972bf92b1ba58f3764c2168528e",
  "changedAt": "2024-12-20T20:02:21+0000",
  "project": {
    "key": "sonarsource-auto-resolver-service",
    "name": "Auto Resolver Service",
    "url": "https://nautilus.sonarqube.org/dashboard?id=sonarsource-auto-resolver-service"
  },
  "branch": {
    "name": "7",
    "type": "PULL_REQUEST",
    "isMain": false,
    "url": "https://nautilus.sonarqube.org/dashboard?id=sonarsource-auto-resolver-service&pullRequest=7"
  },
  "qualityGate": {
    "name": "Sonar way",
    "status": "ERROR",
    "conditions": [
      {
        "metric": "new_coverage",
        "operator": "LESS_THAN",
        "value": "0.0",
        "status": "ERROR",
        "errorThreshold": "80"
      },
      {
        "metric": "new_duplicated_lines_density",
        "operator": "GREATER_THAN",
        "value": "0.0",
        "status": "OK",
        "errorThreshold": "3"
      },
      {
        "metric": "new_security_hotspots_reviewed",
        "operator": "LESS_THAN",
        "status": "NO_VALUE",
        "errorThreshold": "100"
      },
      {
        "metric": "new_violations",
        "operator": "GREATER_THAN",
        "value": "1",
        "status": "ERROR",
        "errorThreshold": "0"
      }
    ]
  },
  "properties": {
    "sonar.analysis.detectedscm": "git",
    "sonar.analysis.detectedci": "Github Actions"
  }
}
```

## Notes
* Only GitHub is currently supported
* The SonarQube project must be bound to the GitHub project
* The service will create a new branch unless it was the author of the PR to avoid recursive PRs 
* Each commit contains the fixes for a single file
* The service checks to make sure that the branch has not been updated since the last scan was initiated
* Fixes are applied in order based on descending issue severity
* If multiple fixes impact a particular line of code, only the initial fix will be applied 