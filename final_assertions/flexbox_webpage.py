import re

def get_assertion(response, context=None):
    """
    Promptfoo assertion function that evaluates HTML flexbox layout.
    """
    
    def extract_html_code(text):
        """Extract HTML code from the response"""
        # Remove language specifiers from code blocks
        text = re.sub('```[a-z]*', '```', text)
        
        if "```" in text:
            # Extract code from markdown code block
            parts = text.split("```")
            if len(parts) >= 2:
                return parts[1].strip()
        
        # If no code block, return the whole response
        return text.strip()

    def check_flexbox_properties(html_code):
        """Check if the HTML code contains required flexbox properties"""
        html_code = html_code.lower()
        
        # Required properties to check
        requirements = {
            'container': {
                'display: flex': False,
                'flex-direction': False,
            },
            'header': {
                'background': False,
                'red': False,
                'height': False
            },
            'sidebar': {
                'flex': False,
                'blue': False,
                'green': False,
                'width': False
            }
        }
        
        # Check for container properties
        if 'display: flex' in html_code or 'display:flex' in html_code:
            requirements['container']['display: flex'] = True
        if 'flex-direction' in html_code:
            requirements['container']['flex-direction'] = True
            
        # Check for header properties
        if 'background' in html_code and ('red' in html_code or '#ff' in html_code or 'rgb(255' in html_code):
            requirements['header']['background'] = True
            requirements['header']['red'] = True
        if 'height' in html_code:
            requirements['header']['height'] = True
            
        # Check for sidebar properties
        if 'flex' in html_code:
            requirements['sidebar']['flex'] = True
        if 'blue' in html_code or '#00f' in html_code or 'rgb(0,0,255)' in html_code:
            requirements['sidebar']['blue'] = True
        if 'green' in html_code or '#0f0' in html_code or 'rgb(0,255,0)' in html_code:
            requirements['sidebar']['green'] = True
        if 'width' in html_code:
            requirements['sidebar']['width'] = True
            
        # Check style tag exists
        has_style = '<style>' in html_code
        
        # Check flexbox structure
        has_container = 'class="container"' in html_code or 'id="container"' in html_code
        has_header = '<header' in html_code or 'class="header"' in html_code
        has_sidebars = ('class="sidebar"' in html_code or 
                       'class="left-sidebar"' in html_code or 
                       'class="right-sidebar"' in html_code)
        
        # Calculate score based on requirements
        total_requirements = sum(len(category) for category in requirements.values())
        met_requirements = sum(sum(props.values()) for props in requirements.values())
        
        # Additional structural requirements
        structure_requirements = [has_style, has_container, has_header, has_sidebars]
        total_requirements += len(structure_requirements)
        met_requirements += sum(1 for req in structure_requirements if req)
        
        score = met_requirements / total_requirements
        
        return {
            'score': score,
            'requirements': requirements,
            'structure': {
                'has_style': has_style,
                'has_container': has_container,
                'has_header': has_header,
                'has_sidebars': has_sidebars
            }
        }

    # Extract HTML code from response
    html_code = extract_html_code(response)
    
    if not html_code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No HTML code found in response'
        }
    
    # Check layout
    result = check_flexbox_properties(html_code)
    
    # Determine if the implementation passes minimum requirements
    min_score_to_pass = 0.8  # 80% of requirements must be met
    passes = result['score'] >= min_score_to_pass
    
    # Generate detailed reason
    missing_requirements = []
    for category, props in result['requirements'].items():
        for prop, met in props.items():
            if not met:
                missing_requirements.append(f"{category}: {prop}")
    
    for item, present in result['structure'].items():
        if not present:
            missing_requirements.append(f"Missing {item}")
    
    reason = "All requirements met" if passes else f"Missing requirements: {', '.join(missing_requirements)}"
    
    return {
        'pass': passes,
        'score': result['score'],
        'reason': reason
    }