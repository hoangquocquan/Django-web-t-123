# Staging root Terraform

Run from this directory only after operator inputs are approved:

```text
terraform fmt -check
terraform init -backend=false
terraform validate
terraform plan -var-file=terraform.tfvars
```

The current skeleton intentionally contains no backend state configuration and no real account/domain values. A meaningful plan requires AWS credentials/account, selected region/AZs, networking policy, certificate/domain inputs and operator-approved sizes. Never run `terraform apply` in this feature.
