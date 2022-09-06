# AWS CloudWAN Workshop Code - Pulumi/Python

This directory contains the code for

The code is organized into the following stacks:

1. `cloudwan/` defines the Global Network and Core Network resources. Its resources are segregated into a separate stack due to the time to provision (about 15 minutes) and to limit blast radius. This stack must be deployed first.
1. `inspection/` defines an inspection VPCs on the shared services network segment through which firewall traffic to the internet runs. Because this stack references the `cloudwan` stack, it has a required config parameter that can be set as follows after logging in to Pulumi:

   ```bash
   cd inspection && pulumi config set aws-cloudwan-workshop-inspection:org $(pulumi whoami)
   ```

1. `workload/` defines VPCs in which a typical workload would run. Because this stack references the `cloudwan` stack, it has a required config parameter that can be set as follows after logging in to Pulumi:

   ```bash
   cd workload && pulumi config set aws-cloudwan-workshop-workload:org $(pulumi whoami)
   ```
