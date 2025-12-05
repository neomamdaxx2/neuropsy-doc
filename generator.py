import sys
import os
import json
import yaml
from docxtpl import DocxTemplate

def load_data(data_path):
    """Loads data from a JSON or YAML file."""
    with open(data_path, 'r', encoding='utf-8') as f:
        if data_path.endswith('.json'):
            return json.load(f)
        elif data_path.endswith('.yaml') or data_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            raise ValueError("Unsupported data file format. Use JSON or YAML.")

def generate_document(template_path, data_path, output_path):
    """Generates a Word document by filling the template with data."""
    if not os.path.exists(template_path):
        print(f"Error: Template file '{template_path}' not found.")
        sys.exit(1)
    
    if not os.path.exists(data_path):
        print(f"Error: Data file '{data_path}' not found.")
        sys.exit(1)

    try:
        print(f"Loading data from {data_path}...")
        data = load_data(data_path)
        
        print(f"Loading template from {template_path}...")
        doc = DocxTemplate(template_path)
        
        print("Rendering document...")
        doc.render(data)
        
        print(f"Saving to {output_path}...")
        doc.save(output_path)
        print(f"Successfully generated document: {output_path}")
    except Exception as e:
        print(f"Error generating document: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generator.py <template_path> <data_path> [output_path]")
        sys.exit(1)

    template_file = sys.argv[1]
    data_file = sys.argv[2]
    
    if len(sys.argv) >= 4:
        output_file = sys.argv[3]
    else:
        # Determine output filename automatically in 'output' directory
        base_name = os.path.splitext(os.path.basename(template_file))[0]
        output_filename = f"{base_name}_generated.docx"
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, output_filename)

    generate_document(template_file, data_file, output_file)

def get_identifiers_from_template(template_path):
    """
    Extracts jinja2 tags/variables from the docx template.
    Returns a set of unique keys.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
        
    doc = DocxTemplate(template_path)
    # create a dummy context to force parsing if needed, but get_undeclared covers it
    return doc.get_undeclared_template_variables()
