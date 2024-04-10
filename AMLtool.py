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
import datetime

class AML_GUI_App:
    def __init__(self, root):
        self.root = root
        self.root.title("AutomationML tool")

        # parse configuration file
        self.mainfolder = os.getcwd()
        Configfolder = os.path.join(self.mainfolder, "src")
        Config_txt_file_name = 'Config.json'
        config_file_path = os.path.join(Configfolder, Config_txt_file_name)
        self.parse_config_file(config_file_path)

        self.AML_master_path = os.path.join(self.mainfolder, self.automationml_files_folder, self.master_file_name)
        self.AutomationMLtemplate_path = os.path.join(self.mainfolder, self.automationml_files_folder, self.template_file_name)
        self.W_IDs_txt_path = os.path.join(self.mainfolder, self.sources_file, self.W_IDs_txt_file_name)
        self.PathOfDoE = 'Not DoE selected' # Default value
        self.workflow_column_name = "Workflow Options" # Name to be shown on the App
        self.outputs_name = "Output Options" # Name to be shown on the App
        self.selections = {self.workflow_column_name: None, self.outputs_name: []}
        
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
        self.Software_Parameters_OutputFile_name = 'output_file'

        # Create the titles, bottons, etc.
        self.create_widgets()

    # Read configuration file and store information in internal variables
    # strings are to be modified in the script and in the config file with the same string characters
    def parse_config_file(self, config_file_path):
        with open(config_file_path, "r") as json_file:
            data = json.load(json_file)
            self.master_file_name = data['master_file_name']
            self.template_file_name = data['template_file_name']
            self.Workflow_options = data['Workflow_options']
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

    def add_attribute_on_AML_element(self, Internal_Element_obj, attribute_name):
        new_attribute = etree.Element("Attribute", Name=attribute_name, AttributeDataType="xs:string")
        Internal_Element_obj.append(new_attribute)

        
    def get_value_AML_element(self, AML, InternalElement, attribute_name):
        IE = AML.root.find(".//*[@Name={}]".format(InternalElement))
        Atrbt = IE.find(".//*[@Name={}]".format(attribute_name))
        value = Atrbt.__element__.Value
        return value
    
    def get_max_value_AML_workflow(self,AML, InternalElement):
        IE = AML.find(f"./*[@Name='{InternalElement}']")
        max_value = 0
        for atribute in IE.iterchildren():
            value = int(atribute.__element__.attrib['Name'].replace("w", ""))
            if value > max_value:
                max_value = value
        return max_value

    def find_all_children_by_name(self, element, name, matching_elements=None):
        if matching_elements is None:
            matching_elements = []
    
        if element.get('Name') == name:
            matching_elements.append(element)
    
        for child in element.iterchildren():
            self.find_all_children_by_name(child, name, matching_elements)
    
        return matching_elements

    def write_value_on_AML_attribute(self, InternalElementObj, attribute_name, value):
        Atrbt = InternalElementObj.find(f"./*[@Name='{attribute_name}']")
        Atrbt.__element__.Value = value

    def write_ID_w_on_txt(self, W_IDs_txt_path, value):
        with open(W_IDs_txt_path, 'a') as f:
            f.write(str(value) + '\n')
            
    def create_widgets(self):
        #Select DoE
        self.frame_Select_DoE = tk.Frame(self.root)
        self.frame_Select_DoE.grid(row=0, column=0, padx=10, pady=5, sticky="n")
        self.select_DoE_button = tk.Button(self.frame_Select_DoE, text="Select DoE", command=self.select_DoE)
        self.select_DoE_button.pack()

        #Select Workflow
        self.workflow_frame = tk.Frame(self.root)
        self.workflow_frame.grid(row=0, column=1, padx=10, pady=5, sticky="n")
        self.workflow_label = tk.Label(self.workflow_frame, text=self.workflow_column_name)
        self.workflow_label.pack()
        self.show_radio_buttons(self.Workflow_options, self.workflow_frame, self.workflow_column_name)

        #Select Outputs
        self.outputs_frame = tk.Frame(self.root)
        self.outputs_frame.grid(row=0, column=2, padx=10, pady=5, sticky="n")
        self.outputs_label = tk.Label(self.outputs_frame, text=self.outputs_name)
        self.outputs_label.pack()
        self.show_checkboxes(self.output_options, self.outputs_frame, self.outputs_name)

        #Save
        self.save_AML_button = tk.Button(self.root, text="Save to AutomationML", command=self.save_AML)
        self.save_AML_button.grid(row=1, columnspan=2, padx=10, pady=10, sticky="e")

    def select_DoE(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    csv_reader = csv.reader(file)
                    data = [next(csv_reader) for _ in range(3)]
                    print(data)  # Update WW with the data or do other processing

                # Save the path of the DoE file
                self.PathOfDoE = file_path
                print("DoE Path:", self.PathOfDoE)

            except Exception as e:
                print("Error reading CSV file:", e)

    def show_radio_buttons(self, options, frame, set_name):
        var = tk.StringVar()
        for option in options:
            radio_button = tk.Radiobutton(
                frame, text=option, variable=var, value=option
            )
            radio_button.pack(anchor="w", padx=5, pady=2)
        self.selections[set_name] = var

    def show_checkboxes(self, options, frame, set_name):
        for option in options:
            var = tk.StringVar(value="")
            checkbox = tk.Checkbutton(
                frame, text=option, variable=var, onvalue=option, offvalue=""
            )
            checkbox.pack(anchor="w", padx=5, pady=2)
            self.selections[set_name].append(var)

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
        new_workflow_number = value + 1
        print(f'New workflow ID is {new_workflow_number}')

        # write ID number on txt file (keep an extra copy of the information to avoid misuse)
        self.write_ID_w_on_txt(self.W_IDs_txt_path, new_workflow_number)

        # Set AML ID name like 'w + ID number + .aml' 
        self.workflow_instance_name = 'w' + str(new_workflow_number)
        print(f'New workflow name is {self.workflow_instance_name}')
        self.template_instance_name = 'w' + str(new_workflow_number) + '.aml'
        print(f'New workflow file name is {self.template_instance_name}')
        self.template_instance_path = os.path.join(self.automationml_files_folder, self.template_instance_name)

        # write ID on master file as an attribute in Workflows IE and as an element
        WorkflowsObj = self.master.find(f"./*[@Name='{self.Master_WorkflowsIE_name}']")
        self.add_attribute_on_AML_element(WorkflowsObj, self.workflow_instance_name)
        self.create_AML_element(WorkflowsObj, self.workflow_instance_name)
        Workflow_instance_Obj = WorkflowsObj.find(f".//{{http://www.dke.de/CAEX}}InternalElement[@Name='{self.workflow_instance_name}']")
        self.add_attribute_on_AML_element(Workflow_instance_Obj, 'path')
        
        # write selected workflow type in AutomationML template on information IE on the text of the existing attribute 'Sequence_type' 
        InformationIE = self.workflow_instance.find(f"./*[@Name='{self.Workflow_InformationIE_name}']")
        self.write_value_on_AML_attribute(InformationIE, 'ID', self.workflow_instance_name)
        self.write_value_on_AML_attribute(InformationIE, self.Information_Sequence_type_name, self.selections[self.workflow_column_name].get())
        current_date = datetime.date.today()
        formatted_date = current_date.strftime("%Y/%m/%d")
        self.write_value_on_AML_attribute(InformationIE,'Date', str(formatted_date))
        
        Info_OutputsIE = InformationIE.find("./*[@Name='Outputs']")
        selected_output_options = [var.get() for var in self.selections[self.outputs_name]]
        self.filtered_selected_output_options = [item for item in selected_output_options if item.strip() != ""]
        for output_element in self.filtered_selected_output_options:
            self.create_AML_element(Info_OutputsIE, output_element)
        
        # write selected workflow information in AutomationML template on Workflow Definition for execution
        
        # write phases when they exist
        Workflow_DefinitionIE = self.workflow_instance.find(f"./*[@Name='{self.Workflow_DefinitionIE_name}']")
        PhasesIE = Workflow_DefinitionIE.find(f"./*[@Name='{self.PhasesIE_name}']")
        # extract the models:
        Selected_Workflow_Simulations = self.Predefined_workflows[self.selections[self.workflow_column_name].get()]
        Preprocess_models = [element for element in self.Models["Preprocess"] if element in Selected_Workflow_Simulations]
        Simulation_models = [element for element in self.Models["Simulation"] if element in Selected_Workflow_Simulations]
        Postprocess_models = [element for element in self.Models["Postprocess"] if element in Selected_Workflow_Simulations]
        # 1a. Preprocess
        Bool_Preproc_models = any(element in self.Models["Preprocess"] for element in self.Predefined_workflows[self.selections[self.workflow_column_name].get()])
        if Bool_Preproc_models:
            self.create_AML_element(PhasesIE, 'Preprocess')
            PreprocessIE = PhasesIE.find("./*[@Name='Preprocess']")
            #create chain of charaters for HPC:
            chain_string = ""
            for element in Preprocess_models:
                chain_string += f'{element}.run>>'
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
                self.write_value_on_AML_attribute(ElementIE, self.Software_softwareID_name, element)
                #add Parameters IE
                self.create_AML_element(ElementIE, 'Parameters')
                #get Parameters IE
                ParametersIE = ElementIE.find("./*[@Name='Parameters']")
                #add output_file atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_OutputFile_name)
        else:
            print("No preprocess")

        # 1b. Preprocess
        Bool_Sim_models = any(element in self.Models["Simulation"] for element in self.Predefined_workflows[self.selections[self.workflow_column_name].get()])
        if Bool_Sim_models:
            self.create_AML_element(PhasesIE, 'Simulations')
            SimulationsIE = PhasesIE.find("./*[@Name='Simulations']")
            #create chain of charaters for HPC:
            chain_string = ""
            for element in Simulation_models:
                chain_string += f'{element}.run>>'
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
                self.write_value_on_AML_attribute(ElementIE, self.Software_softwareID_name, element)
                #add Parameters IE
                self.create_AML_element(ElementIE, 'Parameters')
                #get Parameters IE
                ParametersIE = ElementIE.find("./*[@Name='Parameters']")
                #add values atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_values_name)
                self.write_value_on_AML_attribute(ParametersIE, 'values', '{doe_row}')
                #add output_file atribute to Parameters IE
                self.add_attribute_on_AML_element(ParametersIE, self.Software_Parameters_OutputFile_name)
                value_field = '{results_folder}/' + element + '_{line_number}.out'
                self.write_value_on_AML_attribute(ParametersIE, self.Software_Parameters_OutputFile_name, value_field)
                if idx > 0:
                    #add inputs_file atribute to Parameters IE
                    self.add_attribute_on_AML_element(ParametersIE, 'input_file')
                    value_field = '{results_folder}/' + Simulation_models[idx-1] + '_{line_number}.out'
                    self.write_value_on_AML_attribute(ParametersIE, 'input_file', value_field)
                    
        else:
            print("No simulations")

        # 1c. Postprocess
        Bool_Postproc_models = any(element in self.Models["Postprocess"] for element in self.Predefined_workflows[self.selections[self.workflow_column_name].get()])
        if Bool_Postproc_models:
            self.create_AML_element(PhasesIE, 'Postprocess')
            PostprocessIE = PhasesIE.find("./*[@Name='Postprocess']")
            #create chain of charaters for HPC:
            chain_string = ""
            for element in Postprocess_models:
                chain_string += f'{element}.run>>'
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
                self.write_value_on_AML_attribute(ElementIE, self.Software_softwareID_name, element)
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
        self.write_value_on_AML_attribute(DoEIE, 'source', self.PathOfDoE)
        #write destination?
        
        # write outputs in Workflow_definition
        OutputsIE = Workflow_DefinitionIE.find(f"./*[@Name='{self.OutputsIE_name}']")
        for output_element in self.filtered_selected_output_options:
            self.add_attribute_on_AML_element(OutputsIE, output_element)
        
        # save all modifications
        roottemplate.save(self.template_instance_path)
        rootmaster.save(self.AML_master_path)

    def save_AML(self):
        selected_output_options = [var.get() for var in self.selections[self.outputs_name]]
        self.filtered_selected_output_options = [item for item in selected_output_options if item.strip() != ""]

        self.write_on_AML()

        print('Data has been saved to the instance AutomationML file: {}'.format(self.template_instance_path))
        print('Data has been saved to the master AutomationML file: {}'.format(self.AML_master_path))

if __name__ == "__main__":
    root = tk.Tk()
    app = AML_GUI_App(root)
    root.mainloop()


