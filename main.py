from trafilatura import extract
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
import re

def html_to_xml(html_content: str):
    """
    Use trafilatura to extract xml content from html and return it as XML format.
    """
    xml_elements = extract(html_content,
                           output_format='xml',
                           include_links=False,
                           include_comments=False)
    return xml_elements


def xml_to_markdown(element, parent_node=None):
    """
    Convert xml element to markdown format.
    """
    markdown_content = ""
    if element.text is None:
        # to avoid NoneType error
        element.text = "\n"

    if element.tag == "doc":
        metadata = {key: element.attrib.get(key, '') for key in ['title', 'date', 'categories', 'tags']}
        markdown_content += f"# {metadata['title']}\n\nDate: {metadata['date']}\nCategories: {metadata['categories']}\nTags: {metadata['tags']}\n\n"

    elif element.tag == "head":
        rend_mapping = {'h1': '#', 'h2': '##', 'h3': '###'}
        rend = element.attrib.get('rend', '')
        symbol = rend_mapping.get(rend, '#')
        markdown_content += f"\n\n{symbol} {element.text.strip()}\n\n"

    elif element.tag == "p" or element.tag == "lb":
        # if have child, no \n\n
        if element.text:
            # there are spans, do not add \n before the text
            if len(element) >= 1:
                # traverse all elements
                markdown_content += element.text.strip()
            else:
                markdown_content += f"\n{element.text.strip()}\n\n"

    elif element.tag == "code" or element.tag == "pre":
        code_content = element.text.strip()
        # if code content is one line, then use inline code
        is_inline_code = '\n' not in code_content and len(code_content) <= 30
        # if the parent node is a paragraph, then we should use inline code
        if parent_node and parent_node.tag == "p":
            is_inline_code = True
        markdown_content += f"\n\n```\n{code_content}\n```\n\n" if not is_inline_code else f" `{code_content}` "

    elif element.tag == "table":
        try:
            markdown_content += "\n\n" + "| " + " | ".join(cell.text.strip() for cell in element.find("row").findall("cell")) + " |\n"
            markdown_content += "| --- " * len(element.find("row").findall("cell")) + " |\n"
            for row in element.findall("row")[1:]:
                markdown_content += "| " + " | ".join(cell.text.strip() for cell in row.findall("cell")) + " |\n"
            markdown_content += "\n\n"
        except:
            markdown_content += f"\n{ET.tostring(element, encoding='unicode', method='text').strip()}\n"

    elif element.tag == "list":
        markdown_content += "\n\n"

    elif element.tag == "item":
        markdown_content += f"* {element.text.strip()}\n"

    elif element.tag == "main":
        markdown_content += element.text.strip()

    elif element.tag == "quote":
        markdown_content += f"> {element.text.strip()}\n"
    
    elif element.tag == "del":
        markdown_content += f"~~{element.text.strip()}~~\n"

    else:
        # directly take the text
        markdown_content += f"{ET.tostring(element, encoding='unicode', method='text').strip()}\n"
        if element.tag not in ["div", "row", "cell", "lb", "th", "td", "t", "unnamed"]:
            print(markdown_content[:100])
            # raise Exception("Unknown tag ", element.tag)
            print("Unknown tag ", element.tag)

    if element.tag != "table":
        child_elements = [xml_to_markdown(child, element) for child in element]
        markdown_content += "".join(child_elements)
        
    if element.tail:
        # the remaining part in a paragraph
        markdown_content += element.tail.strip()

    return markdown_content


def post_processing(markdown_content: str):
    """
    Post processing to remove extra spaces and new lines.
    """
    lines = [line for line in markdown_content.split("\n")]
    # if this line matches spaces, then replace with ""
    lines = [re.sub(r"^\s+$", "", line) for line in lines]
    markdown_content = "\n".join(lines)
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
    # replace ` .` with `.
    markdown_content = re.sub(r"` \.", "`.", markdown_content)
    markdown_content = re.sub(r"` \,", "`,", markdown_content)
    return markdown_content.strip()


def code_html_to_markdown(html_content: str):
    """
    Convert html code block to markdown code block.
    """
    xml_elements = html_to_xml(html_content)
    xml_elements = ET.fromstring(xml_elements)
    markdown_content = xml_to_markdown(xml_elements)
    markdown_content = post_processing(markdown_content)
    return markdown_content


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", type=str, default="demo.html", help="Input html file path")
    parser.add_argument("--output", type=str, default="demo.md", help="Output markdown file path")
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        html_content = f.read()

    markdown_content = code_html_to_markdown(html_content)
    
    with open(args.output, 'w') as f:
        f.write(markdown_content)