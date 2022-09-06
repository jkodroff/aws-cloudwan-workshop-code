import json
import pulumi
import pulumi_aws_native as aws_native

# TODO: Remove this before merging
# aws_native does not yet support defaultTags: https://github.com/pulumi/pulumi-aws-native/issues/107
owner_tag = {
    "key": "owner",
    "value": "jkodroff",
}

repo_tag = {
    "key": "repo",
    "value": "aws-samples/aws-cloudwan-workshop-code/pulumi_python",
}

global_network = aws_native.networkmanager.GlobalNetwork(
    "global-network",
    aws_native.networkmanager.GlobalNetworkArgs(
        description="AWS CloudWAN Workshop",
        tags=[
            aws_native.networkmanager.GlobalNetworkTagArgs(
                key="Name",
                value="AWS CloudWAN Workshop",
            ),
            owner_tag,
            repo_tag,
        ],
    )
)

with open("files/core-network-policy.json", "r") as file:
    core_network_policy_string = str(file.read())

core_network_policy = json.loads(core_network_policy_string)

core_network = aws_native.networkmanager.CoreNetwork(
    "core-network",
    aws_native.networkmanager.CoreNetworkArgs(
        description="AWS CloudWAN Workshop",
        global_network_id=global_network.id,
        policy_document=core_network_policy,
        tags=[
            owner_tag,
            repo_tag,
        ]
    )
)

pulumi.export("core_network_id", core_network.id)
pulumi.export("core_network_arn", core_network.core_network_arn)
