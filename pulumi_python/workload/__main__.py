"""A Python Pulumi program"""

import pulumi
import pulumi_aws as aws
from components import workload_vpc, WorkloadVpcArgs


config = pulumi.Config()
stack = pulumi.get_stack()
org = config.require("org")

stack_ref = pulumi.StackReference(
    f"{org}/aws-cloudwan-workshop-cloudwan/{stack}")

core_network_id = stack_ref.get_output("core_network_id")
core_network_arn = stack_ref.get_output("core_network_arn")

us_east_1_provider = aws.Provider(
    "us-east-1",
    region="us-east-1"
)

prod_us_workload = workload_vpc(
    "prod-us-workload",
    WorkloadVpcArgs(
        core_network_id=core_network_id,
        core_network_arn=core_network_arn,
        vpc_cidr='10.0.0.0/22',
        cloudwan_segment="prod",
    ),
    provider=us_east_1_provider,
)

nonprod_us_workload = workload_vpc(
    "nonprod-us-workload",
    WorkloadVpcArgs(
        core_network_id=core_network_id,
        core_network_arn=core_network_arn,
        vpc_cidr='10.0.4.0/22',
        cloudwan_segment="nonprod",
    ),
    provider=us_east_1_provider,
)
