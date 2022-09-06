import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx


class WorkloadVpcArgs:
    def __init__(
        self,
        core_network_id: str,
        core_network_arn: str,
        vpc_cidr: str,
        cloudwan_segment: str,
    ):
        self.core_network_id = core_network_id
        self.core_network_arn = core_network_arn
        self.vpc_cidr = vpc_cidr
        self.cloudwan_segment = cloudwan_segment


def workload_vpc(name: str, args: WorkloadVpcArgs, provider: aws.Provider):
    vpc = awsx.ec2.Vpc(
        f"workload-{name}",
        awsx.ec2.VpcArgs(
            cidr_block=args.vpc_cidr,
            subnet_specs=[
                awsx.ec2.SubnetSpecArgs(
                    name="Workload",
                    type=awsx.ec2.SubnetType.ISOLATED,
                    cidr_mask=24
                ),
            ],
            nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
                strategy=awsx.ec2.NatGatewayStrategy.NONE,
            ),
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

    vpc_attachment = aws.networkmanager.VpcAttachment(
        f"vpc-attachment-{name}",
        aws.networkmanager.VpcAttachmentArgs(
            core_network_id=args.core_network_id,
            vpc_arn=vpc.vpc.arn,
            subnet_arns=isolated_subnet_arns,
            tags={
                args.cloudwan_segment: "cloudwan-segment",
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
        )
    )

    def add_route(route_table_id):
        aws.ec2.Route(
            f"route-to-cloudwan-{route_table_id}",
            aws.ec2.RouteArgs(
                core_network_arn=args.core_network_arn,
                destination_cidr_block="0.0.0.0/32",
                route_table_id=route_table_id,
            ),
            opts=pulumi.ResourceOptions(
                provider=provider,
                depends_on=vpc_attachment,
            )
        )

    def add_routes(route_tables):
        for route_table in route_tables:
            route_table.id.apply(add_route)

    vpc.route_tables.apply(add_routes)

    endpoint_security_group = aws.ec2.SecurityGroup(
        "vpc-endpoint",
        aws.ec2.SecurityGroupArgs(
            description="Allow HTTPS ingress",
            vpc_id=vpc.vpc_id,
            ingress=[{
                "protocol": "tcp",
                "from_port": 443,
                "to_port": 443,
                "cidr_blocks": [args.vpc_cidr],
            }]
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            depends_on=vpc_attachment,
        ),
    )

    def add_vpc_endpoints(subnet_ids, region, security_group_id, vpc_id):
        aws.ec2.VpcEndpoint(
            f"ssm-endpoint",
            aws.ec2.VpcEndpointArgs(
                service_name=f"com.amazonaws.{region}.ssm",
                vpc_id=vpc_id,
                vpc_endpoint_type="Interface",
                security_group_ids=[security_group_id],
                subnet_ids=subnet_ids,
                private_dns_enabled=True
            ),
            opts=pulumi.ResourceOptions(
                provider=provider,
                depends_on=vpc_attachment,
            ),
        )

    pulumi.Output.all(vpc.isolated_subnet_ids, region_result.name, endpoint_security_group.id, vpc.vpc_id).apply(
        lambda args: add_vpc_endpoints(args[0], args[1], args[2], args[3]))

    # amazon_linux_2 = aws.ec2.get_ami(
    #     most_recent=True,
    #     filters=[
    #         {
    #             "name": "name",
    #             "values": ["amzn2-ami-hvm*"],
    #         },
    #         {
    #             "name": "architecture",
    #             "values": ["x86_64"],
    #         },
    #     ],
    #     owners=["amazon"],
    #     opts=pulumi.InvokeOptions(
    #         provider=provider,
    #     )
    # )
