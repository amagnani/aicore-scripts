
import argparse
import sys
import json
import re
from collections import OrderedDict

from ai_api_client_sdk import ai_api_v2_client
from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client

resource_dict = {
   'application': 
                     {'resource_name': 'application_name', 
                        'path': '/admin/applications'
                     },
   'resourceGroup': 
                     {'resource_name': 'resource_group_id', 
                        'path': '/admin/resourceGroups'
                     },
   'dockerRegistry': 
                     {'resource_name': 'name', 
                        'path': '/admin/dockerRegistrySecrets'
                     }
} 

def create_client(aicore_service_key):
   # Read AI Core Service Key and create an AI Core API Client 
   try:
      # Load the service key file
      with open(aicore_service_key) as ask:
         service_key = json.load(ask)
      # Creating an AI API client instance
      ai_api_client = AIAPIV2Client( 
         base_url = service_key["serviceurls"]["AI_API_URL"] + "/v2", 
         auth_url=  service_key["url"] + "/oauth/token",
         client_id = service_key['clientid'],
         client_secret = service_key['clientsecret']
      )
      return ai_api_client
   except FileNotFoundError:
      print ("{aicore_service_key} Does not exists")
      return
   except json.JSONDecodeError:
      print ("aicore_service_key must be in JSON format ")
      return
      

def delete_resource(ai_api_client,resource, resource_name):
   path = resource_dict[resource]['path']+'/'+resource_name
   print (path)
   try:
      ai_api_client.rest_client.delete(
         path=path,
      )
      print ("{} {} has been deleted".format(resource,resource_name))
   except:
      print ("{} {} could not be deleted".format(resource, resource_name))   
   return

def make_lists(response, resource, keep, delete):
   
   to_delete=[]
   to_keep=[]
   
   if delete:
      to_delete = [r[resource_dict[resource]['resource_name']] for r in response if re.search(delete,r[resource_dict[resource]['resource_name']] ) ]
      to_keep = [r[resource_dict[resource]['resource_name']]  for r in response if not re.search(delete,r[resource_dict[resource]['resource_name']] ) ]
   elif keep:
      to_delete = [r[resource_dict[resource]['resource_name']]  for r in response if not re.search(keep,r[resource_dict[resource]['resource_name']] ) ]
      to_keep = [r[resource_dict[resource]['resource_name']]  for r in response if re.search(keep,r[resource_dict[resource]['resource_name']] )]
   else:
      to_delete=[r[resource_dict[resource]['resource_name']]  for r in response]

   print ("{}  will be saved \n {}".format(len(to_keep), to_keep))
   print ("{}  will be deleted \n {}".format(len(to_delete), to_delete))

   if handshake():
      return to_delete
   else:
      return False

def handshake():
   user_input = input('Are you sure you want to delete these resources? [Y/N] ')      
   # input validation  
   if user_input.lower() in ('y', 'yes'):
      return True
   else:
      return False


def clean_resources( ai_api_client, resource, keep, delete ):    
   
   # Grab list of resources
   response = ai_api_client.rest_client.get( path = resource_dict[resource]['path'])
   
   #Get list of resources to be deleted
   print ("\n Scanning {}s  ".format(resource))
   to_delete = make_lists( response["resources"],resource, keep, delete)

   #Delete resources
   if to_delete:
      for r in to_delete:
         delete_resource( ai_api_client, resource, r)
   return 

def main(argv):

   parser = argparse.ArgumentParser(description='Clear an SAP AI Core tenant.')
   parser.add_argument('aicore_service_key', metavar='key', type=str, 
                       help='AI Core tenant service key in json format')
   parser.add_argument('--resource', nargs='*', 
                        default=['application','resourceGroup','dockerRegistry'], 
                        choices=['application','resourceGroup','dockerRegistry'],
                        help='Resources to be deleted')
   group = parser.add_mutually_exclusive_group()
   group.add_argument('--delete', metavar='delete', type=str, 
                       help='regex expression. Resources whose name contains this expression will be deleted')
   group.add_argument('--keep', metavar='keep', type=str, 
                       help='regex expression. Resources whose name contains this expression will not be deleted')
 
   args = parser.parse_args()
   
   # Create AI API Client
   ai_api_client=create_client(args.aicore_service_key)

   #Clean Resources:
   for resource in args.resource:
      clean_resources(ai_api_client, resource, args.keep, args.delete )
   


if __name__ == "__main__":
   main(sys.argv[1:])