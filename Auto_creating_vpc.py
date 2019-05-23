import boto3
client = boto3.client('ec2')
ec2 = boto3.resource('ec2')
test_script= """#!/bin/bash 
            sudo yum -y install httpd
            sudo  systemctl start httpd
            echo "<h1> Welcome to auto configure vpc</h1>"  >> /var/www/html/index.html """

print ("Now creating vpc")
response = client.create_vpc(
    CidrBlock='10.0.0.0/19',
        DryRun= False,
    InstanceTenancy='default',
)
Vpc_id=  response['Vpc']['VpcId']
print (Vpc_id)
response1 = client.create_tags(
    DryRun=False,
    Resources=[
        Vpc_id
    ],
    Tags=[
        {
            'Key': 'vpc_iffco',
            'Value': 'phulpur'
        },
    ]
)
print ("Now creating SecurityGroup")
response_secg = client.create_security_group(
    Description='test_sgd',
    GroupName='test_sg',
    VpcId= Vpc_id,
    DryRun= False
)

sec_group_id = response_secg['GroupId']
print (sec_group_id)
print("Security group update")
data = client.authorize_security_group_ingress(
    GroupId=sec_group_id,
    IpPermissions=[
        {'IpProtocol': 'tcp',
         'FromPort': 80,
         'ToPort': 80,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp',
         'FromPort': 22,
         'ToPort': 22,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ])
print('Ingress Successfully Set %s' % data)

print ("Now create internet gateway")

alpha = client.create_internet_gateway(
    DryRun=False
)
print(alpha['InternetGateway']['InternetGatewayId'])
Ig_idn = alpha['InternetGateway']['InternetGatewayId']
print ('Now attaching internet gateway with vpc')
response = client.attach_internet_gateway(
    DryRun= False,
    InternetGatewayId= Ig_idn,
    VpcId= Vpc_id,
)

print ("Now creating Public subnet")
response_sub = client.create_subnet(
           CidrBlock='10.0.0.0/20',
        VpcId=Vpc_id,
    DryRun=False
)

response_subnet= response_sub['Subnet']['SubnetId']
print (response_subnet)
response_sub_pub = client.create_tags(
    DryRun=False,
    Resources=[
        response_subnet
    ],
    Tags=[
        {
            'Key': 'kfc_pub',
            'Value': 'pub',
        },
    ]
)

print ("Now creating Private subnet")
response_sub = client.create_subnet(
           CidrBlock='10.0.16.0/20',
        VpcId=Vpc_id,
    DryRun=False
)

response_subnet_private= response_sub['Subnet']['SubnetId']
print (response_subnet_private)
response_sub_pub = client.create_tags(
    DryRun=False,
    Resources=[
        response_subnet_private
    ],
    Tags=[
        {
            'Key': 'kfc_pri',
            'Value': 'pri',
        },
    ]
)
print("Now finding Main route_table")
route_alpha = client.describe_route_tables()
print(route_alpha['RouteTables'][0]['RouteTableId'])
route_table_main= route_alpha['RouteTables'][0]['RouteTableId']
#print(route_table_main)

print ("Now creating the route-table")

response_rt = client.create_route_table(
    DryRun= False,
    VpcId=Vpc_id,
     )
response_rt_id= response_rt['RouteTable']['RouteTableId']
print (response_rt_id)
response = client.associate_route_table(
    DryRun= False,
    RouteTableId=response_rt_id,
    SubnetId=response_subnet_private
)

response_sub_pub = client.create_tags(
    DryRun=False,
    Resources=[
        route_table_main
    ],
    Tags=[
        {
            'Key': 'kfc_pub_rt',
            'Value': 'pub_rt',
        },
    ]
)

#print (response_rt_id)
response_cr = client.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    DryRun= False,
     GatewayId=Ig_idn ,
    RouteTableId= route_table_main,

)
response = client.associate_route_table(
    DryRun= False,
    RouteTableId=route_table_main,
    SubnetId=response_subnet
)

print ("Now creating the instance in public subnet")

instance = ec2.create_instances(
    ImageId = 'ami-0de53d8956e8dcf80',
    MinCount = 1,
    MaxCount = 1,
    InstanceType = 't2.micro',
    SubnetId = response_subnet ,
    SecurityGroupIds = [sec_group_id] ,
    KeyName = 'kfc',
    UserData = test_script,
)
print(instance[0].id)
web_server = instance[0].id
print("Now elistic ip address")

response_el_Ip = client.allocate_address(
    Domain=Vpc_id,
)

#print(response_el_Ip)
elistic_Ip = (response_el_Ip['PublicIp'])
elistic_allocationId= (response_el_Ip['AllocationId'])
print ( elistic_Ip)
print (elistic_allocationId)

for instance in instance:
 print("Waiting until running...")
 instance.wait_until_running()
 instance.reload()
 print((instance.id, instance.state, instance.public_dns_name,
instance.public_ip_address))

response_ass_Ip = client.associate_address(
#    AllocationId= 'eipalloc-0d610d12d652ee923',
    PublicIp= elistic_Ip,
    DryRun= False,
    InstanceId=web_server,
)

print (response_ass_Ip)

response_cr = client.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    DryRun= False,
     InstanceId= web_server,
    RouteTableId= response_rt_id,

)

print ("Now creating the instance in private subnet")

instance = ec2.create_instances(
    ImageId = 'ami-0de53d8956e8dcf80',
    MinCount = 1,
    MaxCount = 1,
    InstanceType = 't2.micro',
    SubnetId = response_subnet_private ,
    SecurityGroupIds = [sec_group_id] ,
    KeyName = 'kfc',

)
print(instance[0].id)
