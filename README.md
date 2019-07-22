Copyright 2019, Doug Knight
All Rights Reserved.

This is a work in progress; not intended for public consumption.

1. Create account.  After receiving Email confirmation:
2. Go to aws.amazon.com and login to console with root account and:

        a. Setup multi-factor authentication for the root account
           (Located under: account dropdown > My Security Credentials >
            Multi-factor authentication > Activate MFA)

        b. Set region.

        c. Deploy master-bootstrap stack.
           (Services > CloudFormation > Create stack)

        d. Setup AWSCLI
           (Services > IAM > Users > org-admin > Security credentials > Create access key)
                aws configure
                aws iam list-roles --output text --query 'Roles[?starts_with(RoleName, `org-manager-tools-`) == `true`].Arn|[0]'

        e. Upload scripts:
           ```
           OMT_BUCKET=$( aws cloudformation describe-stack-resources --stack-name org-manager-tools --output text --query 'StackResources[?LogicalResourceId==`OrgManagerToolsBucket`].PhysicalResourceId' )
           aws --profile admin s3 sync scripts s3://$OMT_BUCKET
           ```
