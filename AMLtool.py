# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 10:07:20 2024

@author: SMO
"""

'''
Santiago Montagud
ESI Group
'''

import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from pyautomationml import PyAutomationML
from pyautomationml import AmlElement
from pyautomationml import Element
from lxml import etree
import csv
import os
import json
from datetime import datetime, date

class Config_parser():
    def __init__(self):
        # parse configuration file
        self.mainfolder = os.getcwd()
        Configfolder = os.path.join(self.mainfolder, "src")
        Config_txt_file_name = 'Config.json'
        config_file_path = os.path.join(Configfolder, Config_txt_file_name)
        self.parse_config_file(config_file_path)

    # Get data from config file:
    def get_predifined_workflows(self):
        return self.Predefined_workflows
    
    def get_possible_outputs(self):
        return self.output_options

    # Read configuration file and store information in internal variables
    # strings are to be modified in the script and in the config file with the same string characters
    def parse_config_file(self, config_file_path):
        with open(config_file_path, "r") as json_file:
            data = json.load(json_file)
            self.output_options = data['output_options']
            self.Predefined_workflows = data['Predefined_workflows']
            

class AML_App():
    def __init__(self, PathOfDoE, Selected_Workflow_Simulations, selected_output_options):
        # parse configuration file
        self.mainfolder = os.getcwd()
        Configfolder = os.path.join(self.mainfolder, "src")
        Config_txt_file_name = 'Config.json'
        config_file_path = os.path.join(Configfolder, Config_txt_file_name)
        self.parse_config_file(config_file_path)

        self.AML_master_path = os.path.join(self.mainfolder, self.automationml_files_folder, self.master_file_name)
        self.AutomationMLtemplate_path = os.path.join(self.mainfolder, self.automationml_files_folder, self.template_file_name)
        self.W_IDs_txt_path = os.path.join(self.mainfolder, self.sources_file, self.W_IDs_txt_file_name)
        self.workflow_column_name = "Workflow Options" # Name to be shown on the App
        self.outputs_name = "Output Options" # Name to be shown on the App
        self.selections = {self.workflow_column_name: None, self.outputs_name: []}
        
        # user inputs
        self.PathOfDoE = PathOfDoE
        self.selected_output_options = selected_output_options
        self.Selected_Workflow_Simulations = Selected_Workflow_Simulations
        self.selections[self.workflow_column_name] = Selected_Workflow_Simulations
        
        #Names of Internal Elements
        self.Master_WorkflowsIE_name = 'Workflows' # Interal element where the IDs of the workflows are stored to avoid repetition of IDs
        self.Workflow_InformationIE_name = 'Information'
        self.Workflow_DefinitionIE_name = 'Workflow_definition'
        self.Information_Sequence_type_name = 'Sequence_type'
        self.InputsIE_name = 'Inputs'
        self.DoEIE_name = 'DoE'
        self.OutputsIE_name = 'Outputs'
        self.PhasesIE_name = 'Phases'
        self.Software_softwareID_name = 'software_ID'
        self.Software_Parameters_values_name = 'values'
        self.Software_Parameters_OutputFile_name = 'outputs_folder'

    # Read configuration file and store information in internal variables
    # strings are to be modified in the script and in the config file with the same string characters
    def parse_config_file(self, config_file_path):
        with open(config_file_path, "r") as json_file:
            data = json.load(json_file)
            self.master_file_name = data['master_file_name']
            self.template_file_name = data['template_file_name']
            self.ftp_destination_main_folder = data['ftp_destination_main_folder']
            self.output_options = data['output_options']
            self.W_IDs_txt_file_name = data['W_IDs_txt_file_name']
            self.automationml_files_folder = data['automationml_files_folder']
            self.sources_file = data['sources_file']
            self.Predefined_workflows = data['Predefined_workflows']
            self.Models = data['Models']

    def create_AML_element(self, parent, Name, text=None):
        # default:
        context_global = {}
        context_local = {}
        # Define the tag, attributes, and text for the new element
        tag = "{http://www.dke.de/CAEX}InternalElement"
        attribute = {"Name": Name}
        new_aml_element = Element(tag, attrib=attribute, text=text, context_global=context_global, context_local=context_local)
        parent.append(new_aml_element.__element__)
        return new_aml_element

    def add_attribute_on_AML_element(self, Internal_Element_obj, attribute_name):
        new_attribute = etree.Element("Attribute", Name=attribute_name, AttributeDataType="xs:string")
        Internal_Element_obj.append(new_attribute)
    
    def get_max_value_AML_workflow(self,AML, InternalElement):
        IE = AML.find(f"./*[@Name='{InternalElement}']")
        max_value = 0
        for child in IE.iterchildren():
            if child.tag.endswith('Attribute'):
                value = int(child.__element__.attrib['Name'].replace("w", ""))
                if value > max_value:
                    max_value = value
        return max_value

    def write_value_on_AML_attribute(self, InternalElementObj, attribute_name, value):
        Atrbt = InternalElementObj.find(f"./*[@Name='{attribute_name}']")
        Atrbt.__element__.Value = value

    def write_ID_w_on_txt(self, W_IDs_txt_path, value):
        with open(W_IDs_txt_path, 'a') as f:
            f.write(str(value) + '\n')

    def date_time_to_integer(self):
        now = datetime.now()
        formatted_date_time = now.strftime("%Y%m%d%H%M%S")
        integer_representation = int(formatted_date_time)
    
        return integer_representation

    def write_on_AML(self):
        rootmaster = PyAutomationML(self.AML_master_path)

        if os.path.exists(self.AutomationMLtemplate_path):
            roottemplate = PyAutomationML(self.AutomationMLtemplate_path)
        else:
            print(f"The path '{self.AutomationMLtemplate_path}' does not exist.")

        # Get the root of the master file
        self.master = rootmaster.root.find("./*[@Name='Workflow']")

        # Get the root of the AutomationML template
        self.workflow_instance = roottemplate.root.find("./*[@Name='Workflow']")

        # get workflow last value
        value = self.get_max_value_AML_workflow(self.master, self.Master_WorkflowsIE_name)
        print(f'Old workflow ID is {value}')
        self.new_workflow_number = int(value) + 1
        self.new_workflow_ID = 'w' + str(value + 1) + '_' + str(self.date_time_to_integer())
        print(f'New workflow number is {self.new_workflow_number}')

        # write ID number on txt file (keep an extra copy of the information to avoid misuse)
        self.write_ID_w_on_txt(self.W_IDs_txt_path, str(self.new_workflow_number))

        # Set AML ID name as 'w + ID number + .aml' 
        self.template_instance_name = str(self.new_workflow_ID) + '.aml'
        print(f'New workflow file name is {self.template_instance_name}')
        self.template_instance_path = os.path.join(self.automationml_files_folder, self.template_instance_name)

        # write number on master file as an attribute in Workflows IE
        WorkflowsObj = self.master.find(f"./*[@Name='{self.Master_WorkflowsIE_name}']")
        self.add_attribute_on_AML_element(WorkflowsObj, str(self.new_workflow_number))

        # write workflow ID on master file as an element
        self.create_AML_element(WorkflowsObj, self.new_workflow_ID)
        Workflow_instance_Obj = WorkflowsObj.find(f".//{{http://www.dke.de/CAEX}}InternalElement[@Name='{self.new_workflow_ID}']")
        self.add_attribute_on_AML_element(Workflow_instance_Obj, 'path')
        self.ftp_destination_workflow_folder = os.path.join(self.ftp_destination_main_folder, self.new_workflow_ID)
        self.write_value_on_AML_attribute(Workflow_instance_Obj, 'path', os.path.normpath(self.ftp_destination_workflow_folder))

        # write selected workflow type in AutomationML template on information IE on the text of the existing attribute 'Sequence_type' 
        InformationIE = self.workflow_instance.find(f"./*[@Name='{self.Workflow_InformationIE_name}']")
        self.write_value_on_AML_attribute(InformationIE, 'ID', self.new_workflow_ID)
        self.write_value_on_AML_attribute(InformationIE, self.Information_Sequence_type_name, self.selections[self.workflow_column_name])
        current_date = datetime.now().date()
        formatted_date = current_date.strftime("%Y/%m/%d")
        self.write_value_on_AML_attribute(InformationIE,'Date', str(formatted_date))

        Info_OutputsIE = InformationIE.find("./*[@Name='Outputs']")

        self.filtered_selected_output_options = [item for item in self.selected_output_options if item.strip() != ""]
        for output_element in self.filtered_selected_output_options:
            self.create_AML_element(Info_OutputsIE, output_element)
        
        # write selected workflow information in AutomationML template on Workflow Definition for execution
        
        # write phases when they exist
        Workflow_DefinitionIE = self.workflow_instance.find(f"./*[@Name='{self.Workflow_DefinitionIE_name}']")
        PhasesIE = Workflow_DefinitionIE.find(f"./*[@Name='{self.PhasesIE_name}']")
        # extract the models:
        Selected_Workflow_Simulations = self.Predefined_workflows[self.selections[self.workflow_column_name]]
        Preprocess_models = [element for element in self.Models["Preprocess"] if element in Selected_Workflow_Simulations]
        Simulation_models = [element for element in self.Models["Simulation"] if element in Selected_Workflow_Simulations]
        Postprocess_models = [element for element in self.Models["Postprocess"] if element in Selected_Workflow_Simulations]
        # 1a. Preprocess
        Bool_Preproc_models = any(element in self.Models["Preprocess"] for element in self.Predefined_workflows[self.selections[self.workflow_column_name]])
        if Bool_Preproc_models:
            PreprocessIE = self.create_AML_element(PhasesIE, 'Phase')
            self.add_attribute_on_AML_element(PreprocessIE, 'Name')
            self.write_value_on_AML_attribute(PreprocessIE, 'Name', 'Preprocess')
            
            #create chain of charaters for HPC:
            chain_string = ""
            for element in Preprocess_models:
                chain_string += f'{element}>>'
            chain_string = chain_string.rstrip('>>')
            #add attribute 'Sequence':
            self.add_attribute_on_AML_element(PreprocessIE, 'Sequence')
            #add chain to attribute 'Sequence'
            self.write_value_on_AML_attribute(PreprocessIE, 'Sequence', chain_string)
            #create the phase internal elements
            for element in Preprocess_models:
                self.create_AML_element(PreprocessIE, element)
                #get the element just created
                ElementIE = PreprocessIE.find(f"./*[@Name='{element}']")
                #add ID attribute
                self.add_attribute_on_AML_element(ElementIE, self.Software_softwareID_name)
                #fill in ID attribute
                self.write_value_on_AML_attribute(ElementIE, self.Software_softwareID_name, element + '.run')
                #add Parameters IE
                self.create_AML_element(ElementIE, 'Parameters')
                #get Parameters IE
                ParametersIE = ElementIE.find("./*[@Name='Parameters']")
                #add output_file atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_OutputFile_name)
        else:
            print("No preprocess")

        # 1b. Preprocess
        Bool_Sim_models = any(element in self.Models["Simulation"] for element in self.Predefined_workflows[self.selections[self.workflow_column_name]])
        if Bool_Sim_models:
            SimulationsIE = self.create_AML_element(PhasesIE, 'Phase')
            self.add_attribute_on_AML_element(SimulationsIE, 'Name')
            self.write_value_on_AML_attribute(SimulationsIE, 'Name', 'Simulation')
            #create chain of charaters for HPC:
            chain_string = ""
            for element in Simulation_models:
                chain_string += f'{element}>>'
            chain_string = chain_string.rstrip('>>')
            #add it to attribute 'Sequence':
            self.add_attribute_on_AML_element(SimulationsIE, 'Sequence')
            #add chain to attribute 'Sequence'
            self.write_value_on_AML_attribute(SimulationsIE, 'Sequence', chain_string)
            #create the phase internal elements
            idx = 0
            for idx,element in enumerate(Simulation_models):
                self.create_AML_element(SimulationsIE, element)
                #get the element just created
                ElementIE = SimulationsIE.find(f"./*[@Name='{element}']")
                #add ID attribute
                self.add_attribute_on_AML_element(ElementIE, self.Software_softwareID_name)
                #fill in ID attribute
                self.write_value_on_AML_attribute(ElementIE, self.Software_softwareID_name, element + '.run')
                #add Parameters IE
                self.create_AML_element(ElementIE, 'Parameters')
                #get Parameters IE
                ParametersIE = ElementIE.find("./*[@Name='Parameters']")
                #add values atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_values_name)
                self.write_value_on_AML_attribute(ParametersIE, 'values', '{variables.doe_row}')
                #add output_file atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_OutputFile_name)
                value_field = '{variables.results_folder}/{variables.line_number}/' + element
                self.write_value_on_AML_attribute(ParametersIE, self.Software_Parameters_OutputFile_name, value_field)
                if idx > 0:
                    #add inputs_file atribute to Parameters IE
                    self.add_attribute_on_AML_element(ParametersIE, 'inputs_folder')
                    value_field = '{variables.results_folder}/{variables.line_number}/' + Simulation_models[idx-1]
                    self.write_value_on_AML_attribute(ParametersIE, 'inputs_folder', value_field)
                    
        else:
            print("No simulations")

        # 1c. Postprocess
        Bool_Postproc_models = any(element in self.Models["Postprocess"] for element in self.Predefined_workflows[self.selections[self.workflow_column_name]])
        if Bool_Postproc_models:
            PostprocessIE = self.create_AML_element(PhasesIE, 'Phase')
            self.add_attribute_on_AML_element(PostprocessIE, 'Name')
            self.write_value_on_AML_attribute(PostprocessIE, 'Name', 'Postprocess')

            #create chain of charaters for HPC:
            chain_string = ""
            for element in Postprocess_models:
                chain_string += f'{element}>>'
            chain_string = chain_string.rstrip('>>')
            #add it to attribute 'Sequence':
            self.add_attribute_on_AML_element(PostprocessIE, 'Sequence')
            #add chain to attribute 'Sequence'
            self.write_value_on_AML_attribute(PostprocessIE, 'Sequence', chain_string)
            #create the phase internal elements
            for element in Postprocess_models:
                self.create_AML_element(PostprocessIE, element)
                #get the element just created
                ElementIE = PostprocessIE.find(f"./*[@Name='{element}']")
                #add ID attribute
                self.add_attribute_on_AML_element(ElementIE, self.Software_softwareID_name)
                #fill in ID attribute
                self.write_value_on_AML_attribute(ElementIE, self.Software_softwareID_name, element + '.run')
                #add Parameters IE
                self.create_AML_element(ElementIE, 'Parameters')
                #get Parameters IE
                ParametersIE = ElementIE.find("./*[@Name='Parameters']")
                #add output_file atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_OutputFile_name)
        else:
            print("No postprocess")
            
        # write inputs in Workflow_definition
        #find inputs IE
        InputsIE = Workflow_DefinitionIE.find(f"./*[@Name='{self.InputsIE_name}']")
        #find DoE
        DoEIE = InputsIE.find(f"./*[@Name='{self.DoEIE_name}']")
        #write DoE source in source attribute from the user's input
        self.write_value_on_AML_attribute(DoEIE, 'source', os.path.normpath(self.PathOfDoE))
        self.write_value_on_AML_attribute(DoEIE, 'destination', os.path.normpath(self.ftp_destination_workflow_folder))
        
        # write outputs in Workflow_definition
        OutputsIE = Workflow_DefinitionIE.find(f"./*[@Name='{self.OutputsIE_name}']")
        for output_element in self.filtered_selected_output_options:
            self.add_attribute_on_AML_element(OutputsIE, output_element)
        results_folderIE = OutputsIE.find("./*[@Name='results_folder']")
        self.write_value_on_AML_attribute(results_folderIE, 'destination', os.path.normpath(self.ftp_destination_workflow_folder))
        
        # save all modifications
        roottemplate.save(self.template_instance_path)
        rootmaster.save(self.AML_master_path)

    def save_AML(self):
        self.filtered_selected_output_options = [item for item in self.selected_output_options if item.strip() != ""]
        self.write_on_AML()

        print('Data has been saved to the instance AutomationML file: {}'.format(self.template_instance_path))
        print('Data has been saved to the master AutomationML file: {}'.format(self.AML_master_path))

if __name__ == "__main__":

    CP = Config_parser()
    
    # Get data from config file:
    Predefined_workflows = CP.get_predifined_workflows()
    output_options = CP.get_possible_outputs()
    
    pathofDOEprovidedbyBSCinterface= os.path.normpath(r'/.statelite/tmpfs/gpfs/projects/bsce81/esi/tests/2024_03_28_ML/001_Data\Doe_FormatExample.csv')
    outputsselectionfromBSCinterface = ["Resin_pressure_field", "Resin_velocity_field"]
    inputsfromBSCinterface = 'w2'
    
    # Update data in the template
    AML = AML_App(pathofDOEprovidedbyBSCinterface, inputsfromBSCinterface,outputsselectionfromBSCinterface)
    
    # Save data into a new AutomationMl file
    AML.save_AML()





