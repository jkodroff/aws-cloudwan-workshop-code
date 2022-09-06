import pulumi
import pulumi_awsx as awsx
import pulumi_aws as aws

# Design note: For the purpose of simplicity, we'll default to AWS Classic
# resources to avoid needing to pass multiple providers to our components.


class InspectionVpcArgs:
    def __init__(
        self,
        core_network_id: str,
        org_cidr: str,
    ):
        self.core_network_id = core_network_id
        self.org_cidr = org_cidr


def inspection_vpc(name: str, args: InspectionVpcArgs, provider: aws.Provider):
    vpc = awsx.ec2.Vpc(
        f"vpc-{name}",
        awsx.ec2.VpcArgs(
            subnet_specs=[
                awsx.ec2.SubnetSpecArgs(
                    name="CloudWANAttachments",
                    type=awsx.ec2.SubnetType.ISOLATED,
                    cidr_mask=24
                ),
                awsx.ec2.SubnetSpecArgs(
                    name="Firewall",
                    type=awsx.ec2.SubnetType.PRIVATE,
                    cidr_mask=24
                ),
                awsx.ec2.SubnetSpecArgs(
                    name="Public",
                    type=awsx.ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
            ],
            tags={
                "Name": "InspectionVPC"
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider
        )
    )

    region_result = aws.get_region(
        opts=pulumi.InvokeOptions(
            provider=provider
        )
    )

    caller_identity_result = aws.get_caller_identity(
        opts=pulumi.InvokeOptions(
            provider=provider
        )
    )

    isolated_subnet_arns = pulumi.Output.all(region_result, caller_identity_result, vpc.isolated_subnet_ids) \
        .apply(lambda args: list(map(lambda subnet_id: f"arn:aws:ec2:{args[0].name}:{args[1].account_id}:subnet/{subnet_id}", args[2])))

    # TODO: Consider a custom timeout for creation, since it stays in the
    # "updating" state for a long time (60m?)
    aws.networkmanager.VpcAttachment(
        f"vpc-attachment-{name}",
        aws.networkmanager.VpcAttachmentArgs(
            core_network_id=args.core_network_id,
            vpc_arn=vpc.vpc.arn,
            subnet_arns=isolated_subnet_arns,
            tags={
                "sharedservices": "cloudwan-segment",
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
        )
    )

    aws.networkfirewall.RuleGroup(
        f"stateless-allow-{name}",
        aws.networkfirewall.RuleGroupArgs(
            capacity=10,
            type="STATELESS",
            rule_group=aws.networkfirewall.RuleGroupRuleGroupArgs(
                rules_source=aws.networkfirewall.RuleGroupRuleGroupRulesSourceArgs(
                    stateless_rules_and_custom_actions=aws.networkfirewall.RuleGroupRuleGroupRulesSourceStatelessRulesAndCustomActionsArgs(
                        stateless_rules=[
                            aws.networkfirewall.RuleGroupRuleGroupRulesSourceStatelessRulesAndCustomActionsStatelessRuleArgs(
                                priority=1,
                                rule_definition=aws.networkfirewall.RuleGroupRuleGroupRulesSourceStatelessRulesAndCustomActionsStatelessRuleRuleDefinitionArgs(
                                    actions=["aws:pass"],
                                    match_attributes={
                                        "protocols": [1],
                                        "sources": [{"address_definition": "0.0.0.0/0"}],
                                        "destinations": [{"address_definition": "0.0.0.0/0"}],
                                    }
                                )
                            )
                        ]
                    )
                )
            )
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
        )
    )

    aws.networkfirewall.RuleGroup(
        f"stateful-allow-{name}",
        aws.networkfirewall.RuleGroupArgs(
            capacity=10,
            type="STATEFUL",
            rule_group=aws.networkfirewall.RuleGroupRuleGroupArgs(
                rules_source=aws.networkfirewall.RuleGroupRuleGroupRulesSourceArgs(
                    stateful_rules=[
                        {
                            "action": 'PASS',
                            "header": {
                                "destination": "ANY",
                                "destination_port": "80",
                                "source": args.org_cidr,
                                "source_port": "ANY",
                                "protocol": "TCP",
                                "direction": "FORWARD",
                            },
                            "rule_options": [{
                                "keyword": "sid:1"
                            }],
                        },
                        {
                            "action": 'PASS',
                            "header": {
                                "destination": "ANY",
                                "destination_port": "443",
                                "source": args.org_cidr,
                                "source_port": "ANY",
                                "protocol": "TCP",
                                "direction": "FORWARD",
                            },
                            "rule_options": [{
                                "keyword": "sid:2"
                            }],
                        },
                        {
                            "action": 'PASS',
                            "header": {
                                "destination": "ANY",
                                "destination_port": "123",
                                "source": args.org_cidr,
                                "source_port": "ANY",
                                "protocol": "UDP",
                                "direction": "FORWARD",
                            },
                            "rule_options": [{
                                "keyword": "sid:3"
                            }],
                        },
                    ]
                )
            )
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
        )
    )
