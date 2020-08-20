import boto3
regions = {
            'us-east-1':'US East (N. Virginia)',
            #'us-east-2':'US East (Ohio)',
            #'us-west-1':'US West (N. California)',
            #'us-west-2':'US West (Oregon)',
            #'ca-central-1':'Canada (Central)',
            #'ap-south-1':'Asia Pacific (Mumbai)',
            #'ap-northeast-2':'Asia Pacific (Seoul)',
            #'ap-southeast-1':'Asia Pacific (Singapore)',
            #'ap-southeast-2':'Asia Pacific (Sydney)',
            #'ap-northeast-1':'Asia Pacific (Tokyo)',
            #'eu-central-1':'EU (Frankfurt)',
            #'eu-west-1':'EU (Ireland)',
            #'eu-west-2':'EU (London)',
            #'sa-east-1':'South America (Sao Paulo)'
        }

def ApplyAllEc2tag(aws_client, instanceid, resourceid):
    ec2 = aws_client.describe_instances(InstanceIds=[instanceid])
    instances = ec2['Reservations'][0]['Instances'][0]
    tags = instances['Tags']
    for tag in tags:
        ec2 = aws_client.describe_volumes(VolumeIds=[resourceid])
        ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':tag['Key'],'Value':tag['Value']}])
        
# EC2 LookUp Tags and apply to EBS volumes
def EC2TagLookup(aws_client, instanceid, resourceid):
    ec2 = aws_client.describe_instances(InstanceIds=[instanceid])
    instances = ec2['Reservations'][0]['Instances'][0]
    if 'Tags' in instances:
        tags = instances['Tags']
        local_tag_appname = local_tag_costcenter = local_tag_env = local_tag_projectid = local_tag_name = "N/A"
        for tag in tags:
            if tag['Key'] == "Application-Name":
                local_tag_appname = tag['Value']
            if tag['Key'] == "Cost-Center":
                local_tag_costcenter = tag['Value']
            if tag['Key'] == "Environment":
                local_tag_env = tag['Value']
            if tag['Key'] == "Name":
                local_tag_name = tag['Value']
            if tag['Key'] == "Project-ID":
                local_tag_projectid = tag['Value']
        return  local_tag_appname, local_tag_costcenter, local_tag_env, local_tag_projectid, local_tag_name, tag
    else:
        print "No Tags for Instances"
        local_tag_appname = local_tag_costcenter = local_tag_env = local_tag_projectid = local_tag_name = "N/A"
        return  local_tag_appname, local_tag_costcenter, local_tag_env, local_tag_projectid, local_tag_name


# Applying Default Tags evenif not present in EC2
def ApplyDefaultTag(aws_client, resourceid, appname, costcenter, env, instanceid, mountpoint, projectid):
    ec2 = aws_client.describe_volumes(VolumeIds=[resourceid])
    print "Checking for volume tags on %s" %resourceid
    vol = ec2['Volumes'][0]
    if 'Tags' in vol:
        tags = vol['Tags']
        print "%s" %tags
        #local_tag_volappname = local_tag_volcostcenter = local_tag_volenv = local_tag_volprojectid = local_tag_volname = "N/A"
        for tag in tags:
            if (tag['Key'] == "Application-Name" and len(tag['Value']) != 0):
                local_tag_volappname = tag['Value']
                print "Tag Application-Name already exist %s" % local_tag_volappname
            else:
                ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':'Application-Name','Value':appname}])
            if (tag['Key'] == "Cost-Center" and len(tag['Value']) != 0):
                local_tag_volcostcenter = tag['Value']
                print "Tag Cost-Center already exist %s" % local_tag_volcostcenter
            else:
                ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':'Cost-Center','Value':costcenter}])
            if (tag['Key'] == "Environment" and len(tag['Value']) != 0):
                local_tag_volenv = tag['Value']
                print "Tag Environment already exist %s" % local_tag_volenv

            else:
                ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':'Environment','Value':env}])
            if (tag['Key'] == "Project-ID" and len(tag['Value']) != 0):
                local_tag_volprojectid = tag['Value']
                print "Tag Project-ID already exist %s" % local_tag_volprojectid

            else:
                ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':'Project-ID','Value':projectid}])
            if (tag['Key'] == "Name" and len(tag['Value']) != 0):
                local_tag_volname = tag['Value']
                print "Tag Name already exist %s" % local_tag_volname

            else:
                ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':'Name','Value': instanceid + "_" + mountpoint}])

    else:
        print "No Tags for volume %s" % resourceid
        ec2 = aws_client.create_tags(Resources=[resourceid], Tags=[{'Key':'Application-Name','Value':appname},{'Key':'Cost-Center','Value':costcenter},{'Key':'Project-ID','Value':projectid},{'Key':'Environment','Value':env},{'Key':'Name','Value': instanceid + "_" + mountpoint},{'Key':'Project-ID','Value':projectid}])
def create_aws_client(key):
    client = boto3.client('ec2',region_name = key)
    return client

def ebs_tag_rule(aws_client, aws_region_name):
    print "Volume Tagging Check in Region: " + aws_region_name
    responses = aws_client.describe_volumes()
    volumes = responses['Volumes']
#Iterate through the volumes
    for volume in volumes:
            attachments = volume['Attachments']
            for attachemntAttrib in attachments:
                    if attachemntAttrib['State'] == 'attached':
                        local_volumeid = volume['VolumeId']
                        print "Working on %s" % local_volumeid
                        local_is_volumeattached = True
                        local_instanceid = attachemntAttrib['InstanceId']
                        local_mount_point = attachemntAttrib['Device']
                        appname,costcenter,env,projectid,instancename,tag = EC2TagLookup(aws_client, local_instanceid, local_volumeid)
                        print "Applying Tags to " + local_volumeid
                        ApplyDefaultTag(aws_client,local_volumeid,appname,costcenter,env,instancename,local_mount_point,projectid)
                        ApplyAllEc2tag(aws_client, local_instanceid, local_volumeid)
                    else:
                        local_is_volumeattached = False
            local_is_tags = False

    return

def lambda_handler(event, context):
    for key, value in regions.iteritems():
        aws_client = create_aws_client(key)
        ebs_tag_rule(aws_client, value)
    return "Completed"
