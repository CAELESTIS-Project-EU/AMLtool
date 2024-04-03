# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 14:24:06 2024

@author: SMO
When launched, the workflow information is read from an AutmationML file.
If ADDPATH is in the workflow definition, a request is sent to them with the
required information to launch their simulations. (ADDPATH communication is TBD)
When finished, HPC is requested to launch the rest of the workflow.

"""

#%% required modules
from pyautomationml import PyAutomationML
import subprocess
import sys

#%% functions
class HTPorchestrator():
    def __init__(self, AMLfile):
        #Read AML file and extract selected workflow
        AMLojb = PyAutomationML(AMLfile)
        WorkflowIE = AMLojb.root.find("./*[@Name='Workflow']")
        WorkflowDefinitionIE = WorkflowIE.find("./*[@Name='Workflow_definition']")
        self.selected_workflow = HTPorchestrator.get_attribute_from_AML_element(self, WorkflowDefinitionIE, 'Sequence', 'Simulations')
        
    def launch_curl_request(self):
        # curl command definition
        curl_command = [
            "curl",
            "-X", "POST",
            "-H", "Authorization: Token XXXXX",
            "-H", "MachineChoice: bsce81722@nord1.bsc.es",
            "-H", "SecToken: YYYYY",
            "-H", "Content-Type: multipart/form-data",
            "-F", "numNodes=1",
            "-F", "name_sim=remote_test",
            "-F", "execTime=20",
            "-F", "qos=cc_cs",
            "-F", "branch=main",
            "-F", "document=@C:\\Users\\SMO\\Template.aml",
            "https://caelestis.bsc.es/simulations/"
            ]

        completed_process = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Get the stdout and stderr
        stdout = completed_process.stdout.decode('utf-8')
        stderr = completed_process.stderr.decode('utf-8')
        
        print("Standard Output:")
        print(stdout)
        print("\nStandard Error:")
        print(stderr)
    
    def get_attribute_from_AML_element(self, AML, attribute_name, InternalElement_name):
        def find_element_by_name(InternalElement, InternalElement_name):
            if InternalElement.attrib.get('Name') == InternalElement_name:
                return InternalElement
            else:
                for child in InternalElement.iterchildren():
                    found_element = find_element_by_name(child, InternalElement_name)
                    if found_element is not None:
                        return found_element
            return None
        # Find the element with the specified name within the AML tree
        InternalElement = find_element_by_name(AML, InternalElement_name)
        # If InternalElement is found, get the attribute value
        if InternalElement is not None:
            for atribute in InternalElement.iterchildren():
                if atribute.__element__.attrib['Name'] == attribute_name:
                    attribute_value = atribute.text()
                    return attribute_value
        
        # If InternalElement is not found, return None
        return None
    
def main():
    if len(sys.argv) != 2:
        print("Usage: python AMLorchestrator.py workflow_file.aml")
        
    wfile = sys.argv[1]
    HTPo = HTPorchestrator(wfile)

    ADDPATH_ID = 'ADD'
    #%% call ADDPATH in case
    if ADDPATH_ID in HTPo.selected_workflow:
        #call ADDPATH
        print('ADDPATH communication under testing')
    #%% call HPC
    HTPo.launch_curl_request()
            
# #%% start application
if __name__ == "__main__":
    main()

    