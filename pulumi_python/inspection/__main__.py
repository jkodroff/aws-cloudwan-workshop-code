"""A Python Pulumi program"""

import pulumi
import pulumi_aws as aws
from components import inspection_vpc, InspectionVpcArgs

config = pulumi.Config()
stack = pulumi.get_stack()
org = config.require("org")

stack_ref = pulumi.StackReference(
    f"{org}/aws-cloudwan-workshop-cloudwan/{stack}")

core_network_id = stack_ref.get_output("core_network_id")

us_east_1_provider = aws.Provider(
    "us-east-1",
    region="us-east-1"
)

ORG_CIDR = "10.0.0.0/8"

us_east_1_inspection_vpc = inspection_vpc(
    name="us-east-1-inspection",
    args=InspectionVpcArgs(
        core_network_id=core_network_id,
        org_cidr=ORG_CIDR,
    ),
    provider=us_east_1_provider
)

eu_west_1_provider = aws.Provider(
    "eu-west-1",
    region="eu-west-1"
)

eu_west_1_inspection_vpc = inspection_vpc(
    name="eu-west-1-inspection",
    args=InspectionVpcArgs(
        core_network_id=core_network_id,
        org_cidr=ORG_CIDR,
    ),
    provider=eu_west_1_provider
)
