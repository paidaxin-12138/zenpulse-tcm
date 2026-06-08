try:
    from langchain.prompts import ChatPromptTemplate
    print('Successfully imported from langchain.prompts')
except ImportError as e:
    print(f'Error importing from langchain.prompts: {e}')

try:
    from langchain_core.prompts import ChatPromptTemplate
    print('Successfully imported from langchain_core.prompts')
except ImportError as e:
    print(f'Error importing from langchain_core.prompts: {e}')

try:
    import langchain_core
    print(f'langchain_core version: {langchain_core.__version__}')
    print(f'langchain_core path: {langchain_core.__file__}')
except ImportError as e:
    print(f'Error importing langchain_core: {e}')