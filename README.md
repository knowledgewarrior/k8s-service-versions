# Cluster Info

Cluster info for the versions dashboard retrieves a list of images from a remote k8s cluster
and posts the results to a DynamoDB Table generated by `Serverless`.

A separate `serverless` deployment is required for each K8S cluster, eg. for
each cluster, we need to run `sls deploy`, as per below, to create a Lambda
Cron Task for each K8S cluster from which to obtain a list of images.

## Serverless Deploy

A `serverless-versiondash` IAM user was created in AWS account `648265802301`
(Elastic Path DevOps)

Obtain AWS Key and Secret from Ops `1Password` and add to a profile in `~/.aws/credentials`:
```
[sls-versiondash]
aws_access_key_id = AKIAxxxxxxxx
aws_secret_access_key = xxxxxxxxxx
region = us-west-2
```

Run command to deploy:
```
sls deploy --aws-profile sls-versiondash --stage <epcc-environment>
```
where `<epcc-environment>` in:
- staging
- integrations
- production

## Serverless Invoke
Run the following to invoke the function instead of waiting for it to be run
on AWS:
```
sls invoke --aws-profile sls-versiondash --stage staging -f staging-getimages -l
```

# Local Development
## Installation
Install requirements by running:
```
python3 -m pip install -r requirements.txt
```
## Environment variables

Copy the file `.env.example` to `.env` and modify variables according to the
target cluster:
```
epcc-env = '' # environment where apps are running
api-token = '' # api token, preferably based on `EKS_Restricted` AWS role
cluster_host = '' # host in .kube/config to connect to for K8S API
```
