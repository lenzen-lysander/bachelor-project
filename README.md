# bachelor-project
This project automates the extraction of relevant values regarding statistical testing from scientific papers in both PDF and HTML formats. The goal is to streamline the statistical review process by automatically identifying and extracting key statistical data, making it easier for analysts to review and analyze the information without manually searching through the papers. The core functionality of this project relies on the ChatGPT API by OpenAI. By utilizing this API, the system processes the content of research papers and extracts the most pertinent statistical information.

## **Performance**
- **HTML Support**: High performance in extracting statistical values from HTML versions of papers.
- **PDF Support**: While less reliable than with HTML versions, PDF support still outperforms most open-source tools available for the same task.  

For more in-depth information, please consult **BachelorThesis.pdf**.

## **Usage**

**Disclaimer**: To use this project’s code, an API key for OpenAI is required.

To extract statistical values from scientific papers, provide the following data to **main.py**:
1. An API key from OpenAI.
2. The file path to the scientific paper (the file must end with either `.html` or `.pdf`).

Once this information is provided, you can execute **main.py**, and the relevant statistical information will be output in the console.

### **Customization**
The information to be extracted can be customized by adjusting the prompt given to the LLM (Language Learning Model). The prompts can be found and modified in **content_gpt.py** and **table_gpt.py**.
